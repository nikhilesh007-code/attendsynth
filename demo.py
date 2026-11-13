"""AttendSynth AI: End-to-End Demonstration Script.

Demonstrates:
1. Synthetic longitudinal student engagement & attendance cohort generation
2. Educational privacy audit (Zero-PII verification & k-anonymity)
3. Statistical fidelity evaluation against educational research benchmarks
4. Early Warning System (EWS) model training & feature importance analysis
5. Real-time predictive risk scoring
6. What-If policy intervention simulation
7. Ed-Fi standard export
"""

import json
import os
from attendsynth.config import Presets
from attendsynth.generator import AttendSynthGenerator
from attendsynth.privacy import PrivacyAuditor, DifferentialPrivacyEngine
from attendsynth.metrics import FidelityEvaluator
from attendsynth.models.early_warning import EarlyWarningPredictor
from attendsynth.simulator import PolicySimulator
from attendsynth.export import DataExporter


def run_demo():
    print("=" * 70)
    print("🎓 ATTENDSYNTH AI: SYNTHETIC STUDENT ENGAGEMENT GENERATOR")
    print("=" * 70)

    os.makedirs("data", exist_ok=True)

    # 1. Generate Synthetic Cohort
    print("\n[Step 1] Synthesizing student cohort...")
    config = Presets.standard_district(num_students=200, seed=42)
    generator = AttendSynthGenerator(config)
    cohort = generator.generate()

    summary = cohort["summary"]
    print(f"✓ Generated {summary['total_students']} students over {summary['total_school_days']} school days.")
    print(f"  • Average Attendance Rate:   {summary['average_attendance_rate'] * 100:.1f}%")
    print(f"  • Chronic Absenteeism Rate: {summary['chronic_absenteeism_rate'] * 100:.1f}% ({summary['chronic_absenteeism_count']} students)")
    print(f"  • Mean Daily LMS Minutes:   {summary['average_daily_lms_minutes']:.1f} mins/day")
    print(f"  • EWS Flagged Early:        {summary['early_warning_flagged_pct'] * 100:.1f}% with ~{summary['average_early_warning_lead_time_days']:.0f} days lead time")

    # 2. Privacy Audit
    print("\n[Step 2] Running Privacy Audit (FERPA & k-Anonymity)...")
    auditor = PrivacyAuditor(k_threshold=5)
    priv_report = auditor.audit_cohort(cohort["students"])
    print(f"✓ Zero PII Verification:      {'PASSED ✓' if priv_report['zero_pii_check']['is_compliant'] else 'FAILED'}")
    print(f"✓ k-Anonymity Compliance:     {priv_report['k_anonymity']['protected_student_ratio'] * 100:.1f}% students meet k=5")
    print(f"✓ Privacy Rating:             {priv_report['privacy_rating']}")

    dp_engine = DifferentialPrivacyEngine(epsilon=1.0)
    dp_summary = dp_engine.privatize_summary(summary, len(cohort["students"]))
    print(f"✓ Differential Privacy (ε=1): Raw Chronic Count = {summary['chronic_absenteeism_count']} -> DP Noisy Count = {dp_summary['chronic_absenteeism_count']}")

    # 3. Statistical Fidelity Evaluation
    print("\n[Step 3] Evaluating Statistical Fidelity...")
    evaluator = FidelityEvaluator()
    fid_report = evaluator.evaluate(cohort["students"])
    print(f"✓ Synthetic Quality Score:    {fid_report['synthetic_quality_score']}/100 ({fid_report['quality_grade']})")
    print(f"✓ Attendance KS-Test:         Statistic = {fid_report['ks_tests']['attendance_rate']['statistic']} (Passed: {fid_report['ks_tests']['attendance_rate']['passed']})")
    print(f"✓ LMS Telemetry KS-Test:      Statistic = {fid_report['ks_tests']['lms_active_minutes']['statistic']} (Passed: {fid_report['ks_tests']['lms_active_minutes']['passed']})")
    print(f"✓ Attendance Status JSD:      {fid_report['jensen_shannon_divergence']['attendance_distribution_jsd']}")

    # 4. Train Early Warning ML Model
    print("\n[Step 4] Training Early Warning System (EWS) Predictor...")
    print("  • Feature Window: First 6 weeks")
    print("  • Target Outcome: End-of-Semester Chronic Absenteeism (>= 10% missed)")
    predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
    ml_metrics = predictor.train_and_evaluate(cohort)
    print(f"✓ Model Trained Successfully!")
    print(f"  • ROC-AUC Score: {ml_metrics['roc_auc']:.4f}")
    print(f"  • Accuracy:      {ml_metrics['accuracy'] * 100:.1f}%")
    print(f"  • Precision:     {ml_metrics['precision']:.4f}")
    print(f"  • Recall:        {ml_metrics['recall']:.4f}")
    print(f"  • F1 Score:      {ml_metrics['f1_score']:.4f}")
    print("  • Top 3 Leading Predictive Signals:")
    for feat in ml_metrics["feature_importances"][:3]:
        print(f"    - {feat['feature']}: {feat['importance'] * 100:.1f}% weight")

    # 5. Real-Time Risk Inference
    print("\n[Step 5] Testing Real-Time Early Risk Inference...")
    sample_student_features = {
        "early_attendance_rate": 0.88,
        "early_tardy_rate": 0.15,
        "early_unexcused_rate": 0.08,
        "early_avg_daily_lms_minutes": 25.0,
        "early_lms_trend_decay": 0.35,  # 35% drop in LMS engagement
        "early_submission_rate": 0.75,
        "early_quiz_average": 68.0,
        "baseline_gpa": 2.7,
    }
    prediction = predictor.predict_risk(sample_student_features)
    print(f"✓ Input Student Profile: Attn=88%, Tardy=15%, LMS=25m, LMS Decay=+35%")
    print(f"  • Predicted Risk Probability: {prediction['predicted_risk_probability'] * 100:.1f}%")
    print(f"  • Predicted Risk Tier:        {prediction['predicted_risk_tier']}")
    print(f"  • Recommended Intervention:   {prediction['recommended_action']}")

    # 6. Policy Simulator
    print("\n[Step 6] Running What-If Policy Intervention Simulation...")
    sim_result = PolicySimulator.simulate_policy_intervention(
        base_cohort=cohort,
        policy_name="counselor_case_management",
        intervention_intensity=0.7,
    )
    print(f"✓ Policy: Dedicated Counselor Case Management (Intensity = 70%)")
    print(f"  • Baseline Chronic Rate:        {sim_result['baseline']['chronic_absenteeism_rate'] * 100:.1f}%")
    print(f"  • Post-Intervention Rate:       {sim_result['post_intervention']['chronic_absenteeism_rate'] * 100:.1f}%")
    print(f"  • Relative Risk Reduction:      -{sim_result['relative_chronic_reduction_pct']:.1f}%")
    print(f"  • Students Saved from Crisis:   {sim_result['students_saved_from_chronic_absenteeism']} students")

    # 7. Exports
    print("\n[Step 7] Exporting Standardized Datasets...")
    students_csv = DataExporter.to_csv_students(cohort["students"])
    with open("data/synthetic_students.csv", "w", encoding="utf-8") as f:
        f.write(students_csv)

    daily_csv = DataExporter.to_csv_daily_records(cohort["daily_records"][:1000])
    with open("data/synthetic_daily_attendance_sample.csv", "w", encoding="utf-8") as f:
        f.write(daily_csv)

    edfi_json = DataExporter.to_ed_fi_json(cohort)
    with open("data/synthetic_edfi_aligned.json", "w", encoding="utf-8") as f:
        f.write(edfi_json)

    print("✓ Successfully exported:")
    print("  - data/synthetic_students.csv")
    print("  - data/synthetic_daily_attendance_sample.csv")
    print("  - data/synthetic_edfi_aligned.json (Ed-Fi Alliance 3.3 compatible)")

    print("\n" + "=" * 70)
    print("✨ DEMO COMPLETED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    run_demo()

