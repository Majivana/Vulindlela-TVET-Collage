"""
Announcement Model

System announcements for students and staff.
"""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey, 
    Text, Boolean, JSON, Enum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


if TYPE_CHECKING:
    from app.models.user import User
    from app.models.module import Module


class AnnouncementTarget(str, enum.Enum):
    """Target audience for announcement."""
    GLOBAL = "global"              # All users
    STUDENTS = "students"          # All students
    LECTURERS = "lecturers"        # All lecturers
    STAFF = "staff"                # All staff
    MODULE = "module"              # Specific module
    SECTOR = "sector"              # Specific sector
    ROLE = "role"                  # Specific role


class AnnouncementPriority(str, enum.Enum):
    """Priority level for announcements."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class Announcement(Base):
    """
    Announcement model for system-wide and targeted communications.
    
    Attributes:
        id: Primary key
        author_id: User who created the announcement
        title: Announcement title
        body: Main content
        target: Target audience type
        target_id: Specific target ID (module, sector, etc.)
        priority: Priority level
        attachments: File references
        is_pinned: Whether pinned to top
        is_published: Whether visible
        publish_at: Scheduled publish time
        expires_at: When announcement expires
        view_count: Number of views
    """
    
    __tablename__ = "announcements"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Author
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Content
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    excerpt: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Targeting
    target: Mapped[AnnouncementTarget] = mapped_column(
        Enum(AnnouncementTarget),
        default=AnnouncementTarget.GLOBAL,
        nullable=False
    )
    target_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Priority & Type
    priority: Mapped[AnnouncementPriority] = mapped_column(
        Enum(AnnouncementPriority),
        default=AnnouncementPriority.NORMAL,
        nullable=False
    )
    category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Media
    attachments: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Visibility
    is_pinned: Mapped[bool] = mapped_column(default=False)
    is_published: Mapped[bool] = mapped_column(default=True)
    
    # Scheduling
    publish_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Analytics
    view_count: Mapped[int] = mapped_column(default=0)
    
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
    author: Mapped["User"] = relationship("User", back_populates="announcements")
    
    def __repr__(self) -> str:
        return f"<Announcement(id={self.id}, title={self.title}, target={self.target.value})>"
    
    @property
    def is_expired(self) -> bool:
        """Check if announcement has expired."""
        if self.expires_at:
            return datetime.now() > self.expires_at
        return False
    
    @property
    def is_scheduled(self) -> bool:
        """Check if announcement is scheduled for future."""
        if self.publish_at:
            return datetime.now() < self.publish_at
        return False
    
    @property
    def is_visible(self) -> bool:
        """Check if announcement should be visible."""
        return (
            self.is_published and
            not self.is_expired and
            not self.is_scheduled
        )
    
    @property
    def summary(self) -> str:
        """Get short summary of announcement."""
        if self.excerpt:
            return self.excerpt
        if self.body:
            return self.body[:200] + "..." if len(self.body) > 200 else self.body
        return ""
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "author_id": self.author_id,
            "author_name": self.author.full_name if self.author else None,
            "title": self.title,
            "body": self.body,
            "excerpt": self.excerpt or self.summary,
            "target": self.target.value,
            "target_id": self.target_id,
            "target_role": self.target_role,
            "priority": self.priority.value,
            "category": self.category,
            "attachments": self.attachments or {},
            "image_url": self.image_url,
            "is_pinned": self.is_pinned,
            "is_published": self.is_published,
            "is_expired": self.is_expired,
            "is_scheduled": self.is_scheduled,
            "is_visible": self.is_visible,
            "publish_at": self.publish_at.isoformat() if self.publish_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "view_count": self.view_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AnnouncementRead(Base):
    """
    Track which users have read which announcements.
    
    This allows for read receipts and unread counts.
    """
    
    __tablename__ = "announcement_reads"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    announcement_id: Mapped[int] = mapped_column(
        ForeignKey("announcements.id", ondelete="CASCADE"),
        nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    read_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    
    # Unique constraint to prevent duplicate reads
    __table_args__ = (
        # Each user can only read an announcement once
    )
    
    def __repr__(self) -> str:
        return f"<AnnouncementRead(announcement={self.announcement_id}, user={self.user_id})>"
