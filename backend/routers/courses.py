"""
Courses Router for AttendSynth AI.
Provides complete dynamic course management, search, and department/semester filtering.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import CourseModel, DepartmentModel
from ..schemas import (
    CourseCreateRequest,
    CourseUpdateRequest,
    CourseResponse,
)

router = APIRouter(prefix="/courses", tags=["Courses"])


def _to_course_response(course: CourseModel, db: Session) -> CourseResponse:
    dept_name = None
    if course.department_id:
        dept = db.query(DepartmentModel).filter(DepartmentModel.id == course.department_id).first()
        if dept:
            dept_name = dept.name
    return CourseResponse(
        id=course.id,
        code=course.code,
        name=course.name,
        department_id=course.department_id,
        department_name=dept_name,
        semester=course.semester or "Semester 1",
        credits=course.credits or 3,
        description=course.description or "",
        created_at=course.created_at,
    )


@router.get("", response_model=List[CourseResponse])
def list_courses(
    department_id: Optional[str] = None,
    semester: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """Lists courses with optional filtering by department, semester, and search keyword."""
    query = db.query(CourseModel)

    if department_id:
        query = query.filter(CourseModel.department_id == department_id)
    if semester:
        query = query.filter(CourseModel.semester.ilike(f"%{semester.strip()}%"))
    if search:
        s = f"%{search.strip()}%"
        query = query.filter((CourseModel.code.ilike(s)) | (CourseModel.name.ilike(s)) | (CourseModel.description.ilike(s)))

    courses = query.order_by(CourseModel.code.asc()).all()
    return [_to_course_response(c, db) for c in courses]


@router.post("", response_model=CourseResponse, status_code=201)
def create_course(req: CourseCreateRequest, db: Session = Depends(get_db)):
    """Creates a new academic course."""
    # Check duplicate code in same department (or globally)
    existing = db.query(CourseModel).filter(CourseModel.code.ilike(req.code.strip())).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Course with code '{req.code.strip()}' already exists ({existing.name}).",
        )

    if req.department_id:
        dept = db.query(DepartmentModel).filter(DepartmentModel.id == req.department_id).first()
        if not dept:
            raise HTTPException(status_code=404, detail="Department not found.")

    course_id = f"CRS_{uuid.uuid4().hex[:8].upper()}"
    new_course = CourseModel(
        id=course_id,
        code=req.code.strip().upper(),
        name=req.name.strip(),
        department_id=req.department_id,
        semester=req.semester.strip() if req.semester else "Semester 1",
        credits=req.credits,
        description=req.description.strip() if req.description else "",
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    return _to_course_response(new_course, db)


@router.get("/{course_id}", response_model=CourseResponse)
def get_course(course_id: str, db: Session = Depends(get_db)):
    """Retrieves a single course by its ID."""
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")
    return _to_course_response(course, db)


@router.put("/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: str,
    req: CourseUpdateRequest,
    db: Session = Depends(get_db),
):
    """Updates an existing course record."""
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    if req.code is not None:
        clean_code = req.code.strip().upper()
        conflict = (
            db.query(CourseModel)
            .filter(CourseModel.code.ilike(clean_code), CourseModel.id != course_id)
            .first()
        )
        if conflict:
            raise HTTPException(
                status_code=400,
                detail=f"Course code '{clean_code}' is already in use by {conflict.name}.",
            )
        course.code = clean_code

    if req.name is not None:
        course.name = req.name.strip()
    if req.department_id is not None:
        if req.department_id != "":
            dept = db.query(DepartmentModel).filter(DepartmentModel.id == req.department_id).first()
            if not dept:
                raise HTTPException(status_code=404, detail="Department not found.")
            course.department_id = req.department_id
        else:
            course.department_id = None
    if req.semester is not None:
        course.semester = req.semester.strip()
    if req.credits is not None:
        course.credits = req.credits
    if req.description is not None:
        course.description = req.description.strip()

    db.commit()
    db.refresh(course)
    return _to_course_response(course, db)


@router.delete("/{course_id}")
def delete_course(course_id: str, db: Session = Depends(get_db)):
    """Deletes a course record."""
    course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found.")

    code = course.code
    db.delete(course)
    db.commit()
    return {"message": f"Course '{code}' ({course_id}) deleted successfully."}
