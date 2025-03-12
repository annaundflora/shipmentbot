# Shipmentbot

A LangGraph-based bot for extracting shipment data from text inputs.

## Project Structure

```
shipmentbot/
├── graph/                         # LangGraph implementation
│   ├── __init__.py
│   ├── shipment_graph.py          # Main graph definition
│   ├── config.py                  # Central configuration
│   ├── models/                    # Data models
│   │   ├── __init__.py
│   │   └── shipment_models.py     # Pydantic models for structured data
│   └── nodes/                     # Nodes for the graph
│       ├── __init__.py
│       └── shipment_extractor.py  # Extractor for shipment data
├── app.py                         # Streamlit UI for local development
├── langgraph_main.py              # Entry point for LangGraph Platform
├── requirements.txt
└── README.md
```

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/shipmentbot.git
cd shipmentbot

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file with the following variables:

```
ANTHROPIC_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_ENDPOINT=https://eu.smith.langchain.com  # or your own endpoint
LANGSMITH_PROJECT=Shipmentbot
LANGSMITH_TRACING=true  # for development, optional
```

## Local Execution with Streamlit

```bash
streamlit run app.py
```

## Deployment on LangGraph Platform

1. Ensure that `langgraph_main.py` exports the `app` variable.
2. Set the required environment variables in the LangGraph Platform.
3. Deploy the code according to the LangGraph Platform documentation.

## Using the LangGraph Platform API

After deployment, the graph can be used via the LangGraph Platform API:

```python
import requests

# API endpoint
url = "https://api.langgraph.com/your-app-id"

# Send request
response = requests.post(url, json={
    "messages": ["I have 5 pallets with 100kg weight each..."],
    "extracted_data": None,
    "message": None
})

# Process result
result = response.json()
print(result["extracted_data"])
```

## Features

- **Structured Data Extraction**: Converts unstructured text about shipments into structured data
- **Validation**: Automatically validates and completes missing fields
- **Error Handling**: Comprehensive error handling with informative messages
- **International Support**: Full English language support in code and documentation
- **Retry Logic**: Built-in retry mechanism for network issues

## Testing

Run the tests with:

```bash
python -m tests.run_tests
```

This will execute all tests and generate a coverage report in `tests/reports/coverage/`. 