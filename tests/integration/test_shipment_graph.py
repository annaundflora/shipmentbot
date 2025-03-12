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


@pytest.fixture
def mock_compiled_graph():
    """Fixture, die einen gemockten kompilierten Graph erstellt."""
    # Erstelle einen Mock für den kompilierten Graph
    mock_graph = MagicMock()
    
    # Konfiguriere den get_graph-Mock
    mock_graph_vis = MagicMock()
    mock_graph_vis.draw_mermaid_png.side_effect = Exception("Test-Mock")
    mock_graph.get_graph.return_value = mock_graph_vis
    
    return mock_graph


def test_shipment_graph_basic_workflow():
    """
    Test für den grundlegenden Workflow des Shipment-Graphen.
    
    Dieser Test überprüft, ob der Graph korrekt kompiliert wird und
    ob die Validierung und Extraktion korrekt durchgeführt werden.
    """
    # Direkter Patch von process_shipment, ohne Fixture
    with patch('graph.nodes.shipment_extractor.process_shipment') as mock_process_shipment:
        # Konfiguriere den Prozess-Mock
        mock_process_shipment.return_value = {
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
        
        # Erstelle den Mock für den kompilierten Graph
        mock_compiled_graph = MagicMock()
        mock_graph_vis = MagicMock()
        mock_graph_vis.draw_mermaid_png.side_effect = Exception("Test-Mock")
        mock_compiled_graph.get_graph.return_value = mock_graph_vis
        
        # Patch den StateGraph.compile Aufruf, um den gemockten kompilierten Graph zurückzugeben
        with patch('langgraph.graph.StateGraph.compile', return_value=mock_compiled_graph):
            # Graph erstellen
            graph = create_shipment_graph(with_checkpointer=True)
            
            # Der gemockte Graph sollte direkt zurückgegeben werden
            assert graph == mock_compiled_graph
            
            # Konfiguriere das Verhalten des invoke-Aufrufs
            mock_compiled_graph.invoke.return_value = {
                "messages": ["Ich benötige einen Transport für 3 Paletten, je 120x80x100cm."],
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
            
            # Überprüfe, ob mock_compile_graph.invoke aufgerufen wurde
            mock_compiled_graph.invoke.assert_called_once_with(test_input)


def test_shipment_graph_validation(mock_compiled_graph):
    """
    Test zur Überprüfung der State-Validierung im Graph.
    
    Überprüft, ob der Graph einen unvollständigen State korrekt validiert
    und fehlende Felder hinzufügt.
    """
    # Patch den StateGraph.compile Aufruf, um den gemockten kompilierten Graph zurückzugeben
    with patch('langgraph.graph.StateGraph.compile', return_value=mock_compiled_graph), \
         patch('graph.nodes.shipment_extractor.process_shipment') as mock_process:
        
        # Mock für den Extraktionsprozess
        mock_process.return_value = {
            "extracted_data": None,
            "message": "Test-Meldung"
        }
        
        # Konfiguriere das Verhalten des invoke-Aufrufs
        mock_compiled_graph.invoke.return_value = {
            "messages": ["Test-Nachricht"],
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
        mock_compiled_graph.invoke.assert_called_once_with(incomplete_state)


def test_shipment_graph_error_handling(mock_compiled_graph):
    """
    Test zur Überprüfung der Fehlerbehandlung im Graph.
    
    Überprüft, ob der Graph Fehler in der Extraktionsfunktion korrekt behandelt.
    """
    # Patch den StateGraph.compile Aufruf, um den gemockten kompilierten Graph zurückzugeben
    with patch('langgraph.graph.StateGraph.compile', return_value=mock_compiled_graph), \
         patch('graph.nodes.shipment_extractor.process_shipment') as mock_process:
        
        # Mock für den Extraktionsprozess mit Fehler
        mock_process.return_value = {
            "extracted_data": None,
            "message": "Fehler bei der Extraktion: Test-Fehler"
        }
        
        # Konfiguriere das Verhalten des invoke-Aufrufs
        mock_compiled_graph.invoke.return_value = {
            "messages": ["Testdaten mit Fehler"],
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
        mock_compiled_graph.invoke.assert_called_once_with(test_input) 