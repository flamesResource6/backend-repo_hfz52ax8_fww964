"""
Database Schemas for Gas Cylinder Management

Each Pydantic model corresponds to a MongoDB collection. The collection
name is the lowercase of the class name.
"""
from typing import Optional, List, Literal
from pydantic import BaseModel, Field


class User(BaseModel):
    email: str = Field(..., description="Email address used for login")
    name: str = Field(..., description="Display name")
    role: Literal["admin", "staff", "driver"] = Field("admin", description="User role")
    password: Optional[str] = Field(None, description="Plain demo password (do not use in production)")
    is_active: bool = Field(True, description="Whether user is active")


class Cylinder(BaseModel):
    barcode: str = Field(..., description="Unique cylinder barcode/serial")
    gas_type: Literal["LPG", "O2", "CO2", "N2", "Ar", "Other"] = Field("LPG")
    capacity_kg: float = Field(..., gt=0, description="Cylinder capacity in KG")
    status: Literal["in_stock", "reserved", "out_for_delivery", "delivered", "maintenance"] = Field("in_stock")
    location: Optional[str] = Field(None, description="Warehouse bin or current location")
    notes: Optional[str] = None


class Customer(BaseModel):
    name: str
    phone: str
    address: str
    email: Optional[str] = None


class OrderItem(BaseModel):
    gas_type: str
    capacity_kg: float
    quantity: int = Field(..., gt=0)


class Order(BaseModel):
    customer_id: str = Field(..., description="Reference to customer _id as string")
    items: List[OrderItem]
    status: Literal["pending", "preparing", "out_for_delivery", "delivered", "cancelled"] = "pending"
    assigned_to: Optional[str] = Field(None, description="Driver user id")


class DeliveryTask(BaseModel):
    order_id: str
    driver_id: Optional[str] = None
    status: Literal["assigned", "picked_up", "en_route", "delivered", "failed"] = "assigned"
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    note: Optional[str] = None
