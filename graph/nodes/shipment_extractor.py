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
from typing import Dict, Any, List, Optional, Union

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

def process_shipment(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    Verwendet das Pydantic-Modell für strukturierte Ausgabe.
    
    Args:
        state: Der aktuelle Zustand mit messages, extracted_data und message
        
    Returns:
        Ein aktualisierter Zustand mit extrahierten Daten und ggf. Fehlermeldungen
    """
    messages = state["messages"]
    input_text = messages[-1]

    # Prompt aus LangSmith oder lokaler Datei laden
    prompt_template = load_prompt(DEFAULT_PROMPT_NAME)
    
    if prompt_template is None:
        return {
            "extracted_data": None,
            "message": ERROR_MESSAGES["prompt_not_found"]
        }
    
    # LangSmith Tracing einrichten
    callbacks = []
    if LANGSMITH_TRACING:
        callbacks.append(LangChainTracer(
            project_name=LANGSMITH_PROJECT,
            tags=["shipment_extractor"]
        ))
    
    # Erstelle PromptTemplate, falls es noch keines ist
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
    chain = prompt_template | structured_llm
    
    try:
        # Führe die Chain aus - das Ergebnis ist bereits eine Shipment-Instanz
        result = chain.invoke({"input": input_text})
        
        # Extrahiere die Nachricht aus dem Ergebnis
        message = result.message if hasattr(result, "message") else None
        
        # Konvertiere zu Dictionary für Weiterverarbeitung
        return {
            "extracted_data": result.model_dump(),
            "message": message
        }
    except ValueError as e:
        # Fehler bei der Strukturierung/Validierung der Daten
        print(f"Format-/Validierungsfehler: {e}")
        return {
            "extracted_data": None,
            "message": ERROR_MESSAGES["format_error"].format(str(e))
        }
    except TypeError as e:
        # Typfehler, z.B. wenn das LLM unerwartete Werte zurückgibt
        print(f"Typfehler: {e}")
        return {
            "extracted_data": None,
            "message": ERROR_MESSAGES["format_error"].format(str(e))
        }
    except KeyError as e:
        # Fehlende Schlüssel im Dictionary
        print(f"Fehlender Schlüssel: {e}")
        return {
            "extracted_data": None,
            "message": ERROR_MESSAGES["format_error"].format(f"Fehlender Wert für {e}")
        }
    except Exception as e:
        # Allgemeiner Fallback für alle anderen Fehler
        print(f"Unerwarteter Fehler bei der strukturierten Extraktion: {e}")
        return {
            "extracted_data": None,
            "message": ERROR_MESSAGES["unknown_error"].format(str(e))
        } 