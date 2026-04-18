from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool


@tool
def translate_text(text: str, to_language: str, from_language: str = "auto") -> str:
    """Translate text between languages using the local LLM.
    Works offline — no API key or internet required.

    Args:
        text: The text to translate.
        to_language: Target language (e.g., "Spanish", "Hindi", "French", "Japanese").
        from_language: Source language. Use "auto" to auto-detect (default).
    """
    from config import get_llm

    try:
        llm = get_llm()

        from_clause = ""
        if from_language and from_language.lower() != "auto":
            from_clause = f" from {from_language}"

        messages = [
            SystemMessage(content=(
                f"Translate the following text{from_clause} to {to_language}. "
                "Return ONLY the translation, nothing else."
            )),
            HumanMessage(content=text),
        ]

        response = llm.invoke(messages)
        translation = response.content.strip()
        return translation if translation else "Translation returned empty."
    except Exception as e:
        return f"Error translating text: {e}"
