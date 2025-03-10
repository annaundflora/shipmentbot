from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
import json
import re
from langchain_core.tracers import LangChainTracer
import os
from langsmith import Client
from langchain_core.messages import HumanMessage, SystemMessage

# Initialisiere den LangSmith Client
client = Client(
    api_key=os.getenv("LANGSMITH_API_KEY"),
    api_url=os.getenv("LANGSMITH_ENDPOINT")
)

# Prompt-Cache auf Modulebene
_prompt_cache = {}

def get_cached_prompt(prompt_name):
    """
    Holt einen Prompt aus dem Cache oder lädt ihn von LangSmith,
    wenn er noch nicht im Cache ist.
    """
    if prompt_name not in _prompt_cache:
        try:
            print(f"Lade Prompt '{prompt_name}' von LangSmith...")
            _prompt_cache[prompt_name] = client.pull_prompt(prompt_name, include_model=True)
            print(f"Prompt '{prompt_name}' erfolgreich geladen und gecached.")
        except Exception as e:
            print(f"Fehler beim Laden des Prompts '{prompt_name}' von LangSmith: {e}")
            # Fallback: Lokale Datei laden
            try:
                with open(f"instructions/instr_{prompt_name.split('_')[-1]}.md", "r", encoding="utf-8") as f:
                    prompt_text = f.read()
                    _prompt_cache[prompt_name] = PromptTemplate.from_template(prompt_text)
                    print(f"Fallback: Prompt '{prompt_name}' aus lokaler Datei geladen und gecached.")
            except Exception as e2:
                print(f"Auch Fallback fehlgeschlagen für '{prompt_name}': {e2}")
                return None
    return _prompt_cache[prompt_name]

def process_precise(state: dict) -> dict:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    """
    messages = state["messages"]
    input_text = messages[-1]

    # Prompt aus Cache oder LangSmith holen
    prompt_runnable = get_cached_prompt("shipmentbot_shipment")
    
    if prompt_runnable is None:
        return {
            "extracted_data": None,
            "notes": "Fehler: Konnte den Prompt nicht laden."
        }
    
    # LangSmith Tracing einrichten
    callbacks = []
    if os.getenv("LANGSMITH_TRACING") == "true":
        callbacks.append(LangChainTracer(
            project_name=os.getenv("LANGSMITH_PROJECT", "Shipmentbot"),
            tags=["shipment_extractor"]
        ))
    
    try:
        # Versuche, den Prompt direkt als Runnable zu verwenden
        result = prompt_runnable.invoke({"input": input_text})
        
        # Das Ergebnis sollte bereits die formatierte Antwort vom LLM sein
        if isinstance(result, dict) and "content" in result:
            content = result["content"]
        elif hasattr(result, "content"):
            content = result.content
        else:
            content = str(result)
            
        print(f"Ergebnis vom LangSmith-Prompt (gekürzt): {content[:100]}...")
        
    except Exception as e:
        print(f"Fehler beim Verwenden des LangSmith-Prompts: {e}")
        
        # Fallback: Eigenes LLM verwenden
        # Erstellen des Chat-Models mit expliziten Parametern für Claude und Callbacks
        llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0,
            max_tokens=4096,
            timeout=10,
            callbacks=callbacks
        )
        
        # Wenn prompt_runnable ein PromptTemplate ist
        if hasattr(prompt_runnable, 'template'):
            try:
                # Versuche, das Template zu formatieren
                formatted_prompt = prompt_runnable.format(input=input_text)
            except Exception as format_error:
                print(f"Fehler beim Formatieren des Templates: {format_error}")
                # Manuelles Ersetzen der Mustache-Variable
                formatted_prompt = prompt_runnable.template.replace("{{input}}", input_text)
        else:
            # Fallback: Verwende den Prompt als String
            formatted_prompt = str(prompt_runnable).replace("{{input}}", input_text)
        
        # Erstellen der Nachrichten für die Anthropic API
        system_message = SystemMessage(content="Du bist ein hilfreicher Assistent, der Sendungsdaten extrahiert.")
        human_message = HumanMessage(content=formatted_prompt)
        
        # Invoke mit den korrekten Message-Objekten
        response = llm.invoke([system_message, human_message])
        content = response.content
    
    # Bereinigen der Antwort von Markdown-Codeblöcken
    if "```" in content:
        # Extrahiere den JSON-Teil zwischen den Codeblöcken
        match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
        if match:
            content = match.group(1)
    
    try:
        extracted_data = json.loads(content)
        # Nur extracted_data zurückgeben, keine notes
        return {
            "extracted_data": extracted_data
        }
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Content: {content}")
        
        # Versuche, die Antwort in ein JSON-Format zu konvertieren
        # Die Antwort scheint in Markdown-Format zu sein
        items = []
        current_item = {}
        
        lines = content.split('\n')
        for line in lines:
            if line.startswith('## Item'):
                if current_item:  # Speichere das vorherige Item, wenn es existiert
                    items.append(current_item)
                current_item = {}
            elif line.startswith('- '):
                # Extrahiere Key-Value-Paare
                parts = line[2:].split(': ', 1)
                if len(parts) == 2:
                    key, value = parts
                    key = key.lower()
                    
                    # Konvertiere Werte in entsprechende Typen
                    if key == 'quantity' or key == 'length' or key == 'width' or key == 'height' or key == 'weight':
                        try:
                            # Extrahiere nur die Zahl
                            num_match = re.search(r'(\d+)', value)
                            if num_match:
                                value = int(num_match.group(1))
                            else:
                                value = None
                        except:
                            value = None
                    elif key == 'stackable':
                        value = value.lower() == 'true'
                    elif key == 'load carrier':
                        # Extrahiere nur die Zahl
                        num_match = re.search(r'(\d+)', value)
                        if num_match:
                            value = int(num_match.group(1))
                        else:
                            value = None
                    
                    current_item[key] = value
        
        # Füge das letzte Item hinzu
        if current_item:
            items.append(current_item)
        
        if items:
            return {
                "extracted_data": {"items": items}
            }
        else:
            return {
                "extracted_data": None
            } 