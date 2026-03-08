"""
Assignment Model

Assignment creation, submission, and grading system.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Float, Boolean, JSON, Enum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.module import Module
    from app.models.lecturer import Lecturer
    from app.models.student_profile import StudentProfile


class AssignmentType(str, enum.Enum):
    """Type of assignment."""
    HOMEWORK = "homework"
    PROJECT = "project"
    LAB_REPORT = "lab_report"
    QUIZ = "quiz"
    TEST = "test"
    EXAM = "exam"
    PRACTICAL = "practical"
    PORTFOLIO = "portfolio"
    PRESENTATION = "presentation"


class SubmissionStatus(str, enum.Enum):
    """Submission status."""
    NOT_SUBMITTED = "not_submitted"
    SUBMITTED = "submitted"
    LATE = "late"
    GRADED = "graded"
    PENDING_REGRADE = "pending_regrade"


class Assignment(Base):
    """
    Assignment model representing a task given to students.
    
    Attributes:
        id: Primary key
        module_id: Associated module
        created_by_id: Lecturer who created it
        title: Assignment title
        description: Detailed description
        assignment_type: Type of assignment
        due_date: When it's due
        max_score: Maximum possible score
        weight: Weight towards final grade (%)
        attachments: File references
        instructions: Detailed instructions
        resources: Additional resources
        allow_late_submission: Whether late submissions allowed
        late_penalty_percent: Penalty for late submission
        is_published: Whether visible to students
        is_group_assignment: Whether group work
        max_group_size: Maximum group size
    """
    
    __tablename__ = "assignments"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("lecturers.id"),
        nullable=False
    )
    
    # Assignment Details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignment_type: Mapped[AssignmentType] = mapped_column(
        Enum(AssignmentType),
        default=AssignmentType.HOMEWORK,
        nullable=False
    )
    
    # Timing
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    available_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Scoring
    max_score: Mapped[float] = mapped_column(default=100.0)
    weight: Mapped[Optional[float]] = mapped_column(nullable=True)
    pass_mark: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Content
    instructions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    attachments: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rubric: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Submission Settings
    allow_late_submission: Mapped[bool] = mapped_column(default=False)
    late_penalty_percent: Mapped[float] = mapped_column(default=0.0)
    max_file_size_mb: Mapped[int] = mapped_column(default=10)
    allowed_file_types: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Group Settings
    is_group_assignment: Mapped[bool] = mapped_column(default=False)
    max_group_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Status
    is_published: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    module: Mapped["Module"] = relationship("Module", back_populates="assignments")
    created_by: Mapped["Lecturer"] = relationship("Lecturer", back_populates="assignments_created")
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="assignment",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Assignment(id={self.id}, title={self.title}, module={self.module_id})>"
    
    @property
    def is_overdue(self) -> bool:
        """Check if assignment is past due date."""
        return datetime.now() > self.due_date
    
    @property
    def submission_count(self) -> int:
        """Get number of submissions received."""
        return len([s for s in self.submissions if s.status != SubmissionStatus.NOT_SUBMITTED])
    
    @property
    def graded_count(self) -> int:
        """Get number of graded submissions."""
        return len([s for s in self.submissions if s.status == SubmissionStatus.GRADED])
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "module_id": self.module_id,
            "module_code": self.module.code if self.module else None,
            "module_title": self.module.title if self.module else None,
            "created_by_id": self.created_by_id,
            "created_by_name": self.created_by.full_name if self.created_by else None,
            "title": self.title,
            "description": self.description,
            "assignment_type": self.assignment_type.value,
            "due_date": self.due_date.isoformat(),
            "available_from": self.available_from.isoformat() if self.available_from else None,
            "is_overdue": self.is_overdue,
            "max_score": self.max_score,
            "weight": self.weight,
            "pass_mark": self.pass_mark,
            "instructions": self.instructions,
            "attachments": self.attachments or {},
            "resources": self.resources,
            "rubric": self.rubric,
            "allow_late_submission": self.allow_late_submission,
            "late_penalty_percent": self.late_penalty_percent,
            "max_file_size_mb": self.max_file_size_mb,
            "allowed_file_types": self.allowed_file_types,
            "is_group_assignment": self.is_group_assignment,
            "max_group_size": self.max_group_size,
            "is_published": self.is_published,
            "is_active": self.is_active,
            "submission_count": self.submission_count,
            "graded_count": self.graded_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Submission(Base):
    """
    Student submission for an assignment.
    
    Attributes:
        id: Primary key
        assignment_id: Associated assignment
        student_id: Student who submitted
        submitted_at: When submitted
        file_path: Path to uploaded file
        file_name: Original file name
        file_size: File size in bytes
        text_content: Text submission content
        status: Submission status
        grade: Assigned grade
        feedback: Lecturer feedback
        graded_by: Who graded it
        graded_at: When graded
        is_late: Whether submitted after deadline
    """
    
    __tablename__ = "submissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    assignment_id: Mapped[int] = mapped_column(
        ForeignKey("assignments.id", ondelete="CASCADE"),
        nullable=False
    )
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    graded_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lecturers.id"),
        nullable=True
    )
    
    # Submission Content
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    file_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    text_content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus),
        default=SubmissionStatus.SUBMITTED,
        nullable=False
    )
    is_late: Mapped[bool] = mapped_column(default=False)
    
    # Grading
    grade: Mapped[Optional[float]] = mapped_column(nullable=True)
    percentage: Mapped[Optional[float]] = mapped_column(nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    private_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    graded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Plagiarism Check
    plagiarism_score: Mapped[Optional[float]] = mapped_column(nullable=True)
    plagiarism_report: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    assignment: Mapped["Assignment"] = relationship("Assignment", back_populates="submissions")
    student: Mapped["StudentProfile"] = relationship("StudentProfile", back_populates="submissions")
    graded_by: Mapped[Optional["Lecturer"]] = relationship("Lecturer")
    
    def __repr__(self) -> str:
        return f"<Submission(id={self.id}, assignment={self.assignment_id}, student={self.student_id})>"
    
    @property
    def has_file(self) -> bool:
        """Check if submission includes a file."""
        return self.file_path is not None
    
    @property
    def has_text(self) -> bool:
        """Check if submission includes text."""
        return self.text_content is not None and len(self.text_content.strip()) > 0
    
    @property
    def is_graded(self) -> bool:
        """Check if submission has been graded."""
        return self.status == SubmissionStatus.GRADED and self.grade is not None
    
    def calculate_percentage(self) -> Optional[float]:
        """Calculate percentage score."""
        if self.grade is not None and self.assignment:
            return round((self.grade / self.assignment.max_score) * 100, 2)
        return None
    
    def to_dict(self, include_feedback: bool = True) -> dict:
        """
        Convert submission to dictionary.
        
        Args:
            include_feedback: Whether to include feedback (for student view)
            
        Returns:
            Dictionary representation
        """
        data = {
            "id": self.id,
            "assignment_id": self.assignment_id,
            "assignment_title": self.assignment.title if self.assignment else None,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "submitted_at": self.submitted_at.isoformat(),
            "file": {
                "name": self.file_name,
                "size": self.file_size,
                "type": self.file_type,
                "has_file": self.has_file,
            } if self.has_file else None,
            "text_content": self.text_content if self.has_text else None,
            "has_text": self.has_text,
            "status": self.status.value,
            "is_late": self.is_late,
            "is_graded": self.is_graded,
            "grade": self.grade,
            "percentage": self.percentage or self.calculate_percentage(),
            "graded_by_name": self.graded_by.full_name if self.graded_by else None,
            "graded_at": self.graded_at.isoformat() if self.graded_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        
        if include_feedback:
            data["feedback"] = self.feedback
            data["private_notes"] = self.private_notes
            
        return data
