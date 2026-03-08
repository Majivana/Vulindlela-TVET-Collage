"""
Attendance API Router

Handles attendance check-in/out and hours logging.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
import math

from app.db.database import get_db
from app.core.config import settings
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile
from app.models.attendance import (
    AttendanceRecord, 
    AttendanceStatus, 
    AttendanceMethod,
    HoursLog,
    HoursLogStatus
)
from app.models.timetable import Venue
from app.models.campus_map import CampusBoundary
from app.schemas.attendance import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceResponse,
    HoursLogCreate,
    HoursLogResponse,
    GeofenceStatusResponse,
    VenueResponse,
)


router = APIRouter()


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Calculate distance between two points in meters using Haversine formula.
    
    Args:
        lat1, lng1: First point coordinates
        lat2, lng2: Second point coordinates
        
    Returns:
        Distance in meters
    """
    R = 6371000  # Earth's radius in meters
    
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lng2 - lng1)
    
    a = (math.sin(delta_phi / 2) ** 2 + 
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def is_within_campus(lat: float, lng: float, db: Session) -> tuple:
    """
    Check if coordinates are within campus geofence.
    
    Args:
        lat, lng: Coordinates to check
        db: Database session
        
    Returns:
        Tuple of (is_inside, distance_from_center)
    """
    # Use configured campus center
    campus_lat = settings.CAMPUS_LAT
    campus_lng = settings.CAMPUS_LNG
    campus_radius = settings.CAMPUS_RADIUS
    
    distance = calculate_distance(lat, lng, campus_lat, campus_lng)
    
    return (distance <= campus_radius, distance)


@router.get("/geofence/status")
async def check_geofence_status(
    lat: float,
    lng: float,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if current location is within campus geofence.
    
    Returns geofence status and nearest venue information.
    """
    inside, distance = is_within_campus(lat, lng, db)
    
    # Find nearest venue
    venues = db.query(Venue).filter(Venue.is_active == True).all()
    nearest = None
    min_venue_distance = float('inf')
    
    for venue in venues:
        if venue.lat and venue.lng:
            d = calculate_distance(lat, lng, venue.lat, venue.lng)
            if d < min_venue_distance:
                min_venue_distance = d
                nearest = venue
    
    return GeofenceStatusResponse(
        inside_campus=inside,
        distance_from_center=round(distance, 2),
        campus_center={"lat": settings.CAMPUS_LAT, "lng": settings.CAMPUS_LNG},
        campus_radius=settings.CAMPUS_RADIUS,
        nearest_venue={
            "id": nearest.id,
            "name": nearest.name,
            "distance": round(min_venue_distance, 2),
        } if nearest else None,
        can_check_in=inside,
        message="You are within campus" if inside else "You are outside campus area",
    )


@router.post("/checkin", response_model=AttendanceResponse)
async def check_in(
    request: Request,
    checkin_data: AttendanceCheckInRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check in for attendance with geolocation verification.
    
    Records check-in time and validates location against campus geofence.
    """
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can check in"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Check if already checked in today without checkout
    today = date.today()
    existing = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        func.date(AttendanceRecord.check_in_time) == today,
        AttendanceRecord.check_out_time == None
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Already checked in today. Please check out first."
        )
    
    # Verify location
    inside, distance = is_within_campus(checkin_data.lat, checkin_data.lng, db)
    
    # Create attendance record
    attendance = AttendanceRecord(
        student_id=student.id,
        module_id=checkin_data.module_id,
        check_in_lat=checkin_data.lat,
        check_in_lng=checkin_data.lng,
        check_in_accuracy=checkin_data.accuracy,
        method=AttendanceMethod.AUTO_GEOFENCE,
        status=AttendanceStatus.PRESENT,
        verified=inside,
        verification_notes="Within campus" if inside else "Outside campus area",
        notes=checkin_data.notes,
        user_agent=request.headers.get("user-agent"),
        ip_address=request.client.host if request.client else None,
    )
    
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    
    return AttendanceResponse.model_validate(attendance)


@router.post("/checkout")
async def check_out(
    request: Request,
    checkout_data: AttendanceCheckOutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check out from attendance session.
    
    Records check-out time and calculates session duration.
    """
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can check out"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Find active check-in
    today = date.today()
    attendance = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id,
        func.date(AttendanceRecord.check_in_time) == today,
        AttendanceRecord.check_out_time == None
    ).first()
    
    if not attendance:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active check-in found"
        )
    
    # Update check-out
    attendance.check_out_time = datetime.utcnow()
    attendance.check_out_lat = checkout_data.lat
    attendance.check_out_lng = checkout_data.lng
    attendance.check_out_accuracy = checkout_data.accuracy
    
    if checkout_data.notes:
        attendance.notes = checkout_data.notes
    
    db.commit()
    db.refresh(attendance)
    
    return {
        "message": "Checked out successfully",
        "attendance_id": attendance.id,
        "check_in_time": attendance.check_in_time.isoformat(),
        "check_out_time": attendance.check_out_time.isoformat(),
        "duration_minutes": attendance.duration_minutes,
        "duration_hours": attendance.duration_hours,
    }


@router.get("/history", response_model=List[AttendanceResponse])
async def get_attendance_history(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance history for current student.
    
    Optional date range filtering.
    """
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access attendance history"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    query = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id
    )
    
    if start_date:
        query = query.filter(func.date(AttendanceRecord.check_in_time) >= start_date)
    
    if end_date:
        query = query.filter(func.date(AttendanceRecord.check_in_time) <= end_date)
    
    records = query.order_by(AttendanceRecord.check_in_time.desc()).all()
    
    return [AttendanceResponse.model_validate(r) for r in records]


@router.get("/summary")
async def get_attendance_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get attendance summary statistics.
    """
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access attendance summary"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    records = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id
    ).all()
    
    total = len(records)
    attended = len([r for r in records if r.status == AttendanceStatus.PRESENT])
    late = len([r for r in records if r.status == AttendanceStatus.LATE])
    absent = len([r for r in records if r.status == AttendanceStatus.ABSENT])
    
    total_hours = sum([r.duration_hours or 0 for r in records])
    
    return {
        "total_sessions": total,
        "attended": attended,
        "late": late,
        "absent": absent,
        "attendance_rate": round((attended + late) / total * 100, 2) if total > 0 else 0,
        "total_hours": round(total_hours, 2),
    }


# Hours Log endpoints
@router.post("/hours", response_model=HoursLogResponse)
async def create_hours_log(
    hours_data: HoursLogCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a manual hours log entry for workshop/practical hours.
    
    Requires lecturer approval.
    """
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can log hours"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    hours_log = HoursLog(
        student_id=student.id,
        module_id=hours_data.module_id,
        date=hours_data.date,
        hours_worked=hours_data.hours_worked,
        description=hours_data.description,
        skills_practiced=hours_data.skills_practiced,
        equipment_used=hours_data.equipment_used,
        status=HoursLogStatus.PENDING,
    )
    
    db.add(hours_log)
    db.commit()
    db.refresh(hours_log)
    
    return HoursLogResponse.model_validate(hours_log)


