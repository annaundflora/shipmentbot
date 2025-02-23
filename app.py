import streamlit as st
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated, Sequence

from nodes.complexity_classifier import process_complexity
from nodes.precise_extractor import process_precise
from nodes.notes_extractor import process_notes

# Laden der Umgebungsvariablen
load_dotenv()

# Definition des Zustandstyps
class AgentState(TypedDict):
    messages: Sequence[str]
    next_step: str
    extracted_data: dict | None
    notes: str | None

# Erstellen des LLM und des Prompts
llm = ChatOpenAI(model="gpt-3.5-turbo")
prompt = ChatPromptTemplate.from_messages([
    ("system", "Du bist ein hilfreicher Assistent."),
    ("human", "{input}")
])

# Definieren der Verarbeitungsfunktion
def process_complexity(state: AgentState):
    messages = state["messages"]
    
    # Hier kommt Ihre Logik für den Complexity Classifier
    chain = prompt | llm
    response = chain.invoke({"input": messages[-1]})
    
    # Beispiellogik - sollte mit Ihrem tatsächlichen Klassifikator ersetzt werden
    if "complex" in response.content.lower():
        return {"messages": messages, "next_step": "precise_extractor", "extracted_data": {}}
    else:
        # Hier würde der Fast Extractor die Daten verarbeiten
        return {"messages": messages, "next_step": "end", "extracted_data": {}}

def process_precise(state: AgentState):
    messages = state["messages"]
    
    # Hier kommt Ihre Logik für den Precise Extractor
    chain = prompt | llm
    response = chain.invoke({"input": messages[-1]})
    
    # Beispiel-Extraktion - ersetzen Sie dies mit Ihrer tatsächlichen Extraktionslogik
    extracted_data = {
        "items": [
            {
                "load_carrier": 1,
                "name": "example",
                "quantity": 1,
                "length": 120,
                "width": 100,
                "height": 80,
                "weight": 320,
                "stackable": "no"
            }
        ]
    }
    
    return {"messages": messages, "next_step": "end", "extracted_data": extracted_data}

# Erstellen des Workflow-Graphen
def create_workflow():
    workflow = StateGraph(AgentState)
    
    # Nodes hinzufügen
    workflow.add_node("complexity", process_complexity)
    workflow.add_node("precise_extractor", process_precise)
    workflow.add_node("notes_extractor", process_notes)
    
    # Kanten definieren
    workflow.add_edge("complexity", "precise_extractor")
    workflow.add_edge("complexity", END)
    workflow.add_edge("precise_extractor", "notes_extractor")
    workflow.add_edge("precise_extractor", END)
    workflow.add_edge("notes_extractor", END)
    
    return workflow.compile()

# Streamlit UI
st.title("Shipmentbot")

# Eingabefeld
user_input = st.text_area("Bitte geben Sie Ihre Sendungsdaten ein:", height=200)

if st.button("Verarbeiten"):
    if user_input:
        # Workflow ausführen
        chain = create_workflow()
        response = chain.invoke({
            "messages": [user_input],
            "next_step": "complexity",
            "extracted_data": None,
            "notes": None
        })
        
        # Ergebnisse anzeigen
        if response["extracted_data"]:
            st.success("Sendungsdaten erfolgreich extrahiert!")
            st.json(response["extracted_data"])
            
            if response["notes"]:
                st.info("Zusätzliche Hinweise:")
                st.write(response["notes"])
        else:
            st.error("Keine Daten konnten extrahiert werden.")
    else:
        st.warning("Bitte geben Sie Sendungsdaten ein.")

# Optionaler Debug-Bereich
if st.checkbox("Debug-Informationen anzeigen"):
    st.write("Rohdaten der letzten Verarbeitung:")
    if 'response' in locals():
        st.write(response)