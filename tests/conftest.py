"""
Zentrale Test-Konfiguration für die Testsuite.

Diese Datei enthält globale Fixtures und Konfigurationen für alle Tests.
"""
import pytest
import os
import sys


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """
    Richtet die Testumgebung ein.
    
    Dieses Fixture wird automatisch zu Beginn der Testsuite ausgeführt
    und richtet die Umgebung für die Tests ein.
    """
    # Füge das Projektverzeichnis zum Pfad hinzu
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Setze Umgebungsvariablen für Tests
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LLM_TIMEOUT"] = "1"  # Kurzes Timeout für Tests
    
    # Yield, um den Test auszuführen
    yield
    
    # Cleanup nach Abschluss aller Tests
    pass  # Hier könnten Cleanup-Schritte stehen


@pytest.fixture
def test_data():
    """
    Fixture, die Testdaten für verschiedene Tests bereitstellt.
    """
    return {
        "simple_message": "Ich benötige einen Transport für 3 Paletten.",
        "complex_message": """
        Ich benötige einen Transport für folgende Sendung:
        - 3 Europaletten, jeweils 120x80x100cm, 50kg, stapelbar
        - 2 Pakete, jeweils 40x30x20cm, 5kg, nicht stapelbar
        Die Sendung sollte vorsichtig behandelt werden und am Montag abgeholt werden.
        """,
        "no_shipment_message": "Hallo, wie geht es dir?",
        "invalid_message": "123"
    } 