from __future__ import annotations
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Mapping, MutableMapping, Type
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from shared.models.llm_promt import Prompt

class PromptBuilder(ABC):
    """
    Abstract base class for all prompt builders.
    """

    def __init__(self, env: Environment):
        self._env: Environment = env
        self._context: MutableMapping[str, Any] = {}

    #standart prompt engineering techniques
    def add_example(self, *, input_example: str, output_example: Mapping[str, Any] ) :
        """
        Add a few-shot example.

        Args:
            input_example: Example input.
            output_example: Example output (snake_case).
        Return: assign context to self
        """
        self._context["example"] = {
            "input": input_example,
            "output": json.dumps(output_example, indent=2),
        }
        return self

    def add_payload(self, payload: str) :
        """
        Set the concrete payload to process.

        Args:
            payload: Raw input that the LLM should handle.
        Return: assign payload to self
        """
        self._context["payload"] = payload
        return self

    def add_schema(self, schema: Mapping[str, str]) :
        """
        Define the target JSON schema.

        Args:
            schema: Mapping of field → description / datatype.
        Return: assign schema to self
        """
        self._context["schema"] = json.dumps(schema, indent=2)
        return self



    def build(self) -> Prompt:
        """
        Build and return the :class:`Prompt` instance.
        Args: None
        Return: Prompt instance with the built template
        """
        template = self._env.get_template(self._get_template_name())
        missing = [k for k in self.required_context() if k not in self._context]
        if missing:
            raise ValueError(f"Missing context keys: {missing}")
        return Prompt(template=template, context=self._context)


    def _get_template_name(self) -> str:
        """
        Select the template
        Args: None
        Returns: template name
        """
        base_name = self.template_name()
        self._env.get_template(base_name)
        return base_name


    @abstractmethod
    def template_name(self) -> str:
        """
        Return the base Jinja template filename
        Return: raise error if not implemented in child class
        """
        raise NotImplementedError

    @abstractmethod
    def required_context(self):
        """
        Return the tuple of required context keys.
        Return: raise error if not implemented in child class
        """
        raise NotImplementedError


class JsonExtractionPromptBuilder(PromptBuilder):
    """
    Builder for structured JSON extraction tasks.
    """

    def template_name(self) -> str:
        """
        Return the template
        Args: None
        Return: explicit template name task.j2
        """
        return "json_extraction.j2"

    def required_context(self) -> tuple[str, ...]:
        """
        Return the required context keys for Json Extraktion task. Example Schema and Payload
        Args: None
        Return: Schema and Payload as tuple
        """
        return ("schema", "payload")


class PromptFactory:
    """
    Create the appropriate builder/prompt for a given task name.
    """
    # task's for which the llm has a prebuild prompt
    _TASK_REGISTRY: Dict[str, Type[PromptBuilder]] = {
        "json_extraction": JsonExtractionPromptBuilder,
    }

    def __init__(self, template_dir: str) -> None:
        """
        Args:
        template_dir: directory that contains all Jinja templates
        """
        if not os.path.isdir(template_dir):
            raise FileNotFoundError(template_dir)
        self._env = Environment(
            loader=FileSystemLoader(template_dir),
            undefined=StrictUndefined,
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

    def new_builder(self, task: str) -> PromptBuilder:
        """
        Return a pre-configured builder for the chosen task.
        Args: task: t name must exist in the task registry
        Return: builder instance with the chosen template
        """
        builder_task = self._TASK_REGISTRY.get(task)
        if builder_task is None:
            raise ValueError(
                f"Unknown task '{task}' list of valid task for LLM: {list(self._TASK_REGISTRY)}"
            )
        return builder_task(self._env)

        #construct the whole promt
    def create_prompt(self, task: str, **context: Any) :
        """
        Build the prompt in a single function call.

        Args:
            task: Task name (must exist in the registry).
            **context: Context arguments picked by the chosen builder.

        Returns:
            Prompt instance with the built template
        """
        builder = self.new_builder(task)
        # match the context to the builders
        for method_name, value in context.items():
            # try to call the builder's method with the same name as the context key'
            method = getattr(builder, f"add_{method_name}", None)
            if method is None:
               print(f"no method {method_name}")
            # for example example method take multiple values
            if method_name == "example":
                method(**value)
            else:
                method(value)
        return builder.build()


