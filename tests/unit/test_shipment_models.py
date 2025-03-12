"""
Unit Tests für die Shipment-Modelle.

Diese Tests überprüfen die korrekte Funktionalität der Shipment-Modellklassen.
"""
import pytest
from graph.models.shipment_models import ShipmentItem, Shipment, LoadCarrierType


def test_shipment_item_initialization():
    """Test für die korrekte Initialisierung von ShipmentItem."""
    # Test mit Standardwerten (alle Felder None)
    item = ShipmentItem()
    assert item.load_carrier is None
    assert item.name is None
    assert item.quantity is None
    assert item.length is None
    assert item.width is None
    assert item.height is None
    assert item.weight is None
    assert item.stackable is None
    
    # Test mit vollständigen Werten
    item = ShipmentItem(
        load_carrier=LoadCarrierType.PALLET,
        name="Testpaket",
        quantity=5,
        length=100,
        width=80,
        height=120,
        weight=25,
        stackable=True
    )
    assert item.load_carrier == LoadCarrierType.PALLET
    assert item.name == "Testpaket"
    assert item.quantity == 5
    assert item.length == 100
    assert item.width == 80
    assert item.height == 120
    assert item.weight == 25
    assert item.stackable is True
    
    # Test des Model-Dump-Formats
    item_dict = item.model_dump()
    assert item_dict["load_carrier"] == 1  # PALLET hat den IntEnum-Wert 1
    assert item_dict["name"] == "Testpaket"


def test_shipment_initialization():
    """Test für die korrekte Initialisierung von Shipment."""
    # Test mit Standardwerten
    shipment = Shipment()
    assert shipment.items == []
    assert shipment.shipment_notes is None
    assert shipment.message is None
    
    # Test mit befüllten Werten
    test_item = ShipmentItem(
        load_carrier=LoadCarrierType.PACKAGE,
        name="Testpaket",
        quantity=1
    )
    
    shipment = Shipment(
        items=[test_item],
        shipment_notes="Testnotiz",
        message="Erfolgreich extrahiert"
    )
    
    assert len(shipment.items) == 1
    assert shipment.items[0].name == "Testpaket"
    assert shipment.items[0].load_carrier == LoadCarrierType.PACKAGE
    assert shipment.shipment_notes == "Testnotiz"
    assert shipment.message == "Erfolgreich extrahiert"
    
    # Test des Model-Dump-Formats
    shipment_dict = shipment.model_dump()
    assert len(shipment_dict["items"]) == 1
    assert shipment_dict["items"][0]["load_carrier"] == 2  # PACKAGE hat den IntEnum-Wert 2
    assert shipment_dict["shipment_notes"] == "Testnotiz"


def test_load_carrier_type_enum():
    """Test für die korrekte Funktionalität des LoadCarrierType-Enums."""
    assert LoadCarrierType.PALLET.value == 1
    assert LoadCarrierType.PACKAGE.value == 2
    assert LoadCarrierType.EURO_PALLET_CAGE.value == 3
    assert LoadCarrierType.DOCUMENT.value == 4
    assert LoadCarrierType.OTHER.value == 5
    
    # Test der Umwandlung von IntEnum zu int
    assert int(LoadCarrierType.PALLET) == 1
    
    # Test der Umwandlung von int zu IntEnum
    assert LoadCarrierType(2) == LoadCarrierType.PACKAGE 