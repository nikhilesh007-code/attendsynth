"""
Departments Router for AttendSynth AI.
Provides CRUD operations for academic departments.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..database import get_db
from ..models import DepartmentModel, InstitutionModel, CourseModel
from ..schemas import (
    DepartmentCreateRequest,
    DepartmentUpdateRequest,
    DepartmentResponse,
    CourseResponse,
)

router = APIRouter(prefix="/departments", tags=["Departments"])


def _to_department_response(dept: DepartmentModel, db: Session) -> DepartmentResponse:
    inst = db.query(InstitutionModel).filter(InstitutionModel.id == dept.institution_id).first()
    c_count = db.query(func.count(CourseModel.id)).filter(CourseModel.department_id == dept.id).scalar() or 0
    return DepartmentResponse(
        id=dept.id,
        name=dept.name,
        institution_id=dept.institution_id,
        institution_name=inst.name if inst else None,
        created_at=dept.created_at,
        courses_count=int(c_count),
    )


@router.get("", response_model=List[DepartmentResponse])
def list_departments(
    institution_id: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists departments with optional filtering by institution or search term."""
    query = db.query(DepartmentModel)
    if institution_id:
        query = query.filter(DepartmentModel.institution_id == institution_id)
    if search:
        query = query.filter(DepartmentModel.name.ilike(f"%{search.strip()}%"))

    depts = query.order_by(DepartmentModel.name.asc()).all()
    return [_to_department_response(d, db) for d in depts]


@router.post("", response_model=DepartmentResponse, status_code=201)
def create_department(req: DepartmentCreateRequest, db: Session = Depends(get_db)):
    """Creates a new department linked to an institution."""
    inst = db.query(InstitutionModel).filter(InstitutionModel.id == req.institution_id).first()
    if not inst:
        raise HTTPException(status_code=404, detail="Parent institution not found.")

    dept_id = f"DEPT_{uuid.uuid4().hex[:8].upper()}"
    new_dept = DepartmentModel(
        id=dept_id,
        name=req.name.strip(),
        institution_id=req.institution_id,
    )
    db.add(new_dept)
    db.commit()
    db.refresh(new_dept)
    return _to_department_response(new_dept, db)


@router.get("/{department_id}", response_model=DepartmentResponse)
def get_department(department_id: str, db: Session = Depends(get_db)):
    """Retrieves a single department by ID."""
    dept = db.query(DepartmentModel).filter(DepartmentModel.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")
    return _to_department_response(dept, db)


@router.put("/{department_id}", response_model=DepartmentResponse)
def update_department(
    department_id: str,
    req: DepartmentUpdateRequest,
    db: Session = Depends(get_db),
):
    """Updates a department record."""
    dept = db.query(DepartmentModel).filter(DepartmentModel.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    if req.institution_id is not None:
        inst = db.query(InstitutionModel).filter(InstitutionModel.id == req.institution_id).first()
        if not inst:
            raise HTTPException(status_code=404, detail="Specified institution not found.")
        dept.institution_id = req.institution_id

    if req.name is not None:
        dept.name = req.name.strip()

    db.commit()
    db.refresh(dept)
    return _to_department_response(dept, db)


@router.delete("/{department_id}")
def delete_department(department_id: str, db: Session = Depends(get_db)):
    """Deletes a department and cascades deletion to courses."""
    dept = db.query(DepartmentModel).filter(DepartmentModel.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    name = dept.name
    db.delete(dept)
    db.commit()
    return {"message": f"Department '{name}' ({department_id}) deleted successfully."}


@router.get("/{department_id}/courses", response_model=List[CourseResponse])
def get_department_courses(department_id: str, db: Session = Depends(get_db)):
    """Lists courses offered under a specific department."""
    dept = db.query(DepartmentModel).filter(DepartmentModel.id == department_id).first()
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found.")

    courses = db.query(CourseModel).filter(CourseModel.department_id == department_id).order_by(CourseModel.code.asc()).all()
    return [
        CourseResponse(
            id=c.id,
            code=c.code,
            name=c.name,
            department_id=c.department_id,
            department_name=dept.name,
            semester=c.semester or "Semester 1",
            credits=c.credits or 3,
            description=c.description or "",
            created_at=c.created_at,
        )
        for c in courses
    ]
