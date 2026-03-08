"""
Student Profile Schemas

Pydantic schemas for student profile operations.
"""

from datetime import date, datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

from app.models.student_profile import ApplicationStatus, StudySector


# Base schema
class StudentProfileBase(BaseModel):
    """Base student profile schema."""
    id_number: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    sector: Optional[StudySector] = None


# Request schemas
class StudentProfileCreate(StudentProfileBase):
    """Schema for creating student profile."""
    pass


class StudentProfileUpdate(BaseModel):
    """Schema for updating student profile."""
    id_number: Optional[str] = Field(None, max_length=20)
    date_of_birth: Optional[date] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=10)
    emergency_contact_name: Optional[str] = Field(None, max_length=100)
    emergency_contact_phone: Optional[str] = Field(None, max_length=20)
    emergency_contact_relationship: Optional[str] = Field(None, max_length=50)
    sector: Optional[StudySector] = None
    previous_education: Optional[str] = None
    work_experience: Optional[str] = None
    special_requirements: Optional[str] = None


class ApplicationSubmit(BaseModel):
    """Schema for submitting application."""
    sector: StudySector
    id_number: str = Field(..., max_length=20)
    date_of_birth: date
    address: str
    city: str = Field(..., max_length=100)
    postal_code: str = Field(..., max_length=10)
    emergency_contact_name: str = Field(..., max_length=100)
    emergency_contact_phone: str = Field(..., max_length=20)
    previous_education: Optional[str] = None


class ApplicationStatusUpdate(BaseModel):
    """Schema for updating application status (admin only)."""
    status: ApplicationStatus
    notes: Optional[str] = None


class FundingUpdate(BaseModel):
    """Schema for updating funding information."""
    funded: bool
    funding_amount: Optional[float] = None
    funding_source: Optional[str] = Field(None, max_length=100)
    funding_reference: Optional[str] = Field(None, max_length=50)


# Response schemas
class StudentProfileResponse(StudentProfileBase):
    """Schema for student profile response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    student_number: Optional[str] = None
    application_status: ApplicationStatus
    application_date: Optional[datetime] = None
    enrollment_date: Optional[date] = None
    expected_graduation_date: Optional[date] = None
    funded: bool
    funding_amount: Optional[float] = None
    funding_source: Optional[str] = None
    funding_reference: Optional[str] = None
    documents: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    sector_display: Optional[str] = None
    age: Optional[int] = None


class StudentDetailResponse(StudentProfileResponse):
    """Detailed student response with user info."""
    user: Optional[dict] = None
    module_enrollments: List[dict] = []
    attendance_summary: Optional[dict] = None
    results_summary: Optional[dict] = None


class ApplicationStatusResponse(BaseModel):
    """Schema for application status response."""
    status: ApplicationStatus
    status_display: str
    application_date: Optional[datetime] = None
    sector: Optional[str] = None
    sector_display: Optional[str] = None
    funded: bool
    funding_amount: Optional[float] = None
    funding_source: Optional[str] = None
    next_steps: Optional[str] = None


class FundingStatusResponse(BaseModel):
    """Schema for funding status response."""
    funded: bool
    funding_amount: Optional[float] = None
    funding_source: Optional[str] = None
    funding_reference: Optional[str] = None
    application_status: ApplicationStatus


# Dashboard schema
class StudentDashboardResponse(BaseModel):
    """Schema for student dashboard data."""
    student: StudentProfileResponse
    user: dict
    
    # Enrolled modules
    enrolled_modules: List[dict] = []
    
    # Upcoming events
    upcoming_classes: List[dict] = []
    upcoming_assignments: List[dict] = []
    
    # Announcements
    announcements: List[dict] = []
    
    # Attendance summary
    attendance_summary: dict = {
        "total_sessions": 0,
        "attended": 0,
        "absent": 0,
        "attendance_rate": 0.0,
    }
    
    # Results summary
    results_summary: dict = {
        "modules_completed": 0,
        "average_grade": 0.0,
        "current_gpa": 0.0,
    }
    
    # Helpdesk
    open_tickets: int = 0
    recent_tickets: List[dict] = []
    
    # Funding
    funding_status: Optional[FundingStatusResponse] = None
    
    # Application progress
    application_progress: Optional[dict] = None
