"""
Ticket Model

Helpdesk support ticket system for student inquiries.
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
    from app.models.student_profile import StudentProfile


class TicketDepartment(str, enum.Enum):
    """Department that handles tickets."""
    ADMISSIONS = "admissions"
    FINANCE = "finance"
    ACADEMIC = "academic"
    FACILITIES = "facilities"
    IT_SUPPORT = "it_support"
    STUDENT_AFFAIRS = "student_affairs"
    SUPPLIERS = "suppliers"
    GENERAL = "general"


class TicketStatus(str, enum.Enum):
    """Ticket status."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    WAITING_FOR_USER = "waiting_for_user"
    WAITING_FOR_THIRD_PARTY = "waiting_for_third_party"
    RESOLVED = "resolved"
    CLOSED = "closed"
    REOPENED = "reopened"


class TicketPriority(str, enum.Enum):
    """Ticket priority level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(str, enum.Enum):
    """Ticket category/type."""
    GENERAL_INQUIRY = "general_inquiry"
    TECHNICAL_ISSUE = "technical_issue"
    BILLING = "billing"
    ENROLLMENT = "enrollment"
    GRADES = "grades"
    TIMETABLE = "timetable"
    DOCUMENTS = "documents"
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    OTHER = "other"


class Ticket(Base):
    """
    Support ticket model for student helpdesk.
    
    Attributes:
        id: Primary key
        ticket_number: Human-readable ticket number (e.g., TKT-2024-0001)
        student_id: Student who created the ticket
        department: Assigned department
        category: Ticket category
        priority: Priority level
        subject: Short subject line
        body: Detailed description
        attachments: File references
        status: Current status
        assigned_to_id: Staff member assigned
        created_at: When ticket was created
        updated_at: Last update
        resolved_at: When resolved
        closed_at: When closed
        satisfaction_rating: User satisfaction (1-5)
    """
    
    __tablename__ = "tickets"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Ticket Number (human-readable)
    ticket_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True
    )
    
    # Creator
    student_id: Mapped[int] = mapped_column(
        ForeignKey("student_profiles.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Classification
    department: Mapped[TicketDepartment] = mapped_column(
        Enum(TicketDepartment),
        default=TicketDepartment.GENERAL,
        nullable=False
    )
    category: Mapped[TicketCategory] = mapped_column(
        Enum(TicketCategory),
        default=TicketCategory.GENERAL_INQUIRY,
        nullable=False
    )
    priority: Mapped[TicketPriority] = mapped_column(
        Enum(TicketPriority),
        default=TicketPriority.MEDIUM,
        nullable=False
    )
    
    # Content
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Attachments
    attachments: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Status
    status: Mapped[TicketStatus] = mapped_column(
        Enum(TicketStatus),
        default=TicketStatus.OPEN,
        nullable=False
    )
    
    # Assignment
    assigned_to_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True
    )
    
    # Timing
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
    first_response_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    
    # Resolution
    resolution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    satisfaction_comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Internal
    internal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationships
    student: Mapped["StudentProfile"] = relationship(
        "StudentProfile",
        back_populates="tickets_created"
    )
    
    assigned_to: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[assigned_to_id],
        back_populates="tickets_assigned"
    )
    
    replies: Mapped[list["TicketReply"]] = relationship(
        "TicketReply",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="TicketReply.created_at"
    )
    
    def __repr__(self) -> str:
        return f"<Ticket(id={self.id}, number={self.ticket_number}, status={self.status.value})>"
    
    @property
    is_open(self) -> bool:
        """Check if ticket is open."""
        return self.status in [TicketStatus.OPEN, TicketStatus.IN_PROGRESS, TicketStatus.REOPENED]
    
    @property
    is_resolved(self) -> bool:
        """Check if ticket is resolved."""
        return self.status in [TicketStatus.RESOLVED, TicketStatus.CLOSED]
    
    @property
    response_time_hours(self) -> Optional[float]:
        """Calculate time to first response in hours."""
        if self.first_response_at and self.created_at:
            delta = self.first_response_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    @property
    resolution_time_hours(self) -> Optional[float]:
        """Calculate time to resolution in hours."""
        if self.resolved_at and self.created_at:
            delta = self.resolved_at - self.created_at
            return round(delta.total_seconds() / 3600, 2)
        return None
    
    @property
    reply_count(self) -> int:
        """Get number of replies."""
        return len(self.replies)
    
    def generate_ticket_number(self) -> str:
        """Generate a unique ticket number."""
        year = datetime.now().year
        return f"TKT-{year}-{self.id:05d}"
    
    def to_dict(self, include_internal: bool = False) -> dict:
        """
        Convert ticket to dictionary.
        
        Args:
            include_internal: Whether to include internal notes
            
        Returns:
            Dictionary representation
        """
        data = {
            "id": self.id,
            "ticket_number": self.ticket_number,
            "student_id": self.student_id,
            "student_name": self.student.user.full_name if self.student and self.student.user else None,
            "department": self.department.value,
            "category": self.category.value,
            "priority": self.priority.value,
            "subject": self.subject,
            "body": self.body,
            "attachments": self.attachments or {},
            "status": self.status.value,
            "is_open": self.is_open,
            "is_resolved": self.is_resolved,
            "assigned_to_id": self.assigned_to_id,
            "assigned_to_name": self.assigned_to.full_name if self.assigned_to else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "first_response_at": self.first_response_at.isoformat() if self.first_response_at else None,
            "response_time_hours": self.response_time_hours,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_time_hours": self.resolution_time_hours,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "resolution_notes": self.resolution_notes,
            "satisfaction_rating": self.satisfaction_rating,
            "satisfaction_comment": self.satisfaction_comment,
            "reply_count": self.reply_count,
        }
        
        if include_internal:
            data["internal_notes"] = self.internal_notes
            
        return data


class TicketReply(Base):
    """
    Reply/comment on a support ticket.
    
    Attributes:
        id: Primary key
        ticket_id: Parent ticket
        author_id: User who wrote the reply
        body: Reply content
        is_internal: Whether visible only to staff
        attachments: File references
    """
    
    __tablename__ = "ticket_replies"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    ticket_id: Mapped[int] = mapped_column(
        ForeignKey("tickets.id", ondelete="CASCADE"),
        nullable=False
    )
    
    author_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Content
    body: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Visibility
    is_internal: Mapped[bool] = mapped_column(default=False)
    
    # Attachments
    attachments: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
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
    ticket: Mapped["Ticket"] = relationship("Ticket", back_populates="replies")
    author: Mapped["User"] = relationship("User", back_populates="ticket_replies")
    
    def __repr__(self) -> str:
        return f"<TicketReply(id={self.id}, ticket={self.ticket_id}, author={self.author_id})>"
    
    def to_dict(self, include_internal: bool = False) -> dict:
        """
        Convert reply to dictionary.
        
        Args:
            include_internal: Whether to include internal replies
            
        Returns:
            Dictionary representation
        """
        if self.is_internal and not include_internal:
            return None
            
        return {
            "id": self.id,
            "ticket_id": self.ticket_id,
            "author_id": self.author_id,
            "author_name": self.author.full_name if self.author else None,
            "author_role": self.author.role.value if self.author else None,
            "body": self.body,
            "is_internal": self.is_internal,
            "attachments": self.attachments or {},
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
