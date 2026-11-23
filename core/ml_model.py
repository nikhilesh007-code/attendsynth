"""
Machine Learning Model Training & Evaluation Engine for AttendSynth AI.
Implements Scikit-learn Random Forest and Decision Tree classifiers for synthetic risk benchmarking.
"""

from typing import Dict, Any
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix


class AcademicMLBenchmarker:
    """Trains and benchmarks transparent ML models on synthetic academic features."""

    FEATURE_COLS = [
        "attendance_pct",
        "participation_score",
        "assignment_completion_pct",
        "lms_logins_per_week",
        "avg_marks",
        "late_submissions",
    ]

    @classmethod
    def train_and_evaluate(
        cls,
        df: pd.DataFrame,
        model_type: str = "Random Forest",
        test_size: float = 0.25,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Trains model to predict High Risk Status (binary target: 1 = High Risk, 0 = Non-High).
        Evaluates precision, recall, accuracy, F1, and feature importances.
        """
        if df.empty or len(df) < 30:
            return {"error": "Dataset must contain at least 30 students to train an ML model."}

        # Features & Target
        X = df[cls.FEATURE_COLS].copy()
        # Binary target: High Risk learner (1) vs Low/Medium (0)
        y = (df["risk_level"] == "High").astype(int)

        # Check for class balance in sample
        if y.nunique() < 2:
            return {
                "error": "The current dataset does not contain both High-Risk and Low-Risk students. "
                         "Please regenerate data with the 'Balanced engagement' or 'At-risk-heavy' profile."
            }

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        if model_type == "Decision Tree":
            model = DecisionTreeClassifier(max_depth=5, random_state=random_state)
        else:
            model = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=random_state)

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))

        cm = confusion_matrix(y_test, y_pred).tolist()

        # Feature importances
        importances = model.feature_importances_
        fi_list = [
            {"feature": col, "importance": round(float(imp), 4), "percentage": round(float(imp) * 100.0, 1)}
            for col, imp in zip(cls.FEATURE_COLS, importances)
        ]
        fi_list.sort(key=lambda x: x["importance"], reverse=True)

        return {
            "model_type": model_type,
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "confusion_matrix": cm,
            "feature_importances": fi_list,
            "disclaimer": (
                "Notice: This model was trained purely on synthetic educational distributions for demonstration "
                "and prototyping purposes. Accuracy on synthetic data must not be interpreted as evidence of "
                "real-world diagnostic validity."
            ),
        }
