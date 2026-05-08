"""Train the alert classifier.

Run:  python -m app.ml.train

Generates a synthetic labeled dataset, trains an XGBoost binary classifier,
prints precision/recall/F1/confusion matrix, and saves to ML_MODEL_PATH.
"""
from __future__ import annotations

import os
from pathlib import Path

import joblib
import numpy as np
from sklearn.metrics import (
    classification_report, confusion_matrix, precision_recall_fscore_support
)
from sklearn.model_selection import train_test_split
import xgboost as xgb

from app.core.config import settings
from app.ml.features import alerts_to_dataframe, FEATURE_NAMES
from app.ml.synthetic import generate_dataset


LABEL_TO_INT = {"false_positive": 0, "threat": 1}
INT_TO_LABEL = {v: k for k, v in LABEL_TO_INT.items()}


def main() -> None:
    print(">>> Generating synthetic training data...")
    data = generate_dataset(n_threats=2000, n_fp=2000)
    X = alerts_to_dataframe(data)
    y = np.array([LABEL_TO_INT[d["label"]] for d in data])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(">>> Training XGBoost classifier...")
    model = xgb.XGBClassifier(
        n_estimators=300,
        max_depth=6,
        learning_rate=0.08,
        subsample=0.9,
        colsample_bytree=0.9,
        eval_metric="logloss",
        tree_method="hist",
        n_jobs=-1,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    print("\n>>> Classification report:\n")
    print(classification_report(y_test, y_pred, target_names=["false_positive", "threat"]))
    p, r, f1, _ = precision_recall_fscore_support(y_test, y_pred, average="binary", pos_label=1)
    print(f"Precision: {p:.4f}  Recall: {r:.4f}  F1: {f1:.4f}")
    print(">>> Confusion matrix (rows=true, cols=pred):")
    print(confusion_matrix(y_test, y_pred))

    out_path = Path(settings.ML_MODEL_PATH)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "model": model,
        "feature_names": FEATURE_NAMES,
        "label_map": INT_TO_LABEL,
        "version": "v1",
    }
    joblib.dump(bundle, out_path)
    print(f"\n>>> Saved model bundle to {out_path}")


if __name__ == "__main__":
    main()
