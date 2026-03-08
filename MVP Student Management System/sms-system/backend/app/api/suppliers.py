"""
Suppliers API Router

Supplier management for equipment and services.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.api.auth import get_current_user, require_role
from app.models.user import User, UserRole
from app.models.supplier import Supplier, ServiceCategory, SupplierStatus


router = APIRouter()


@router.get("/")
async def get_suppliers(
    category: Optional[str] = None,
    status: Optional[str] = SupplierStatus.ACTIVE,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all suppliers with optional filtering."""
    query = db.query(Supplier)
    
    if category:
        query = query.filter(Supplier.service_category == category)
    
    if status:
        query = query.filter(Supplier.status == status)
    
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Supplier.name.ilike(search_filter)) |
            (Supplier.contact_person.ilike(search_filter)) |
            (Supplier.email.ilike(search_filter))
        )
    
    suppliers = query.all()
    return [s.to_dict() for s in suppliers]


@router.get("/{supplier_id}")
async def get_supplier(
    supplier_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get supplier details."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    return supplier.to_dict(include_sensitive=current_user.is_admin)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_supplier(
    supplier_data: dict,
    current_user: User = Depends(require_role(UserRole.SUPPLIER_MANAGER)),
    db: Session = Depends(get_db)
):
    """Create a new supplier (supplier manager only)."""
    supplier = Supplier(
        name=supplier_data.get("name"),
        contact_person=supplier_data.get("contact_person"),
        email=supplier_data.get("email"),
        phone=supplier_data.get("phone"),
        service_category=supplier_data.get("service_category", ServiceCategory.OTHER),
        services_description=supplier_data.get("services_description"),
        address=supplier_data.get("address"),
        city=supplier_data.get("city"),
        postal_code=supplier_data.get("postal_code"),
        website=supplier_data.get("website"),
        notes=supplier_data.get("notes"),
        created_by_id=current_user.id,
    )
    
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    
    return supplier.to_dict()


@router.put("/{supplier_id}")
async def update_supplier(
    supplier_id: int,
    supplier_data: dict,
    current_user: User = Depends(require_role(UserRole.SUPPLIER_MANAGER)),
    db: Session = Depends(get_db)
):
    """Update supplier information."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    for field, value in supplier_data.items():
        if hasattr(supplier, field):
            setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    
    return supplier.to_dict()


@router.delete("/{supplier_id}")
async def delete_supplier(
    supplier_id: int,
    current_user: User = Depends(require_role(UserRole.SUPPLIER_MANAGER)),
    db: Session = Depends(get_db)
):
    """Delete or deactivate a supplier."""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Supplier not found"
        )
    
    # Soft delete by setting status to inactive
    supplier.status = SupplierStatus.INACTIVE
    db.commit()
    
    return {"message": "Supplier deactivated successfully"}


@router.get("/categories/list")
async def get_categories(
    current_user: User = Depends(get_current_user)
):
    """Get list of supplier categories."""
    return [
        {"value": cat.value, "label": cat.value.replace("_", " ").title()}
        for cat in ServiceCategory
    ]
