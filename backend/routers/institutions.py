"""
Institutions Router for AttendSynth AI.
Provides CRUD operations for institutions and departments.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import InstitutionModel, DepartmentModel, DatasetModel
from ..schemas import (
    InstitutionCreateRequest,
    InstitutionUpdateRequest,
    InstitutionResponse,
    DepartmentResponse,
)

router = APIRouter(prefix="/institutions", tags=["Institutions"])


def _to_institution_response(inst: InstitutionModel, db: Session) -> InstitutionResponse:
    dept_cnt = db.query(func.count(DepartmentModel.id)).filter(DepartmentModel.institution_id == inst.id).scalar() or 0
    cohort_cnt = db.query(func.count(DatasetModel.id)).filter(DatasetModel.institution_id == inst.id).scalar() or 0
    return InstitutionResponse(
        id=inst.id,
        name=inst.name,
        type=inst.type or "University",
        location=inst.location or "",
        description=inst.description or "",
        created_at=inst.created_at,
        departments_count=int(dept_cnt),
        cohorts_count=int(cohort_cnt),
    )


@router.get("", response_model=List[InstitutionResponse])
def list_institutions(
    search: Optional[str] = None,
    type_filter: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists all registered institutions with department and cohort counts."""
    query = db.query(InstitutionModel)
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((InstitutionModel.name.ilike(s)) | (InstitutionModel.location.ilike(s)))
    if type_filter:
        query = query.filter(InstitutionModel.type == type_filter)

    institutions = query.order_by(InstitutionModel.name.asc()).all()
    return [_to_institution_response(inst, db) for inst in institutions]


@router.post("", response_model=InstitutionResponse, status_code=201)
def create_institution(req: InstitutionCreateRequest, db: Session = Depends(get_db)):
    """Registers a new academic institution."""
    inst_id = f"INST_{uuid.uuid4().hex[:8].upper()}"
    new_inst = InstitutionModel(
        id=inst_id,
        name=req.name.strip(),
        type=req.type.strip() if req.type else "University",
        location=req.location.strip() if req.location else "",
        description=req.description.strip() if req.description else "",
    )
    db.add(new_inst)
    db.commit()
    db.refresh(new_inst)
    return _to_institution_response(new_inst, db)


@router.get("/{institution_id}", response_model=InstitutionResponse)
def get_institution(institution_id: str, db: Session = Depends(get_db)):
    """Retrieves an institution by its unique ID."""
    inst = db.query(InstitutionModel).filter(InstitutionModel.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")
    return _to_institution_response(inst, db)


@router.put("/{institution_id}", response_model=InstitutionResponse)
def update_institution(
    institution_id: str,
    req: InstitutionUpdateRequest,
    db: Session = Depends(get_db),
):
    """Updates an existing institution record."""
    inst = db.query(InstitutionModel).filter(InstitutionModel.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    if req.name is not None:
        inst.name = req.name.strip()
    if req.type is not None:
        inst.type = req.type.strip()
    if req.location is not None:
        inst.location = req.location.strip()
    if req.description is not None:
        inst.description = req.description.strip()

    db.commit()
    db.refresh(inst)
    return _to_institution_response(inst, db)


@router.delete("/{institution_id}")
def delete_institution(institution_id: str, db: Session = Depends(get_db)):
    """Deletes an institution and cascades to associated departments."""
    inst = db.query(InstitutionModel).filter(InstitutionModel.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    name = inst.name
    db.delete(inst)
    db.commit()
    return {"message": f"Institution '{name}' ({institution_id}) deleted successfully."}


@router.get("/{institution_id}/departments", response_model=List[DepartmentResponse])
def get_institution_departments(institution_id: str, db: Session = Depends(get_db)):
    """Lists departments under a specific institution."""
    inst = db.query(InstitutionModel).filter(InstitutionModel.id == institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Institution not found.")

    from ..models import CourseModel

    depts = db.query(DepartmentModel).filter(DepartmentModel.institution_id == institution_id).order_by(DepartmentModel.name.asc()).all()
    res = []
    for d in depts:
        c_count = db.query(func.count(CourseModel.id)).filter(CourseModel.department_id == d.id).scalar() or 0
        res.append(
            DepartmentResponse(
                id=d.id,
                name=d.name,
                institution_id=d.institution_id,
                institution_name=inst.name,
                created_at=d.created_at,
                courses_count=int(c_count),
            )
        )
    return res
