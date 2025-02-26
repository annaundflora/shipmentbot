import streamlit as st
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Annotated, Sequence

from nodes.precise_extractor import process_precise

# Laden der Umgebungsvariablen
load_dotenv()

# Definition des Zustandstyps
class AgentState(TypedDict):
    messages: Sequence[str]
    next_step: str
    extracted_data: dict | None

def create_workflow():
    """Erstellt den Workflow-Graphen mit dem precise_extractor"""
    workflow = StateGraph(AgentState)
    
    # Nur precise_extractor Node hinzufügen
    workflow.add_node("precise_extractor", process_precise)
    
    # Einfacher Workflow: START -> precise_extractor -> END
    workflow.add_edge(START, "precise_extractor")
    workflow.add_edge("precise_extractor", END)
    
    # Visualisiere den Workflow
    try:
        graph = workflow.compile()
        png_data = graph.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
        print("Workflow-Diagramm wurde als 'workflow_graph.png' gespeichert.")
    except Exception as e:
        print(f"Visualisierung konnte nicht erstellt werden: {e}")
    
    return workflow.compile()

# Streamlit UI
def main():
    st.title("Shipmentbot")

    # Eingabefeld
    user_input = st.text_area("Bitte geben Sie Ihre Sendungsdaten ein:", height=200)

    if st.button("Verarbeiten"):
        if user_input:
            # Workflow ausführen
            chain = create_workflow()
            response = chain.invoke({
                "messages": [user_input],
                "next_step": "precise_extractor",
                "extracted_data": None
            })
            
            # Ergebnisse anzeigen
            if response["extracted_data"]:
                st.success("Sendungsdaten erfolgreich extrahiert!")
                st.json(response["extracted_data"])
            else:
                st.error("Keine Daten konnten extrahiert werden.")
        else:
            st.warning("Bitte geben Sie Sendungsdaten ein.")

    # Optionaler Debug-Bereich
    if st.checkbox("Debug-Informationen anzeigen"):
        st.write("Rohdaten der letzten Verarbeitung:")
        if 'response' in locals():
            st.write(response)

if __name__ == "__main__":
    main()