from dataclasses import field
from pydantic import BaseModel

class TaskSpec(BaseModel):
    """
    Specifications for a large language model task.
    name: name of task
    must_contain: keywords that must be contained in the page
    prefer_keywords: keywords that should be contained in the page
    max_chars: maximum number of characters to extract from the content
    """
    name: str
    must_contain: set[str] = field(default_factory=set)
    prefer_keywords: set[str] = field(default_factory=set)
    max_chars: int = 6000