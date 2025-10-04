from jinja2 import Template
from typing import Any, Mapping
from pydantic import BaseModel, ConfigDict

class Prompt(BaseModel):
    """
    holds a jinja template for a prompt

        template: render Jinja2-Template.
        context: context of the task
    """
    template: Template
    context: Mapping[str, Any]
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def render(self) -> str:
        """
        Render final prompt from jinja file to string
        Args: None
        Returns:
            string: final prompt for LLM
        """
        return self.template.render(**self.context)