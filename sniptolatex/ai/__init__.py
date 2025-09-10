from .gemini import GeminiRequest
from .chatgpt import ChatGPTRequest

def create_request(model_name: str):
    name = (model_name or "").strip().lower()
    if name in ("gemini", "google", "google-gemini"):
        return GeminiRequest()
    if name in ("chatgpt", "gpt", "openai"):
        return ChatGPTRequest()
    # default fallback
    return GeminiRequest()

__all__ = ["GeminiRequest", "ChatGPTRequest", "create_request"]
