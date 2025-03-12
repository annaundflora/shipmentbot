"""
Shipment extractor node for LangGraph.

Dieser Knoten extrahiert strukturierte Sendungsdaten aus Texteingaben mit Claude.
"""
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
import json
import re
from langchain_core.tracers import LangChainTracer
import os
from langsmith import Client
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List, Optional, Union, Callable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Importiere die Modelle aus dem models-Verzeichnis
from graph.models.shipment_models import Shipment, ShipmentItem, LoadCarrierType

# Importiere die zentrale Konfiguration
from graph.config import (
    LLM_MODEL, 
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS, 
    LLM_TIMEOUT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    DEFAULT_PROMPT_NAME,
    ERROR_MESSAGES
)

# Initialisiere den LangSmith Client
client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY", LANGSMITH_API_KEY),
    api_url=os.getenv("LANGSMITH_ENDPOINT", LANGSMITH_ENDPOINT)
)


def load_prompt(prompt_name: str) -> Optional[PromptTemplate]:
    """
    Lädt einen Prompt von LangSmith oder aus einer lokalen Datei.
    Das Caching ist deaktiviert, es wird immer ein frischer Prompt geladen.
    
    Args:
        prompt_name: Name des Prompts in LangSmith
        
    Returns:
        Ein PromptTemplate oder None, wenn der Prompt nicht geladen werden konnte
    """
    try:
        print(f"Lade Prompt '{prompt_name}' von LangSmith...")
        prompt = client.pull_prompt(prompt_name, include_model=False)
        print(f"Prompt '{prompt_name}' erfolgreich geladen.")
        return prompt
    except Exception as e:
        print(f"Fehler beim Laden des Prompts '{prompt_name}' von LangSmith: {e}")
        # Fallback: Lokale Datei laden
        try:
            with open(f"instructions/instr_{prompt_name.split('_')[-1]}.md", "r", encoding="utf-8") as f:
                prompt_text = f.read()
                prompt = PromptTemplate.from_template(prompt_text)
                print(f"Fallback: Prompt '{prompt_name}' aus lokaler Datei geladen.")
                return prompt
        except Exception as e2:
            print(f"Auch Fallback fehlgeschlagen für '{prompt_name}': {e2}")
            return None


def create_error_response(error_type: str, details: str = "") -> Dict[str, Any]:
    """
    Erstellt eine einheitliche Fehlerantwort.
    
    Args:
        error_type: Art des Fehlers, referenziert einen Schlüssel in ERROR_MESSAGES
        details: Zusätzliche Details zum Fehler für Formatstrings
        
    Returns:
        Ein Dictionary mit extracted_data=None und einer Fehlermeldung
    """
    error_message = ERROR_MESSAGES[error_type]
    if details and "{}" in error_message:
        error_message = error_message.format(details)
    
    print(f"Fehler: {error_type} - {details}")
    return {
        "extracted_data": None,
        "message": error_message
    }


def create_extraction_chain(prompt_template):
    """
    Erstellt die Extraction Chain mit LLM und Prompt.
    
    Args:
        prompt_template: Das PromptTemplate für die Chain
        
    Returns:
        Eine Chain für die strukturierte Extraktion
    """
    # LangSmith Tracing einrichten
    callbacks = []
    if LANGSMITH_TRACING:
        callbacks.append(LangChainTracer(
            project_name=LANGSMITH_PROJECT,
            tags=["shipment_extractor"]
        ))
    
    # Falls prompt_template kein PromptTemplate ist, konvertieren
    if not isinstance(prompt_template, PromptTemplate):
        prompt_template = PromptTemplate.from_template(str(prompt_template))
    
    # LLM mit Pydantic-Modell für strukturierte Ausgabe
    llm = ChatAnthropic(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT,
        callbacks=callbacks
    )
    
    # LLM mit strukturierter Ausgabe konfigurieren
    structured_llm = llm.with_structured_output(Shipment)
    
    # Chain zusammenbauen mit Pipeline-Syntax
    return prompt_template | structured_llm


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
def invoke_chain_with_retry(chain, input_data: Dict[str, str]) -> Any:
    """
    Führt den Chain-Aufruf mit Retry-Logik aus.
    
    Args:
        chain: Die zu verwendende Chain
        input_data: Die Eingabedaten für die Chain
        
    Returns:
        Das Ergebnis der Chain-Ausführung
        
    Raises:
        Verschiedene Exceptions basierend auf der Chain-Ausführung
    """
    return chain.invoke(input_data)


def extract_shipment_data(chain, input_text: str) -> Dict[str, Any]:
    """
    Führt die eigentliche Extraktion durch und behandelt Fehler.
    
    Args:
        chain: Die zu verwendende Chain
        input_text: Der zu extrahierende Text
        
    Returns:
        Ein Dictionary mit den extrahierten Daten oder Fehlermeldungen
    """
    try:
        # Führe die Chain aus mit Retries für Netzwerkprobleme
        result = invoke_chain_with_retry(chain, {"input": input_text})
        
        # Extrahiere die Nachricht aus dem Ergebnis
        message = result.message if hasattr(result, "message") else None
        
        # Konvertiere zu Dictionary für Weiterverarbeitung
        extracted_data = result.model_dump()
        
        # Zusätzliche Validierung der extrahierten Daten
        if not extracted_data.get("items"):
            return {
                "extracted_data": extracted_data,
                "message": "Warnung: Keine Sendungspositionen gefunden."
            }
        
        # Formatierungsprüfung für jede Position
        for item in extracted_data.get("items", []):
            if item.get("length", 0) <= 0 or item.get("width", 0) <= 0 or item.get("height", 0) <= 0:
                return {
                    "extracted_data": extracted_data,
                    "message": "Warnung: Einige Positionen haben ungültige Abmessungen."
                }
        
        # Erfolgreiche Extraktion
        return {
            "extracted_data": extracted_data,
            "message": message or "Extraktion erfolgreich."
        }
    except ValueError as e:
        return create_error_response("format_error", str(e))
    except TypeError as e:
        return create_error_response("format_error", str(e))
    except KeyError as e:
        return create_error_response("format_error", f"Fehlender Wert für {e}")
    except TimeoutError:
        return create_error_response("extraction_error", "Zeitüberschreitung bei der Anfrage")
    except ConnectionError:
        return create_error_response("extraction_error", "Verbindungsfehler beim API-Aufruf")
    except Exception as e:
        return create_error_response("unknown_error", str(e))


def process_shipment(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    Verwendet das Pydantic-Modell für strukturierte Ausgabe.
    
    Args:
        state: Der aktuelle Zustand mit messages, extracted_data und message
        
    Returns:
        Ein aktualisierter Zustand mit extrahierten Daten und ggf. Fehlermeldungen
    """
    try:
        messages = state["messages"]
        input_text = messages[-1]
        
        # Prompt aus LangSmith oder lokaler Datei laden
        prompt_template = load_prompt(DEFAULT_PROMPT_NAME)
        if prompt_template is None:
            return create_error_response("prompt_not_found")
        
        # Chain erstellen und ausführen
        chain = create_extraction_chain(prompt_template)
        return extract_shipment_data(chain, input_text)
    except Exception as e:
        # Allgemeiner Fallback für unerwartete Fehler
        return create_error_response("unknown_error", str(e)) 