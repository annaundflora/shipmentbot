"""
Shipment extractor node for LangGraph.

This node extracts structured shipment data from text inputs using Claude.
"""
from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
import json
import re
from langchain_core.tracers import LangChainTracer
import os
from langsmith import Client
from langchain_core.messages import HumanMessage, SystemMessage
from typing import Dict, Any, List, Optional, Union, Callable
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Import models from the models directory
from graph.models.shipment_models import Shipment, ShipmentItem, LoadCarrierType

# Import central configuration
from graph.config import (
    LLM_MODEL, 
    LLM_TEMPERATURE, 
    LLM_MAX_TOKENS, 
    LLM_TIMEOUT,
    LANGSMITH_PROJECT,
    LANGSMITH_TRACING,
    LANGSMITH_API_KEY,
    LANGSMITH_ENDPOINT,
    DEFAULT_PROMPT_NAME,
    ERROR_MESSAGES
)

# Initialize the LangSmith Client
client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY", LANGSMITH_API_KEY),
    api_url=os.getenv("LANGSMITH_ENDPOINT", LANGSMITH_ENDPOINT)
)


def load_prompt(prompt_name: str) -> Optional[PromptTemplate]:
    """
    Loads a prompt from LangSmith or from a local file.
    Caching is disabled, a fresh prompt is always loaded.
    
    Args:
        prompt_name: Name of the prompt in LangSmith
        
    Returns:
        A PromptTemplate or None if the prompt could not be loaded
    """
    try:
        print(f"Loading prompt '{prompt_name}' from LangSmith...")
        prompt = client.pull_prompt(prompt_name, include_model=False)
        print(f"Prompt '{prompt_name}' successfully loaded.")
        return prompt
    except Exception as e:
        print(f"Error loading prompt '{prompt_name}' from LangSmith: {e}")
        # Fallback: Load local file
        try:
            with open(f"instructions/instr_{prompt_name.split('_')[-1]}.md", "r", encoding="utf-8") as f:
                prompt_text = f.read()
                prompt = PromptTemplate.from_template(prompt_text)
                print(f"Fallback: Prompt '{prompt_name}' loaded from local file.")
                return prompt
        except Exception as e2:
            print(f"Fallback also failed for '{prompt_name}': {e2}")
            return None


def create_error_response(error_type: str, details: str = "") -> Dict[str, Any]:
    """
    Creates a standardized error response.
    
    Args:
        error_type: Type of error, references a key in ERROR_MESSAGES
        details: Additional details about the error for format strings
        
    Returns:
        A dictionary with extracted_data=None and an error message
    """
    error_message = ERROR_MESSAGES[error_type]
    if details and "{}" in error_message:
        error_message = error_message.format(details)
    
    print(f"Error: {error_type} - {details}")
    return {
        "extracted_data": None,
        "message": error_message
    }


def create_extraction_chain(prompt_template):
    """
    Creates the extraction chain with LLM and prompt.
    
    Args:
        prompt_template: The PromptTemplate for the chain
        
    Returns:
        A chain for structured extraction
    """
    # Set up LangSmith tracing
    callbacks = []
    if LANGSMITH_TRACING:
        callbacks.append(LangChainTracer(
            project_name=LANGSMITH_PROJECT,
            tags=["shipment_extractor"]
        ))
    
    # If prompt_template is not a PromptTemplate, convert it
    if not isinstance(prompt_template, PromptTemplate):
        prompt_template = PromptTemplate.from_template(str(prompt_template))
    
    # LLM with Pydantic model for structured output
    llm = ChatAnthropic(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
        timeout=LLM_TIMEOUT,
        callbacks=callbacks
    )
    
    # Configure LLM with structured output
    structured_llm = llm.with_structured_output(Shipment)
    
    # Build chain with pipeline syntax
    return prompt_template | structured_llm


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((TimeoutError, ConnectionError))
)
def invoke_chain_with_retry(chain, input_data: Dict[str, str]) -> Any:
    """
    Executes the chain call with retry logic.
    
    Args:
        chain: The chain to use
        input_data: The input data for the chain
        
    Returns:
        The result of the chain execution
        
    Raises:
        Various exceptions based on the chain execution
    """
    return chain.invoke(input_data)


def extract_shipment_data(chain, input_text: str) -> Dict[str, Any]:
    """
    Performs the actual extraction and handles errors.
    
    Args:
        chain: The chain to use
        input_text: The text to extract from
        
    Returns:
        A dictionary with extracted data or error messages
    """
    try:
        # Execute the chain with retries for network issues
        result = invoke_chain_with_retry(chain, {"input": input_text})
        
        # Extract the message from the result
        message = result.message if hasattr(result, "message") else None
        
        # Convert to dictionary for further processing
        extracted_data = result.model_dump()
        
        # Successful extraction - we leave validation to the LLM
        # and take the message directly from the LLM
        return {
            "extracted_data": extracted_data,
            "message": message or "Extraction successful."
        }
    except ValueError as e:
        return create_error_response("format_error", str(e))
    except TypeError as e:
        return create_error_response("format_error", str(e))
    except KeyError as e:
        return create_error_response("format_error", f"Missing value for {e}")
    except TimeoutError:
        return create_error_response("extraction_error", "Request timeout")
    except ConnectionError:
        return create_error_response("extraction_error", "Connection error during API call")
    except Exception as e:
        return create_error_response("unknown_error", str(e))


def process_shipment(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Performs a precise extraction of shipment data.
    Uses the Pydantic model for structured output.
    
    Args:
        state: The current state with messages, extracted_data and message
        
    Returns:
        An updated state with extracted data and/or error messages
    """
    try:
        messages = state["messages"]
        input_text = messages[-1]
        
        # Load prompt from LangSmith or local file
        prompt_template = load_prompt(DEFAULT_PROMPT_NAME)
        if prompt_template is None:
            return create_error_response("prompt_not_found")
        
        # Create and execute chain
        chain = create_extraction_chain(prompt_template)
        return extract_shipment_data(chain, input_text)
    except Exception as e:
        # General fallback for unexpected errors
        return create_error_response("unknown_error", str(e)) 