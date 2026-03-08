"""
Module Model

Course modules representing individual subjects or training units.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, 
    Enum, Float, Boolean
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.lecturer import Lecturer
    from app.models.student_profile import StudentProfile
    from app.models.timetable import TimetableSlot
    from app.models.assignment import Assignment
    from app.models.result import Result


class ModuleLevel(str, enum.Enum):
    """Module difficulty/level classification."""
    LEVEL_1 = "level_1"  # Introductory
    LEVEL_2 = "level_2"  # Intermediate
    LEVEL_3 = "level_3"  # Advanced
    LEVEL_4 = "level_4"  # Expert/Specialized


class ModuleStatus(str, enum.Enum):
    """Module availability status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DRAFT = "draft"


class StudySector(str, enum.Enum):
    """Study sectors - same as in student_profile."""
    DIESEL_MECHANIC = "diesel_mechanic"
    PLUMBING = "plumbing"
    ELECTRICIAN = "electrician"
    WELDING = "welding"
    ICT = "ict"


class Module(Base):
    """
    Module model representing a course subject or training unit.
    
    Modules are the building blocks of the curriculum. Each module
    belongs to a specific sector and is taught by a lecturer.
    
    Attributes:
        id: Primary key
        code: Unique module code (e.g., "DM101", "ICT201")
        title: Module name/title
        description: Detailed module description
        sector: Study sector this module belongs to
        level: Difficulty level
        credits: Credit value of the module
        duration_weeks: Duration in weeks
        theory_hours: Total theory hours
        practical_hours: Total practical hours
        prerequisites: Required prior modules
        learning_outcomes: Expected learning outcomes
        status: Module availability status
        lecturer_id: Assigned lecturer
    """
    
    __tablename__ = "modules"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Module Information
    code: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Classification
    sector: Mapped[StudySector] = mapped_column(
        Enum(StudySector),
        nullable=False
    )
    level: Mapped[ModuleLevel] = mapped_column(
        Enum(ModuleLevel),
        default=ModuleLevel.LEVEL_1,
        nullable=False
    )
    
    # Academic Details
    credits: Mapped[int] = mapped_column(Integer, default=10)
    duration_weeks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    theory_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    practical_hours: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Requirements & Outcomes
    prerequisites: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    learning_outcomes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assessment_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Resources
    required_materials: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    recommended_resources: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[ModuleStatus] = mapped_column(
        Enum(ModuleStatus),
        default=ModuleStatus.ACTIVE,
        nullable=False
    )
    
    # Assignment
    lecturer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lecturers.id"),
        nullable=True
    )
    
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
    lecturer: Mapped[Optional["Lecturer"]] = relationship(
        "Lecturer",
        back_populates="modules_taught",
        foreign_keys=[lecturer_id]
    )
    
    enrollments: Mapped[list["ModuleEnrollment"]] = relationship(
        "ModuleEnrollment",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    
    timetable_slots: Mapped[list["TimetableSlot"]] = relationship(
        "TimetableSlot",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    
    assignments: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="module",
        cascade="all, delete-orphan"
    )
    
    results: Mapped[list["Result"]] = relationship(
        "Result",
        back_populates="module"
    )
    
    def __repr__(self) -> str:
        """String representation of the Module."""
        return f"<Module(id={self.id}, code={self.code}, title={self.title})>"
    
    @property
    def sector_display(self) -> str:
        """Get human-readable sector name."""
        return self.sector.value.replace("_", " ").title()
    
    @property
    def level_display(self) -> str:
        """Get human-readable level name."""
        return self.level.value.replace("_", " ").title()
    
    @property
    def total_hours(self) -> Optional[int]:
        """Calculate total contact hours."""
        if self.theory_hours is not None and self.practical_hours is not None:
            return self.theory_hours + self.practical_hours
        return None
    
    @property
    def enrolled_students_count(self) -> int:
        """Get count of enrolled students."""
        return len([e for e in self.enrollments if e.status == EnrollmentStatus.ACTIVE])
    
    def to_dict(self) -> dict:
        """
        Convert module to dictionary.
        
        Returns:
            Dictionary representation of module
        """
        return {
            "id": self.id,
            "code": self.code,
            "title": self.title,
            "description": self.description,
            "sector": self.sector.value,
            "sector_display": self.sector_display,
            "level": self.level.value,
            "level_display": self.level_display,
            "credits": self.credits,
            "duration_weeks": self.duration_weeks,
            "theory_hours": self.theory_hours,
            "practical_hours": self.practical_hours,
            "total_hours": self.total_hours,
            "prerequisites": self.prerequisites,
            "learning_outcomes": self.learning_outcomes,
            "assessment_criteria": self.assessment_criteria,
            "required_materials": self.required_materials,
            "recommended_resources": self.recommended_resources,
            "status": self.status.value,
            "lecturer_id": self.lecturer_id,
            "lecturer_name": self.lecturer.full_name if self.lecturer else None,
            "enrolled_students": self.enrolled_students_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class EnrollmentStatus(str, enum.Enum):
    """Student enrollment status in a module."""
    PENDING = "pending"        # Awaiting approval
    ACTIVE = "active"          # Currently enrolled
    COMPLETED = "completed"    # Successfully completed
    WITHDRAWN = "withdrawn"    # Student withdrew
    SUSPENDED = "suspended"    # Enrollment suspended
    FAILED = "failed"          # Did not pass module


class ModuleEnrollment(Base):
    """
    Module enrollment linking students to modules.
    
    This junction table tracks student enrollments with status
    and enrollment dates.
    
    Attributes:
        id: Primary key
        student_id: Foreign key to StudentProfile
        module_id: Foreign key to Module
        status: Enrollment status
        enrollment_date: When student enrolled
        completion_date: When student completed
        final_grade: Final grade achieved
        notes: Additional notes
    """
    
    __tablename__ = "module_enrollments"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Enrollment Details
    status: Mapped[EnrollmentStatus] = mapped_column(
        Enum(EnrollmentStatus),
        default=EnrollmentStatus.PENDING,
        nullable=False
    )
    enrollment_date: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    completion_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    final_grade: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Additional Information
    semester: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    academic_year: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="module_enrollments"
    )
    
    module: Mapped["Module"] = relationship(
        "Module",
        back_populates="enrollments"
    )
    
    # Unique constraint to prevent duplicate enrollments
    __table_args__ = (
        # Ensure a student can only be enrolled once per module
        # (though they can re-enroll after withdrawal with a new record)
    )
    
    def __repr__(self) -> str:
        """String representation of the ModuleEnrollment."""
        return f"<ModuleEnrollment(id={self.id}, student={self.student_id}, module={self.module_id})>"
    
    def to_dict(self) -> dict:
        """
        Convert enrollment to dictionary.
        
        Returns:
            Dictionary representation of enrollment
        """
        return {
            "id": self.id,
            "student_id": self.student_id,
            "module_id": self.module_id,
            "module_code": self.module.code if self.module else None,
            "module_title": self.module.title if self.module else None,
            "status": self.status.value,
            "enrollment_date": self.enrollment_date.isoformat() if self.enrollment_date else None,
            "completion_date": self.completion_date.isoformat() if self.completion_date else None,
            "final_grade": self.final_grade,
            "semester": self.semester,
            "academic_year": self.academic_year,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
