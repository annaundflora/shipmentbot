"""
LangGraph Platform Hauptdatei für Shipmentbot.

Diese Datei dient als Einstiegspunkt für die Bereitstellung auf der LangGraph Platform.
Sie exportiert den Shipment-Graphen, der für die Extraktion von Sendungsdaten verwendet wird.
"""
import os
from dotenv import load_dotenv
from graph.shipment_graph import create_shipment_graph

# Lade Umgebungsvariablen
load_dotenv()

# Setze LangSmith Projekt
if "LANGCHAIN_PROJECT" not in os.environ:
    os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGSMITH_PROJECT", "Shipmentbot")

# Erstelle den Graph mit Persistenz für LangGraph Platform
graph = create_shipment_graph(with_checkpointer=True)

# Diese Variable wird von LangGraph Platform erkannt, um den Graph zu verwenden
# Der Name muss genau 'graph' sein
app = graph 