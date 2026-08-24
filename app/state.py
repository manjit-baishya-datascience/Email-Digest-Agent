from typing import TypedDict, List, Optional


class AgentState(TypedDict):
    """Shared state passed between LangGraph nodes. Each node reads
    what it needs and returns only the fields it updates — LangGraph
    merges partial updates into this shape automatically."""

    # Populated by the scraping stage
    emails: Optional[List[dict]]

    # Populated by the summarization stage
    digest_items: Optional[List[dict]]

    # Populated by the persistence stage
    output_path: Optional[str]

    # Populated if any stage fails
    error: Optional[str]
    error_type: Optional[str]

    overview: Optional[str]