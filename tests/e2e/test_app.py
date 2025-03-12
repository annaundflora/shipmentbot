"""
End-to-End Tests für die Streamlit-Anwendung.

Diese Tests überprüfen die korrekte Funktionalität der Streamlit-UI
mit gemockten Antworten.
"""
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st
import sys
import os


@pytest.fixture
def mock_streamlit():
    """
    Fixture, die Streamlit-Komponenten mockt.
    
    Dieses Fixture erstellt Mocks für die Streamlit-Funktionen, die in der App verwendet werden.
    """
    # Mock-Objekte für Streamlit-Funktionen
    with patch('streamlit.title') as mock_title, \
         patch('streamlit.text_area') as mock_text_area, \
         patch('streamlit.checkbox') as mock_checkbox, \
         patch('streamlit.button') as mock_button, \
         patch('streamlit.spinner') as mock_spinner, \
         patch('streamlit.subheader') as mock_subheader, \
         patch('streamlit.success') as mock_success, \
         patch('streamlit.json') as mock_json, \
         patch('streamlit.error') as mock_error:
        
        # Konfiguriere den Button-Mock, um True zurückzugeben (Button wurde geklickt)
        mock_button.return_value = True
        
        # Text-Area-Mock für die Benutzereingabe
        mock_text_area.return_value = "Ich benötige einen Transport für 3 Paletten."
        
        # Checkbox-Mock für die Persistenz-Option
        mock_checkbox.return_value = False
        
        # Context-Manager für spinner
        mock_spinner_context = MagicMock()
        mock_spinner.return_value = mock_spinner_context
        
        yield {
            'title': mock_title,
            'text_area': mock_text_area,
            'checkbox': mock_checkbox,
            'button': mock_button,
            'spinner': mock_spinner,
            'spinner_context': mock_spinner_context,
            'subheader': mock_subheader,
            'success': mock_success,
            'json': mock_json,
            'error': mock_error
        }


@pytest.fixture
def mock_graph():
    """
    Fixture, die den LangGraph mockt.
    
    Dieses Fixture erstellt einen Mock für den LangGraph, der in der App verwendet wird.
    """
    with patch('graph.shipment_graph.create_shipment_graph') as mock_create_graph:
        # Mock-Graph erstellen
        mock_graph = MagicMock()
        
        # Konfiguriere den invoke-Mock, um ein Ergebnis zurückzugeben
        mock_graph.invoke.return_value = {
            "messages": ["Ich benötige einen Transport für 3 Paletten."],
            "extracted_data": {
                "items": [
                    {
                        "load_carrier": 1,  # LoadCarrierType.PALLET
                        "name": "Standardpalette",
                        "quantity": 3,
                        "length": 120,
                        "width": 80,
                        "height": 100,
                        "weight": 50,
                        "stackable": True
                    }
                ],
                "shipment_notes": "Standardtransport",
                "message": "Extraktion erfolgreich."
            },
            "message": "Extraktion erfolgreich."
        }
        
        # Konfiguriere den create_shipment_graph-Mock, um den Mock-Graph zurückzugeben
        mock_create_graph.return_value = mock_graph
        
        yield mock_graph


def test_app_ui_elements(mock_streamlit):
    """
    Test, ob die UI-Elemente korrekt erstellt werden.
    
    Dieser Test importiert die App-Datei und überprüft, ob die UI-Elemente
    wie erwartet erstellt werden.
    """
    # Füge das Hauptverzeichnis zum Pfad hinzu, um app.py zu importieren
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    # Importiere die App
    import app
    
    # Rufe die Hauptfunktion auf
    app.main()
    
    # Überprüfe, ob die UI-Elemente erstellt wurden
    mock_streamlit['title'].assert_called_once()
    mock_streamlit['text_area'].assert_called_once()
    mock_streamlit['checkbox'].assert_called_once()
    mock_streamlit['button'].assert_called_once()


def test_app_workflow(mock_streamlit, mock_graph):
    """
    Test des gesamten App-Workflows.
    
    Dieser Test überprüft, ob der Workflow der App korrekt funktioniert,
    einschließlich der Verarbeitung der Benutzereingabe und der Anzeige der Ergebnisse.
    """
    # Füge das Hauptverzeichnis zum Pfad hinzu, um app.py zu importieren
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
    
    # Importiere die App
    import app
    
    # Ignoriere LangSmith-Tracing
    with patch('langchain.callbacks.tracers.langchain.wait_for_all_tracers'):
        # Rufe die Hauptfunktion auf
        app.main()
        
        # Überprüfe, ob der Graph aufgerufen wurde
        mock_graph.invoke.assert_called_once()
        
        # Überprüfe, ob die Ergebnisse angezeigt wurden
        mock_streamlit['subheader'].assert_called()
        mock_streamlit['success'].assert_called_once()
        mock_streamlit['json'].assert_called()
        

def test_app_error_handling(mock_streamlit):
    """
    Test der Fehlerbehandlung in der App.
    
    Dieser Test überprüft, ob Fehler in der App korrekt behandelt werden.
    """
    # Mock für create_shipment_graph, der eine Exception wirft
    with patch('graph.shipment_graph.create_shipment_graph') as mock_create_graph:
        # Konfiguriere den Mock, um eine Exception zu werfen
        mock_create_graph.side_effect = Exception("Test-Fehler")
        
        # Füge das Hauptverzeichnis zum Pfad hinzu, um app.py zu importieren
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
        
        # Importiere die App
        import app
        
        # Rufe die Hauptfunktion auf - sollte den Fehler abfangen
        app.main()
        
        # Überprüfe, ob eine Fehlermeldung angezeigt wurde
        mock_streamlit['error'].assert_called() 