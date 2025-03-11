from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
import json
import re
from langchain_core.tracers import LangChainTracer
import os
from langsmith import Client
from langchain_core.messages import HumanMessage, SystemMessage

# Importiere die Modelle aus der lokalen Datei
from nodes.shipment_models import Shipment, ShipmentItem, LoadCarrierType

# Initialisiere den LangSmith Client
client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    api_url=os.getenv("LANGSMITH_ENDPOINT")
)


def load_prompt(prompt_name):
    """
    Lädt einen Prompt von LangSmith oder aus einer lokalen Datei.
    Das Caching ist deaktiviert, es wird immer ein frischer Prompt geladen.
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

def process_shipment(state: dict) -> dict:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    Verwendet das Pydantic-Modell für strukturierte Ausgabe.
    """
    messages = state["messages"]
    input_text = messages[-1]

    # Prompt aus Cache oder LangSmith holen
    prompt_template = load_prompt("shipmentbot_shipment")
    
    if prompt_template is None:
        return {
            "extracted_data": None
        }
    
    # LangSmith Tracing einrichten
    callbacks = []
    if os.getenv("LANGSMITH_TRACING") == "true":
        callbacks.append(LangChainTracer(
            project_name=os.getenv("LANGSMITH_PROJECT", "Shipmentbot"),
            tags=["shipment_extractor"]
        ))
    
    # Erstelle PromptTemplate, falls es noch keines ist
    if not isinstance(prompt_template, PromptTemplate):
        prompt_template = PromptTemplate.from_template(str(prompt_template))
    
    # LLM mit Pydantic-Modell für strukturierte Ausgabe
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0,
        max_tokens=4096,
        timeout=10,
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
    except Exception as e:
        print(f"Fehler bei der strukturierten Extraktion: {e}")
        return {
            "extracted_data": None,
            "message": f"Fehler bei der Verarbeitung: {str(e)}"
        } 