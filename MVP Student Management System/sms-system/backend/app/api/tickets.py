"""
Tickets API Router

Helpdesk ticket management for student support.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.ticket import Ticket, TicketReply, TicketStatus, TicketDepartment, TicketPriority, TicketCategory


router = APIRouter()


def generate_ticket_number(db: Session) -> str:
    """Generate a unique ticket number."""
    year = datetime.now().year
    count = db.query(Ticket).filter(
        Ticket.ticket_number.like(f"TKT-{year}-%")
    ).count()
    return f"TKT-{year}-{count + 1:05d}"


@router.get("/my")
async def get_my_tickets(
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get tickets created by current student."""
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
    
    query = db.query(Ticket).filter(Ticket.student_id == student.id)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return [t.to_dict() for t in tickets]


@router.get("/{ticket_id}")
async def get_ticket(
    ticket_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ticket details with replies."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    if current_user.is_student:
        student = current_user.student_profile
        if ticket.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own tickets"
            )
    
    result = ticket.to_dict(include_internal=not current_user.is_student)
    result["replies"] = [
        r.to_dict(include_internal=not current_user.is_student) 
        for r in ticket.replies
    ]
    
    return result


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new support ticket."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can create tickets"
        )
    
    student = current_user.student_profile
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student profile not found"
        )
    
    ticket = Ticket(
        ticket_number=generate_ticket_number(db),
        student_id=student.id,
        department=ticket_data.get("department", TicketDepartment.GENERAL),
        category=ticket_data.get("category", TicketCategory.GENERAL_INQUIRY),
        priority=ticket_data.get("priority", TicketPriority.MEDIUM),
        subject=ticket_data.get("subject"),
        body=ticket_data.get("body"),
        attachments=ticket_data.get("attachments", {}),
        status=TicketStatus.OPEN,
    )
    
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    return {
        "message": "Ticket created successfully",
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
    }


@router.post("/{ticket_id}/reply")
async def add_reply(
    ticket_id: int,
    reply_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add a reply to a ticket."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    # Check permissions
    if current_user.is_student:
        student = current_user.student_profile
        if ticket.student_id != student.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only reply to your own tickets"
            )
    
    reply = TicketReply(
        ticket_id=ticket_id,
        author_id=current_user.id,
        body=reply_data.get("body"),
        is_internal=reply_data.get("is_internal", False) and not current_user.is_student,
        attachments=reply_data.get("attachments", {}),
    )
    
    db.add(reply)
    
    # Update ticket status
    if current_user.is_student:
        if ticket.status == TicketStatus.WAITING_FOR_USER:
            ticket.status = TicketStatus.IN_PROGRESS
    else:
        if ticket.status == TicketStatus.OPEN:
            ticket.status = TicketStatus.IN_PROGRESS
            ticket.first_response_at = datetime.utcnow()
    
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(reply)
    
    return {
        "message": "Reply added successfully",
        "reply_id": reply.id,
    }


# Staff endpoints
@router.get("/staff/all")
async def get_all_tickets(
    status: Optional[str] = None,
    department: Optional[str] = None,
    assigned_to_me: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all tickets (staff only)."""
    if current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot access this endpoint"
        )
    
    query = db.query(Ticket)
    
    if status:
        query = query.filter(Ticket.status == status)
    
    if department:
        query = query.filter(Ticket.department == department)
    
    if assigned_to_me:
        query = query.filter(Ticket.assigned_to_id == current_user.id)
    
    tickets = query.order_by(Ticket.created_at.desc()).all()
    
    return [t.to_dict(include_internal=True) for t in tickets]


@router.put("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: int,
    assign_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Assign ticket to staff member."""
    if current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot assign tickets"
        )
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    ticket.assigned_to_id = assign_data.get("assigned_to_id")
    ticket.status = TicketStatus.IN_PROGRESS
    ticket.updated_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "message": "Ticket assigned successfully",
        "ticket_id": ticket_id,
        "assigned_to": ticket.assigned_to_id,
    }


@router.put("/{ticket_id}/status")
async def update_ticket_status(
    ticket_id: int,
    status_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update ticket status."""
    if current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Students cannot update ticket status"
        )
    
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    new_status = status_data.get("status")
    ticket.status = new_status
    
    if new_status == TicketStatus.RESOLVED:
        ticket.resolved_at = datetime.utcnow()
        ticket.resolution_notes = status_data.get("resolution_notes")
    elif new_status == TicketStatus.CLOSED:
        ticket.closed_at = datetime.utcnow()
    
    ticket.updated_at = datetime.utcnow()
    db.commit()
    
    return {
        "message": "Ticket status updated",
        "ticket_id": ticket_id,
        "status": new_status,
    }


@router.post("/{ticket_id}/satisfaction")
async def submit_satisfaction(
    ticket_id: int,
    satisfaction_data: dict,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit satisfaction rating for resolved ticket."""
    if not current_user.is_student:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only students can submit satisfaction ratings"
        )
    
    student = current_user.student_profile
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    
    if not ticket or ticket.student_id != student.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found"
        )
    
    ticket.satisfaction_rating = satisfaction_data.get("rating")
    ticket.satisfaction_comment = satisfaction_data.get("comment")
    
    db.commit()
    
    return {
        "message": "Thank you for your feedback",
        "ticket_id": ticket_id,
    }
