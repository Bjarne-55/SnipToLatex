import os
from PyQt5.QtGui import QPixmap

from .request import Request

try:
    import google.generativeai as genai
except Exception:
    genai = None

class GeminiRequest(Request):
    def __init__(self):
        super().__init__("gemini_image_to_latex.txt")

    def send_image(self, image: QPixmap) -> str:
        prompt: str = self._read_prompt_from_file()
        if genai is None:
            print("Gemini SDK not installed. Skipping send.")
            return
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")

        if not api_key:
            print("GEMINI_API_KEY/GOOGLE_API_KEY not set. Skipping send.")
            return
        try:
            genai.configure(api_key=api_key)
            model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
            model = genai.GenerativeModel(model_name)
            image_part = {"mime_type": "image/png", "data": image}
            resp = model.generate_content([prompt, image_part])
            text = getattr(resp, "text", None)
            if text:
                return text
            else:
                print("Gemini: response received (no text)")
        except Exception as exc:
            print("Gemini error:", exc)