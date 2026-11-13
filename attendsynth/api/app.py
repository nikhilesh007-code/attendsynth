"""FastAPI REST API backend for AttendSynth AI."""

import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field

from attendsynth.config import ArchetypeType, CohortConfig, Presets, SchoolCalendarConfig
from attendsynth.generator import AttendSynthGenerator
from attendsynth.privacy import DifferentialPrivacyEngine, PrivacyAuditor
from attendsynth.metrics import FidelityEvaluator
from attendsynth.models.early_warning import EarlyWarningPredictor
from attendsynth.simulator import PolicySimulator
from attendsynth.export import DataExporter

# Initialize FastAPI application
app = FastAPI(
    title="AttendSynth AI API",
    description="Synthetic Student Engagement & Attendance Generator for Early-Warning Predictive Models",
    version="1.0.0",
)

# Enable CORS for developer ease
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory application state
GLOBAL_STATE: Dict[str, Any] = {
    "current_cohort": None,
    "current_model": None,
    "privacy_auditor": PrivacyAuditor(k_threshold=5),
    "fidelity_evaluator": FidelityEvaluator(),
}


class GenerateRequest(BaseModel):
    preset_name: Optional[str] = None
    num_students: int = Field(default=250, ge=20, le=2000)
    total_weeks: int = Field(default=16, ge=4, le=36)
    random_seed: int = Field(default=42)
    district_name: str = Field(default="Horizon Metro Public Schools")
    archetype_weights: Optional[Dict[str, float]] = None
    enable_dp_noise: bool = False
    dp_epsilon: float = 1.0


class TrainModelRequest(BaseModel):
    model_config = {"protected_namespaces": ()}
    model_type: str = Field(default="random_forest")  # random_forest, gradient_boosting, logistic_regression
    observation_weeks: int = Field(default=6, ge=2, le=12)


class PredictRiskRequest(BaseModel):
    early_attendance_rate: float = Field(default=0.88, ge=0.0, le=1.0)
    early_tardy_rate: float = Field(default=0.10, ge=0.0, le=1.0)
    early_unexcused_rate: float = Field(default=0.05, ge=0.0, le=1.0)
    early_avg_daily_lms_minutes: float = Field(default=35.0, ge=0.0, le=240.0)
    early_lms_trend_decay: float = Field(default=0.25, ge=-1.0, le=1.0)
    early_submission_rate: float = Field(default=0.80, ge=0.0, le=1.0)
    early_quiz_average: float = Field(default=72.0, ge=0.0, le=100.0)
    baseline_gpa: float = Field(default=2.9, ge=0.0, le=4.0)


class PolicySimRequest(BaseModel):
    policy_name: str = Field(default="counselor_case_management")
    intervention_intensity: float = Field(default=0.6, ge=0.1, le=1.0)


@app.on_event("startup")
def startup_event():
    """Generates an initial default cohort and baseline model on boot so the UI is immediately interactive."""
    gen = AttendSynthGenerator(Presets.standard_district(num_students=200, seed=42))
    cohort = gen.generate()
    GLOBAL_STATE["current_cohort"] = cohort
    
    # Pre-train a default model
    predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
    predictor.train_and_evaluate(cohort)
    GLOBAL_STATE["current_model"] = predictor


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "AttendSynth AI",
        "version": "1.0.0",
        "cohort_loaded": GLOBAL_STATE["current_cohort"] is not None,
        "model_trained": GLOBAL_STATE["current_model"] is not None and GLOBAL_STATE["current_model"].is_trained,
    }


@app.get("/api/presets")
def get_presets():
    return [
        {
            "id": "standard_district",
            "name": "Standard District Benchmark",
            "description": "Balanced K-12 public district cohort reflecting typical suburban/urban baseline engagement.",
            "default_students": 250,
        },
        {
            "id": "urban_at_risk",
            "name": "Urban At-Risk Cohort (High Sensitivity)",
            "description": "Cohort with elevated proportion of gradual disengagers and sporadic attendees for stress-testing EWS.",
            "default_students": 250,
        },
        {
            "id": "hybrid_academy",
            "name": "Blended / Hybrid Digital Academy",
            "description": "Online and blended learning students with heavy dependence on LMS telemetry and digital engagement.",
            "default_students": 250,
        },
    ]


@app.post("/api/generate")
def generate_cohort(req: GenerateRequest):
    cal = SchoolCalendarConfig(
        total_weeks=req.total_weeks,
        district_name=req.district_name,
    )

    if req.preset_name == "urban_at_risk":
        cfg = Presets.urban_at_risk(num_students=req.num_students, seed=req.random_seed)
        cfg.calendar = cal
    elif req.preset_name == "hybrid_academy":
        cfg = Presets.hybrid_academy(num_students=req.num_students, seed=req.random_seed)
        cfg.calendar = cal
    else:
        weights = {}
        if req.archetype_weights:
            for k, v in req.archetype_weights.items():
                try:
                    weights[ArchetypeType(k)] = float(v)
                except ValueError:
                    pass
        cfg = CohortConfig(
            cohort_id=f"cohort_{req.random_seed}_{req.num_students}",
            name=f"Synthesized Cohort ({req.num_students} Students)",
            num_students=req.num_students,
            random_seed=req.random_seed,
            calendar=cal,
            enable_dp_noise=req.enable_dp_noise,
            dp_epsilon=req.dp_epsilon,
        )
        if weights:
            cfg.archetype_weights = weights

    generator = AttendSynthGenerator(cfg)
    cohort = generator.generate()
    GLOBAL_STATE["current_cohort"] = cohort

    # Re-train model on the newly generated cohort automatically
    predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
    predictor.train_and_evaluate(cohort)
    GLOBAL_STATE["current_model"] = predictor

    return {
        "success": True,
        "message": f"Successfully synthesized cohort with {req.num_students} students over {req.total_weeks} weeks.",
        "cohort_id": cohort["cohort_id"],
        "summary": cohort["summary"],
    }


