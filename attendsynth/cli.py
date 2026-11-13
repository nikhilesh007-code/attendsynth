"""Command-line interface (CLI) for AttendSynth AI."""

import argparse
import json
import sys
import uvicorn

from attendsynth.config import CohortConfig, Presets, SchoolCalendarConfig
from attendsynth.generator import AttendSynthGenerator
from attendsynth.privacy import PrivacyAuditor
from attendsynth.metrics import FidelityEvaluator
from attendsynth.models.early_warning import EarlyWarningPredictor
from attendsynth.export import DataExporter


def main():
    parser = argparse.ArgumentParser(
        prog="attendsynth",
        description="AttendSynth AI: Synthetic Student Engagement & Early-Warning Data Studio",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Command: generate
    gen_parser = subparsers.add_parser("generate", help="Synthesize a new student cohort")
    gen_parser.add_argument("--students", type=int, default=250, help="Number of students")
    gen_parser.add_argument("--weeks", type=int, default=16, help="Instructional weeks")
    gen_parser.add_argument("--seed", type=int, default=42, help="Random seed")
    gen_parser.add_argument("--preset", type=str, choices=["standard_district", "urban_at_risk", "hybrid_academy"], default="standard_district")
    gen_parser.add_argument("--output", type=str, default="data/cohort.json", help="Output JSON path")

    # Command: train
    train_parser = subparsers.add_parser("train", help="Train an early-warning predictor on synthetic data")
    train_parser.add_argument("--data", type=str, required=True, help="Path to synthetic cohort JSON")
    train_parser.add_argument("--model", type=str, choices=["random_forest", "gradient_boosting", "logistic_regression"], default="random_forest")
    train_parser.add_argument("--weeks", type=int, default=6, help="Early observation window weeks")

    # Command: audit
    audit_parser = subparsers.add_parser("audit", help="Audit privacy compliance and statistical fidelity")
    audit_parser.add_argument("--data", type=str, required=True, help="Path to synthetic cohort JSON")

    # Command: export
    export_parser = subparsers.add_parser("export", help="Export synthetic cohort to CSV or Ed-Fi format")
    export_parser.add_argument("--data", type=str, required=True, help="Path to synthetic cohort JSON")
    export_parser.add_argument("--format", type=str, choices=["students_csv", "daily_csv", "edfi_json"], default="edfi_json")
    export_parser.add_argument("--output", type=str, required=True, help="Output destination file")

    # Command: serve
    serve_parser = subparsers.add_parser("serve", help="Launch the FastAPI server and Web UI dashboard")
    serve_parser.add_argument("--host", type=str, default="127.0.0.1", help="Host interface")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port")

    args = parser.parse_args()

    if args.command == "generate":
        print(f"Generating synthetic cohort ({args.students} students, {args.weeks} weeks, preset={args.preset})...")
        if args.preset == "urban_at_risk":
            cfg = Presets.urban_at_risk(num_students=args.students, seed=args.seed)
        elif args.preset == "hybrid_academy":
            cfg = Presets.hybrid_academy(num_students=args.students, seed=args.seed)
        else:
            cfg = Presets.standard_district(num_students=args.students, seed=args.seed)
        
        cfg.calendar.total_weeks = args.weeks
        generator = AttendSynthGenerator(cfg)
        cohort = generator.generate()

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(cohort, f, indent=2)

        summary = cohort["summary"]
        print(f"✓ Generated {summary['total_students']} students across {summary['total_school_days']} instructional days.")
        print(f"✓ Chronic Absenteeism Rate: {summary['chronic_absenteeism_rate'] * 100:.1f}%")
        print(f"✓ Mean Attendance: {summary['average_attendance_rate'] * 100:.1f}%")
        print(f"✓ Saved to {args.output}")

    elif args.command == "train":
        print(f"Loading data from {args.data}...")
        with open(args.data, "r", encoding="utf-8") as f:
            cohort = json.load(f)

        predictor = EarlyWarningPredictor(model_type=args.model, observation_weeks=args.weeks)
        metrics = predictor.train_and_evaluate(cohort)

        print("\n--- Early Warning System (EWS) Model Performance ---")
        print(f"Model Type:        {metrics['model_type']}")
        print(f"Observation Window:{metrics['observation_weeks']} weeks")
        print(f"ROC-AUC:           {metrics['roc_auc']:.4f}")
        print(f"Accuracy:          {metrics['accuracy'] * 100:.2f}%")
        print(f"Precision:         {metrics['precision']:.4f}")
        print(f"Recall:            {metrics['recall']:.4f}")
        print(f"F1 Score:          {metrics['f1_score']:.4f}")
        print("\nTop 3 Leading Predictive Signals:")
        for feat in metrics["feature_importances"][:3]:
            print(f" - {feat['feature']}: {feat['importance'] * 100:.1f}%")

    elif args.command == "audit":
        with open(args.data, "r", encoding="utf-8") as f:
            cohort = json.load(f)

        students = cohort.get("students", [])
        auditor = PrivacyAuditor(k_threshold=5)
        priv_report = auditor.audit_cohort(students)

        evaluator = FidelityEvaluator()
        fid_report = evaluator.evaluate(students)

        print("\n--- Privacy Audit Report ---")
        print(f"Zero Real PII:       {'PASSED ✓' if priv_report['zero_pii_check']['is_compliant'] else 'FAILED ✗'}")
        print(f"k-Anonymity (k=5):   {priv_report['k_anonymity']['protected_student_ratio'] * 100:.1f}% protected")
        print(f"Privacy Rating:      {priv_report['privacy_rating']}")

        print("\n--- Statistical Fidelity Report ---")
        print(f"Synthetic Quality:   {fid_report['synthetic_quality_score']}/100 ({fid_report['quality_grade']})")
        print(f"Attendance KS-Test:  Stat = {fid_report['ks_tests']['attendance_rate']['statistic']} (Passed: {fid_report['ks_tests']['attendance_rate']['passed']})")
        print(f"LMS Telemetry Match: Stat = {fid_report['ks_tests']['lms_active_minutes']['statistic']} (Passed: {fid_report['ks_tests']['lms_active_minutes']['passed']})")

    elif args.command == "export":
        with open(args.data, "r", encoding="utf-8") as f:
            cohort = json.load(f)

        if args.format == "students_csv":
            out_str = DataExporter.to_csv_students(cohort.get("students", []))
        elif args.format == "daily_csv":
            out_str = DataExporter.to_csv_daily_records(cohort.get("daily_records", []))
        else:
            out_str = DataExporter.to_ed_fi_json(cohort)

        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_str)
        print(f"✓ Exported {args.format} to {args.output}")

    elif args.command == "serve":
        print(f"Starting AttendSynth AI server at http://{args.host}:{args.port}")
        uvicorn.run("attendsynth.api.app:app", host=args.host, port=args.port, reload=False)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

