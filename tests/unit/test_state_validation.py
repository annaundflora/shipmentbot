"""
Unit Tests für die State-Validierungsfunktion.

Diese Tests überprüfen die korrekte Funktionalität der Validierungsfunktion.
"""
import pytest
from graph.shipment_graph import validate_state


def test_validate_state_empty():
    """Test für die Validierung eines leeren States."""
    empty_state = {}
    result = validate_state(empty_state)
    
    # Überprüfe, ob alle erforderlichen Felder vorhanden sind
    assert "messages" in result
    assert "extracted_data" in result
    assert "message" in result
    
    # Überprüfe Standardwerte
    assert result["messages"] == []
    assert result["extracted_data"] is None
    assert result["message"] is None
    

def test_validate_state_with_data():
    """Test für die Validierung eines States mit bereits enthaltenen Daten."""
    initial_state = {
        "messages": ["Test message"],
        "extracted_data": {"items": []},
        "message": "Test message"
    }
    
    result = validate_state(initial_state)
    
    # Überprüfe, ob die vorhandenen Daten erhalten bleiben
    assert result["messages"] == ["Test message"]
    assert result["extracted_data"] == {"items": []}
    assert result["message"] == "Test message"


def test_validate_state_with_partial_data():
    """Test für die Validierung eines States mit teilweise fehlenden Daten."""
    partial_state = {
        "messages": ["Test message"]
    }
    
    result = validate_state(partial_state)
    
    # Überprüfe, ob vorhandene Daten erhalten bleiben
    assert result["messages"] == ["Test message"]
    
    # Überprüfe, ob fehlende Felder ergänzt wurden
    assert "extracted_data" in result
    assert "message" in result
    assert result["extracted_data"] is None
    assert result["message"] is None


def test_validate_state_invalid_messages():
    """Test für die Validierung eines States mit ungültigem messages-Feld."""
    invalid_state = {
        "messages": "Keine Liste, sondern ein String"
    }
    
    result = validate_state(invalid_state)
    
    # Überprüfe, ob messages korrigiert wurde
    assert isinstance(result["messages"], list)
    assert result["messages"] == []
    
    # Überprüfe, ob andere Felder korrekt gesetzt wurden
    assert result["extracted_data"] is None
    assert result["message"] is None


def test_validate_state_immutability():
    """Test, ob die Validierungsfunktion den ursprünglichen State unverändert lässt."""
    original_state = {
        "messages": ["Originalnachricht"],
        "extracted_data": {"items": [{"name": "Original"}]}
    }
    
    # Kopie erstellen, um später zu vergleichen
    original_copy = original_state.copy()
    
    # Validieren
    _ = validate_state(original_state)
    
    # Überprüfen, ob das Original unverändert bleibt
    assert original_state == original_copy 