import sys
from abc import ABC
from typing import Dict
import requests
import logging
import os
from datetime import datetime
import json
from updater.updater.llm_support.promtbuilder import PromptFactory #used for most deterministic extraction with llm
from typing_extensions import override, Optional
from updater.updater.llm_support.llm_interface import LLMInterface
import re
logging.basicConfig(level=logging.INFO)


class GeminiLlmInstance(LLMInterface, ABC):
    """
    implementation of LLMInterface for Google Gemini API
    """

    def __init__(self, url: str, env_key_name: str, template_dir: Optional[str] = None,):
        super().__init__()
        self.GEMINI_API_URL = url
        self.env_key_name = env_key_name
        # init logger
        self.logger = logging.getLogger(__name__)

        # .env in root | dont move this file from llm support without changing the Base Directory
        BASE_DIR = os.path.dirname(
            (os.path.dirname(
                os.path.dirname(os.path.abspath(__file__))
            ))
        )
        key_path = os.path.join(BASE_DIR, ".env")

        # test key
        self.GEMINI_API_KEY = self.find_valid_key(key_path, env_key_name)

        self.usage_log: list[str] = []
        self.logger.info("LLM API key found")

        # Prompt factory for most deterministic extraction with llm
        self.prompt_factory: PromptFactory
        if template_dir is not None:
            self.prompt_factory = PromptFactory(template_dir)

    def find_valid_key(self, path, env_key_name):
        """
        find valid Gemini API key in .env file
        Args: path: path to .env
              env_key_name: name of key in .env to find
        Return: key if found else None
        """
        try:
            with open(path) as write:
                for line in write:
                    line = line
                    if line.startswith(env_key_name):
                        # individual keys are assigned as key=
                        return line.split("=", 1)[1].strip()
        except Exception:
            self.logger.error("failure")
            # program exit if no key found
            sys.exit("no valid key found in .env file")
        return None

    @override
    def usage_logging(self, tokens, valid):
        """
        log usage of Gemini in the usage log for cost and request tracking
        Args: tokens: length of response
              valid: true if response is valid
        Return: key if found else None
        """
        entry = {
            "time": datetime.utcnow().isoformat(timespec="seconds"),
            "response length": tokens,
            "valid try": valid,
        }

        self.usage_log.append(entry)

        # save log
        try:
            log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "llm_log.json")
            with open(log_file, "a") as write:
                write.write(json.dumps(entry) + "\n")
        except Exception:
            print("logging failed")

    @override
    def query(self, prompt: str, type_temperature: float = 0.0):
        """
        configure gemini api and prompt it with a task input
        Args: prompt: task input for Gemini
              type_temperature: set temperature for gemini default is 0.2 for natural response
        Return: query result from Gemini
        """

        # modelconfig 500 OutTokens is pretty fast
        headers = {"Content-Type": "json handling and data extraction"}
        params = {"key": self.GEMINI_API_KEY}
        data = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": type_temperature,
                "maxOutputTokens": 5000,
            },
        }
        # response state
        valid = False
        # implmentation to fit other models if gemini is decided later as llm use genai
        response = requests.post(
            self.GEMINI_API_URL, headers=headers, params=params, json=data, timeout=30
        )
        # 200 is statuscode from google documentation , Gemini things it's fine :)
        if response.status_code == 200:
            response_text = response.json()["candidates"][0]["content"]["parts"][0][
                "text"
            ]
            # response state valid
            valid = True

        else:
            print(response.status_code)
            response_text = "no valid dataentry"
        # log usage in json
        self.usage_logging(len(response_text), valid)

        return response_text

    def __del__(self):
        """
        remove api key from memory
        """
        self.GEMINI_API_KEY = None
        del self.GEMINI_API_KEY







    def query_build(self, task: str, **prompt_args) -> str:
        """
        Build the prompt via prompt-factory and prompt Gemini with task

        Args:
            task: task name for example "url_classification"
            **prompt_kwargs: keys for the builders
               for example (schema, payload, example summary

        Returns:
            Gemini Answer
        """
        if self.prompt_factory is None:
            raise RuntimeError("PromptFactory nicht initialisiert")
        prompt_obj = self.prompt_factory.create_prompt(task, **prompt_args)
        # prompts gemini with a rendered jinja file
        return self.query("ausschließlich auf deutsch antworten"+ prompt_obj.render() )

    def query_parsed(self, task: str, **prompt_args) -> dict:
        """
        Call query_build and parse the response as json.
        Args: task: task name
                **prompt_kwargs: keys for the builders
        return: dict with response
        """
        raw = self.query_build(task, **prompt_args)

        # clean content from fences
        clean = re.sub(r"^```(?:json)?\s*\n", "", raw)
        clean = re.sub(r"\n```$", "", clean).strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return {}

def query_validation(self, content: str, regex_result: Dict) -> str:
    """
    validate the response with a regex mostly useful in testing
    """
    return self.query_build(
        "validation",
        payload=content,
        cross_validation=regex_result
    )


if __name__ == "__main__":

    try:
        # Test
        gemini = GeminiLlmInstance(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
            "GEMINI_API_KEY=",
        )

        result = gemini.query("Warum sollten Maschinen die Welt übernehmen")
        print(f"Response: {result}")

    except Exception as e:
        print(f"Fehler: {e}")
