"""
Students API Router

Handles student profile management and application processing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os
import uuid

from app.db.database import get_db
from app.core.config import settings, get_upload_path
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile, ApplicationStatus, StudySector
from app.schemas.student import (
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
    ApplicationSubmit,
    ApplicationStatusUpdate,
    FundingUpdate,
)


router = APIRouter()


def save_upload_file(file: UploadFile, subdirectory: str) -> str:
    """Save uploaded file and return relative path."""
    upload_dir = get_upload_path(subdirectory)
    
    # Generate unique filename
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_name)
    
    # Save file
    with open(file_path, "wb") as f:
        content = file.file.read()
        f.write(content)
    
    # Return relative path
    return os.path.join(subdirectory, unique_name)


@router.get("/profile", response_model=StudentProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current student's profile."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    profile = current_user.student_profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    return StudentProfileResponse.model_validate(profile)


@router.put("/profile", response_model=StudentProfileResponse)
async def update_my_profile(
    profile_data: StudentProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current student's profile."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    profile = current_user.student_profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Update fields
    for field, value in profile_data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return StudentProfileResponse.model_validate(profile)


@router.post("/application/submit")
async def submit_application(
    application: ApplicationSubmit,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit student application."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit applications"
        )
    
    profile = current_user.student_profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if already submitted or beyond
    if profile.application_status not in [ApplicationStatus.DRAFT, ApplicationStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Application already {profile.application_status.value}"
        )
    
    # Update profile with application data
    profile.id_number = application.id_number
    profile.date_of_birth = application.date_of_birth
    profile.address = application.address
    profile.city = application.city
    profile.postal_code = application.postal_code
    profile.emergency_contact_name = application.emergency_contact_name
    profile.emergency_contact_phone = application.emergency_contact_phone
    profile.sector = application.sector
    profile.previous_education = application.previous_education
    
    # Update status
    profile.application_status = ApplicationStatus.SUBMITTED
    profile.application_date = datetime.utcnow()
    
    db.commit()
    db.refresh(profile)
    
    return {
        "message": "Application submitted successfully",
        "application_status": profile.application_status.value,
        "application_date": profile.application_date.isoformat(),
    }


@router.get("/application/status")
async def get_application_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current application status."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this endpoint"
        )
    
    profile = current_user.student_profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Determine next steps based on status
    next_steps = {
        ApplicationStatus.DRAFT: "Complete and submit your application",
        ApplicationStatus.SUBMITTED: "Your application is under review",
        ApplicationStatus.UNDER_REVIEW: "We are reviewing your documents",
        ApplicationStatus.DOCUMENTS_REQUIRED: "Please upload required documents",
        ApplicationStatus.INTERVIEW_SCHEDULED: "Attend your scheduled interview",
        ApplicationStatus.ACCEPTED: "Complete enrollment to secure your place",
        ApplicationStatus.ENROLLED: "Welcome! Check your dashboard for next steps",
        ApplicationStatus.REJECTED: "Contact admissions for more information",
    }
    
    return {
        "status": profile.application_status.value,
        "status_display": profile.application_status.value.replace("_", " ").title(),
        "application_date": profile.application_date.isoformat() if profile.application_date else None,
        "sector": profile.sector.value if profile.sector else None,
        "sector_display": profile.sector_display,
        "funded": profile.funded,
        "funding_amount": profile.funding_amount,
        "funding_source": profile.funding_source,
        "next_steps": next_steps.get(profile.application_status, "Contact support for assistance"),
    }


@router.post("/documents/upload")
async def upload_document(
    document_type: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload a document for the student profile."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can upload documents"
        )
    
    profile = current_user.student_profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Validate file type
    file_ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
    if file_ext not in settings.allowed_extensions_list:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions_list)}"
        )
    
    # Save file
    relative_path = save_upload_file(file, "documents")
    
    # Update documents in profile
    if not profile.documents:
        profile.documents = {}
    
    profile.documents[document_type] = relative_path
    db.commit()
    
    return {
        "message": "Document uploaded successfully",
        "document_type": document_type,
        "file_path": relative_path,
    }


# Admin endpoints
@router.get("/applications/pending", response_model=List[dict])
async def get_pending_applications(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all pending applications (admin only)."""
    applications = db.query(StudentProfile).filter(
        StudentProfile.application_status.in_([
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.DOCUMENTS_REQUIRED,
        ])
    ).all()
    
    result = []
    for app in applications:
        result.append({
            "id": app.id,
            "student_name": app.user.full_name if app.user else None,
            "email": app.user.email if app.user else None,
            "phone": app.user.phone if app.user else None,
            "sector": app.sector.value if app.sector else None,
            "status": app.application_status.value,
            "application_date": app.application_date.isoformat() if app.application_date else None,
            "documents": app.documents,
        })
    
    return result


@router.put("/applications/{student_id}/status")
async def update_application_status(
    student_id: int,
    status_update: ApplicationStatusUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update application status (admin only)."""
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    old_status = profile.application_status
    profile.application_status = status_update.status
    
    # If accepted, set enrollment date
    if status_update.status == ApplicationStatus.ENROLLED and old_status != ApplicationStatus.ENROLLED:
        from datetime import date
        profile.enrollment_date = date.today()
        # Generate student number
        if not profile.student_number:
            year = date.today().year
            profile.student_number = f"STU{year}{profile.id:05d}"
    
    db.commit()
    
    return {
        "message": "Application status updated",
        "student_id": student_id,
        "old_status": old_status.value,
        "new_status": profile.application_status.value,
    }


@router.put("/applications/{student_id}/funding")
async def update_funding(
    student_id: int,
    funding: FundingUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update student funding information (admin only)."""
    profile = db.query(StudentProfile).filter(StudentProfile.id == student_id).first()
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    profile.funded = funding.funded
    profile.funding_amount = funding.funding_amount
    profile.funding_source = funding.funding_source
    profile.funding_reference = funding.funding_reference
    
    db.commit()
    
    return {
        "message": "Funding information updated",
        "student_id": student_id,
        "funded": profile.funded,
        "funding_amount": profile.funding_amount,
    }
