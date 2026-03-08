"""
Security Module

Handles password hashing, JWT token creation/verification,
and other security-related functionality.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

from app.core.config import settings


# Password hashing context using Argon2
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password
        hashed_password: The hashed password from database
        
    Returns:
        True if passwords match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password.
    
    Args:
        password: The plain text password to hash
        
    Returns:
        The hashed password
    """
    return pwd_context.hash(password)


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token (typically user_id, email, role)
        expires_delta: Optional custom expiration time
        
    Returns:
        The encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "type": "access",
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any]) -> str:
    """
    Create a JWT refresh token with longer expiration.
    
    Args:
        data: The data to encode in the token
        
    Returns:
        The encoded JWT refresh token string
    """
    to_encode = data.copy()
    
    expire = datetime.utcnow() + timedelta(
        days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
    )
    
    to_encode.update({
        "exp": expire,
        "type": "refresh",
        "iat": datetime.utcnow()
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify a JWT token.
    
    Args:
        token: The JWT token to decode
        
    Returns:
        The decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def verify_token_type(payload: Dict[str, Any], expected_type: str) -> None:
    """
    Verify that a token is of the expected type.
    
    Args:
        payload: The decoded token payload
        expected_type: The expected token type ('access' or 'refresh')
        
    Raises:
        HTTPException: If token type doesn't match
    """
    token_type = payload.get("type")
    if token_type != expected_type:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token type. Expected {expected_type} token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Role-based access control constants
class Role:
    """User role constants."""
    STUDENT = "student"
    LECTURER = "lecturer"
    ADMIN = "admin"
    SUPPORT_AGENT = "support_agent"
    SUPPLIER_MANAGER = "supplier_manager"
    
    ALL_ROLES = [STUDENT, LECTURER, ADMIN, SUPPORT_AGENT, SUPPLIER_MANAGER]


class Permission:
    """Permission constants for fine-grained access control."""
    
    # Student permissions
    VIEW_OWN_PROFILE = "view_own_profile"
    EDIT_OWN_PROFILE = "edit_own_profile"
    VIEW_OWN_MODULES = "view_own_modules"
    VIEW_OWN_RESULTS = "view_own_results"
    SUBMIT_ASSIGNMENT = "submit_assignment"
    CREATE_TICKET = "create_ticket"
    CHECK_IN_ATTENDANCE = "check_in_attendance"
    
    # Lecturer permissions
    CREATE_ASSIGNMENT = "create_assignment"
    GRADE_SUBMISSION = "grade_submission"
    VIEW_STUDENT_PROGRESS = "view_student_progress"
    CREATE_ANNOUNCEMENT = "create_announcement"
    APPROVE_HOURS = "approve_hours"
    
    # Admin permissions
    MANAGE_USERS = "manage_users"
    MANAGE_COURSES = "manage_courses"
    MANAGE_MODULES = "manage_modules"
    MANAGE_TIMETABLE = "manage_timetable"
    VIEW_ALL_DATA = "view_all_data"
    
    # Support agent permissions
    MANAGE_TICKETS = "manage_tickets"
    RESPOND_TO_TICKETS = "respond_to_tickets"
    
    # Supplier manager permissions
    MANAGE_SUPPLIERS = "manage_suppliers"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    Role.STUDENT: [
        Permission.VIEW_OWN_PROFILE,
        Permission.EDIT_OWN_PROFILE,
        Permission.VIEW_OWN_MODULES,
        Permission.VIEW_OWN_RESULTS,
        Permission.SUBMIT_ASSIGNMENT,
        Permission.CREATE_TICKET,
        Permission.CHECK_IN_ATTENDANCE,
    ],
    Role.LECTURER: [
        Permission.VIEW_OWN_PROFILE,
        Permission.EDIT_OWN_PROFILE,
        Permission.CREATE_ASSIGNMENT,
        Permission.GRADE_SUBMISSION,
        Permission.VIEW_STUDENT_PROGRESS,
        Permission.CREATE_ANNOUNCEMENT,
        Permission.APPROVE_HOURS,
    ],
    Role.ADMIN: [
        Permission.MANAGE_USERS,
        Permission.MANAGE_COURSES,
        Permission.MANAGE_MODULES,
        Permission.MANAGE_TIMETABLE,
        Permission.VIEW_ALL_DATA,
        Permission.CREATE_ANNOUNCEMENT,
    ],
    Role.SUPPORT_AGENT: [
        Permission.MANAGE_TICKETS,
        Permission.RESPOND_TO_TICKETS,
        Permission.VIEW_OWN_PROFILE,
    ],
    Role.SUPPLIER_MANAGER: [
        Permission.MANAGE_SUPPLIERS,
        Permission.VIEW_OWN_PROFILE,
    ],
}


def has_permission(user_role: str, permission: str) -> bool:
    """
    Check if a user role has a specific permission.
    
    Args:
        user_role: The user's role
        permission: The permission to check
        
    Returns:
        True if the role has the permission
    """
    permissions = ROLE_PERMISSIONS.get(user_role, [])
    return permission in permissions


def require_permission(permission: str):
    """
    Decorator factory to require a specific permission.
    
    Args:
        permission: The required permission
        
    Returns:
        Decorator function
    """
    def decorator(func):
        """Decorator to check permissions."""
        async def wrapper(*args, **kwargs):
            # This would be integrated with FastAPI dependency injection
            # For now, it's a placeholder for the pattern
            return await func(*args, **kwargs)
        return wrapper
    return decorator
