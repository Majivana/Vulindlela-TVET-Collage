"""
Campus Map API Router

Campus navigation and points of interest.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.campus_map import CampusMapPoint, CampusBoundary, MapPointType
from app.models.timetable import Venue


router = APIRouter()


@router.get("/points")
async def get_map_points(
    point_type: Optional[str] = None,
    building: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all campus map points."""
    query = db.query(CampusMapPoint).filter(CampusMapPoint.is_active == True)
    
    if point_type:
        query = query.filter(CampusMapPoint.point_type == point_type)
    
    if building:
        query = query.filter(CampusMapPoint.building == building)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (CampusMapPoint.name.ilike(search_filter)) |
            (CampusMapPoint.description.ilike(search_filter))
        )
    
    points = query.order_by(CampusMapPoint.display_order).all()
    
    return [p.to_dict() for p in points]


@router.get("/points/{point_id}")
async def get_map_point(
    point_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific map point details."""
    point = db.query(CampusMapPoint).filter(CampusMapPoint.id == point_id).first()
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map point not found"
        )
    
    return point.to_dict()


@router.get("/buildings")
async def get_buildings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all buildings."""
    buildings = db.query(CampusMapPoint.building).distinct().all()
    return [b[0] for b in buildings if b[0]]


@router.get("/types")
async def get_point_types(
    current_user: User = Depends(get_current_user)
):
    """Get list of map point types."""
    return [
        {"value": t.value, "label": t.value.replace("_", " ").title()}
        for t in MapPointType
    ]


@router.get("/boundary")
async def get_campus_boundary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get campus boundary for geofencing."""
    boundary = db.query(CampusBoundary).filter(
        CampusBoundary.is_active == True,
        CampusBoundary.is_primary == True
    ).first()
    
    if not boundary:
        # Return default boundary from config
        return {
            "center": {
                "lat": -33.9249,
                "lng": 18.4241,
            },
            "radius": 500,
        }
    
    return boundary.to_dict()


@router.get("/directions")
async def get_directions(
    from_lat: float,
    from_lng: float,
    to_point_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get directions to a campus point."""
    destination = db.query(CampusMapPoint).filter(CampusMapPoint.id == to_point_id).first()
    if not destination:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Destination not found"
        )
    
    # In a real implementation, this would integrate with a routing service
    # For now, return basic information
    return {
        "from": {"lat": from_lat, "lng": from_lng},
        "to": {
            "id": destination.id,
            "name": destination.name,
            "lat": destination.lat,
            "lng": destination.lng,
        },
        "message": f"Navigate to {destination.name} at {destination.full_location}",
    }


# Admin endpoints
@router.post("/points", status_code=status.HTTP_201_CREATED)
async def create_map_point(
    point_data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new map point (admin only)."""
    point = CampusMapPoint(
        name=point_data.get("name"),
        description=point_data.get("description"),
        point_type=point_data.get("point_type", MapPointType.OTHER),
        building=point_data.get("building"),
        floor=point_data.get("floor"),
        room_number=point_data.get("room_number"),
        lat=point_data.get("lat"),
        lng=point_data.get("lng"),
        icon=point_data.get("icon"),
        color=point_data.get("color", "#D4A84B"),
        is_accessible=point_data.get("is_accessible", True),
        has_parking=point_data.get("has_parking", False),
        has_wifi=point_data.get("has_wifi", False),
        operating_hours=point_data.get("operating_hours"),
        contact_phone=point_data.get("contact_phone"),
        contact_email=point_data.get("contact_email"),
    )
    
    db.add(point)
    db.commit()
    db.refresh(point)
    
    return point.to_dict()


@router.put("/points/{point_id}")
async def update_map_point(
    point_id: int,
    point_data: dict,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Update a map point (admin only)."""
    point = db.query(CampusMapPoint).filter(CampusMapPoint.id == point_id).first()
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map point not found"
        )
    
    for field, value in point_data.items():
        if hasattr(point, field):
            setattr(point, field, value)
    
    db.commit()
    db.refresh(point)
    
    return point.to_dict()


@router.delete("/points/{point_id}")
async def delete_map_point(
    point_id: int,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Delete a map point (admin only)."""
    point = db.query(CampusMapPoint).filter(CampusMapPoint.id == point_id).first()
    if not point:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map point not found"
        )
    
    db.delete(point)
    db.commit()
    
    return {"message": "Map point deleted successfully"}


# Venues are also shown on the map
@router.get("/venues")
async def get_venues_for_map(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get venues for map display."""
    venues = db.query(Venue).filter(Venue.is_active == True).all()
    
    result = []
    for venue in venues:
        if venue.lat and venue.lng:
            result.append({
                "id": f"venue_{venue.id}",
                "name": venue.name,
                "point_type": "lecture_hall" if "lecture" in venue.venue_type.lower() else "workshop",
                "building": venue.building,
                "floor": venue.floor,
                "room_number": venue.room_number,
                "lat": venue.lat,
                "lng": venue.lng,
                "color": "#4A90D9",
            })
    
    return result
