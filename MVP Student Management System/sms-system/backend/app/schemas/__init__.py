"""
Schemas Package

Contains Pydantic schemas for request/response validation.
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserRegister,
    UserUpdate,
    UserResponse,
    LoginRequest,
    TokenResponse,
)

from app.schemas.student import (
    StudentProfileBase,
    StudentProfileCreate,
    StudentProfileUpdate,
    StudentProfileResponse,
    StudentDashboardResponse,
)

from app.schemas.attendance import (
    AttendanceCheckInRequest,
    AttendanceCheckOutRequest,
    AttendanceResponse,
    HoursLogCreate,
    HoursLogResponse,
    GeofenceStatusResponse,
)

__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserRegister",
    "UserUpdate",
    "UserResponse",
    "LoginRequest",
    "TokenResponse",
    # Student schemas
    "StudentProfileBase",
    "StudentProfileCreate",
    "StudentProfileUpdate",
    "StudentProfileResponse",
    "StudentDashboardResponse",
    # Attendance schemas
    "AttendanceCheckInRequest",
    "AttendanceCheckOutRequest",
    "AttendanceResponse",
    "HoursLogCreate",
    "HoursLogResponse",
    "GeofenceStatusResponse",
]
