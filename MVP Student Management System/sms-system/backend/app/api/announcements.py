"""
Announcements API Router

System announcements and notifications.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.announcement import Announcement, AnnouncementTarget, AnnouncementPriority, AnnouncementRead


router = APIRouter()


@router.get("/")
async def get_announcements(
    target: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get announcements for current user."""
    query = db.query(Announcement).filter(
        Announcement.is_published == True,
        Announcement.is_active == True
    )
    
    # Filter by visibility
    if current_user.is_student:
        query = query.filter(
            (Announcement.target == AnnouncementTarget.GLOBAL) |
            (Announcement.target == AnnouncementTarget.STUDENTS)
        )
    elif current_user.is_lecturer:
        query = query.filter(
            (Announcement.target == AnnouncementTarget.GLOBAL) |
            (Announcement.target == AnnouncementTarget.LECTURERS) |
            (Announcement.target == AnnouncementTarget.STAFF)
        )
    
    if target:
        query = query.filter(Announcement.target == target)
    
    if priority:
        query = query.filter(Announcement.priority == priority)
    
    # Order by pinned first, then date
    announcements = query.order_by(
        Announcement.is_pinned.desc(),
        Announcement.created_at.desc()
    ).limit(limit).all()
    
    return [a.to_dict() for a in announcements]


@router.get("/{announcement_id}")
async def get_announcement(
    announcement_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get announcement details."""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    # Increment view count
    announcement.view_count += 1
    
    # Mark as read
    existing_read = db.query(AnnouncementRead).filter(
        AnnouncementRead.announcement_id == announcement_id,
        AnnouncementRead.user_id == current_user.id
    ).first()
    
    if not existing_read:
        read_record = AnnouncementRead(
            announcement_id=announcement_id,
            user_id=current_user.id
        )
        db.add(read_record)
    
    db.commit()
    
    return announcement.to_dict()


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Create a new announcement (lecturer/admin only)."""
    from datetime import datetime
    
    announcement = Announcement(
        author_id=current_user.id,
        title=announcement_data.get("title"),
        body=announcement_data.get("body"),
        excerpt=announcement_data.get("excerpt"),
        target=announcement_data.get("target", AnnouncementTarget.GLOBAL),
        target_id=announcement_data.get("target_id"),
        priority=announcement_data.get("priority", AnnouncementPriority.NORMAL),
        category=announcement_data.get("category"),
        attachments=announcement_data.get("attachments", {}),
        is_pinned=announcement_data.get("is_pinned", False),
        is_published=announcement_data.get("is_published", True),
        publish_at=datetime.fromisoformat(announcement_data.get("publish_at")) if announcement_data.get("publish_at") else None,
        expires_at=datetime.fromisoformat(announcement_data.get("expires_at")) if announcement_data.get("expires_at") else None,
    )
    
    db.add(announcement)
    db.commit()
    db.refresh(announcement)
    
    return announcement.to_dict()


@router.put("/{announcement_id}")
async def update_announcement(
    announcement_id: int,
    announcement_data: dict,
    current_user: User = Depends(require_role(UserRole.LECTURER)),
    db: Session = Depends(get_db)
):
    """Update an announcement."""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    # Check ownership (only author or admin can edit)
    if announcement.author_id != current_user.id and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only edit your own announcements"
        )
    
    for field, value in announcement_data.items():
        if hasattr(announcement, field):
            setattr(announcement, field, value)
    
    db.commit()
    db.refresh(announcement)
    
    return announcement.to_dict()


@router.delete("/{announcement_id}")
async def delete_announcement(
    announcement_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete an announcement (admin only)."""
    announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if not announcement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Announcement not found"
        )
    
    db.delete(announcement)
    db.commit()
    
    return {"message": "Announcement deleted successfully"}


@router.get("/unread/count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get count of unread announcements."""
    # Get IDs of read announcements
    read_ids = [
        r.announcement_id for r in db.query(AnnouncementRead).filter(
            AnnouncementRead.user_id == current_user.id
        ).all()
    ]
    
    # Count visible announcements that haven't been read
    query = db.query(Announcement).filter(
        Announcement.is_published == True,
        Announcement.is_active == True,
        ~Announcement.id.in_(read_ids) if read_ids else True
    )
    
    if current_user.is_student:
        query = query.filter(
            (Announcement.target == AnnouncementTarget.GLOBAL) |
            (Announcement.target == AnnouncementTarget.STUDENTS)
        )
    
    count = query.count()
    
    return {"unread_count": count}
