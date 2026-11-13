"""Machine Learning Early-Warning System (EWS) modeling pipeline."""

from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


FEATURE_NAMES = [
    "early_attendance_rate",
    "early_tardy_rate",
    "early_unexcused_rate",
    "early_avg_daily_lms_minutes",
    "early_lms_trend_decay",
    "early_submission_rate",
    "early_quiz_average",
    "baseline_gpa",
]


class EarlyWarningPredictor:
    """Trains and evaluates predictive early-warning models on synthetic cohort data."""

    def __init__(self, model_type: str = "random_forest", observation_weeks: int = 6):
        self.model_type = model_type
        self.observation_weeks = observation_weeks
        self.scaler = StandardScaler()
        self.feature_names = FEATURE_NAMES
        
        if model_type == "gradient_boosting":
            self.clf = GradientBoostingClassifier(n_estimators=100, max_depth=3, random_state=42)
        elif model_type == "logistic_regression":
            self.clf = LogisticRegression(random_state=42, max_iter=500)
        else:
            self.clf = RandomForestClassifier(n_estimators=100, max_depth=5, random_state=42)
            
        self.is_trained = False
        self.evaluation_metrics: Dict[str, Any] = {}

    def extract_features_and_targets(
        self, cohort_data: Dict[str, Any]
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """Extracts early-window engagement features and full-term risk outcome targets."""
        students = cohort_data.get("students", [])
        daily_records = cohort_data.get("daily_records", [])

        # Group daily records by student_id
        records_by_student: Dict[str, List[Dict[str, Any]]] = {}
        for r in daily_records:
            stu_id = r["student_id"]
            if stu_id not in records_by_student:
                records_by_student[stu_id] = []
            records_by_student[stu_id].append(r)

        X_rows = []
        y_targets = []
        student_ids = []

        obs_days = self.observation_weeks * 5  # 5 days per school week

        for s in students:
            stu_id = s["student_id"]
            records = records_by_student.get(stu_id, [])
            
            # Slice early observation window
            early_records = [r for r in records if r["day_index"] < obs_days]
            if not early_records:
                continue

            n_days = len(early_records)
            p_count = sum(1 for r in early_records if r["attendance_status"] == "PRESENT")
            t_count = sum(1 for r in early_records if r["attendance_status"] == "TARDY")
            u_count = sum(1 for r in early_records if r["attendance_status"] == "UNEXCUSED_ABSENCE")

            early_att_rate = (p_count + t_count) / max(1, n_days)
            early_tardy_rate = t_count / max(1, n_days)
            early_unexcused_rate = u_count / max(1, n_days)

            lms_minutes_list = [r["lms_active_minutes"] for r in early_records]
            early_lms_mean = float(np.mean(lms_minutes_list)) if lms_minutes_list else 0.0

            # Trend decay: compare second half of early window to first half
            half = max(1, n_days // 2)
            first_half_lms = float(np.mean(lms_minutes_list[:half])) if lms_minutes_list[:half] else 1.0
            second_half_lms = float(np.mean(lms_minutes_list[half:])) if lms_minutes_list[half:] else 1.0
            early_lms_trend_decay = float(np.clip((first_half_lms - second_half_lms) / max(1.0, first_half_lms), -1.0, 1.0))

            subs_due = sum(1 for r in early_records if r.get("assignment_due"))
            subs_done = sum(1 for r in early_records if r.get("submission_status") in ["ON_TIME", "LATE"])
            early_sub_rate = subs_done / max(1, subs_due)

            quizzes = [r["quiz_score"] for r in early_records if r.get("quiz_score") is not None]
            early_quiz_avg = float(np.mean(quizzes)) if quizzes else 75.0

            baseline_gpa = float(s.get("baseline_gpa", 3.0))

            features = [
                early_att_rate,
                early_tardy_rate,
                early_unexcused_rate,
                early_lms_mean,
                early_lms_trend_decay,
                early_sub_rate,
                early_quiz_avg,
                baseline_gpa,
            ]

            # Target: whether student reached Chronic Absenteeism (absence >= 10% across whole semester)
            target = 1 if s.get("chronic_absenteeism_flag", False) else 0

            X_rows.append(features)
            y_targets.append(target)
            student_ids.append(stu_id)

        return np.array(X_rows), np.array(y_targets), student_ids

    def train_and_evaluate(self, cohort_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trains the early-warning model and outputs detailed evaluation metrics."""
        X, y, student_ids = self.extract_features_and_targets(cohort_data)

        if len(y) < 20:
            return {"error": "Insufficient student sample size for training"}

        # Check class balance
        pos_count = int(np.sum(y))
        neg_count = len(y) - pos_count
        if pos_count == 0 or neg_count == 0:
            return {"error": "Target contains only one class in the cohort"}

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.25, random_state=42, stratify=y
        )

        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        self.clf.fit(X_train_scaled, y_train)
        self.is_trained = True

        # Predictions & Probabilities
        y_pred = self.clf.predict(X_test_scaled)
        y_prob = self.clf.predict_proba(X_test_scaled)[:, 1]

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred, zero_division=0))
        f1 = float(f1_score(y_test, y_pred, zero_division=0))
        auc = float(roc_auc_score(y_test, y_prob))

        # Confusion Matrix
        cm = confusion_matrix(y_test, y_pred).tolist()

        # ROC Curve points
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_points = [
            {"fpr": round(float(f), 4), "tpr": round(float(t), 4)}
            for f, t in zip(fpr, tpr)
        ]

        # Feature Importances
        if hasattr(self.clf, "feature_importances_"):
            importances = self.clf.feature_importances_
        else:
            importances = np.abs(self.clf.coef_[0])
            importances = importances / np.sum(importances)

        feature_importance_list = [
            {"feature": name, "importance": round(float(imp), 4)}
            for name, imp in sorted(zip(self.feature_names, importances), key=lambda x: x[1], reverse=True)
        ]

        self.evaluation_metrics = {
            "model_type": self.model_type,
            "observation_weeks": self.observation_weeks,
            "train_samples": len(y_train),
            "test_samples": len(y_test),
            "target_positive_samples": pos_count,
            "target_negative_samples": neg_count,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(auc, 4),
            "confusion_matrix": {
                "true_negative": cm[0][0],
                "false_positive": cm[0][1],
                "false_negative": cm[1][0],
                "true_positive": cm[1][1],
            },
            "roc_curve": roc_points,
            "feature_importances": feature_importance_list,
        }

        return self.evaluation_metrics

    def predict_risk(self, feature_dict: Dict[str, float]) -> Dict[str, Any]:
        """Inference endpoint to evaluate student risk given early indicators."""
        if not self.is_trained:
            raise ValueError("Model has not been trained yet.")

        vec = np.array([[feature_dict.get(fn, 0.0) for fn in self.feature_names]])
        vec_scaled = self.scaler.transform(vec)
        prob = float(self.clf.predict_proba(vec_scaled)[0, 1])

        if prob >= 0.70:
            level = "CRITICAL"
            action = "Immediate Multi-Tiered Support & Counselor Meeting"
        elif prob >= 0.45:
            level = "ELEVATED"
            action = "Targeted Academic Tutoring & Weekly Check-In"
        elif prob >= 0.25:
            level = "MODERATE"
            action = "Automated Attendance SMS Nudge to Guardian"
        else:
            level = "LOW"
            action = "Standard Academic Progress Monitoring"

        return {
            "predicted_risk_probability": round(prob, 4),
            "predicted_risk_tier": level,
            "recommended_action": action,
            "confidence": round(max(prob, 1.0 - prob), 3),
        }

