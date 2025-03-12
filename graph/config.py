"""
Central configuration for Shipmentbot.

This file contains all configuration parameters and loads environment variables.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# LLM configuration
LLM_MODEL = os.getenv("LLM_MODEL", "claude-3-7-sonnet-20250219")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "4096"))
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "10"))

# LangSmith configuration
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "Shipmentbot")
LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY", "")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://eu.smith.langchain.com")

# Prompt configuration
DEFAULT_PROMPT_NAME = "shipmentbot_shipment"

# Error messages
ERROR_MESSAGES = {
    "prompt_not_found": "Error: Could not load the prompt.",
    "format_error": "Error in data format: {}",
    "extraction_error": "Error during extraction: {}",
    "unknown_error": "Unexpected error: {}"
} 