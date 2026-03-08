"""
Lecturer Model

Profile information for lecturer/instructor users.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, Text, Enum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.module import Module
    from app.models.assignment import Assignment
    from app.models.attendance import HoursLog


class Department(str, enum.Enum):
    """
    Enumeration of academic departments.
    
    Departments organize lecturers and modules by subject area.
    """
    DIESEL_MECHANICS = "diesel_mechanics"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    WELDING = "welding"
    ICT = "ict"
    GENERAL_STUDIES = "general_studies"
    ADMINISTRATION = "administration"


class Lecturer(Base):
    """
    Lecturer profile model containing instructor information.
    
    This model stores lecturer-specific data including department,
    qualifications, and module assignments.
    
    Attributes:
        id: Primary key
        user_id: Foreign key to User model
        employee_number: Internal employee ID
        department: Academic department
        qualification: Highest qualification
        specialization: Area of specialization
        biography: Brief professional biography
        office_location: Office room/location
        office_hours: Available office hours
        hire_date: Date of employment
        is_full_time: Whether lecturer is full-time
    """
    
    __tablename__ = "lecturers"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Link to User
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    
    # Employment Information
    employee_number: Mapped[Optional[str]] = mapped_column(
        String(20),
        unique=True,
        nullable=True
    )
    department: Mapped[Optional[Department]] = mapped_column(
        Enum(Department),
        nullable=True
    )
    
    # Professional Information
    qualification: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    specialization: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    certification: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    years_of_experience: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Contact & Availability
    biography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    office_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    office_hours: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Employment Status
    hire_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    is_full_time: Mapped[bool] = mapped_column(Boolean, default=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
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
    user: Mapped["User"] = relationship("User", back_populates="lecturer_profile")
    
    modules_taught: Mapped[list["Module"]] = relationship(
        "Module",
        back_populates="lecturer",
        foreign_keys="Module.lecturer_id"
    )
    
    assignments_created: Mapped[list["Assignment"]] = relationship(
        "Assignment",
        back_populates="created_by"
    )
    
    hours_approved: Mapped[list["HoursLog"]] = relationship(
        "HoursLog",
        back_populates="approved_by"
    )
    
    def __repr__(self) -> str:
        """String representation of the Lecturer."""
        return f"<Lecturer(id={self.id}, user_id={self.user_id}, dept={self.department})>"
    
    @property
    def department_display(self) -> Optional[str]:
        """Get human-readable department name."""
        if self.department:
            return self.department.value.replace("_", " ").title()
        return None
    
    @property
    def full_name(self) -> str:
        """Get lecturer's full name from user."""
        if self.user:
            return self.user.full_name
        return "Unknown"
    
    @property
    def email(self) -> Optional[str]:
        """Get lecturer's email from user."""
        if self.user:
            return self.user.email
        return None
    
    def to_dict(self) -> dict:
        """
        Convert lecturer profile to dictionary.
        
        Returns:
            Dictionary representation of lecturer profile
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "employee_number": self.employee_number,
            "full_name": self.full_name,
            "email": self.email,
            "department": self.department.value if self.department else None,
            "department_display": self.department_display,
            "qualification": self.qualification,
            "specialization": self.specialization,
            "certification": self.certification,
            "years_of_experience": self.years_of_experience,
            "biography": self.biography,
            "office_location": self.office_location,
            "office_hours": self.office_hours,
            "hire_date": self.hire_date.isoformat() if self.hire_date else None,
            "is_full_time": self.is_full_time,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
