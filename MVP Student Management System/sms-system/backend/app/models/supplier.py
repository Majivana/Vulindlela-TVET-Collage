"""
Supplier Model

Supplier management for equipment, materials, and services.
"""

from datetime import datetime
from typing import Optional, List
from sqlalchemy import (
    Column, Integer, String, DateTime, Text, 
    Boolean, JSON, Enum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
import enum

from app.db.database import Base


class ServiceCategory(str, enum.Enum):
    """Category of supplier services."""
    EQUIPMENT = "equipment"
    TOOLS = "tools"
    MATERIALS = "materials"
    CONSUMABLES = "consumables"
    SERVICES = "services"
    MAINTENANCE = "maintenance"
    TRANSPORT = "transport"
    IT = "it"
    OFFICE_SUPPLIES = "office_supplies"
    OTHER = "other"


class SupplierStatus(str, enum.Enum):
    """Supplier status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"
    BLACKLISTED = "blacklisted"


class Supplier(Base):
    """
    Supplier model for vendor management.
    
    Attributes:
        id: Primary key
        name: Company/organization name
        contact_person: Primary contact name
        email: Contact email
        phone: Contact phone
        mobile: Mobile number
        fax: Fax number
        website: Company website
        registration_number: Business registration
        tax_number: Tax/VAT number
        service_category: Primary service category
        services_description: Detailed service description
        address: Physical address
        city: City
        postal_code: Postal code
        status: Supplier status
        rating: Internal rating (1-5)
        notes: Additional notes
        documents: Contract documents, etc.
        payment_terms: Payment terms
        bank_details: Banking information
    """
    
    __tablename__ = "suppliers"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Company Information
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    trading_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    registration_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    tax_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Contact Person
    contact_person: Mapped[str] = mapped_column(String(100), nullable=False)
    contact_position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Contact Details
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    mobile: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    fax: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    website: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Services
    service_category: Mapped[ServiceCategory] = mapped_column(
        Enum(ServiceCategory),
        nullable=False
    )
    services_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Address
    address: Mapped[str] = mapped_column(Text, nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    postal_code: Mapped[str] = mapped_column(String(20), nullable=False)
    province: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="South Africa")
    
    # Status & Rating
    status: Mapped[SupplierStatus] = mapped_column(
        Enum(SupplierStatus),
        default=SupplierStatus.ACTIVE,
        nullable=False
    )
    rating: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Business Details
    payment_terms: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    credit_limit: Mapped[Optional[float]] = mapped_column(nullable=True)
    lead_time_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Documents & Notes
    documents: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Banking (encrypted in production)
    bank_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_branch: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    bank_branch_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
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
    
    # Audit
    created_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    def __repr__(self) -> str:
        return f"<Supplier(id={self.id}, name={self.name}, category={self.service_category.value})>"
    
    @property
    def full_address(self) -> str:
        """Get full address string."""
        parts = [
            self.address,
            self.city,
            self.province,
            self.postal_code,
            self.country
        ]
        return ", ".join(filter(None, parts))
    
    @property
    def contact_summary(self) -> str:
        """Get contact summary."""
        return f"{self.contact_person} ({self.email}, {self.phone})"
    
    def to_dict(self, include_sensitive: bool = False) -> dict:
        """
        Convert supplier to dictionary.
        
        Args:
            include_sensitive: Whether to include banking details
            
        Returns:
            Dictionary representation
        """
        data = {
            "id": self.id,
            "name": self.name,
            "trading_name": self.trading_name,
            "registration_number": self.registration_number,
            "tax_number": self.tax_number,
            "contact_person": self.contact_person,
            "contact_position": self.contact_position,
            "email": self.email,
            "phone": self.phone,
            "mobile": self.mobile,
            "fax": self.fax,
            "website": self.website,
            "service_category": self.service_category.value,
            "services_description": self.services_description,
            "address": self.address,
            "city": self.city,
            "postal_code": self.postal_code,
            "province": self.province,
            "country": self.country,
            "full_address": self.full_address,
            "status": self.status.value,
            "rating": self.rating,
            "payment_terms": self.payment_terms,
            "credit_limit": self.credit_limit,
            "lead_time_days": self.lead_time_days,
            "documents": self.documents or {},
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
        
        if include_sensitive:
            data["bank_name"] = self.bank_name
            data["bank_account"] = self.bank_account
            data["bank_branch"] = self.bank_branch
            data["bank_branch_code"] = self.bank_branch_code
            
        return data


class PurchaseRequest(Base):
    """
    Purchase request linked to suppliers.
    
    For future expansion of procurement workflow.
    """
    
    __tablename__ = "purchase_requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    request_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suppliers.id"),
        nullable=True
    )
    
    # Request Details
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    items: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    
    # Financial
    estimated_cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    actual_cost: Mapped[Optional[float]] = mapped_column(nullable=True)
    
    # Status
    status: Mapped[str] = mapped_column(String(50), default="pending")
    
    # Approval
    requested_by_id: Mapped[int] = mapped_column(Integer, nullable=False)
    approved_by_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
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
        return f"<PurchaseRequest(id={self.id}, number={self.request_number})>"
