"""Gemini model request implementation."""

import os
from PyQt5.QtGui import QPixmap

from .request import Request
from sniptolatex.config import read_model_settings

try:
    import google.generativeai as genai
except Exception:
    genai = None

class GeminiRequest(Request):
    """Send a PNG image to Gemini and return the generated text.

    Attributes:
        (inherited) _prompt_file (Path): Path to the prompt template used for requests.
    """

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
            print("Gemini SDK not installed. Skipping send.")
            return
        # Ensure config exists and try to read API key from it first

        if not self._api_key:
            print("GEMINI_API_KEY/GOOGLE_API_KEY not set. Skipping send.")
            return
        try:
            genai.configure(api_key=self._api_key)
            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            model = genai.GenerativeModel(model_name)
            image_part = {"mime_type": "image/png", "data": image}
            resp = model.generate_content([self._prompt, image_part])
            text = getattr(resp, "text", None)
            if text:
                return text
            else:
                print("Gemini: response received (no text)")
        except Exception as exc:
            print("Gemini error:", exc)
