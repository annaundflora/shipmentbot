from langchain_core.prompts import ChatPromptTemplate
from langchain_anthropic import ChatAnthropic
import re

def process_notes(state: dict) -> dict:
    """
    Extrahiert zusätzliche Hinweise und Bemerkungen aus der Eingabe.
    """
    messages = state["messages"]
    input_text = messages[-1]
    
    # Laden der Instruktionen
    with open("instructions/instr_notes_extractor.md", "r", encoding="utf-8") as f:
        instructions = f.read()
    
    # Erstellen des Chat-Models mit expliziten Parametern für Claude
    llm = ChatAnthropic(
        model="claude-3-7-sonnet-20250219",
        temperature=0,
        max_tokens=4096,
        timeout=10
    )
    
    # Prompt für die Extraktion von Hinweisen
    prompt = ChatPromptTemplate.from_messages([
        ("system", instructions),
        ("human", "{input}")
    ])
    
    response = llm.invoke(prompt.format_messages(input=input_text))
    
    # Bereinigen der Antwort - entferne Markdown-Formatierung falls vorhanden
    content = response.content
    
    # Überprüfen, ob content eine Liste ist
    if isinstance(content, list):
        # Wenn die Liste leer ist, setze content auf leeren String
        if not content:
            content = ""
        else:
            # Sonst verbinde die Elemente zu einem String
            content = " ".join(content)
    
    # Entferne Markdown-Codeblöcke falls vorhanden
    if isinstance(content, str) and "```" in content:
        content = re.sub(r'```.*?```', '', content, flags=re.DOTALL).strip()
    
    # Entferne Anführungszeichen falls vorhanden
    if isinstance(content, str):
        content = content.strip('"\'')
    else:
        content = ""
    
    return {
        "notes": content.strip() if content else ""
    } 