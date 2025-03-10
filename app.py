import streamlit as st
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import os
from langsmith import Client
from langchain.callbacks.tracers.langchain import wait_for_all_tracers

from nodes.precise_extractor import process_precise as process_shipment
from nodes.notes_extractor import process_notes
from nodes.addresses_extractor import process_addresses

# Laden der Umgebungsvariablen
load_dotenv()

# LangSmith Client initialisieren
client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    api_url=os.getenv("LANGSMITH_ENDPOINT")
)

# LangSmith Projekt setzen
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "Shipmentbot")

# Definition des Zustandstyps mit Annotated für parallele Verarbeitung
class AgentState(TypedDict):
    messages: Sequence[str]
    extracted_data: Dict[str, Any] | None
    notes: str | None
    addresses: Dict[str, Any] | None

# Definieren der Routing-Funktion für parallele Ausführung
def router(state: AgentState) -> Dict[str, List[str]]:
    """
    Routing-Funktion, die bestimmt, welche Nodes parallel ausgeführt werden sollen.
    """
    return {"next": ["shipment_extractor", "notes_extractor", "addresses_extractor"]}

def create_workflow():
    """Erstellt den Workflow-Graphen mit paralleler Ausführung"""
    workflow = StateGraph(AgentState)
    
    # Nodes hinzufügen
    workflow.add_node("shipment_extractor", process_shipment)
    workflow.add_node("notes_extractor", process_notes)
    workflow.add_node("addresses_extractor", process_addresses)
    
    # Parallele Ausführung einrichten
    workflow.add_node("parallel_processing", router)
    
    # Kanten definieren
    workflow.add_edge(START, "parallel_processing")
    workflow.add_edge("parallel_processing", "shipment_extractor")
    workflow.add_edge("parallel_processing", "notes_extractor")
    workflow.add_edge("parallel_processing", "addresses_extractor")
    workflow.add_edge("shipment_extractor", END)
    workflow.add_edge("notes_extractor", END)
    workflow.add_edge("addresses_extractor", END)
    
    # Workflow kompilieren und nur einmal visualisieren
    compiled_workflow = workflow.compile()
    
    # Visualisiere den Workflow nur einmal
    try:
        png_data = compiled_workflow.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
        print("Workflow-Diagramm wurde als 'workflow_graph.png' gespeichert.")
    except Exception as e:
        print(f"Visualisierung konnte nicht erstellt werden: {e}")
    
    return compiled_workflow

# Streamlit UI
def main():
    st.title("Shipmentbot")

    # Eingabefeld
    user_input = st.text_area("Bitte geben Sie Ihre Sendungsdaten ein:", height=200)

    if st.button("Verarbeiten"):
        if user_input:
            # Workflow ausführen mit LangSmith Tracing
            chain = create_workflow()
            
            # Ausführen mit Tracing
            with st.spinner("Verarbeite Sendungsdaten..."):
                response = chain.invoke({
                    "messages": [user_input],
                    "extracted_data": None,
                    "notes": None,
                    "addresses": None
                })
                
                # Warten auf Abschluss aller Traces
                wait_for_all_tracers()
            
            # Ergebnisse anzeigen
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Extrahierte Daten")
                if response["extracted_data"]:
                    st.success("Sendungsdaten erfolgreich extrahiert!")
                    st.json(response["extracted_data"])
                else:
                    st.error("Keine Daten konnten extrahiert werden.")
                
                if response["addresses"]:
                    st.success("Adressen erfolgreich extrahiert!")
                    st.json(response["addresses"])
                else:
                    st.error("Keine Adressen konnten extrahiert werden.")
            
            with col2:
                st.subheader("Zusätzliche Hinweise")
                if response["notes"] and response["notes"].strip():
                    st.info(response["notes"])
                else:
                    st.warning("Keine zusätzlichen Hinweise gefunden.")
                    
                # LangSmith Link anzeigen
                if os.getenv("LANGSMITH_TRACING") == "true":
                    st.subheader("LangSmith Tracing")
                    langsmith_url = f"{os.getenv('LANGSMITH_ENDPOINT', 'https://eu.smith.langchain.com')}/projects/{os.getenv('LANGSMITH_PROJECT', 'Shipmentbot')}"
                    st.markdown(f"[Öffne LangSmith Dashboard]({langsmith_url})")
        else:
            st.warning("Bitte geben Sie Sendungsdaten ein.")

    # Optionaler Debug-Bereich
    if st.checkbox("Debug-Informationen anzeigen"):
        st.write("Rohdaten der letzten Verarbeitung:")
        if 'response' in locals():
            st.write(response)
        
        # LangSmith Konfiguration anzeigen
        st.subheader("LangSmith Konfiguration")
        st.write(f"LANGSMITH_TRACING: {os.getenv('LANGSMITH_TRACING')}")
        st.write(f"LANGSMITH_PROJECT: {os.getenv('LANGSMITH_PROJECT')}")
        st.write(f"LANGSMITH_ENDPOINT: {os.getenv('LANGSMITH_ENDPOINT')}")

if __name__ == "__main__":
    main()