"""
Two small, cheap-to-compute JSON exports the dashboard's extra views
need, on top of reports/demo_feed.json:

- historical_summary.json: per-ward danger-rate over the FULL 3-season
  synthetic dataset (not just the 10-day demo window), plus
  season-level rainfall totals.
- feature_importance.json: model_b's built-in feature_importances_,
  for the Risk Analysis view - not SHAP, just what the model itself
  reports as most-used, which is a legitimate and much cheaper signal.
"""

import json
import joblib
import pandas as pd
from pathlib import Path

from data.make_dataset import load_or_build
from features import ALL_COLS

df = load_or_build()

by_ward = (
    df.groupby("ward")["flood_risk_future"]
    .value_counts(normalize=True)
    .unstack(fill_value=0)
    .reindex(columns=["safe", "watch", "warning", "danger"], fill_value=0)
)
ward_summary = [
    {"ward": w, **{lvl: round(float(by_ward.loc[w, lvl]) * 100, 2) for lvl in by_ward.columns}}
    for w in by_ward.index
]
ward_summary.sort(key=lambda r: r["danger"], reverse=True)

df["season"] = df["timestamp"].dt.year
season_totals = (
    df.groupby("season")["rain_mm"].sum().round(0).astype(int).to_dict()
)

Path("reports/historical_summary.json").write_text(json.dumps({
    "ward_risk_rates_pct": ward_summary,
    "season_total_rainfall_mm": {str(k): v for k, v in season_totals.items()},
    "rows_in_training_data": len(df),
}))

payload = joblib.load("models/model_b_rf.joblib")
if hasattr(payload, "feature_importances_"):
    imp = sorted(zip(ALL_COLS, payload.feature_importances_.tolist()), key=lambda x: -x[1])
    Path("reports/feature_importance.json").write_text(json.dumps(
        [{"feature": f, "importance": round(v, 4)} for f, v in imp]
    ))
    print("feature importances:", imp[:3])
else:
    Path("reports/feature_importance.json").write_text("[]")
    print("model has no feature_importances_ (unexpected for this engine)")

print("historical summary:", ward_summary[:3])
