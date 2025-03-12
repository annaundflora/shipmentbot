"""
Unit Tests für den Shipment-Extractor.

Diese Tests überprüfen die korrekte Funktionalität des Shipment-Extractors
mit gemockten LLM-Antworten.
"""
import pytest
from unittest.mock import patch, MagicMock
from graph.nodes.shipment_extractor import process_shipment
from graph.models.shipment_models import Shipment, ShipmentItem, LoadCarrierType


@pytest.fixture
def mock_successful_shipment():
    """Fixture für ein erfolgreiches Shipment-Objekt als Mock-Antwort."""
    mock_shipment = Shipment(
        items=[
            ShipmentItem(
                load_carrier=LoadCarrierType.PALLET,
                name="Testpaket",
                quantity=3,
                length=120,
                width=80,
                height=100,
                weight=50,
                stackable=True
            )
        ],
        shipment_notes="Vorsichtig behandeln",
        message="Extraktion erfolgreich."
    )
    return mock_shipment


@pytest.fixture
def mock_empty_shipment():
    """Fixture für ein leeres Shipment-Objekt als Mock-Antwort."""
    return Shipment(
        items=[],
        message="Keine Sendungsdaten erkannt."
    )


def test_process_shipment_success(mock_successful_shipment):
    """Test für erfolgreiche Extraktion von Sendungsdaten."""
    with patch('graph.nodes.shipment_extractor.load_prompt') as mock_load_prompt, \
         patch('langchain_anthropic.ChatAnthropic.with_structured_output') as mock_with_structured:
        
        # Mock-Objekte konfigurieren
        mock_prompt = MagicMock()
        mock_load_prompt.return_value = mock_prompt
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_successful_shipment
        
        mock_llm = MagicMock()
        mock_with_structured.return_value = mock_chain
        
        # LLM konfigurieren (wird normalerweise in process_shipment erstellt)
        with patch('langchain_anthropic.ChatAnthropic', return_value=mock_llm):
            # Testaufruf
            result = process_shipment({
                "messages": ["Ich benötige Transport für 3 Paletten, je 120x80x100cm, 50kg."]
            })
            
            # Assertions
            assert result["extracted_data"] is not None
            assert "items" in result["extracted_data"]
            assert len(result["extracted_data"]["items"]) == 1
            assert result["extracted_data"]["items"][0]["load_carrier"] == 1  # PALLET
            assert result["extracted_data"]["items"][0]["quantity"] == 3
            assert result["message"] == "Extraktion erfolgreich."
            
            # Verifiziere, dass die Methoden der Mocks aufgerufen wurden
            mock_load_prompt.assert_called_once_with("shipmentbot_shipment")
            mock_with_structured.assert_called_once()


def test_process_shipment_empty(mock_empty_shipment):
    """Test für den Fall, dass keine Sendungsdaten erkannt werden."""
    with patch('graph.nodes.shipment_extractor.load_prompt') as mock_load_prompt, \
         patch('langchain_anthropic.ChatAnthropic.with_structured_output') as mock_with_structured:
        
        # Mock-Objekte konfigurieren
        mock_prompt = MagicMock()
        mock_load_prompt.return_value = mock_prompt
        
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = mock_empty_shipment
        
        mock_llm = MagicMock()
        mock_with_structured.return_value = mock_chain
        
        # LLM konfigurieren (wird normalerweise in process_shipment erstellt)
        with patch('langchain_anthropic.ChatAnthropic', return_value=mock_llm):
            # Testaufruf
            result = process_shipment({
                "messages": ["Hallo, guten Tag!"]
            })
            
            # Assertions
            assert result["extracted_data"] is not None
            assert "items" in result["extracted_data"]
            assert len(result["extracted_data"]["items"]) == 0
            assert result["message"] == "Keine Sendungsdaten erkannt."


def test_process_shipment_prompt_not_found():
    """Test für den Fall, dass der Prompt nicht gefunden wird."""
    with patch('graph.nodes.shipment_extractor.load_prompt', return_value=None):
        # Testaufruf
        result = process_shipment({
            "messages": ["Test"]
        })
        
        # Assertions
        assert result["extracted_data"] is None
        assert "message" in result
        assert "Fehler: Konnte den Prompt nicht laden" in result["message"]


def test_process_shipment_exception():
    """Test für den Fall, dass eine Exception auftritt."""
    with patch('graph.nodes.shipment_extractor.load_prompt') as mock_load_prompt, \
         patch('langchain_anthropic.ChatAnthropic.with_structured_output') as mock_with_structured:
        
        # Mock-Objekte konfigurieren
        mock_prompt = MagicMock()
        mock_load_prompt.return_value = mock_prompt
        
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = ValueError("Test-Fehler")
        
        mock_llm = MagicMock()
        mock_with_structured.return_value = mock_chain
        
        # LLM konfigurieren (wird normalerweise in process_shipment erstellt)
        with patch('langchain_anthropic.ChatAnthropic', return_value=mock_llm):
            # Testaufruf
            result = process_shipment({
                "messages": ["Test"]
            })
            
            # Assertions
            assert result["extracted_data"] is None
            assert "message" in result
            assert "Fehler im Datenformat" in result["message"]
            assert "Test-Fehler" in result["message"] 