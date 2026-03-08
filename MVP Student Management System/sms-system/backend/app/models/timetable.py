"""
Timetable Model

Schedule and venue management for classes, practicals, and exams.
"""

from datetime import datetime, time
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Time, Date, Enum, Text
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.module import Module


class SlotType(str, enum.Enum):
    """Type of timetable slot."""
    LECTURE = "lecture"
    PRACTICAL = "practical"
    WORKSHOP = "workshop"
    TEST = "test"
    EXAM = "exam"
    TUTORIAL = "tutorial"
    FIELD_WORK = "field_work"


class RecurrenceType(str, enum.Enum):
    """Recurrence pattern for recurring slots."""
    NONE = "none"
    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"


class DayOfWeek(str, enum.Enum):
    """Days of the week."""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"


class Venue(Base):
    """
    Venue model representing classrooms, labs, workshops, etc.
    
    Attributes:
        id: Primary key
        name: Venue name
        code: Short venue code
        building: Building name/number
        floor: Floor number
        room_number: Room identifier
        type: Venue type (classroom, lab, workshop)
        capacity: Maximum capacity
        lat: Latitude for geolocation
        lng: Longitude for geolocation
        facilities: Available facilities
        description: Additional details
    """
    
    __tablename__ = "venues"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Venue Information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Classification
    venue_type: Mapped[str] = mapped_column(String(50), default="classroom")
    capacity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Location (for geofencing and maps)
    lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Details
    facilities: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
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
    timetable_slots: Mapped[list["TimetableSlot"]] = relationship(
        "TimetableSlot",
        back_populates="venue"
    )
    
    def __repr__(self) -> str:
        return f"<Venue(id={self.id}, code={self.code}, name={self.name})>"
    
    @property
    def full_location(self) -> str:
        """Get full location string."""
        parts = [self.building]
        if self.floor:
            parts.append(f"Floor {self.floor}")
        if self.room_number:
            parts.append(f"Room {self.room_number}")
        return ", ".join(parts)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "code": self.code,
            "building": self.building,
            "floor": self.floor,
            "room_number": self.room_number,
            "full_location": self.full_location,
            "venue_type": self.venue_type,
            "capacity": self.capacity,
            "lat": self.lat,
            "lng": self.lng,
            "facilities": self.facilities,
            "description": self.description,
            "is_active": self.is_active,
        }


class TimetableSlot(Base):
    """
    Timetable slot representing a scheduled class session.
    
    Supports both one-time and recurring events.
    
    Attributes:
        id: Primary key
        module_id: Associated module
        venue_id: Location
        slot_type: Type of session
        day_of_week: Day for recurring slots
        start_time: Session start time
        end_time: Session end time
        start_date: First occurrence date
        end_date: Last occurrence date (for recurring)
        recurrence: Recurrence pattern
        is_recurring: Whether this repeats
        google_calendar_event_id: Sync with Google Calendar
    """
    
    __tablename__ = "timetable_slots"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Foreign Keys
    module_id: Mapped[int] = mapped_column(
        ForeignKey("modules.id", ondelete="CASCADE"),
        nullable=False
    )
    venue_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("venues.id"),
        nullable=True
    )
    
    # Session Details
    slot_type: Mapped[SlotType] = mapped_column(
        Enum(SlotType),
        default=SlotType.LECTURE,
        nullable=False
    )
    
    # Timing
    day_of_week: Mapped[DayOfWeek] = mapped_column(
        Enum(DayOfWeek),
        nullable=False
    )
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    
    # Date Range
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Recurrence
    is_recurring: Mapped[bool] = mapped_column(default=True)
    recurrence: Mapped[RecurrenceType] = mapped_column(
        Enum(RecurrenceType),
        default=RecurrenceType.WEEKLY
    )
    
    # Additional Information
    topic: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Google Calendar Integration
    google_calendar_event_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_synced: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    is_cancelled: Mapped[bool] = mapped_column(default=False)
    cancellation_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
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
    module: Mapped["Module"] = relationship("Module", back_populates="timetable_slots")
    venue: Mapped[Optional["Venue"]] = relationship("Venue", back_populates="timetable_slots")
    
    def __repr__(self) -> str:
        return f"<TimetableSlot(id={self.id}, module={self.module_id}, day={self.day_of_week.value})>"
    
    @property
    def duration_minutes(self) -> int:
        """Calculate session duration in minutes."""
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        delta = end - start
        return int(delta.total_seconds() / 60)
    
    @property
    def display_time(self) -> str:
        """Get formatted time range."""
        return f"{self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')}"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "module_id": self.module_id,
            "module_code": self.module.code if self.module else None,
            "module_title": self.module.title if self.module else None,
            "venue_id": self.venue_id,
            "venue_name": self.venue.name if self.venue else None,
            "venue_code": self.venue.code if self.venue else None,
            "slot_type": self.slot_type.value,
            "day_of_week": self.day_of_week.value,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "display_time": self.display_time,
            "duration_minutes": self.duration_minutes,
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "is_recurring": self.is_recurring,
            "recurrence": self.recurrence.value,
            "topic": self.topic,
            "notes": self.notes,
            "is_active": self.is_active,
            "is_cancelled": self.is_cancelled,
        }
