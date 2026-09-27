"""
Stage 5 of the roadmap. Tries real XGBoost first; this sandbox has no
internet so it won't be installed here, and falls back to sklearn's
HistGradientBoostingClassifier - same family of model (gradient-
boosted trees), same interface for fit/predict/predict_proba.

On your own machine, `pip install xgboost` and this will pick it up
automatically - nothing else in the file needs to change.
"""

import json
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score, recall_score, classification_report
from sklearn.preprocessing import LabelEncoder

from features import build_feature_table, chronological_split, ALL_COLS

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)

try:
    from xgboost import XGBClassifier
    ENGINE = "xgboost"
except ImportError:
    from sklearn.ensemble import HistGradientBoostingClassifier
    ENGINE = "sklearn-hgb"


def make_classifier():
    if ENGINE == "xgboost":
        return XGBClassifier(
            n_estimators=350, max_depth=6, learning_rate=0.06,
            subsample=0.85, colsample_bytree=0.85,
            eval_metric="mlogloss", random_state=7,
        )
    return HistGradientBoostingClassifier(
        max_iter=350, max_depth=6, learning_rate=0.06, class_weight="balanced", random_state=7,
    )


def train_one(train_df, test_df, target, feature_cols, name, critical_class):
    X_train, y_train_raw = train_df[feature_cols], train_df[target]
    X_test, y_test_raw = test_df[feature_cols], test_df[target]

    # xgboost wants integer labels, sklearn's HGB is fine with strings -
    # encode either way so this file behaves the same on both engines
    enc = LabelEncoder()
    y_train = enc.fit_transform(y_train_raw)
    y_test = enc.transform(y_test_raw)

    clf = make_classifier()
    clf.fit(X_train, y_train)

    preds_enc = clf.predict(X_test)
    preds = enc.inverse_transform(preds_enc)

    acc = accuracy_score(y_test_raw, preds)
    recall_worst = recall_score(y_test_raw, preds, labels=[critical_class], average="macro", zero_division=0)

    print(f"\n{name}  [{ENGINE}]")
    print(f"  accuracy: {acc:.3f}")
    print(f"  recall on '{critical_class}': {recall_worst:.3f}")
    print(classification_report(y_test_raw, preds, zero_division=0))

    joblib.dump({"model": clf, "encoder": enc, "features": feature_cols}, MODEL_DIR / f"{name}_boosted.joblib")
    return {"engine": ENGINE, "accuracy": acc, f"recall_{critical_class}": recall_worst}


def main():
    df = build_feature_table()
    train_df, val_df, test_df = chronological_split(df)

    metrics = {}
    metrics["model_a_boosted"] = train_one(
        train_df, test_df, "rain_category_next", ALL_COLS, "model_a", critical_class="extreme"
    )
    metrics["model_b_boosted"] = train_one(
        train_df, test_df, "flood_risk_future", ALL_COLS, "model_b", critical_class="danger"
    )

    baseline = json.load(open("reports/baseline_metrics.json")) if Path("reports/baseline_metrics.json").exists() else {}
    print("\nbaseline (RF) vs boosted, on the same test set:")
    for key, boosted_key in [("model_a_rf", "model_a_boosted"), ("model_b_rf", "model_b_boosted")]:
        if key in baseline:
            b_acc = baseline[key]["accuracy"]
            u_acc = metrics[boosted_key]["accuracy"]
            print(f"  {key}: {b_acc:.3f} -> {u_acc:.3f}  ({u_acc - b_acc:+.3f})")

    with open("reports/boosted_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
