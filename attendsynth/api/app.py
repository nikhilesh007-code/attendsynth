"""FastAPI REST API backend for AttendSynth AI with SQLite database persistence."""

import os
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from attendsynth.config import ArchetypeType, CohortConfig, Presets, SchoolCalendarConfig
from attendsynth.generator import AttendSynthGenerator
from attendsynth.privacy import DifferentialPrivacyEngine, PrivacyAuditor
from attendsynth.metrics import FidelityEvaluator
from attendsynth.models.early_warning import EarlyWarningPredictor
from attendsynth.simulator import PolicySimulator
from attendsynth.export import DataExporter

from attendsynth.db.database import get_db, init_db, SessionLocal
from attendsynth.db.repository import CohortRepository

# Initialize FastAPI application
app = FastAPI(
    title="AttendSynth AI API",
    description="Synthetic Student Engagement & Attendance Generator with SQLite Relational Persistence",
    version="1.0.0",
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory helper evaluators
PRIVACY_AUDITOR = PrivacyAuditor(k_threshold=5)
FIDELITY_EVALUATOR = FidelityEvaluator()


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
    model_type: str = Field(default="random_forest")
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
    """Initializes the SQLite database and ensures at least one cohort exists in the database."""
    init_db()
    db = SessionLocal()
    try:
        active = CohortRepository.get_active_cohort(db)
        if not active:
            # Generate and persist an initial benchmark cohort into SQLite
            gen = AttendSynthGenerator(Presets.standard_district(num_students=200, seed=42))
            cohort_data = gen.generate()
            saved_cohort = CohortRepository.save_cohort(db, cohort_data)

            # Pre-train baseline early warning model and store in DB
            predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
            metrics = predictor.train_and_evaluate(cohort_data)
            CohortRepository.save_trained_model(db, saved_cohort.id, metrics)
    finally:
        db.close()


def _resolve_session(db: Any) -> Session:
    """Helper ensuring endpoints work both when called via FastAPI HTTP router and directly in unit tests."""
    if db is None or not hasattr(db, "query"):
        return SessionLocal()
    return db


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db = _resolve_session(db)
    stats = CohortRepository.get_database_stats(db)
    return {
        "status": "healthy",
        "service": "AttendSynth AI",
        "version": "1.0.0",
        "cohort_loaded": stats["total_cohorts"] > 0,
        "database": stats,
    }


@app.get("/api/db/stats")
def get_db_stats(db: Session = Depends(get_db)):
    """Returns real-time database connection metrics and record tallies."""
    db = _resolve_session(db)
    return CohortRepository.get_database_stats(db)


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


@app.get("/api/cohorts")
def list_cohorts(db: Session = Depends(get_db)):
    """Lists all cohorts stored in the database."""
    db = _resolve_session(db)
    return CohortRepository.list_cohorts(db)


@app.post("/api/cohorts/select/{cohort_id}")
def select_active_cohort(cohort_id: str, db: Session = Depends(get_db)):
    """Switches the active cohort in the database."""
    db = _resolve_session(db)
    target = CohortRepository.set_active_cohort(db, cohort_id)
    if not target:
        raise HTTPException(status_code=404, detail=f"Cohort {cohort_id} not found in database.")
    return {"success": True, "active_cohort_id": target.id, "name": target.name}


@app.delete("/api/cohorts/{cohort_id}")
def delete_cohort(cohort_id: str, db: Session = Depends(get_db)):
    """Deletes a cohort and all its associated students and telemetry from the database."""
    db = _resolve_session(db)
    success = CohortRepository.delete_cohort(db, cohort_id)
    if not success:
        raise HTTPException(status_code=404, detail="Cohort not found.")
    return {"success": True, "deleted_cohort_id": cohort_id}


@app.post("/api/generate")
def generate_cohort(req: GenerateRequest, db: Session = Depends(get_db)):
    """Synthesizes a new cohort and writes all records directly into the SQLite database."""
    db = _resolve_session(db)
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
            cohort_id=f"cohort_{req.random_seed}_{req.num_students}_{req.total_weeks}w",
            name=f"Synthesized Cohort ({req.num_students} Students, {req.total_weeks} Wks)",
            num_students=req.num_students,
            random_seed=req.random_seed,
            calendar=cal,
            enable_dp_noise=req.enable_dp_noise,
            dp_epsilon=req.dp_epsilon,
        )
        if weights:
            cfg.archetype_weights = weights

    # 1. Run dynamic algorithmic generator
    generator = AttendSynthGenerator(cfg)
    cohort_data = generator.generate()

    # 2. Persist into SQLite Database
    saved_cohort = CohortRepository.save_cohort(db, cohort_data)

    # 3. Train and persist EWS model
    predictor = EarlyWarningPredictor(model_type="random_forest", observation_weeks=6)
    metrics = predictor.train_and_evaluate(cohort_data)
    CohortRepository.save_trained_model(db, saved_cohort.id, metrics)

    db_stats = CohortRepository.get_database_stats(db)

    return {
        "success": True,
        "message": f"Successfully synthesized and persisted {req.num_students} students and {len(cohort_data['daily_records'])} daily logs to SQLite database.",
        "cohort_id": saved_cohort.id,
        "summary": cohort_data["summary"],
        "database": db_stats,
    }


