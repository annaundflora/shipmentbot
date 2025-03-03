from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
import json
import re
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
from langchain_core.tracers import LangChainTracer
import os

def process_precise(state: dict) -> dict:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    """
    messages = state["messages"]
    input_text = messages[-1]

    # Laden der Instruktionen und Escapen der geschweiften Klammern im Beispiel
    with open("instructions/instr_precise_extractor.md", "r", encoding="utf-8") as f:
        instructions = f.read()
        # Ersetze nur die geschweiften Klammern im JSON-Beispiel
        start_marker = '```\n{'
        end_marker = '}\n```'
        if start_marker in instructions and end_marker in instructions:
            start_idx = instructions.index(start_marker)
            end_idx = instructions.index(end_marker) + len(end_marker)
            json_example = instructions[start_idx:end_idx]
            escaped_json = json_example.replace('{', '{{').replace('}', '}}')
            instructions = instructions[:start_idx] + escaped_json + instructions[end_idx:]

    # LangSmith Tracing einrichten
    callbacks = []
    if os.getenv("LANGSMITH_TRACING") == "true":
        callbacks.append(LangChainTracer(
            project_name=os.getenv("LANGSMITH_PROJECT", "Shipmentbot"),
            tags=["precise_extractor"]
        ))
    
    # Erstellen des Chat-Models mit expliziten Parametern für Claude und Callbacks
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0,
        max_tokens=4096,
        timeout=10,
        callbacks=callbacks
    )
    
    # Prompt für die präzise Extraktion
    prompt = ChatPromptTemplate.from_messages([
        ("system", instructions),
        ("human", "{input}")
    ])
    
    response = llm.invoke(prompt.format_messages(input=input_text))
    
    # Bereinigen der Antwort von Markdown-Codeblöcken
    content = response.content
    # Entfernen von Markdown-Codeblöcken
    if "```" in content:
        # Extrahiere den JSON-Teil zwischen den Codeblöcken
        match = re.search(r'```(?:json)?\n(.*?)\n```', content, re.DOTALL)
        if match:
            content = match.group(1)
    
    try:
        extracted_data = json.loads(content)
        return {
            "extracted_data": extracted_data
        }
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error: {e}")
        print(f"Content: {content}")
        return {
            "extracted_data": None,
            "notes": f"Fehler bei der Extraktion der Daten: {str(e)}"
        } 