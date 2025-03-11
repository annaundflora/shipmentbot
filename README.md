# Shipmentbot

Ein LangGraph-basierter Bot zur Extraktion von Sendungsdaten aus Texteingaben.

## Projektstruktur

```
shipmentbot/
├── graph/                         # LangGraph-Implementierung
│   ├── __init__.py
│   ├── shipment_graph.py          # Haupt-Graph-Definition
│   └── nodes/                     # Knoten für den Graph
│       ├── __init__.py
│       ├── shipment_extractor.py  # Extraktor für Sendungsdaten
│       └── shipment_models.py     # Pydantic-Modelle für strukturierte Daten
├── app.py                         # Streamlit UI für lokale Entwicklung
├── langgraph_main.py              # Einstiegspunkt für LangGraph Platform
├── requirements.txt
└── README.md
```

## Installation

```bash
# Repository klonen
git clone https://github.com/yourusername/shipmentbot.git
cd shipmentbot

# Virtuelle Umgebung erstellen und aktivieren
python -m venv venv
source venv/bin/activate  # Unter Windows: venv\Scripts\activate

# Abhängigkeiten installieren
pip install -r requirements.txt
```

## Umgebungsvariablen

Erstelle eine `.env`-Datei mit den folgenden Variablen:

```
ANTHROPIC_API_KEY=sk-...
LANGSMITH_API_KEY=lsv2_...
LANGSMITH_ENDPOINT=https://eu.smith.langchain.com  # oder deine eigene Endpoint
LANGSMITH_PROJECT=Shipmentbot
LANGSMITH_TRACING=true  # für Entwicklung, optional
```

## Lokale Ausführung mit Streamlit

```bash
streamlit run app.py
```

## Deployment auf LangGraph Platform

1. Stelle sicher, dass `langgraph_main.py` die Variable `app` exportiert.
2. Setze die erforderlichen Umgebungsvariablen in der LangGraph Platform.
3. Deploye den Code gemäß der LangGraph Platform-Dokumentation.

## Verwendung mit LangGraph Platform API

Nach dem Deployment kann der Graph über die LangGraph Platform API verwendet werden:

```python
import requests

# API-Endpunkt
url = "https://api.langgraph.com/your-app-id"

# Anfrage senden
response = requests.post(url, json={
    "messages": ["Ich habe 5 Paletten mit je 100kg Gewicht..."],
    "extracted_data": None,
    "message": None
})

# Ergebnis verarbeiten
result = response.json()
print(result["extracted_data"])
``` 