@app.get("/api/cohorts/current")
def get_current_cohort_summary(db: Session = Depends(get_db)):
    """Returns active cohort summary from SQLite database."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=404, detail="No cohorts found in database.")

    import json
    return {
        "cohort_id": active.id,
        "cohort_name": active.name,
        "config": json.loads(active.config_json),
        "summary": json.loads(active.summary_json),
    }


@app.get("/api/cohorts/current/students")
def get_students(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=25, ge=1, le=200),
    search: Optional[str] = None,
    risk_level: Optional[str] = None,
    archetype: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Executes SQL query on the 'students' table with filtering, search, and pagination."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active cohort in database.")

    students, total_count = CohortRepository.query_students(
        db,
        cohort_id=active.id,
        page=page,
        limit=limit,
        search=search,
        risk_level=risk_level,
        archetype=archetype,
    )

    return {
        "total": total_count,
        "page": page,
        "limit": limit,
        "students": students,
    }


@app.get("/api/cohorts/current/students/{student_id}")
def get_student_detail(student_id: str, db: Session = Depends(get_db)):
    """Queries single student and their daily attendance timeline from the SQLite database."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active cohort in database.")

    detail = CohortRepository.get_student_detail(db, active.id, student_id)
    if not detail:
        raise HTTPException(status_code=404, detail=f"Student {student_id} not found in database.")

    return detail


@app.post("/api/models/train")
def train_model(req: TrainModelRequest, db: Session = Depends(get_db)):
    """Trains an EWS model on the active database cohort and persists model metrics into SQLite."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=400, detail="No active cohort in database to train on.")

    cohort_payload = CohortRepository.get_full_cohort_payload(db, active.id)
    if not cohort_payload:
        raise HTTPException(status_code=404, detail="Could not reconstruct cohort from database.")

    predictor = EarlyWarningPredictor(
        model_type=req.model_type,
        observation_weeks=req.observation_weeks,
    )
    results = predictor.train_and_evaluate(cohort_payload)
    if "error" in results:
        raise HTTPException(status_code=400, detail=results["error"])

    # Persist model evaluation metrics in DB
    CohortRepository.save_trained_model(db, active.id, results)

    return {
        "success": True,
        "metrics": results,
    }


@app.get("/api/models/current")
def get_current_model_metrics(db: Session = Depends(get_db)):
    """Fetches the latest trained ML model metrics from the database."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    cohort_id = active.id if active else "default"
    metrics = CohortRepository.get_latest_model(db, cohort_id)
    if not metrics:
        raise HTTPException(status_code=404, detail="No trained model found in database.")
    return metrics


@app.post("/api/models/predict")
def predict_student_risk(req: PredictRiskRequest, db: Session = Depends(get_db)):
    """Inference endpoint scoring student risk using the trained model."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    cohort_id = active.id if active else "default"
    model_metrics = CohortRepository.get_latest_model(db, cohort_id)

    # Re-initialize predictor for inference
    predictor = EarlyWarningPredictor(
        model_type=model_metrics.get("model_type", "random_forest") if model_metrics else "random_forest",
        observation_weeks=model_metrics.get("observation_weeks", 6) if model_metrics else 6,
    )

    if active:
        cohort_payload = CohortRepository.get_full_cohort_payload(db, active.id)
        if cohort_payload:
            predictor.train_and_evaluate(cohort_payload)

    result = predictor.predict_risk(req.model_dump())
    return result


@app.get("/api/audit/privacy")
def audit_privacy(db: Session = Depends(get_db)):
    """Runs privacy and k-anonymity audit on actual database records."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active cohort loaded.")

    students, _ = CohortRepository.query_students(db, active.id, page=1, limit=10000)
    audit_report = PRIVACY_AUDITOR.audit_cohort(students)

    import json
    summary = json.loads(active.summary_json)
    dp_engine = DifferentialPrivacyEngine(epsilon=1.0)
    dp_sample = dp_engine.privatize_summary(summary, len(students))

    return {
        "audit": audit_report,
        "differential_privacy_preview": dp_sample,
    }


@app.get("/api/audit/fidelity")
def audit_fidelity(db: Session = Depends(get_db)):
    """Runs statistical fidelity evaluation on actual database records."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active cohort loaded.")

    students, _ = CohortRepository.query_students(db, active.id, page=1, limit=10000)
    report = FIDELITY_EVALUATOR.evaluate(students)
    return report


@app.post("/api/simulate/policy")
def simulate_policy(req: PolicySimRequest, db: Session = Depends(get_db)):
    """Simulates district policy intervention on actual database cohort."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=400, detail="No active cohort in database.")

    cohort_payload = CohortRepository.get_full_cohort_payload(db, active.id)
    res = PolicySimulator.simulate_policy_intervention(
        base_cohort=cohort_payload,
        policy_name=req.policy_name,
        intervention_intensity=req.intervention_intensity,
    )
    return res


@app.get("/api/export/{export_format}")
def export_data(export_format: str, db: Session = Depends(get_db)):
    """Exports dataset directly from SQLite database."""
    db = _resolve_session(db)
    active = CohortRepository.get_active_cohort(db)
    if not active:
        raise HTTPException(status_code=404, detail="No active cohort to export.")

    cohort_payload = CohortRepository.get_full_cohort_payload(db, active.id)

    if export_format == "students_csv":
        csv_text = DataExporter.to_csv_students(cohort_payload.get("students", []))
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendsynth_students.csv"},
        )
    elif export_format == "daily_csv":
        csv_text = DataExporter.to_csv_daily_records(cohort_payload.get("daily_records", []))
        return Response(
            content=csv_text,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=attendsynth_daily_attendance.csv"},
        )
    elif export_format == "edfi_json":
        json_text = DataExporter.to_ed_fi_json(cohort_payload)
        return Response(
            content=json_text,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=attendsynth_edfi_aligned.json"},
        )
    elif export_format == "full_json":
        import json
        return Response(
            content=json.dumps(cohort_payload, indent=2),
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
