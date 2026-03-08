"""
Attendance Schemas

Pydantic schemas for attendance and hours logging.
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

from app.models.attendance import AttendanceStatus, AttendanceMethod, HoursLogStatus


# Attendance Check-in Schemas
class AttendanceCheckInRequest(BaseModel):
    """Schema for attendance check-in request."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    module_id: Optional[int] = None
    notes: Optional[str] = None


class AttendanceCheckOutRequest(BaseModel):
    """Schema for attendance check-out request."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    accuracy: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = None


class AttendanceResponse(BaseModel):
    """Schema for attendance record response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    student_id: int
    module_id: Optional[int] = None
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    duration_hours: Optional[float] = None
    check_in_location: Optional[dict] = None
    check_out_location: Optional[dict] = None
    distance_from_venue: Optional[float] = None
    method: AttendanceMethod
    status: AttendanceStatus
    verified: bool
    verification_notes: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class AttendanceListResponse(BaseModel):
    """Schema for list of attendance records."""
    records: List[AttendanceResponse]
    total: int
    page: int
    per_page: int


class AttendanceSummaryResponse(BaseModel):
    """Schema for attendance summary."""
    student_id: int
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    
    total_sessions: int
    attended: int
    absent: int
    late: int
    excused: int
    
    attendance_rate: float
    total_hours: float
    
    by_module: List[dict] = []


# Hours Log Schemas
class HoursLogCreate(BaseModel):
    """Schema for creating hours log entry."""
    module_id: Optional[int] = None
    date: date
    hours_worked: float = Field(..., gt=0, le=24)
    description: str = Field(..., min_length=10)
    skills_practiced: Optional[str] = None
    equipment_used: Optional[str] = None


class HoursLogUpdate(BaseModel):
    """Schema for updating hours log entry."""
    hours_worked: Optional[float] = Field(None, gt=0, le=24)
    description: Optional[str] = Field(None, min_length=10)
    skills_practiced: Optional[str] = None
    equipment_used: Optional[str] = None


class HoursLogApproval(BaseModel):
    """Schema for approving/rejecting hours log."""
    status: HoursLogStatus
    rejection_reason: Optional[str] = None


class HoursLogResponse(BaseModel):
    """Schema for hours log response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    student_id: int
    module_id: Optional[int] = None
    module_code: Optional[str] = None
    module_title: Optional[str] = None
    date: date
    hours_worked: float
    description: str
    skills_practiced: Optional[str] = None
    equipment_used: Optional[str] = None
    status: HoursLogStatus
    submitted_at: datetime
    approved_by_id: Optional[int] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    created_at: datetime


class HoursLogListResponse(BaseModel):
    """Schema for list of hours logs."""
    logs: List[HoursLogResponse]
    total: int
    page: int
    per_page: int
    total_hours: float
    approved_hours: float
    pending_hours: float


# Geofence Schemas
class GeofenceStatusResponse(BaseModel):
    """Schema for geofence check response."""
    inside_campus: bool
    distance_from_center: float  # meters
    campus_center: dict  # {lat, lng}
    campus_radius: float  # meters
    nearest_venue: Optional[dict] = None
    can_check_in: bool
    message: str


class VenueResponse(BaseModel):
    """Schema for venue response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    code: str
    building: str
    floor: Optional[int] = None
    room_number: Optional[str] = None
    full_location: str
    venue_type: str
    capacity: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    facilities: Optional[str] = None
    is_active: bool


class CampusMapPointResponse(BaseModel):
    """Schema for campus map point response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    point_type: str
    building: str
    floor: Optional[int] = None
    room_number: Optional[str] = None
    full_location: str
    lat: float
    lng: float
    icon: Optional[str] = None
    color: str
    is_accessible: bool
    has_parking: bool
    has_wifi: bool
    operating_hours: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
