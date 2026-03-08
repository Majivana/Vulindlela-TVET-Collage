"""
Users API Router

User management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.core.security import get_password_hash
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.schemas.user import UserResponse, UserUpdate, UserRoleUpdate


router = APIRouter()


@router.get("/")
async def get_users(
    role: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all users (admin only)."""
    query = db.query(User)
    
    if role:
        query = query.filter(User.role == role)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.email.ilike(search_filter)) |
            (User.first_name.ilike(search_filter)) |
            (User.last_name.ilike(search_filter))
        )
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "users": [UserResponse.model_validate(u) for u in users],
        "total": total,
        "page": skip // limit + 1 if limit > 0 else 1,
        "per_page": limit,
    }


@router.get("/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get user details (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}")
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update user information (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    for field, value in user_data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return UserResponse.model_validate(user)


@router.put("/{user_id}/role")
async def update_user_role(
    user_id: int,
    role_data: UserRoleUpdate,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update user role (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.role = role_data.role
    db.commit()
    
    return {
        "message": "User role updated",
        "user_id": user_id,
        "new_role": user.role.value,
    }


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Deactivate a user (admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Soft delete by deactivating
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}


@router.post("/")
async def create_user(
    user_data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new user (admin only)."""
    # Check if email exists
    existing = db.query(User).filter(User.email == user_data.get("email")).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    user = User(
        email=user_data.get("email"),
        password_hash=get_password_hash(user_data.get("password")),
        role=user_data.get("role", UserRole.STUDENT),
        first_name=user_data.get("first_name"),
        last_name=user_data.get("last_name"),
        phone=user_data.get("phone"),
        is_active=user_data.get("is_active", True),
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create profile based on role
    if user.role == UserRole.STUDENT:
        from app.models.student_profile import StudentProfile, ApplicationStatus
        profile = StudentProfile(
            user_id=user.id,
            application_status=ApplicationStatus.DRAFT,
        )
        db.add(profile)
        db.commit()
    elif user.role == UserRole.LECTURER:
        from app.models.lecturer import Lecturer
        lecturer = Lecturer(
            user_id=user.id,
        )
        db.add(lecturer)
        db.commit()
    
    return UserResponse.model_validate(user)
