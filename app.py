import streamlit as st
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated, Sequence, List, Dict, Any
import os
from langsmith import Client
from langchain.callbacks.tracers.langchain import wait_for_all_tracers

# Import nur des Shipment-Extraktors
from nodes.shipment_extractor import process_precise as process_shipment

# Laden der Umgebungsvariablen
load_dotenv()

# LangSmith Client initialisieren
client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    api_url=os.getenv("LANGSMITH_ENDPOINT")
)

# LangSmith Projekt setzen
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "Shipmentbot")

# Vereinfachte Definition des Zustandstyps
class AgentState(TypedDict):
    messages: Sequence[str]
    extracted_data: Dict[str, Any] | None

def create_workflow():
    """Erstellt einen einfachen Workflow-Graphen mit nur dem Shipment-Extraktor"""
    workflow = StateGraph(AgentState)
    
    # Nur den Shipment-Extraktor hinzufügen
    workflow.add_node("shipment_extractor", process_shipment)
    
    # Einfache Kanten definieren
    workflow.add_edge(START, "shipment_extractor")
    workflow.add_edge("shipment_extractor", END)
    
    # Workflow kompilieren und visualisieren
    compiled_workflow = workflow.compile()
    
    # Visualisiere den Workflow
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
    st.title("Shipmentbot - Sendungsextraktor")

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
                    "extracted_data": None
                })
                
                # Warten auf Abschluss aller Traces
                wait_for_all_tracers()
            
            # Ergebnisse anzeigen
            st.subheader("Extrahierte Sendungsdaten")
            if response["extracted_data"]:
                st.success("Sendungsdaten erfolgreich extrahiert!")
                st.json(response["extracted_data"])
            else:
                st.error("Keine Sendungsdaten konnten extrahiert werden.")
                    
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