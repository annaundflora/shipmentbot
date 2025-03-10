from langchain_core.prompts import PromptTemplate
from langchain_anthropic import ChatAnthropic
import json
import re
from langchain_core.tracers import LangChainTracer
import os
from langsmith import Client
from langchain_core.messages import HumanMessage, SystemMessage

def process_precise(state: dict) -> dict:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    """
    messages = state["messages"]
    input_text = messages[-1]

    # LangSmith Client initialisieren
    client = Client(
        api_key=os.getenv("LANGSMITH_API_KEY"),
        api_url=os.getenv("LANGSMITH_ENDPOINT")
    )
    
    try:
        # Prompt aus LangSmith ziehen
        prompt_runnable = client.pull_prompt("shipmentbot_shipment", include_model=True)
        print(f"Prompt erfolgreich aus LangSmith geladen: {type(prompt_runnable)}")
        
        # Da prompt_runnable ein RunnableSequence ist, können wir es direkt aufrufen
        # mit dem Input als Parameter
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
        
        # Fallback: Lokale Datei laden und eigenes LLM verwenden
        with open("instructions/instr_precise_extractor.md", "r", encoding="utf-8") as f:
            instructions = f.read()
        
        # LangSmith Tracing einrichten
        callbacks = []
        if os.getenv("LANGSMITH_TRACING") == "true":
            callbacks.append(LangChainTracer(
                project_name=os.getenv("LANGSMITH_PROJECT", "Shipmentbot"),
                tags=["shipment_extractor"]
            ))
        
        # Erstellen des Chat-Models mit expliziten Parametern für Claude und Callbacks
        llm = ChatAnthropic(
            model="claude-3-7-sonnet-20250219",
            temperature=0,
            max_tokens=4096,
            timeout=10,
            callbacks=callbacks
        )
        
        # Manuelles Ersetzen der Mustache-Variable
        formatted_prompt = instructions.replace("{{input}}", input_text)
        
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