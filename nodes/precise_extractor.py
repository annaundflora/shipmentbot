from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json

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

    # Erstellen des Chat-Models mit expliziten Parametern
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        streaming=False,
        request_timeout=10
    )
    
    # Prompt für die präzise Extraktion
    prompt = ChatPromptTemplate.from_messages([
        ("system", instructions),
        ("human", "{input}")
    ])
    
    response = llm.invoke(prompt.format_messages(input=input_text))
    
    try:
        extracted_data = json.loads(response.content)
        return {
            "messages": messages,
            "next_step": "end",
            "extracted_data": extracted_data,
            "notes": None
        }
    except json.JSONDecodeError:
        return {
            "messages": messages,
            "next_step": "end",
            "extracted_data": None,
            "notes": "Fehler bei der Extraktion der Daten"
        } 