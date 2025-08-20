from pathlib import Path
from functools import lru_cache
from PyQt5.QtGui import QPixmap

class Request:
    def __init__(self, prompt_file_name: str):
        self._prompt_file = Path(__file__).parent / "prompts" / prompt_file_name
    
    @lru_cache
    def _read_prompt_from_file(self) -> str:
        return self._prompt_file.read_text(encoding="utf-8")

    def send_image(self, image: QPixmap) -> str:
        raise NotImplementedError("Not implemented. Use a subclass for a specific model.")