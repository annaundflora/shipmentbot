from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import TypedDict, Sequence
import json
from langchain_core.tracers import LangChainTracer
import os

class ComplexityClassifierResponse(TypedDict):
    is_complex: bool
    extracted_data: dict | None
    notes: str | None

def process_complexity(state: dict) -> dict:
    """
    Klassifiziert die Komplexität der Eingabe und extrahiert ggf. direkt die Daten
    bei einfachen Eingaben.
    """
    messages = state["messages"]
    input_text = messages[-1]

    # LangSmith Tracing einrichten
    callbacks = []
    if os.getenv("LANGSMITH_TRACING") == "true":
        callbacks.append(LangChainTracer(
            project_name=os.getenv("LANGSMITH_PROJECT", "Shipmentbot"),
            tags=["complexity_classifier"]
        ))

    # Erstellen des Chat-Models mit expliziten Parametern
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        streaming=False,
        request_timeout=10,
        callbacks=callbacks
    )
    
    # Prompt für die Klassifizierung
    classifier_prompt = ChatPromptTemplate.from_messages([
        ("system", "Du bist ein Experte für die Klassifizierung von Sendungsdaten. "
                  "Analysiere die Eingabe und entscheide, ob sie einfach oder komplex ist."),
        ("human", "{input}")
    ])
    
    # Klassifizierung durchführen
    response = llm.invoke(classifier_prompt.format_messages(input=input_text))
    
    # Wenn einfach, direkt extrahieren
    if "simple" in response.content.lower():
        # Fast extraction durchführen
        extraction_prompt = ChatPromptTemplate.from_messages([
            ("system", "Extrahiere die Sendungsdaten im spezifizierten Format."),
            ("human", "{input}")
        ])
        
        extraction_response = llm.invoke(extraction_prompt.format_messages(input=input_text))
        
        try:
            extracted_data = json.loads(extraction_response.content)
            return {
                "messages": messages,
                "next_step": "end",
                "extracted_data": extracted_data,
                "notes": None
            }
        except json.JSONDecodeError:
            # Bei Fehler zur präzisen Extraktion weitergeben
            return {
                "messages": messages,
                "next_step": "precise_extractor",
                "extracted_data": None,
                "notes": None
            }
    
    # Bei komplexer Eingabe zur präzisen Extraktion weitergeben
    return {
        "messages": messages,
        "next_step": "precise_extractor",
        "extracted_data": None,
        "notes": None
    } 