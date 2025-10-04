import os
from updater.updater.llm_support.gemini_api import GeminiLlmInstance

base_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates"
)

# one instance of gemini
gemini = GeminiLlmInstance(
    url="https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent",
    env_key_name="GEMINI_API_KEY=",
    template_dir=base_dir,
)
