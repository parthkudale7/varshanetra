"""
Stage 4 of the roadmap - first real trained models. Nothing clever
yet, just: can a Random Forest learn the two targets at all.

Model A: rain_category_next   (light/moderate/heavy/extreme)
Model B: flood_risk_future    (safe/watch/warning/danger)
"""

import json
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, recall_score, classification_report

from features import build_feature_table, chronological_split, ALL_COLS

MODEL_DIR = Path("models")
MODEL_DIR.mkdir(exist_ok=True)


def train_one(train_df, test_df, target, feature_cols, name, critical_class):
    X_train, y_train = train_df[feature_cols], train_df[target]
    X_test, y_test = test_df[feature_cols], test_df[target]

    clf = RandomForestClassifier(
        n_estimators=150, max_depth=9, min_samples_leaf=8,
        class_weight="balanced", random_state=7, n_jobs=-1,
    )
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    acc = accuracy_score(y_test, preds)
    # for an alert system, recall on the worst class matters more than
    # overall accuracy - missing a real "danger" reading is the costly
    # mistake, not flagging one extra false alarm
    recall_worst = recall_score(y_test, preds, labels=[critical_class], average="macro", zero_division=0)

    print(f"\n{name}")
    print(f"  accuracy: {acc:.3f}")
    print(f"  recall on '{critical_class}': {recall_worst:.3f}")
    print(classification_report(y_test, preds, zero_division=0))

    joblib.dump(clf, MODEL_DIR / f"{name}_rf.joblib")
    return {"accuracy": acc, f"recall_{critical_class}": recall_worst}


def main():
    df = build_feature_table()
    train_df, val_df, test_df = chronological_split(df)

    metrics = {}
    metrics["model_a_rf"] = train_one(
        train_df, test_df, "rain_category_next", ALL_COLS, "model_a", critical_class="extreme"
    )
    metrics["model_b_rf"] = train_one(
        train_df, test_df, "flood_risk_future", ALL_COLS, "model_b", critical_class="danger"
    )

    Path("reports").mkdir(exist_ok=True)
    with open("reports/baseline_metrics.json", "w") as f:
        json.dump(metrics, f, indent=2)


if __name__ == "__main__":
    main()
