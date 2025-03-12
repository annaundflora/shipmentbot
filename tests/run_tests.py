#!/usr/bin/env python
"""
Test-Runner-Skript für die Shipmentbot-Testsuite.

Dieses Skript führt alle Tests aus und erstellt einen HTML-Bericht.
"""
import pytest
import sys
import os
from datetime import datetime


def run_tests():
    """Führt die Tests aus und erstellt einen Bericht."""
    # Erstelle Verzeichnis für Berichte
    reports_dir = os.path.join(os.path.dirname(__file__), "reports")
    if not os.path.exists(reports_dir):
        os.makedirs(reports_dir)
    
    # Generiere Berichtsdateinamen mit Zeitstempel
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_report = os.path.join(reports_dir, f"test_report_{timestamp}.html")
    xml_report = os.path.join(reports_dir, f"test_results_{timestamp}.xml")
    
    # Führe die Tests aus
    exit_code = pytest.main([
        # Pfad zu den Tests
        os.path.dirname(__file__),
        # Berichterstellung
        f"--html={html_report}",
        f"--junitxml={xml_report}",
        # Ausführliche Ausgabe
        "-v",
        # Farbige Ausgabe
        "--color=yes",
        # Testabdeckung
        "--cov=graph",
        "--cov-report=term",
        f"--cov-report=html:{os.path.join(reports_dir, 'coverage')}"
    ])
    
    # Zeige Pfad zum Bericht an
    if os.path.exists(html_report):
        print(f"\nTest-Bericht wurde erstellt: {html_report}")
    if os.path.exists(xml_report):
        print(f"Test-Ergebnisse wurden gespeichert: {xml_report}")
    
    return exit_code


if __name__ == "__main__":
    sys.exit(run_tests()) 