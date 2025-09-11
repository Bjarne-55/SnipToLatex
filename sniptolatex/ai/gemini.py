"""Gemini model request implementation."""

import os

from .request import Request
from .errors import ApiKeyMissing, SdkMissing, EmptyResponse, InvalidApiKey

try:
    import google.generativeai as genai
    from google.api_core.exceptions import InvalidArgument
except Exception:
    genai = None

class GeminiRequest(Request):
    """Send a PNG image to Gemini and return the generated text."""

    def __init__(self):
        """Initialize gemini"""
        super().__init__("gemini")

    def send_image(self, image: bytes) -> str:
        """Send an image to Gemini and return generated text.

        Args:
            image (bytes): PNG-encoded bytes expected by the SDK.

            Note: the caller currently provides PNG bytes from the capture layer.

        Returns:
            Optional[str]: Generated text from Gemini, or None if the SDK is
            unavailable, the API key is missing, or the response has no text.
        """
        if genai is None:
            raise SdkMissing("Gemini SDK not installed")
        # Ensure config exists and try to read API key from it first

        if not self._api_key:
            raise ApiKeyMissing("Missing Gemini API key")
        try:
            genai.configure(api_key=self._api_key)
            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            model = genai.GenerativeModel(model_name)
            image_part = {"mime_type": "image/png", "data": image}
            resp = model.generate_content([self._prompt, image_part])
            try:
                text = getattr(resp, "text", None)
            except AttributeError:
                raise EmptyResponse("Model returned no text")
            return text
        except ValueError:
            raise EmptyResponse("Model returned no text")
        except InvalidArgument as exp:
            if exp.reason == "API_KEY_INVALID":
                raise InvalidApiKey("API key not valid.")
            else:
                raise exp
