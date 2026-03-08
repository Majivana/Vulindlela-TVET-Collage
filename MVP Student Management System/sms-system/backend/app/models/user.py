"""
User Model

Core user account model with authentication and role-based access.
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.student_profile import StudentProfile
    from app.models.lecturer import Lecturer
    from app.models.announcement import Announcement
    from app.models.ticket import Ticket, TicketReply


class UserRole(str, enum.Enum):
    """
    Enumeration of available user roles in the system.
    
    Each role determines the permissions and access level of a user.
    """
    STUDENT = "student"
    LECTURER = "lecturer"
    ADMIN = "admin"
    SUPPORT_AGENT = "support_agent"
    SUPPLIER_MANAGER = "supplier_manager"


class User(Base):
    """
    User model representing a system user account.
    
    This is the central authentication entity. All users (students, lecturers,
    admins, etc.) have a User record with role-based access control.
    
    Attributes:
        id: Primary key
        email: Unique email address (used for login)
        password_hash: Hashed password (Argon2)
        role: User role determining permissions
        first_name: User's first name
        last_name: User's last name
        phone: Contact phone number
        is_active: Whether the account is active
        email_verified: Whether email has been verified
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        last_login: Last successful login timestamp
    """
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Authentication fields
    email: Mapped[str] = mapped_column(
        String(255), 
        unique=True, 
        index=True, 
        nullable=False
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Role-based access control
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole),
        default=UserRole.STUDENT,
        nullable=False
    )
    
    # Profile information
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Account status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    
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
    last_login: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Relationships
    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    lecturer_profile: Mapped[Optional["Lecturer"]] = relationship(
        "Lecturer",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    announcements: Mapped[list["Announcement"]] = relationship(
        "Announcement",
        back_populates="author",
        cascade="all, delete-orphan"
    )
    
    tickets_created: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="Ticket.student_id",
        back_populates="student"
    )
    
    tickets_assigned: Mapped[list["Ticket"]] = relationship(
        "Ticket",
        foreign_keys="Ticket.assigned_to_id",
        back_populates="assigned_to"
    )
    
    ticket_replies: Mapped[list["TicketReply"]] = relationship(
        "TicketReply",
        back_populates="author"
    )
    
    def __repr__(self) -> str:
        """String representation of the User."""
        return f"<User(id={self.id}, email={self.email}, role={self.role.value})>"
    
    @property
    def full_name(self) -> str:
        """Get the user's full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_student(self) -> bool:
        """Check if user is a student."""
        return self.role == UserRole.STUDENT
    
    @property
    def is_lecturer(self) -> bool:
        """Check if user is a lecturer."""
        return self.role == UserRole.LECTURER
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin."""
        return self.role == UserRole.ADMIN
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if user has a specific role.
        
        Args:
            role: The role to check
            
        Returns:
            True if user has the role
        """
        return self.role == role
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert user to dictionary.
        
        Args:
            include_sensitive: Whether to include sensitive fields
            
        Returns:
            Dictionary representation of user
        """
        data = {
            "id": self.id,
            "email": self.email,
            "role": self.role.value,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "phone": self.phone,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
        }
        
        if include_sensitive:
            data["password_hash"] = self.password_hash
            
        return data
