class AgentError(Exception):
    """Base exception for all pipeline errors. Catch this if you want to
    handle any pipeline failure generically; catch a subclass below for
    more specific handling."""
    pass


class ScrapingError(AgentError):
    """Raised when browser automation, login, or scraping fails —
    e.g. session expired, selector not found, page timed out."""
    pass


class LLMError(AgentError):
    """Raised when the LLM call fails outright, or returns output that
    cannot be parsed into the expected structured format."""
    pass


class PersistenceError(AgentError):
    """Raised when saving scraped data or the final digest to disk fails."""
    pass