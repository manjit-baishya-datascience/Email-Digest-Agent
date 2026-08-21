from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    emails: Optional[List[dict]]          # raw scraped emails
    digest_items: Optional[List[dict]]    # LLM-summarized structured data
    output_path: Optional[str]            # where the final markdown got saved
    error: Optional[str]                  # set if something failed