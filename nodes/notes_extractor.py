from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

def process_notes(state: dict) -> dict:
    """
    Extrahiert zusätzliche Hinweise und Bemerkungen aus der Eingabe.
    """
    messages = state["messages"]
    input_text = messages[-1]
    
    # Erstellen des Chat-Models mit expliziten Parametern
    llm = ChatOpenAI(
        model="gpt-4",
        temperature=0,
        streaming=False,
        request_timeout=10
    )
    
    # Prompt für die Extraktion von Hinweisen
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Extrahiere wichtige Hinweise und Bemerkungen aus der Sendungsbeschreibung."),
        ("human", "{input}")
    ])
    
    response = llm.invoke(prompt.format_messages(input=input_text))
    
    return {
        "messages": messages,
        "next_step": "end",
        "extracted_data": state["extracted_data"],
        "notes": response.content
    } 