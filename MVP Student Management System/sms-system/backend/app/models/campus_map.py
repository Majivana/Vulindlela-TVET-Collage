"""
Campus Map Model

Points of interest for campus navigation.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, 
    Float, Boolean, Enum
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class MapPointType(str, enum.Enum):
    """Type of point on the campus map."""
    LECTURE_HALL = "lecture_hall"
    LABORATORY = "laboratory"
    WORKSHOP = "workshop"
    LIBRARY = "library"
    CAFETERIA = "cafeteria"
    ADMIN_OFFICE = "admin_office"
    RECEPTION = "reception"
    SECURITY = "security"
    PARKING = "parking"
    RESTROOM = "restroom"
    FIRST_AID = "first_aid"
    PRAYER_ROOM = "prayer_room"
    ATM = "atm"
    BUS_STOP = "bus_stop"
    ENTRANCE = "entrance"
    EMERGENCY_EXIT = "emergency_exit"
    LANDMARK = "landmark"
    OTHER = "other"


class CampusMapPoint(Base):
    """
    Campus map point for navigation.
    
    Attributes:
        id: Primary key
        name: Display name
        description: Detailed description
        point_type: Type of location
        building: Building name
        floor: Floor number
        room_number: Room identifier
        lat: Latitude coordinate
        lng: Longitude coordinate
        icon: Custom icon identifier
        color: Display color
        is_accessible: Wheelchair accessible
        has_parking: Nearby parking available
        operating_hours: When location is open
        contact_phone: Contact number
        contact_email: Contact email
        photos: Photo URLs
        is_active: Whether visible on map
    """
    
    __tablename__ = "campus_map_points"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Basic Information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    point_type: Mapped[MapPointType] = mapped_column(
        Enum(MapPointType),
        nullable=False
    )
    
    # Location Details
    building: Mapped[str] = mapped_column(String(100), nullable=False)
    floor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    room_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Coordinates
    lat: Mapped[float] = mapped_column(nullable=False)
    lng: Mapped[float] = mapped_column(nullable=False)
    
    # Display
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    color: Mapped[str] = mapped_column(String(7), default="#D4A84B")  # Gold accent
    
    # Features
    is_accessible: Mapped[bool] = mapped_column(default=True)
    has_parking: Mapped[bool] = mapped_column(default=False)
    has_wifi: Mapped[bool] = mapped_column(default=False)
    
    # Contact & Hours
    operating_hours: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    contact_phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    contact_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Media
    photos: Mapped[Optional[dict]] = mapped_column(nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(default=True)
    display_order: Mapped[int] = mapped_column(default=0)
    
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
    
    def __repr__(self) -> str:
        return f"<CampusMapPoint(id={self.id}, name={self.name}, type={self.point_type.value})>"
    
    @property
    full_location(self) -> str:
        """Get full location string."""
        parts = [self.building]
        if self.floor is not None:
            parts.append(f"Floor {self.floor}")
        if self.room_number:
            parts.append(f"Room {self.room_number}")
        return ", ".join(parts)
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "point_type": self.point_type.value,
            "building": self.building,
            "floor": self.floor,
            "room_number": self.room_number,
            "full_location": self.full_location,
            "lat": self.lat,
            "lng": self.lng,
            "icon": self.icon,
            "color": self.color,
            "is_accessible": self.is_accessible,
            "has_parking": self.has_parking,
            "has_wifi": self.has_wifi,
            "operating_hours": self.operating_hours,
            "contact_phone": self.contact_phone,
            "contact_email": self.contact_email,
            "photos": self.photos,
            "is_active": self.is_active,
        }


class CampusBoundary(Base):
    """
    Campus boundary for geofencing.
    
    Defines the polygon that represents the campus area
    for attendance verification.
    """
    
    __tablename__ = "campus_boundaries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Boundary as list of coordinate pairs
    # Format: [{"lat": x, "lng": y}, ...]
    coordinates: Mapped[dict] = mapped_column(nullable=False)
    
    # Alternative: center point + radius for circular geofence
    center_lat: Mapped[Optional[float]] = mapped_column(nullable=True)
    center_lng: Mapped[Optional[float]] = mapped_column(nullable=True)
    radius_meters: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Settings
    is_active: Mapped[bool] = mapped_column(default=True)
    is_primary: Mapped[bool] = mapped_column(default=False)
    
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
    
    def __repr__(self) -> str:
        return f"<CampusBoundary(id={self.id}, name={self.name})>"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coordinates": self.coordinates,
            "center_lat": self.center_lat,
            "center_lng": self.center_lng,
            "radius_meters": self.radius_meters,
            "is_active": self.is_active,
            "is_primary": self.is_primary,
        }
