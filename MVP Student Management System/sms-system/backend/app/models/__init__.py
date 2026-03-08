"""
Models Package

Import all models for easy access.
"""

from app.models.user import User, UserRole
from app.models.student_profile import (
    StudentProfile, 
    ApplicationStatus, 
    StudySector
)
from app.models.lecturer import Lecturer, Department
from app.models.module import (
    Module, 
    ModuleEnrollment, 
    ModuleLevel, 
    ModuleStatus,
    EnrollmentStatus,
    StudySector as ModuleSector
)
from app.models.timetable import (
    TimetableSlot, 
    Venue, 
    SlotType, 
    DayOfWeek,
    RecurrenceType
)
from app.models.attendance import (
    AttendanceRecord, 
    HoursLog, 
    AttendanceStatus,
    AttendanceMethod,
    HoursLogStatus
)
from app.models.assignment import (
    Assignment, 
    Submission, 
    AssignmentType,
    SubmissionStatus
)
from app.models.announcement import (
    Announcement, 
    AnnouncementRead,
    AnnouncementTarget,
    AnnouncementPriority
)
from app.models.result import (
    Result, 
    AcademicRecord,
    AssessmentType
)
from app.models.ticket import (
    Ticket, 
    TicketReply,
    TicketDepartment,
    TicketStatus,
    TicketPriority,
    TicketCategory
)
from app.models.supplier import (
    Supplier, 
    PurchaseRequest,
    ServiceCategory,
    SupplierStatus
)
from app.models.campus_map import (
    CampusMapPoint, 
    CampusBoundary,
    MapPointType
)

__all__ = [
    # User
    "User",
    "UserRole",
    
    # Student
    "StudentProfile",
    "ApplicationStatus",
    "StudySector",
    
    # Lecturer
    "Lecturer",
    "Department",
    
    # Module
    "Module",
    "ModuleEnrollment",
    "ModuleLevel",
    "ModuleStatus",
    "EnrollmentStatus",
    
    # Timetable
    "TimetableSlot",
    "Venue",
    "SlotType",
    "DayOfWeek",
    "RecurrenceType",
    
    # Attendance
    "AttendanceRecord",
    "HoursLog",
    "AttendanceStatus",
    "AttendanceMethod",
    "HoursLogStatus",
    
    # Assignment
    "Assignment",
    "Submission",
    "AssignmentType",
    "SubmissionStatus",
    
    # Announcement
    "Announcement",
    "AnnouncementRead",
    "AnnouncementTarget",
    "AnnouncementPriority",
    
    # Result
    "Result",
    "AcademicRecord",
    "AssessmentType",
    
    # Ticket
    "Ticket",
    "TicketReply",
    "TicketDepartment",
    "TicketStatus",
    "TicketPriority",
    "TicketCategory",
    
    # Supplier
    "Supplier",
    "PurchaseRequest",
    "ServiceCategory",
    "SupplierStatus",
    
    # Campus Map
    "CampusMapPoint",
    "CampusBoundary",
    "MapPointType",
]
