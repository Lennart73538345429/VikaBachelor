import unittest
from typing import Optional
import requests
from updater.updater.llm_support.gemini_api import GeminiLlmInstance


# valid Response mock
class LLM_Mock_Response:
    """
    Mock class to simulate a successful response from the Gemini.

    Attributes:
    status_code (int): HTTP status code set to 200 to simulate success.

    Methods:
    gemini_valid_answer()
    """

    # gemini status code for valid response
    status_code = 200

    # gemini answer format
    def gemini_valid_answer(self):
        """
        Returns a simulated valid JSON response from the Gemini API.
        Args None
        Return: dict: Simulated valid JSON response
        """
        return {
            "candidates": [  # mock llm answer is Testtext
                {"content": {"parts": [{"text": "Testtext"}]}}
            ]
        }

    # has fit the signature of request api
    json = gemini_valid_answer


# invalid Reponse mock
class LLM_Mock_Response_Error:
    """
     Mock class to simulate an error response (HTTP 500) from the Gemini API.

    Attributes:
        status_code int: HTTP invalid status code.

    Methods:
        gemini_valid_answer()
    """

    status_code = 500  # response code for servererror

    def gemini_valid_answer(self):
        """
        Returns a simulated error response body.
        Args None
        Return: dict: Simulated error response.
        """
        return {"error": "no valid dataentry"}

    # has fit the signature of request api
    json = gemini_valid_answer


# fake request post
def mock_post(
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    # important to satisfy request format
    timeout: float = 0.1,
) -> LLM_Mock_Response:
    """
    Simulated requests.post returning a successful mock response.

        Args:
            url str: Gemini endpoint URL
            headers Optional[dict]: Request headers
            params Optional[dict]: URL query parameters
            json Optional[dict]: JSON
            timeout float: Timeout

        Returns:
            LLM_Mock_Response: response
    """
    assert url == "https://llmapi.com"
    assert (
        headers is not None
        and headers.get("Content-Type") == "json handling data extraction"
    )
    assert params is not None and "key" in params
    assert isinstance(json, dict)

    return LLM_Mock_Response()


def test_with_key_and_mockurl(monkeypatch):
    """
    test ensures that promt_query() returns Testtext when
    the Gemini API responds with HTTP 200 and a valid JSON payload.
    for local testing both requests.post and find_valid_key are
    mocked with monkeypatch
    Args:
        monkeypatch : fixture to override requests.post and find_valid_key

    Returns:
        None: Asserts that the result equals "Testtext"
    """

    monkeypatch.setattr(requests, "post", mock_post)

    # mock find_valid_key(key_path, env_key_name) to just return KEY
    monkeypatch.setattr(
        GeminiLlmInstance,
        "find_valid_key",
        # set parameters, key is KEY
        lambda self, path, key: "KEY",
    )
    # initialize LLM_Support with mock key and mock url
    support = GeminiLlmInstance("https://llmapi.com", "KEY")
    assert support.GEMINI_API_KEY == "KEY"
    result = support.query("Hallo")
    assert result == "Testtext"


def mock_post_error(
    url: str,
    headers: Optional[dict] = None,
    params: Optional[dict] = None,
    json: Optional[dict] = None,
    # important to satisfy request format
    timeout: float = 0.1,
):
    """
    Simulation of requests.post that returns an error response.

    Args:
        url str: The API endpoint URL.
        headers Optional[dict]: Request headers.
        params Optional[dict]: URL query parameters.
        json (Optional[dict]): JSON
        timeout (float): Timeout value

    Returns:
        LLM_Mock_Response_Error: mocked error response
    """
    return LLM_Mock_Response_Error()


def test_error_handling(monkeypatch):
    """
    Test ensures that the  promt_query() returns the fallback string when
    the Gemini API responds with HTTP 500.
    for local testing request.post is mocked with monkeypatch
    Args:
    monkeypatch: fixture to override requests.post and find_valid_key

    Returns:
        None: Asserts that the result equals the expected error message.
    """
    monkeypatch.setattr(requests, "post", mock_post_error)
    # mock find_valid_key(key_path, env_key_name) to just return none for key
    monkeypatch.setattr(
        GeminiLlmInstance,
        "find_valid_key",
        lambda self, path, key: None,
    )
    support = GeminiLlmInstance("https://llmapi.com", "KEY")
    result = support.query("Hallo")
    assert result == "no valid dataentry"


if __name__ == "__main__":
    unittest.main()
