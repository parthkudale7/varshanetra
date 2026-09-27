"""
Stage 5's "why did it say that" piece. Tries shap.TreeExplainer first;
if shap isn't installed (true in this sandbox - no internet to pip
install it) it falls back to a simpler local explanation built from
permutation importance and how far each feature sits from the ward's
usual range. It's not a real Shapley value, so don't call it SHAP in
your report if you end up shipping the fallback - call it what it is,
a feature-contribution estimate. Swap in real shap.TreeExplainer the
moment `pip install shap` works on your machine; explain_one() below
is the only function the API calls, so nothing else changes.
"""

import numpy as np
import pandas as pd
import joblib
from sklearn.inspection import permutation_importance

from features import build_feature_table, chronological_split, ALL_COLS

try:
    import shap
    HAVE_SHAP = True
except ImportError:
    HAVE_SHAP = False


def _fallback_importances(model, X_val, y_val, feature_cols):
    result = permutation_importance(
        model, X_val, y_val, n_repeats=8, random_state=7, n_jobs=-1
    )
    imp = pd.Series(result.importances_mean, index=feature_cols)
    return imp.clip(lower=0)


def build_explainer(model, X_val, y_val, feature_cols):
    """
    Returns a function(row) -> list of (feature, contribution) sorted
    by |contribution| descending, most-responsible feature first.
    """
    if HAVE_SHAP:
        explainer = shap.TreeExplainer(model)

        def explain_one(row: pd.Series, predicted_class_idx: int):
            feat_row = row[feature_cols].astype(float)
            sv = explainer.shap_values(feat_row.to_frame().T)
            if isinstance(sv, list):
                # older shap: list of arrays, one per class
                values = sv[predicted_class_idx][0]
            elif sv.ndim == 3:
                # newer shap: shape (1, n_features, n_classes)
                values = sv[0, :, predicted_class_idx]
            else:
                values = sv[0]
            pairs = list(zip(feature_cols, values.tolist()))
            return sorted(pairs, key=lambda p: abs(p[1]), reverse=True)

        return explain_one, "shap"

    importances = _fallback_importances(model, X_val, y_val, feature_cols)
    feature_mean = X_val.mean()
    feature_std = X_val.std().replace(0, 1)

    def explain_one(row: pd.Series, predicted_class_idx: int = None):
        # how unusual is this feature for this row, times how much the
        # model generally relies on that feature - a rough stand-in for
        # a per-prediction contribution, not a true Shapley value
        feat_row = row[feature_cols].astype(float)
        z = (feat_row - feature_mean) / feature_std
        contrib = z * importances
        pairs = list(zip(feature_cols, contrib.values))
        return sorted(pairs, key=lambda p: abs(p[1]), reverse=True)

    return explain_one, "permutation_fallback"


def demo():
    df = build_feature_table()
    train_df, val_df, test_df = chronological_split(df)

    payload = joblib.load("models/model_b_boosted.joblib")
    model, encoder, feature_cols = payload["model"], payload["encoder"], payload["features"]

    explain_one, method = build_explainer(
        model, val_df[feature_cols], encoder.transform(val_df["flood_risk_future"]), feature_cols
    )
    print(f"explanation method: {method}\n")

    # pick a real 'danger' row from the test set to explain
    danger_rows = test_df[test_df.flood_risk_future == "danger"]
    row = danger_rows.iloc[0]
    pred_idx = model.predict(row[feature_cols].to_frame().T.astype(float))[0]
    pred_label = encoder.inverse_transform([pred_idx])[0]

    print(f"ward: {row.ward}   timestamp: {row.timestamp}")
    print(f"actual label: {row.flood_risk_future}   predicted: {pred_label}\n")

    top = explain_one(row, pred_idx)[:5]
    print("top contributing factors:")
    for feat, val in top:
        direction = "raises" if val > 0 else "lowers"
        print(f"  {feat:20s} {direction} risk   (value={row[feat]:.2f}, weight={val:+.3f})")


if __name__ == "__main__":
    demo()
