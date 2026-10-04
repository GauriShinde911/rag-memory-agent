from langchain_core.tools import tool
from app.tools.logger import logged


@tool
@logged
def web_search(query: str) -> str:
    """Search the web (DuckDuckGo) and return the top 3 results as title + snippet. Use for facts you don't know or that may have changed."""
    try:
        from ddgs import DDGS
    except ImportError:
        from duckduckgo_search import DDGS

    cleaned_query = query.strip().strip("'\"`")
    results = list(DDGS().text(cleaned_query, max_results=3))
    if not results:
        raise RuntimeError("No search results found")

    lines = []
    for r in results:
        title = r.get("title", "Untitled")
        body = r.get("body", "") or r.get("snippet", "")
        lines.append(f"- {title}: {body}")
    return "\n".join(lines)
