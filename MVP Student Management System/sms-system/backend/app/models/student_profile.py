"""
Student Profile Model

Extended profile information for student users including
application details, funding status, and enrollment information.
"""

from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, Date, Boolean, 
    ForeignKey, Text, JSON, Enum, Float
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.module import ModuleEnrollment
    from app.models.attendance import AttendanceRecord, HoursLog
    from app.models.assignment import Submission
    from app.models.result import Result


class ApplicationStatus(str, enum.Enum):
    """
    Enumeration of possible application statuses.
    
    Tracks the progress of a student's application through the admission process.
    """
    DRAFT = "draft"                    # Application started but not submitted
    SUBMITTED = "submitted"            # Application submitted, awaiting review
    UNDER_REVIEW = "under_review"      # Application being reviewed
    DOCUMENTS_REQUIRED = "documents_required"  # Additional documents needed
    INTERVIEW_SCHEDULED = "interview_scheduled"  # Interview scheduled
    ACCEPTED = "accepted"              # Application accepted
    REJECTED = "rejected"              # Application rejected
    ENROLLED = "enrolled"              # Student enrolled and active
    WITHDRAWN = "withdrawn"            # Student withdrew application
    SUSPENDED = "suspended"            # Enrollment suspended
    GRADUATED = "graduated"            # Student graduated


class StudySector(str, enum.Enum):
    """
    Enumeration of available study sectors/trades.
    
    These are the vocational training areas offered by the college.
    """
    DIESEL_MECHANIC = "diesel_mechanic"
    PLUMBING = "plumbing"
    ELECTRICIAN = "electrician"
    WELDING = "welding"
    ICT = "ict"


class StudentProfile(Base):
    """
    Student profile model containing extended student information.
    
    This model stores all student-specific data including personal details,
    application status, funding information, and enrollment details.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User model
        id_number: National ID or passport number
        date_of_birth: Student's date of birth
        address: Physical address
        city: City of residence
        postal_code: Postal code
        emergency_contact_name: Emergency contact person
        emergency_contact_phone: Emergency contact phone
        sector: Selected study sector/trade
        application_status: Current application status
        application_date: Date application was submitted
        enrollment_date: Date of enrollment (if accepted)
        funded: Whether student receives funding
        funding_amount: Amount of funding received
        funding_source: Source of funding (e.g., NSFAS, bursary)
        documents: JSON field for document references
        notes: Additional notes about the student
    """
    
    __tablename__ = "student_profiles"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Link to User
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Personal Information
    id_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Address
    address: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    postal_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    
    # Emergency Contact
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    emergency_contact_relationship: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Academic Information
    sector: Mapped[Optional[StudySector]] = mapped_column(
        Enum(StudySector),
        nullable=True
    )
    
    # Application Status
    application_status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus),
        default=ApplicationStatus.DRAFT,
        nullable=False
    )
    application_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Enrollment Information
    enrollment_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    expected_graduation_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    student_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )
    
    # Funding Information
    funded: Mapped[bool] = mapped_column(Boolean, default=False)
    funding_amount: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    funding_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    funding_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Documents (JSON structure for flexibility)
    # Format: {"id_document": "path/to/file.pdf", "matric_certificate": "path/to/file.pdf", ...}
    documents: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    
    # Additional Information
    previous_education: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    work_experience: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    special_requirements: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    user: Mapped["User"] = relationship("User", back_populates="student_profile")
    
    module_enrollments: Mapped[list["ModuleEnrollment"]] = relationship(
        "ModuleEnrollment",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    
    attendance_records: Mapped[list["AttendanceRecord"]] = relationship(
        "AttendanceRecord",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    
    hours_logs: Mapped[list["HoursLog"]] = relationship(
        "HoursLog",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission",
        back_populates="student"
    )
    
    results: Mapped[list["Result"]] = relationship(
        "Result",
        back_populates="student",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        """String representation of the StudentProfile."""
        return f"<StudentProfile(id={self.id}, user_id={self.user_id}, status={self.application_status.value})>"
    
    @property
    def sector_display(self) -> Optional[str]:
        """Get human-readable sector name."""
        if self.sector:
            return self.sector.value.replace("_", " ").title()
        return None
    
    @property
    def age(self) -> Optional[int]:
        """Calculate student's age."""
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - (
                (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
            )
        return None
    
    @property
    is_enrolled(self) -> bool:
        """Check if student is currently enrolled."""
        return self.application_status == ApplicationStatus.ENROLLED
    
    def to_dict(self) -> dict:
        """
        Convert student profile to dictionary.
        
        Returns:
            Dictionary representation of student profile
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "student_number": self.student_number,
            "id_number": self.id_number,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "age": self.age,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "emergency_contact": {
                "name": self.emergency_contact_name,
                "phone": self.emergency_contact_phone,
                "relationship": self.emergency_contact_relationship,
            } if self.emergency_contact_name else None,
            "sector": self.sector.value if self.sector else None,
            "sector_display": self.sector_display,
            "application_status": self.application_status.value,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "enrollment_date": self.enrollment_date.isoformat() if self.enrollment_date else None,
            "expected_graduation_date": self.expected_graduation_date.isoformat() if self.expected_graduation_date else None,
            "funded": self.funded,
            "funding_amount": self.funding_amount,
            "funding_source": self.funding_source,
            "funding_reference": self.funding_reference,
            "documents": self.documents or {},
            "previous_education": self.previous_education,
            "work_experience": self.work_experience,
            "special_requirements": self.special_requirements,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
