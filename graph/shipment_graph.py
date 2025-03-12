"""
Shipment Graph Definition.

This file defines the LangGraph for the extraction of shipment data.
"""
from langgraph.graph import StateGraph, END, START
from typing import TypedDict, Optional, List, Dict, Any, Union, Callable
from langgraph.checkpoint.memory import MemorySaver

# Import of the Shipment Extractor
from graph.nodes.shipment_extractor import process_shipment

# Definition of the state type with precise type annotations
class ShipmentState(TypedDict):
    messages: List[str]  # More precise than Sequence
    extracted_data: Optional[Dict[str, Any]]  # Explicitly Optional
    message: Optional[str]  # Explicitly Optional

def validate_state(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates and completes missing fields in the state.
    
    Args:
        state: The state to validate
        
    Returns:
        A validated state with all required fields
    """
    # Create a copy of the state to avoid modifying the original
    validated_state = state.copy()
    
    # Ensure that messages is a List[str]
    if "messages" not in validated_state or not isinstance(validated_state["messages"], list):
        validated_state["messages"] = []
    
    # Ensure that extracted_data and message exist
    if "extracted_data" not in validated_state:
        validated_state["extracted_data"] = None
    if "message" not in validated_state:
        validated_state["message"] = None
    
    return validated_state

def create_shipment_graph(with_checkpointer: bool = False) -> Callable:
    """
    Creates a LangGraph for the extraction of shipment data.
    
    Args:
        with_checkpointer: Whether to use a memory checkpointer for persistence
        
    Returns:
        A compiled LangGraph that can be used for shipment data extraction
    """
    # Create the graph with the defined state type
    graph = StateGraph(ShipmentState)
    
    # Add the validation function as a separate node
    graph.add_node("validate", validate_state)
    
    # Add the shipment extractor as a node
    graph.add_node("shipment_extractor", process_shipment)
    
    # Define the edges - with validation as the first step
    graph.add_edge(START, "validate")
    graph.add_edge("validate", "shipment_extractor")
    graph.add_edge("shipment_extractor", END)
    
    # Create a checkpointer for persistence, if desired
    checkpointer = MemorySaver() if with_checkpointer else None
    
    # Compile the graph
    compiled_graph = graph.compile(checkpointer=checkpointer)
    
    # Try to visualize the graph
    try:
        png_data = compiled_graph.get_graph().draw_mermaid_png()
        with open("workflow_graph.png", "wb") as f:
            f.write(png_data)
        print("Workflow diagram has been saved as 'workflow_graph.png'.")
    except Exception as e:
        print(f"Visualization could not be created: {e}")
    
    return compiled_graph 