@router.get("/hours", response_model=List[HoursLogResponse])
async def get_hours_logs(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all hours logs for current student."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access hours logs"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    logs = db.query(HoursLog).filter(
        HoursLog.student_id == student.id
    ).order_by(HoursLog.date.desc()).all()
    
    return [HoursLogResponse.model_validate(log) for log in logs]


# Lecturer endpoints for hours approval
@router.get("/hours/pending")
async def get_pending_hours(
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Get pending hours logs for approval (lecturer only)."""
    logs = db.query(HoursLog).filter(
        HoursLog.status == HoursLogStatus.PENDING
    ).all()
    
    result = []
    for log in logs:
        result.append({
            "id": log.id,
            "student_name": log.student.user.full_name if log.student and log.student.user else None,
            "module_code": log.module.code if log.module else None,
            "date": log.date.isoformat(),
            "hours_worked": log.hours_worked,
            "description": log.description,
            "submitted_at": log.submitted_at.isoformat(),
        })
    
    return result


@router.put("/hours/{log_id}/approve")
async def approve_hours(
    log_id: int,
    approve: bool = True,
    rejection_reason: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Approve or reject hours log (lecturer only)."""
    log = db.query(HoursLog).filter(HoursLog.id == log_id).first()
    if not log:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hours log not found"
        )
    
    if approve:
        log.status = HoursLogStatus.APPROVED
        log.approved_by_id = current_user.lecturer_profile.id if current_user.lecturer_profile else None
        log.approved_at = datetime.utcnow()
    else:
        log.status = HoursLogStatus.REJECTED
        log.rejection_reason = rejection_reason
    
    db.commit()
    
    return {
        "message": "Hours log " + ("approved" if approve else "rejected"),
        "log_id": log_id,
        "status": log.status.value,
    }


# Venue endpoints
@router.get("/venues", response_model=List[VenueResponse])
async def get_venues(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all active venues."""
    venues = db.query(Venue).filter(Venue.is_active == True).all()
    return [VenueResponse.model_validate(v) for v in venues]
