from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
import json

def process_precise(state: dict) -> dict:
    """
    Führt eine präzise Extraktion der Sendungsdaten durch.
    """
    messages = state["messages"]
    input_text = messages[-1]

    llm = ChatOpenAI(model="gpt-3.5-turbo")
    
    # Prompt für die präzise Extraktion
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Du bist ein Experte für die Extraktion von Sendungsdaten. "
                  "Extrahiere alle relevanten Informationen präzise im spezifizierten Format."),
        ("human", "{input}")
    ])
    
    response = llm.invoke(prompt.format_messages(input=input_text))
    
    try:
        extracted_data = json.loads(response.content)
        return {
            "messages": messages,
            "next_step": "notes_extractor",
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