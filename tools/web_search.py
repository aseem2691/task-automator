from langchain_core.tools import tool


@tool
def web_search(query: str) -> str:
    """Search the web using DuckDuckGo and return the top 3 results.

    Args:
        query: The search query string.
    """
    try:
        from ddgs import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=3))

        if not results:
            return f"No results found for '{query}'."

        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']}\n   {r['href']}\n   {r['body']}")
        return "\n\n".join(output)
    except Exception as e:
        return f"Error searching the web: {e}"
