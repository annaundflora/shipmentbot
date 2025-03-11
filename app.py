"""
Streamlit UI für den Shipmentbot.

Diese Datei definiert die Streamlit-Benutzeroberfläche für den Shipmentbot.
"""
import streamlit as st
from dotenv import load_dotenv
import os
from langchain.callbacks.tracers.langchain import wait_for_all_tracers

# Import des Shipment-Graphen
from graph.shipment_graph import create_shipment_graph

# Laden der Umgebungsvariablen
load_dotenv()

# LangSmith Projekt setzen
os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "Shipmentbot")

# Streamlit UI
def main():
    st.title("Shipmentbot - Sendungsextraktor")

    # Eingabefeld
    user_input = st.text_area("Bitte geben Sie Ihre Sendungsdaten ein:", height=200)

    # Persistenz-Option (Checkbox)
    use_persistence = st.checkbox("Persistenz aktivieren", value=False, 
                                 help="Aktiviert die Persistenz des Graphen zwischen verschiedenen Anfragen.")

    if st.button("Verarbeiten"):
        if user_input:
            # Workflow erstellen mit optionaler Persistenz
            chain = create_shipment_graph(with_checkpointer=use_persistence)
            
            # Ausführen mit Tracing
            with st.spinner("Verarbeite Sendungsdaten..."):
                response = chain.invoke({
                    "messages": [user_input],
                    "extracted_data": None,
                    "message": None
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
            
            # Nachricht vom LLM anzeigen, falls vorhanden
            if response["message"] and response["message"].strip():
                st.info("Nachricht vom System:")
                st.markdown(response["message"])
                    
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