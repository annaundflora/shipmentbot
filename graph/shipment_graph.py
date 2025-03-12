"""
Shipment Graph Definition.

Diese Datei definiert den LangGraph für die Extraktion von Sendungsdaten.
"""
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Optional, List, Dict, Any, Union, Callable
from langgraph.checkpoint.memory import MemorySaver

# Import des Shipment-Extraktors
from graph.nodes.shipment_extractor import process_shipment

# Definition des Zustandstyps mit präziseren Typannotationen
class ShipmentState(TypedDict):
    messages: List[str]  # Präziser als Sequence
    extracted_data: Optional[Dict[str, Any]]  # Explizit Optional
    message: Optional[str]  # Explizit Optional

def validate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validiert und ergänzt fehlende Felder im State.
    
    Args:
        state: Der zu validierende Zustand
        
    Returns:
        Ein validierter Zustand mit allen erforderlichen Feldern
    """
    # Erstellen einer Kopie des Zustands, um das Original nicht zu verändern
    validated_state = state.copy()
    
    # Stelle sicher, dass messages ein List[str] ist
    if "messages" not in validated_state or not isinstance(validated_state["messages"], list):
        validated_state["messages"] = []
    
    # Stelle sicher, dass extracted_data und message existieren
    if "extracted_data" not in validated_state:
        validated_state["extracted_data"] = None
    if "message" not in validated_state:
        validated_state["message"] = None
    
    return validated_state

def create_shipment_graph(with_checkpointer: bool = False) -> Callable:
    """
    Erstellt einen LangGraph für die Extraktion von Sendungsdaten.
    
    Args:
        with_checkpointer: Ob ein Memory-Checkpointer verwendet werden soll für Persistenz
        
    Returns:
        Ein kompilierter LangGraph, der für die Extraktion von Sendungsdaten verwendet werden kann
    """
    # Erstelle den Graph mit dem definierten Zustandstyp
    graph = StateGraph(ShipmentState)
    
    # Füge die Validierungsfunktion als separaten Knoten hinzu
    graph.add_node("validate", validate_state)
    
    # Füge den Shipment-Extraktor als Knoten hinzu
    graph.add_node("shipment_extractor", process_shipment)
    
    # Definiere die Kanten - mit Validierung als ersten Schritt
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "shipment_extractor")
    graph.add_edge("shipment_extractor", END)
    
    # Erstelle einen Checkpointer für Persistenz, falls gewünscht
    checkpointer = MemorySaver() if with_checkpointer else None
    
    # Kompiliere den Graph
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # Versuche, den Graph zu visualisieren
    try:
        png_data = compiled_graph.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
        print("Workflow-Diagramm wurde als 'workflow_graph.png' gespeichert.")
    except Exception as e:
        print(f"Visualisierung konnte nicht erstellt werden: {e}")
    
    return compiled_graph 