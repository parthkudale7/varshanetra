"""
Stage 6 of the roadmap - does the extra feature engineering
(runoff_pressure, river_pressure, etc, from features.py) actually earn
its place, or is it just noise? Retrains model_b twice, same split,
same model type, only the feature list differs.
"""

import json
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, recall_score, f1_score

from features import build_feature_table, chronological_split, RAW_COLS, ALL_COLS


def score(train_df, test_df, feature_cols, target, critical_class):
    clf = RandomForestClassifier(
        n_estimators=150, max_depth=9, min_samples_leaf=8,
        class_weight="balanced", random_state=7, n_jobs=-1,
    )
    clf.fit(train_df[feature_cols], train_df[target])
    preds = clf.predict(test_df[feature_cols])
    y_test = test_df[target]

    return {
        "accuracy": accuracy_score(y_test, preds),
        "f1_macro": f1_score(y_test, preds, average="macro", zero_division=0),
        f"recall_{critical_class}": recall_score(y_test, preds, labels=[critical_class], average="macro", zero_division=0),
    }


def run_ablation(train_df, test_df, target, critical_class, label):
    raw_result = score(train_df, test_df, RAW_COLS, target, critical_class)
    full_result = score(train_df, test_df, ALL_COLS, target, critical_class)

    print(f"\n{label} - raw columns only:")
    for k, v in raw_result.items():
        print(f"  {k}: {v:.3f}")
    print(f"{label} - with engineered features:")
    for k, v in full_result.items():
        print(f"  {k}: {v:.3f}")

    delta = {k: full_result[k] - raw_result[k] for k in raw_result}
    print(f"{label} - delta (full - raw):")
    for k, v in delta.items():
        print(f"  {k}: {v:+.3f}")

    return {"raw_only": raw_result, "with_engineered": full_result, "delta": delta}


def main():
    df = build_feature_table()
    train_df, val_df, test_df = chronological_split(df)

    results = {
        "model_b_flood_risk": run_ablation(train_df, test_df, "flood_risk_future", "danger", "model_b"),
        "model_a_rain_category": run_ablation(train_df, test_df, "rain_category_next", "extreme", "model_a"),
    }

    with open("reports/ablation.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
