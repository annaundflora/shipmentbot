# Shipmentbot Projektbeschreibung

## Ziel

Die App soll eine Eingabe von Sendungsdaten in verschiedene LLM Nodes verarbeiten und dabei Daten in ein spezifisches Ausgabeformat extrahieren. 

## Voraussetzungen

- Python 3.x
- LangChain und LangGraph
- Sprachmodelle
- Streamlit

## Funktionen

- Eingabefeld für Sendungsdaten als Text
- Anzeige der extrahierten Sendungsdaten in einem Container unterhalb des Eingabefeldes
- Validierung der Eingabe durch verschiedene Nodes
- Exztrahierung der Daten in das definierte Ausgabeformat

## Ausgabeformat

Beispiel für das Ausgabeformat:

{
    "items": [
        {
            "load_carrier": 1,
            "name": "spare parts",
            "quantity": 1,
            "length": 120,
            "width": 100,
            "height": 80,
            "weight": 320,
            "stackable": "no"
        },
        {
            "load_carrier": 1,
            "name": "motor parts",
            "quantity": 2,
            "length": 120,
            "width": 100,
            "height": 120,
            "weight": 500,
            "stackable": "no"
        }
    ]
}


## Node: comlexity classifier & fast extractor
- Klassifiziert die eingegebenen Sendungsdaten nach Komplexität und gibt 
- Wenn sie "simple" ist, werden die Sendungsdaten direkt im gleichen Node "fast extractor" verarbeitet.
- Wenn sie "complex" ist, werden die Sendungsdaten mit dem "precise extractor" verarbeitet.
- Rückgabe entweder "complex" oder die extrahierten Sendungsdaten im Ausgabeformat

## Node: precise extractor
- Extrahiert die Sendungsdaten aus der Eingabe und gibt sie im Ausgabeformat zurück
- Validierung der Eingabe

## Node: notes extractor
- Extrahiere Hinweise und Bemerkungen aus der Eingabe
- Rückgabe als Text

## Node: prohibit and restricted shipment validator
- Validierung der Eingabe auf Beschränkungen und Sperrungen
