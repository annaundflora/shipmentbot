"""
Integrationstests für den Shipment-Graph.

Diese Tests überprüfen die korrekte Funktionalität des gesamten Workflows
mit gemockten LLM-Antworten.
"""
import pytest
from unittest.mock import patch, MagicMock
from graph.shipment_graph import create_shipment_graph
from graph.models.shipment_models import Shipment, ShipmentItem, LoadCarrierType


@pytest.fixture
def mock_process_shipment():
    """Fixture, die die process_shipment-Funktion mockt."""
    with patch('graph.nodes.shipment_extractor.process_shipment') as mock_process:
        # Konfiguriere den Mock für eine erfolgreiche Extraktion
        mock_process.return_value = {
            "extracted_data": {
                "items": [
                    {
                        "load_carrier": 1,  # LoadCarrierType.PALLET
                        "name": "Testpaket",
                        "quantity": 3,
                        "length": 120,
                        "width": 80,
                        "height": 100,
                        "weight": 50,
                        "stackable": True
                    }
                ],
                "shipment_notes": "Vorsichtig behandeln",
                "message": "Extraktion erfolgreich."
            },
            "message": "Extraktion erfolgreich."
        }
        yield mock_process


def test_shipment_graph_basic_workflow(mock_process_shipment):
    """
    Test für den grundlegenden Workflow des Shipment-Graphen.
    
    Dieser Test überprüft, ob der Graph korrekt kompiliert wird und
    ob die Validierung und Extraktion korrekt durchgeführt werden.
    """
    # Erstelle den Graph für Tests
    with patch('graph.shipment_graph.compiled_graph.get_graph') as mock_get_graph:
        # Mock für die Visualisierung
        mock_get_graph.return_value.draw_mermaid_png.side_effect = Exception("Test-Mock")
        
        # Graph erstellen
        graph = create_shipment_graph(with_checkpointer=True)
        
        # Testdaten
        test_input = {
            "messages": ["Ich benötige einen Transport für 3 Paletten, je 120x80x100cm."]
        }
        
        # Graph ausführen
        result = graph.invoke(test_input)
        
        # Überprüfungen
        assert "messages" in result
        assert result["messages"] == ["Ich benötige einen Transport für 3 Paletten, je 120x80x100cm."]
        
        assert "extracted_data" in result
        assert result["extracted_data"] is not None
        assert "items" in result["extracted_data"]
        assert len(result["extracted_data"]["items"]) == 1
        
        # Überprüfe, ob die Mock-Funktion aufgerufen wurde
        mock_process_shipment.assert_called_once()


def test_shipment_graph_validation():
    """
    Test zur Überprüfung der State-Validierung im Graph.
    
    Überprüft, ob der Graph einen unvollständigen State korrekt validiert
    und fehlende Felder hinzufügt.
    """
    # Erstelle den Graph für Tests
    with patch('graph.shipment_graph.compiled_graph.get_graph') as mock_get_graph, \
         patch('graph.nodes.shipment_extractor.process_shipment') as mock_process:
        
        # Mock für die Visualisierung
        mock_get_graph.return_value.draw_mermaid_png.side_effect = Exception("Test-Mock")
        
        # Mock für den Extraktionsprozess
        mock_process.return_value = {
            "extracted_data": None,
            "message": "Test-Meldung"
        }
        
        # Graph erstellen
        graph = create_shipment_graph()
        
        # Unvollständigen State verwenden
        incomplete_state = {
            # Nur messages, keine extracted_data oder message
            "messages": ["Test-Nachricht"]
        }
        
        # Graph ausführen
        result = graph.invoke(incomplete_state)
        
        # Überprüfungen
        assert "messages" in result
        assert "extracted_data" in result
        assert "message" in result
        
        # Überprüfe, ob die Validierung korrekt funktioniert hat
        assert result["messages"] == ["Test-Nachricht"]
        assert result["message"] == "Test-Meldung"


def test_shipment_graph_error_handling():
    """
    Test zur Überprüfung der Fehlerbehandlung im Graph.
    
    Überprüft, ob der Graph Fehler in der Extraktionsfunktion korrekt behandelt.
    """
    # Erstelle den Graph für Tests
    with patch('graph.shipment_graph.compiled_graph.get_graph') as mock_get_graph, \
         patch('graph.nodes.shipment_extractor.process_shipment') as mock_process:
        
        # Mock für die Visualisierung
        mock_get_graph.return_value.draw_mermaid_png.side_effect = Exception("Test-Mock")
        
        # Mock für den Extraktionsprozess mit Fehler
        mock_process.return_value = {
            "extracted_data": None,
            "message": "Fehler bei der Extraktion: Test-Fehler"
        }
        
        # Graph erstellen
        graph = create_shipment_graph()
        
        # Testdaten
        test_input = {
            "messages": ["Testdaten mit Fehler"]
        }
        
        # Graph ausführen
        result = graph.invoke(test_input)
        
        # Überprüfungen
        assert "extracted_data" in result
        assert result["extracted_data"] is None
        assert "message" in result
        assert "Fehler bei der Extraktion" in result["message"] 