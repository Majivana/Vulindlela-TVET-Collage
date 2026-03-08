"""
Dashboard API Router

Provides aggregated dashboard data for different user roles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.student_profile import StudentProfile, ApplicationStatus
from app.models.module import Module, ModuleEnrollment
from app.models.timetable import TimetableSlot, DayOfWeek
from app.models.assignment import Assignment, Submission
from app.models.announcement import Announcement, AnnouncementTarget
from app.models.attendance import AttendanceRecord
from app.models.ticket import Ticket, TicketStatus


router = APIRouter()


@router.get("/student")
async def get_student_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard data for student users.
    
    Returns:
        - User info
        - Student profile
        - Enrolled modules
        - Upcoming classes
        - Upcoming assignments
        - Recent announcements
        - Attendance summary
        - Results summary
        - Helpdesk tickets
        - Funding status
    """
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can access this dashboard"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    # Get enrolled modules
    enrollments = db.query(ModuleEnrollment).filter(
        ModuleEnrollment.student_id == student.id
    ).all()
    
    enrolled_modules = []
    for enrollment in enrollments:
        module = enrollment.module
        if module:
            enrolled_modules.append({
                "id": module.id,
                "code": module.code,
                "title": module.title,
                "sector": module.sector.value,
                "status": enrollment.status.value,
                "enrollment_date": enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
            })
    
    # Get upcoming classes (next 7 days)
    today = datetime.now()
    next_week = today + timedelta(days=7)
    
    upcoming_classes = []
    # Get timetable slots for enrolled modules
    enrolled_module_ids = [e.module_id for e in enrollments]
    if enrolled_module_ids:
        slots = db.query(TimetableSlot).filter(
            TimetableSlot.module_id.in_(enrolled_module_ids),
            TimetableSlot.is_active == True,
            TimetableSlot.is_cancelled == False
        ).all()
        
        for slot in slots[:5]:  # Limit to 5 upcoming
            upcoming_classes.append({
                "id": slot.id,
                "module_code": slot.module.code if slot.module else None,
                "module_title": slot.module.title if slot.module else None,
                "slot_type": slot.slot_type.value,
                "day_of_week": slot.day_of_week.value,
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "venue": slot.venue.name if slot.venue else None,
            })
    
    # Get upcoming assignments
    upcoming_assignments = []
    if enrolled_module_ids:
        assignments = db.query(Assignment).filter(
            Assignment.module_id.in_(enrolled_module_ids),
            Assignment.is_published == True,
            Assignment.due_date >= today
        ).order_by(Assignment.due_date).limit(5).all()
        
        for assignment in assignments:
            # Check if student has submitted
            submission = db.query(Submission).filter(
                Submission.assignment_id == assignment.id,
                Submission.student_id == student.id
            ).first()
            
            upcoming_assignments.append({
                "id": assignment.id,
                "title": assignment.title,
                "module_code": assignment.module.code if assignment.module else None,
                "due_date": assignment.due_date.isoformat(),
                "is_overdue": assignment.is_overdue,
                "submitted": submission is not None,
                "status": submission.status.value if submission else "not_submitted",
            })
    
    # Get recent announcements
    announcements = db.query(Announcement).filter(
        Announcement.is_published == True,
        Announcement.is_active == True
    ).filter(
        # Global announcements or for student's sector
        (Announcement.target == AnnouncementTarget.GLOBAL) |
        (Announcement.target == AnnouncementTarget.STUDENTS)
    ).order_by(Announcement.created_at.desc()).limit(5).all()
    
    announcement_list = []
    for announcement in announcements:
        announcement_list.append({
            "id": announcement.id,
            "title": announcement.title,
            "excerpt": announcement.summary[:150] if announcement.summary else "",
            "priority": announcement.priority.value,
            "is_pinned": announcement.is_pinned,
            "created_at": announcement.created_at.isoformat(),
        })
    
    # Get attendance summary
    attendance_records = db.query(AttendanceRecord).filter(
        AttendanceRecord.student_id == student.id
    ).all()
    
    total_sessions = len(attendance_records)
    attended = len([a for a in attendance_records if a.status.value in ["present", "late"]])
    absent = len([a for a in attendance_records if a.status.value == "absent"])
    
    attendance_rate = (attended / total_sessions * 100) if total_sessions > 0 else 0
    total_hours = sum([a.duration_hours or 0 for a in attendance_records])
    
    attendance_summary = {
        "total_sessions": total_sessions,
        "attended": attended,
        "absent": absent,
        "attendance_rate": round(attendance_rate, 2),
        "total_hours": round(total_hours, 2),
    }
    
    # Get results summary
    results = student.results
    modules_completed = len([r for r in results if r.published])
    
    avg_percentage = 0
    if results:
        percentages = [r.percentage or r.calculate_percentage() for r in results if r.published]
        if percentages:
            avg_percentage = sum(percentages) / len(percentages)
    
    results_summary = {
        "modules_completed": modules_completed,
        "average_grade": round(avg_percentage, 2),
        "current_gpa": round(avg_percentage / 100 * 4, 2) if avg_percentage else 0,
    }
    
    # Get helpdesk tickets
    tickets = db.query(Ticket).filter(
        Ticket.student_id == student.id
    ).order_by(Ticket.created_at.desc()).limit(5).all()
    
    open_tickets = len([t for t in tickets if t.is_open])
    
    ticket_list = []
    for ticket in tickets:
        ticket_list.append({
            "id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "subject": ticket.subject,
            "status": ticket.status.value,
            "department": ticket.department.value,
            "created_at": ticket.created_at.isoformat(),
        })
    
    # Funding status
    funding_status = {
        "funded": student.funded,
        "funding_amount": student.funding_amount,
        "funding_source": student.funding_source,
        "funding_reference": student.funding_reference,
        "application_status": student.application_status.value,
    }
    
    # Application progress
    application_progress = {
        "status": student.application_status.value,
        "status_display": student.application_status.value.replace("_", " ").title(),
        "application_date": student.application_date.isoformat() if student.application_date else None,
        "sector": student.sector.value if student.sector else None,
        "sector_display": student.sector_display,
    }
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "full_name": current_user.full_name,
            "role": current_user.role.value,
        },
        "student": {
            "id": student.id,
            "student_number": student.student_number,
            "application_status": student.application_status.value,
            "sector": student.sector.value if student.sector else None,
            "sector_display": student.sector_display,
            "enrollment_date": student.enrollment_date.isoformat() if student.enrollment_date else None,
        },
        "enrolled_modules": enrolled_modules,
        "upcoming_classes": upcoming_classes,
        "upcoming_assignments": upcoming_assignments,
        "announcements": announcement_list,
        "attendance_summary": attendance_summary,
        "results_summary": results_summary,
        "open_tickets": open_tickets,
        "recent_tickets": ticket_list,
        "funding_status": funding_status,
        "application_progress": application_progress,
    }


