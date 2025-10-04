from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List


class LLMInterface(ABC):
    """
    generic interface for large language models used for updating the CompanyModel

    concrete classes (Gemini, Mistral) must subclass LLMInterface
    """

    def __init__(self) -> None:
        self._usage_log: List[Dict[str, Any]] = []

    @abstractmethod
    def query(self, prompt: str, temperature: float = 0.2) -> str:  # noqa: D401
        """
        Args: prompt: task input for LLM
              type_temperature: set temperature for model default ist 0.2 for natural response
        returns model response for given prompt
        """

    def usage_logging(self, tokens: int, success: bool) -> None:
        """
        log usage of model in the usage log for cost and request tracking
        Args: tokens: length of response
              valid: true if response is valid
        Return: key if found else None
        """
        entry = {
            "ts": datetime.utcnow().isoformat(timespec="seconds"),
            "tokens": tokens,
            "success": success,
        }
        self._usage_log.append(entry)
