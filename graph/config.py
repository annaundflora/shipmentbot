"""
Zentrale Konfiguration für Shipmentbot.

Diese Datei enthält alle Konfigurationsparameter und lädt Umgebungsvariablen.
"""
import os
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

# LLM-Konfiguration
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-7-sonnet-20250219")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "10"))

# LangSmith-Konfiguration
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "Shipmentbot")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://eu.smith.langchain.com")

# Prompt-Konfiguration
DEFAULT_PROMPT_NAME = "shipmentbot_shipment"

# Fehlermeldungen
ERROR_MESSAGES = {
    "prompt_not_found": "Fehler: Konnte den Prompt nicht laden.",
    "format_error": "Fehler im Datenformat: {}",
    "extraction_error": "Fehler bei der Extraktion: {}",
    "unknown_error": "Unerwarteter Fehler: {}"
} 