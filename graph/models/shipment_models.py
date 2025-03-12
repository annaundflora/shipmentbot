"""
Shipment models for structured output.

Diese Datei definiert die Datenmodelle für die Extraktion von Sendungsdaten.
"""
from enum import IntEnum
from typing import Optional, List
from pydantic import BaseModel, Field

class LoadCarrierType(IntEnum):
    PALLET = 1
    PACKAGE = 2
    EURO_PALLET_CAGE = 3
    DOCUMENT = 4
    OTHER = 5

class ShipmentItem(BaseModel):
    """Information about a single shipment item with all necessary details."""
    
    # FIELD GROUP 1: Basic Information
    load_carrier: Optional[LoadCarrierType] = Field(None, description="Type of load carrier (1=pallet, 2=package, 3=euro pallet cage, 4=document, 5=other)")
    name: Optional[str] = Field(None, description="Description of the goods being shipped")
    quantity: Optional[int] = Field(None, description="Number of pieces of this item type")
    
    # FIELD GROUP 2: Dimensions
    length: Optional[int] = Field(None, description="Length in cm")
    width: Optional[int] = Field(None, description="Width in cm")
    height: Optional[int] = Field(None, description="Height in cm")
    weight: Optional[int] = Field(None, description="Weight in kg")
    
    # FIELD GROUP 3: Handling
    stackable: Optional[bool] = Field(None, description="Whether the items can be stacked")

class Shipment(BaseModel):
    """Complete shipment information including items and notes."""
    
    # All items in the shipment
    items: Optional[List[ShipmentItem]] = Field(default_factory=list, description="List of items in the shipment")
    
    # Additional notes about the shipment
    shipment_notes: Optional[str] = Field(None, description="Only very specific notes about the shipment and goods, which are not covered by the other fields.")
    
    # Message to the user
    message: Optional[str] = Field(None, description="Message to the user, e.g. about missing data or other issues.") 