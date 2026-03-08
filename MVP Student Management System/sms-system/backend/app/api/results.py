"""
Results API Router

Academic results and grade management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.result import Result, AcademicRecord, AssessmentType


router = APIRouter()


@router.get("/my")
async def get_my_results(
    term: Optional[str] = None,
    academic_year: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get results for current student."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    query = db.query(Result).filter(Result.student_id == student.id)
    
    if term:
        query = query.filter(Result.term == term)
    
    if academic_year:
        query = query.filter(Result.academic_year == academic_year)
    
    results = query.order_by(Result.created_at.desc()).all()
    
    return [r.to_dict() for r in results if r.published]


@router.get("/my/summary")
async def get_results_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary of academic performance."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    results = [r for r in student.results if r.published]
    
    if not results:
        return {
            "total_assessments": 0,
            "average_percentage": 0,
            "current_gpa": 0,
            "grades_distribution": {},
        }
    
    percentages = [r.percentage or r.calculate_percentage() for r in results]
    avg_percentage = sum(percentages) / len(percentages)
    
    # Calculate GPA (4.0 scale)
    gpa = (avg_percentage / 100) * 4
    
    # Grade distribution
    grades = {}
    for r in results:
        grade = r.grade or r.calculate_grade()
        grades[grade] = grades.get(grade, 0) + 1
    
    return {
        "total_assessments": len(results),
        "average_percentage": round(avg_percentage, 2),
        "current_gpa": round(gpa, 2),
        "grades_distribution": grades,
    }


@router.get("/my/module/{module_id}")
async def get_module_results(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get results for a specific module."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    results = db.query(Result).filter(
        Result.student_id == student.id,
        Result.module_id == module_id,
        Result.published == True
    ).all()
    
    return [r.to_dict() for r in results]


# Lecturer endpoints
@router.get("/module/{module_id}")
async def get_module_all_results(
    module_id: int,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Get all results for a module (lecturer only)."""
    results = db.query(Result).filter(Result.module_id == module_id).all()
    return [r.to_dict(include_private=True) for r in results]


@router.post("/")
async def create_result(
    result_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Create a new result entry (lecturer only)."""
    result = Result(
        student_id=result_data.get("student_id"),
        module_id=result_data.get("module_id"),
        assessment_type=result_data.get("assessment_type", AssessmentType.TEST),
        assessment_name=result_data.get("assessment_name"),
        term=result_data.get("term"),
        academic_year=result_data.get("academic_year"),
        score=result_data.get("score"),
        max_score=result_data.get("max_score", 100),
        weight=result_data.get("weight"),
        contributes_to_final=result_data.get("contributes_to_final", True),
        lecturer_notes=result_data.get("lecturer_notes"),
        student_feedback=result_data.get("student_feedback"),
        published=result_data.get("published", False),
    )
    
    # Calculate percentage and grade
    result.update_calculated_fields()
    
    db.add(result)
    db.commit()
    db.refresh(result)
    
    return result.to_dict(include_private=True)


@router.put("/{result_id}")
async def update_result(
    result_id: int,
    result_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Update a result (lecturer only)."""
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    for field, value in result_data.items():
        if hasattr(result, field):
            setattr(result, field, value)
    
    # Recalculate if score changed
    if "score" in result_data:
        result.update_calculated_fields()
    
    db.commit()
    db.refresh(result)
    
    return result.to_dict(include_private=True)


@router.put("/{result_id}/publish")
async def publish_result(
    result_id: int,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Publish a result to students (lecturer only)."""
    result = db.query(Result).filter(Result.id == result_id).first()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Result not found"
        )
    
    result.published = True
    result.published_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Result published successfully",
        "result_id": result_id,
    }