@app.get("/api/cohorts/current")
def get_current_cohort_summary():
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort generated yet.")
    return {
        "cohort_id": cohort["cohort_id"],
        "cohort_name": cohort["cohort_name"],
        "config": cohort["config"],
        "summary": cohort["summary"],
    }


@app.get("/api/cohorts/current/students")
def get_students(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=200),
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    archetype: Optional[str] = None,
):
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort generated yet.")

    students = cohort.get("students", [])

    # Filters
    filtered = students
    if search:
        search_lower = search.lower()
        filtered = [
            s for s in filtered
            if search_lower in s["display_name"].lower() or search_lower in s["student_id"].lower()
        ]
    if risk_level and risk_level != "ALL":
        filtered = [s for s in filtered if s["risk_level"] == risk_level]
    if archetype and archetype != "ALL":
        filtered = [s for s in filtered if s["archetype"] == archetype]

    total_count = len(filtered)
    start_idx = (page - 1) * limit
    end_idx = start_idx + limit
    page_items = filtered[start_idx:end_idx]

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "students": page_items,
    }


@app.get("/api/cohorts/current/students/{student_id}")
def get_student_detail(student_id: str):
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort generated yet.")

    students = cohort.get("students", [])
    student = next((s for s in students if s["student_id"] == student_id), None)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found.")

    # Fetch daily logs
    daily_records = [
        r for r in cohort.get("daily_records", [])
        if r["student_id"] == student_id
    ]

    return {
        "student": student,
        "daily_timeline": daily_records,
    }


@app.post("/api/models/train")
def train_model(req: TrainModelRequest):
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=400, detail="Generate a cohort before training.")

    predictor = EarlyWarningPredictor(
        model_type=req.model_type,
        observation_weeks=req.observation_weeks,
    )
    results = predictor.train_and_evaluate(cohort)
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])

    GLOBAL_STATE["current_model"] = predictor
    return {
        "success": True,
        "metrics": results,
    }


@app.get("/api/models/current")
def get_current_model_metrics():
    model: Optional[EarlyWarningPredictor] = GLOBAL_STATE.get("current_model")
    if not model or not model.is_trained:
        raise HTTPException(status_code=404, detail="No early warning model trained yet.")
    return model.evaluation_metrics


@app.post("/api/models/predict")
def predict_student_risk(req: PredictRiskRequest):
    model: Optional[EarlyWarningPredictor] = GLOBAL_STATE.get("current_model")
    if not model or not model.is_trained:
        raise HTTPException(status_code=400, detail="Train a model first before running inference.")
    
    features = req.model_dump()
    result = model.predict_risk(features)
    return result


@app.get("/api/audit/privacy")
def audit_privacy():
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort loaded.")

    auditor: PrivacyAuditor = GLOBAL_STATE["privacy_auditor"]
    audit_report = auditor.audit_cohort(cohort.get("students", []))

    # Also compute differential privacy noisy release preview
    dp_engine = DifferentialPrivacyEngine(epsilon=1.0)
    dp_sample = dp_engine.privatize_summary(cohort.get("summary", {}), len(cohort.get("students", [])))

    return {
        "audit": audit_report,
        "differential_privacy_preview": dp_sample,
    }


@app.get("/api/audit/fidelity")
def audit_fidelity():
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort loaded.")

    evaluator: FidelityEvaluator = GLOBAL_STATE["fidelity_evaluator"]
    report = evaluator.evaluate(cohort.get("students", []))
    return report


@app.post("/api/simulate/policy")
def simulate_policy(req: PolicySimRequest):
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=400, detail="Generate a cohort first.")

    res = PolicySimulator.simulate_policy_intervention(
        base_cohort=cohort,
        policy_name=req.policy_name,
        intervention_intensity=req.intervention_intensity,
    )
    return res


@app.get("/api/export/{export_format}")
def export_data(export_format: str):
    cohort = GLOBAL_STATE.get("current_cohort")
    if not cohort:
        raise HTTPException(status_code=404, detail="No cohort to export.")

    if export_format == "students_csv":
        csv_text = DataExporter.to_csv_students(cohort.get("students", []))
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendsynth_students.csv"},
        )
    elif export_format == "daily_csv":
        csv_text = DataExporter.to_csv_daily_records(cohort.get("daily_records", []))
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendsynth_daily_attendance.csv"},
        )
    elif export_format == "edfi_json":
        json_text = DataExporter.to_ed_fi_json(cohort)
        return Response(
            content=json_text,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=attendsynth_edfi_aligned.json"},
        )
    elif export_format == "full_json":
        import json
        return Response(
            content=json.dumps(cohort, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=attendsynth_full_cohort.json"},
        )
    else:
        raise HTTPException(status_code=400, detail="Supported export formats: students_csv, daily_csv, edfi_json, full_json")


# Mount static assets
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def serve_frontend():
        index_file = os.path.join(static_dir, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return PlainTextResponse("AttendSynth AI API is running. index.html not found.")
