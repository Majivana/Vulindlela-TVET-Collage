"""
Attendance Model

Student attendance tracking with geolocation verification.
"""

from datetime import datetime, date, time
from typing import Optional, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Date, Time, Enum, Float, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.student_profile import StudentProfile
    from app.models.module import Module
    from app.models.lecturer import Lecturer


class AttendanceStatus(str, enum.Enum):
    """Attendance status options."""
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    EXCUSED = "excused"
    PENDING = "pending"


class AttendanceMethod(str, enum.Enum):
    """Method used for attendance recording."""
    AUTO_GEOFENCE = "auto_geofence"      # Automatic via geolocation
    MANUAL = "manual"                     # Manual entry by lecturer
    QR_CODE = "qr_code"                   # QR code scan
    BIOMETRIC = "biometric"               # Fingerprint/face scan
    SELF_REPORTED = "self_reported"       # Student self-report


class AttendanceRecord(Base):
    """
    Attendance record for a student at a specific time.
    
    Records check-in/check-out with geolocation data for verification.
    
    Attributes:
        id: Primary key
        student_id: Student who checked in
        module_id: Associated module (optional)
        timetable_slot_id: Associated timetable slot (optional)
        check_in_time: When student checked in
        check_out_time: When student checked out (optional)
        check_in_lat: Latitude at check-in
        check_in_lng: Longitude at check-in
        check_out_lat: Latitude at check-out
        check_out_lng: Longitude at check-out
        accuracy_meters: GPS accuracy in meters
        method: How attendance was recorded
        status: Attendance status
        verified: Whether location was verified
        verification_notes: Notes on verification
        device_info: Device used for check-in
        ip_address: IP address of check-in
    """
    
    __tablename__ = "attendance_records"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    module_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("modules.id"),
        nullable=True
    )
    
    # Check-in Details
    check_in_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    check_out_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Geolocation - Check In
    check_in_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    check_in_lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    check_in_accuracy: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Geolocation - Check Out
    check_out_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    check_out_lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    check_out_accuracy: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Distance from expected location
    distance_from_venue: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Recording Method
    method: Mapped[AttendanceMethod] = mapped_column(
        Enum(AttendanceMethod),
        default=AttendanceMethod.AUTO_GEOFENCE,
        nullable=False
    )
    
    # Status
    status: Mapped[AttendanceStatus] = mapped_column(
        Enum(AttendanceStatus),
        default=AttendanceStatus.PRESENT,
        nullable=False
    )
    
    # Verification
    verified: Mapped[bool] = mapped_column(default=False)
    verification_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Device Information
    user_agent: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    
    # Notes
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
        back_populates="attendance_records"
    )
    
    def __repr__(self) -> str:
        return f"<AttendanceRecord(id={self.id}, student={self.student_id}, status={self.status.value})>"
    
    @property
    def duration_minutes(self) -> Optional[int]:
        """Calculate attendance duration in minutes."""
        if self.check_out_time and self.check_in_time:
            delta = self.check_out_time - self.check_in_time
            return int(delta.total_seconds() / 60)
        return None
    
    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate attendance duration in hours."""
        minutes = self.duration_minutes
        return round(minutes / 60, 2) if minutes else None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "module_id": self.module_id,
            "check_in_time": self.check_in_time.isoformat() if self.check_in_time else None,
            "check_out_time": self.check_out_time.isoformat() if self.check_out_time else None,
            "duration_minutes": self.duration_minutes,
            "duration_hours": self.duration_hours,
            "check_in_location": {
                "lat": self.check_in_lat,
                "lng": self.check_in_lng,
                "accuracy": self.check_in_accuracy,
            } if self.check_in_lat else None,
            "check_out_location": {
                "lat": self.check_out_lat,
                "lng": self.check_out_lng,
                "accuracy": self.check_out_accuracy,
            } if self.check_out_lat else None,
            "distance_from_venue": self.distance_from_venue,
            "method": self.method.value,
            "status": self.status.value,
            "verified": self.verified,
            "verification_notes": self.verification_notes,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class HoursLogStatus(str, enum.Enum):
    """Status of hours log entry."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVISION_REQUESTED = "revision_requested"


class HoursLog(Base):
    """
    Manual hours logging for workshop/practical sessions.
    
    Students log hours worked, which must be approved by a lecturer.
    
    Attributes:
        id: Primary key
        student_id: Student who logged hours
        module_id: Associated module
        date: Date of work
        hours_worked: Number of hours
        description: Description of work done
        status: Approval status
        approved_by: Lecturer who approved
        approved_at: When approved
        rejection_reason: Reason if rejected
    """
    
    __tablename__ = "hours_logs"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    module_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("modules.id"),
        nullable=True
    )
    approved_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("lecturers.id"),
        nullable=True
    )
    
    # Hours Details
    date: Mapped[date] = mapped_column(Date, nullable=False)
    hours_worked: Mapped[float] = mapped_column(nullable=False)
    
    # Description
    description: Mapped[str] = mapped_column(Text, nullable=False)
    skills_practiced: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    equipment_used: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Status
    status: Mapped[HoursLogStatus] = mapped_column(
        Enum(HoursLogStatus),
        default=HoursLogStatus.PENDING,
        nullable=False
    )
    
    # Approval
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    approved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    rejection_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
        back_populates="hours_logs"
    )
    
    approved_by: Mapped[Optional["Lecturer"]] = relationship(
        "Lecturer",
        back_populates="hours_approved"
    )
    
    def __repr__(self) -> str:
        return f"<HoursLog(id={self.id}, student={self.student_id}, hours={self.hours_worked})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "student_id": self.student_id,
            "module_id": self.module_id,
            "date": self.date.isoformat(),
            "hours_worked": self.hours_worked,
            "description": self.description,
            "skills_practiced": self.skills_practiced,
            "equipment_used": self.equipment_used,
            "status": self.status.value,
            "submitted_at": self.submitted_at.isoformat() if self.submitted_at else None,
            "approved_by_id": self.approved_by_id,
            "approved_by_name": self.approved_by.full_name if self.approved_by else None,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
