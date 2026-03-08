"""
Modules API Router

Handles module management and enrollment.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.module import Module, ModuleEnrollment, ModuleStatus, EnrollmentStatus
from app.models.student_profile import StudentProfile


router = APIRouter()


@router.get("/")
async def get_modules(
    sector: Optional[str] = None,
    level: Optional[str] = None,
    status: Optional[str] = ModuleStatus.ACTIVE,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all modules with optional filtering."""
    query = db.query(Module)
    
    if sector:
        query = query.filter(Module.sector == sector)
    
    if level:
        query = query.filter(Module.level == level)
    
    if status:
        query = query.filter(Module.status == status)
    
    modules = query.all()
    
    return [m.to_dict() for m in modules]


@router.get("/{module_id}")
async def get_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get module details by ID."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    return module.to_dict()


@router.get("/{module_id}/timetable")
async def get_module_timetable(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timetable for a specific module."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    slots = module.timetable_slots
    return [s.to_dict() for s in slots if s.is_active and not s.is_cancelled]


@router.get("/{module_id}/assignments")
async def get_module_assignments(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assignments for a specific module."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    assignments = [a for a in module.assignments if a.is_published]
    return [a.to_dict() for a in assignments]


# Student enrollment endpoints
@router.post("/{module_id}/enroll")
async def enroll_in_module(
    module_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enroll current student in a module."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can enroll in modules"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    # Check if already enrolled
    existing = db.query(ModuleEnrollment).filter(
        ModuleEnrollment.student_id == student.id,
        ModuleEnrollment.module_id == module_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already enrolled in this module"
        )
    
    # Create enrollment
    enrollment = ModuleEnrollment(
        student_id=student.id,
        module_id=module_id,
        status=EnrollmentStatus.ACTIVE,
    )
    
    db.add(enrollment)
    db.commit()
    
    return {
        "message": "Successfully enrolled in module",
        "module_id": module_id,
        "module_code": module.code,
        "module_title": module.title,
    }


@router.get("/my/enrolled")
async def get_my_enrolled_modules(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get modules enrolled by current student."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access enrolled modules"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    enrollments = db.query(ModuleEnrollment).filter(
        ModuleEnrollment.student_id == student.id
    ).all()
    
    result = []
    for enrollment in enrollments:
        module = enrollment.module
        if module:
            result.append({
                "enrollment_id": enrollment.id,
                "status": enrollment.status.value,
                "enrollment_date": enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
                "module": module.to_dict(),
            })
    
    return result


# Admin endpoints
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_module(
    module_data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new module (admin only)."""
    module = Module(
        code=module_data.get("code"),
        title=module_data.get("title"),
        description=module_data.get("description"),
        sector=module_data.get("sector"),
        level=module_data.get("level"),
        credits=module_data.get("credits", 10),
        theory_hours=module_data.get("theory_hours"),
        practical_hours=module_data.get("practical_hours"),
        lecturer_id=module_data.get("lecturer_id"),
    )
    
    db.add(module)
    db.commit()
    db.refresh(module)
    
    return module.to_dict()


@router.put("/{module_id}")
async def update_module(
    module_id: int,
    module_data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update a module (admin only)."""
    module = db.query(Module).filter(Module.id == module_id).first()
    if not module:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Module not found"
        )
    
    for field, value in module_data.items():
        if hasattr(module, field):
            setattr(module, field, value)
    
    db.commit()
    db.refresh(module)
    
    return module.to_dict()
