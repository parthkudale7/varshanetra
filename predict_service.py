"""
The actual "given rainfall + a ward, what's the risk" logic, kept
independent of FastAPI so it can be unit-tested/run directly (this
sandbox can't install fastapi - no internet - but this file has no
fastapi import in it, so it runs fine here and in api/main.py alike).
"""

import joblib
import pandas as pd
from pathlib import Path

from features import add_engineered_features, RAW_COLS, ALL_COLS
from data.wards import load_wards
from explain import build_explainer

MODEL_DIR = Path("models")

_wards_df = load_wards().set_index("ward")
_model_a = None
_model_b = None
_explainer_b = None


def _load_models():
    global _model_a, _model_b, _explainer_b
    if _model_a is not None:
        return
    a_path = MODEL_DIR / "model_a_boosted.joblib"
    b_path = MODEL_DIR / "model_b_boosted.joblib"
    if not a_path.exists() or not b_path.exists():
        raise RuntimeError("models not trained yet - run train_baseline.py then train_boosted.py first")
    _model_a = joblib.load(a_path)
    _model_b = joblib.load(b_path)

    # the explainer needs a real validation set to judge "how unusual is
    # this value" against (see explain.py) - build it once at load time,
    # not per-request, both for speed and because a single row isn't
    # enough data for permutation importance to mean anything
    from features import build_feature_table, chronological_split
    df = build_feature_table()
    _, val_df, _ = chronological_split(df)
    b_model, b_enc, b_feats = _model_b["model"], _model_b["encoder"], _model_b["features"]
    explain_one, method = build_explainer(
        b_model, val_df[b_feats], b_enc.transform(val_df["flood_risk_future"]), b_feats
    )
    _explainer_b = (explain_one, method)


def _row_from_history(ward: str, history: pd.DataFrame) -> pd.Series:
    """
    history: dataframe of the last several 3h readings for one ward,
    columns = ['timestamp', 'rain_mm'], most recent last.
    """
    w = _wards_df.loc[ward]
    rain_3h = history["rain_mm"].iloc[-1]
    rain_6h = history["rain_mm"].iloc[-2:].sum()
    rain_24h = history["rain_mm"].iloc[-8:].sum()
    prev_rain_3h = history["rain_mm"].iloc[-2] if len(history) >= 2 else 0.0

    row = pd.Series({
        "ward": ward,
        "rain_3h": rain_3h,
        "rain_6h": rain_6h,
        "rain_24h": rain_24h,
        "elevation_m": w.elevation_m,
        "slope_deg": w.slope_deg,
        "dist_river_km": w.dist_river_km,
        "drainage_quality": w.drainage_quality,
    })
    row["rain_trend"] = rain_3h - prev_rain_3h
    ward_avg_24h = history["rain_mm"].rolling(8, min_periods=1).sum().mean()
    row["rain24_anomaly"] = rain_24h / (ward_avg_24h or 1)
    row["runoff_pressure"] = rain_6h * (1 - w.drainage_quality) / (w.slope_deg + 0.5)
    row["river_pressure"] = rain_24h / (w.dist_river_km + 0.5)
    return row


def predict(ward: str, history: pd.DataFrame) -> dict:
    """
    Main entry point. history is at least 24h (8 rows) of 3-hourly
    rain_mm readings for `ward`, oldest first. Returns rainfall
    outlook, flood risk, and the top factors behind the flood call.
    """
    _load_models()
    row = _row_from_history(ward, history)

    a_model, a_enc, a_feats = _model_a["model"], _model_a["encoder"], _model_a["features"]
    b_model, b_enc, b_feats = _model_b["model"], _model_b["encoder"], _model_b["features"]

    a_pred_idx = a_model.predict(row[a_feats].to_frame().T.astype(float))[0]
    a_label = a_enc.inverse_transform([a_pred_idx])[0]
    a_conf = float(a_model.predict_proba(row[a_feats].to_frame().T.astype(float)).max())

    b_pred_idx = b_model.predict(row[b_feats].to_frame().T.astype(float))[0]
    b_label = b_enc.inverse_transform([b_pred_idx])[0]
    b_conf = float(b_model.predict_proba(row[b_feats].to_frame().T.astype(float)).max())

    explain_one, method = _explainer_b
    top_factors = explain_one(row, b_pred_idx)[:3]

    return {
        "ward": ward,
        "rainfall_outlook": {"category": a_label, "confidence": round(a_conf, 3)},
        "flood_risk": {"level": b_label, "confidence": round(b_conf, 3)},
        "why": [
            {"feature": f, "effect": "raises" if v > 0 else "lowers"}
            for f, v in top_factors
        ],
        "explanation_method": method,
    }
