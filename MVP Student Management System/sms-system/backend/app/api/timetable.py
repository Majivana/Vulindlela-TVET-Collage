"""
Timetable API Router

Schedule and timetable management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.timetable import TimetableSlot, Venue, DayOfWeek
from app.models.module import ModuleEnrollment


router = APIRouter()


@router.get("/my")
async def get_my_timetable(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get timetable for current student's enrolled modules."""
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
    
    if not enrolled_module_ids:
        return []
    
    # Get timetable slots
    slots = db.query(TimetableSlot).filter(
        TimetableSlot.module_id.in_(enrolled_module_ids),
        TimetableSlot.is_active == True,
        TimetableSlot.is_cancelled == False
    ).order_by(
        TimetableSlot.day_of_week,
        TimetableSlot.start_time
    ).all()
    
    return [s.to_dict() for s in slots]


@router.get("/weekly")
async def get_weekly_timetable(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get weekly timetable organized by day."""
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
    
    enrolled_module_ids = [e.module_id for e in student.module_enrollments]
    
    if not enrolled_module_ids:
        return {day.value: [] for day in DayOfWeek}
    
    slots = db.query(TimetableSlot).filter(
        TimetableSlot.module_id.in_(enrolled_module_ids),
        TimetableSlot.is_active == True,
        TimetableSlot.is_cancelled == False
    ).order_by(TimetableSlot.start_time).all()
    
    # Organize by day
    weekly = {day.value: [] for day in DayOfWeek}
    
    for slot in slots:
        weekly[slot.day_of_week.value].append(slot.to_dict())
    
    return weekly


@router.get("/venues")
async def get_venues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all venues."""
    venues = db.query(Venue).filter(Venue.is_active == True).all()
    return [v.to_dict() for v in venues]


@router.get("/venues/{venue_id}")
async def get_venue(
    venue_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get venue details."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Venue not found"
        )
    
    return venue.to_dict()


# Admin/Lecturer endpoints
@router.post("/slots")
async def create_timetable_slot(
    slot_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Create a timetable slot (lecturer/admin only)."""
    from datetime import time, date
    
    slot = TimetableSlot(
        module_id=slot_data.get("module_id"),
        venue_id=slot_data.get("venue_id"),
        slot_type=slot_data.get("slot_type"),
        day_of_week=slot_data.get("day_of_week"),
        start_time=time.fromisoformat(slot_data.get("start_time")),
        end_time=time.fromisoformat(slot_data.get("end_time")),
        start_date=date.fromisoformat(slot_data.get("start_date")),
        end_date=date.fromisoformat(slot_data.get("end_date")) if slot_data.get("end_date") else None,
        is_recurring=slot_data.get("is_recurring", True),
        recurrence=slot_data.get("recurrence"),
        topic=slot_data.get("topic"),
        notes=slot_data.get("notes"),
    )
    
    db.add(slot)
    db.commit()
    db.refresh(slot)
    
    return slot.to_dict()


@router.post("/venues")
async def create_venue(
    venue_data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a venue (admin only)."""
    venue = Venue(
        name=venue_data.get("name"),
        code=venue_data.get("code"),
        building=venue_data.get("building"),
        floor=venue_data.get("floor"),
        room_number=venue_data.get("room_number"),
        venue_type=venue_data.get("venue_type", "classroom"),
        capacity=venue_data.get("capacity"),
        lat=venue_data.get("lat"),
        lng=venue_data.get("lng"),
        facilities=venue_data.get("facilities"),
        description=venue_data.get("description"),
    )
    
    db.add(venue)
    db.commit()
    db.refresh(venue)
    
    return venue.to_dict()
