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

# Prompt-Cache auf Modulebene
_prompt_cache = {}

def get_cached_prompt(prompt_name):
    """
    Holt einen Prompt aus dem Cache oder lädt ihn von LangSmith,
    wenn er noch nicht im Cache ist.
    """
    if prompt_name not in _prompt_cache:
        try:
            print(f"Lade Prompt '{prompt_name}' von LangSmith...")
            _prompt_cache[prompt_name] = client.pull_prompt(prompt_name, include_model=False)
            print(f"Prompt '{prompt_name}' erfolgreich geladen und gecached.")
        except Exception as e:
            print(f"Fehler beim Laden des Prompts '{prompt_name}' von LangSmith: {e}")
            # Fallback: Lokale Datei laden
            try:
                with open(f"instructions/instr_{prompt_name.split('_')[-1]}.md", "r", encoding="utf-8") as f:
                    prompt_text = f.read()
                    _prompt_cache[prompt_name] = PromptTemplate.from_template(prompt_text)
                    print(f"Fallback: Prompt '{prompt_name}' aus lokaler Datei geladen und gecached.")
            except Exception as e2:
                print(f"Auch Fallback fehlgeschlagen für '{prompt_name}': {e2}")
                return None
    return _prompt_cache[prompt_name]

def process_precise(state: dict) -> dict:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    Verwendet das Pydantic-Modell für strukturierte Ausgabe.
    """
    messages = state["messages"]
    input_text = messages[-1]

    # Prompt aus Cache oder LangSmith holen
    prompt_template = get_cached_prompt("shipmentbot_shipment")
    
    if prompt_template is None:
        return {
            "extracted_data": None,
            "notes": "Fehler: Konnte den Prompt nicht laden."
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
        
        # Konvertiere zu Dictionary für Weiterverarbeitung
        return {
            "extracted_data": result.model_dump()
        }
    except Exception as e:
        print(f"Fehler bei der strukturierten Extraktion: {e}")
        return {
            "extracted_data": None,
            "notes": f"Fehler: {str(e)}"
        } 