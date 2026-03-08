"""
Assignments API Router

Handles assignment creation, submission, and grading.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import os

from app.db.database import get_db
from app.core.config import settings, get_upload_path
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.assignment import Assignment, Submission, AssignmentType, SubmissionStatus


router = APIRouter()


@router.get("/my")
async def get_my_assignments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assignments for current student's enrolled modules."""
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
    
    # Get enrolled module IDs
    enrolled_module_ids = [e.module_id for e in student.module_enrollments]
    
    # Get assignments for enrolled modules
    assignments = db.query(Assignment).filter(
        Assignment.module_id.in_(enrolled_module_ids),
        Assignment.is_published == True
    ).order_by(Assignment.due_date).all()
    
    result = []
    for assignment in assignments:
        # Check submission status
        submission = db.query(Submission).filter(
            Submission.assignment_id == assignment.id,
            Submission.student_id == student.id
        ).first()
        
        result.append({
            "id": assignment.id,
            "title": assignment.title,
            "module_code": assignment.module.code if assignment.module else None,
            "module_title": assignment.module.title if assignment.module else None,
            "assignment_type": assignment.assignment_type.value,
            "due_date": assignment.due_date.isoformat(),
            "is_overdue": assignment.is_overdue,
            "max_score": assignment.max_score,
            "submitted": submission is not None,
            "submission_status": submission.status.value if submission else "not_submitted",
            "grade": submission.grade if submission else None,
            "percentage": submission.percentage if submission else None,
        })
    
    return result


@router.get("/{assignment_id}")
async def get_assignment(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get assignment details."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if student is enrolled in the module
    if current_user.is_student:
        student = current_user.student_profile
        enrolled = any(e.module_id == assignment.module_id for e in student.module_enrollments)
        if not enrolled and not assignment.is_published:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not enrolled in this module"
            )
    
    return assignment.to_dict()


@router.post("/{assignment_id}/submit")
async def submit_assignment(
    assignment_id: int,
    text_content: Optional[str] = None,
    file: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit an assignment."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit assignments"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    # Check if already submitted
    existing = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == student.id
    ).first()
    
    if existing and existing.status == SubmissionStatus.GRADED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assignment already graded. Contact lecturer for regrade."
        )
    
    # Handle file upload
    file_path = None
    file_name = None
    file_size = None
    file_type = None
    
    if file:
        # Validate file type
        file_ext = os.path.splitext(file.filename)[1].lower().replace(".", "")
        if file_ext not in settings.allowed_extensions_list:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file type. Allowed: {', '.join(settings.allowed_extensions_list)}"
            )
        
        # Save file
        upload_dir = get_upload_path("assignments")
        import uuid
        unique_name = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(upload_dir, unique_name)
        
        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)
            file_size = len(content)
        
        file_name = file.filename
        file_type = file_ext
    
    # Create or update submission
    if existing:
        existing.text_content = text_content
        if file_path:
            existing.file_path = file_path
            existing.file_name = file_name
            existing.file_size = file_size
            existing.file_type = file_type
        existing.submitted_at = datetime.utcnow()
        existing.is_late = assignment.is_overdue
        existing.status = SubmissionStatus.SUBMITTED
        db.commit()
        submission = existing
    else:
        submission = Submission(
            assignment_id=assignment_id,
            student_id=student.id,
            text_content=text_content,
            file_path=file_path,
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            is_late=assignment.is_overdue,
            status=SubmissionStatus.SUBMITTED,
        )
        db.add(submission)
        db.commit()
        db.refresh(submission)
    
    return {
        "message": "Assignment submitted successfully",
        "submission_id": submission.id,
        "submitted_at": submission.submitted_at.isoformat(),
        "is_late": submission.is_late,
    }


@router.get("/{assignment_id}/submission")
async def get_my_submission(
    assignment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current student's submission for an assignment."""
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
    
    submission = db.query(Submission).filter(
        Submission.assignment_id == assignment_id,
        Submission.student_id == student.id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    return submission.to_dict(include_feedback=True)


# Lecturer endpoints
@router.post("/")
async def create_assignment(
    assignment_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Create a new assignment (lecturer only)."""
    lecturer = current_user.lecturer_profile
    if not lecturer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecturer profile not found"
        )
    
    from datetime import datetime
    
    assignment = Assignment(
        module_id=assignment_data.get("module_id"),
        created_by_id=lecturer.id,
        title=assignment_data.get("title"),
        description=assignment_data.get("description"),
        assignment_type=assignment_data.get("assignment_type", AssignmentType.HOMEWORK),
        due_date=datetime.fromisoformat(assignment_data.get("due_date")),
        max_score=assignment_data.get("max_score", 100),
        weight=assignment_data.get("weight"),
        instructions=assignment_data.get("instructions"),
        allow_late_submission=assignment_data.get("allow_late_submission", False),
        late_penalty_percent=assignment_data.get("late_penalty_percent", 0),
        is_published=assignment_data.get("is_published", False),
    )
    
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    
    return assignment.to_dict()


@router.get("/{assignment_id}/submissions")
async def get_assignment_submissions(
    assignment_id: int,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Get all submissions for an assignment (lecturer only)."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assignment not found"
        )
    
    submissions = db.query(Submission).filter(
        Submission.assignment_id == assignment_id
    ).all()
    
    return [s.to_dict(include_feedback=True) for s in submissions]


@router.put("/{assignment_id}/submissions/{submission_id}/grade")
async def grade_submission(
    assignment_id: int,
    submission_id: int,
    grade_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Grade a submission (lecturer only)."""
    submission = db.query(Submission).filter(
        Submission.id == submission_id,
        Submission.assignment_id == assignment_id
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    lecturer = current_user.lecturer_profile
    
    submission.grade = grade_data.get("grade")
    submission.percentage = submission.calculate_percentage()
    submission.feedback = grade_data.get("feedback")
    submission.private_notes = grade_data.get("private_notes")
    submission.graded_by_id = lecturer.id if lecturer else None
    submission.graded_at = datetime.utcnow()
    submission.status = SubmissionStatus.GRADED
    
    db.commit()
    
    return {
        "message": "Submission graded successfully",
        "submission_id": submission_id,
        "grade": submission.grade,
        "percentage": submission.percentage,
    }