@router.get("/lecturer")
async def get_lecturer_dashboard(
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """
    Get dashboard data for lecturer users.
    """
    lecturer = current_user.lecturer_profile
    if not lecturer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lecturer profile not found"
        )
    
    # Get modules taught
    modules = lecturer.modules_taught
    
    # Get pending submissions to grade
    pending_grading = db.query(Submission).join(Assignment).filter(
        Assignment.created_by_id == lecturer.id,
        Submission.status == "submitted"
    ).count()
    
    # Get pending hours approvals
    pending_hours = db.query(func.count('*')).filter(
        # Add hours log model reference here
    ).scalar() or 0
    
    return {
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
        },
        "lecturer": {
            "department": lecturer.department.value if lecturer.department else None,
            "employee_number": lecturer.employee_number,
        },
        "modules_count": len(modules),
        "modules": [{"id": m.id, "code": m.code, "title": m.title} for m in modules[:5]],
        "pending_grading": pending_grading,
        "pending_hours_approvals": pending_hours,
    }


@router.get("/admin")
async def get_admin_dashboard(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """
    Get dashboard data for admin users.
    """
    # User statistics
    total_users = db.query(func.count(User.id)).scalar()
    total_students = db.query(func.count(StudentProfile.id)).scalar()
    pending_applications = db.query(func.count(StudentProfile.id)).filter(
        StudentProfile.application_status == ApplicationStatus.SUBMITTED
    ).scalar()
    
    # Module statistics
    total_modules = db.query(func.count(Module.id)).scalar()
    
    # Ticket statistics
    open_tickets = db.query(func.count(Ticket.id)).filter(
        Ticket.status.in_(["open", "in_progress"])
    ).scalar()
    
    # Recent applications
    recent_applications = db.query(StudentProfile).join(User).filter(
        StudentProfile.application_status == ApplicationStatus.SUBMITTED
    ).order_by(StudentProfile.created_at.desc()).limit(5).all()
    
    return {
        "user": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "email": current_user.email,
        },
        "statistics": {
            "total_users": total_users,
            "total_students": total_students,
            "pending_applications": pending_applications,
            "total_modules": total_modules,
            "open_tickets": open_tickets,
        },
        "recent_applications": [
            {
                "id": app.id,
                "student_name": app.user.full_name if app.user else None,
                "email": app.user.email if app.user else None,
                "sector": app.sector.value if app.sector else None,
                "application_date": app.application_date.isoformat() if app.application_date else None,
            }
            for app in recent_applications
        ],
    }
