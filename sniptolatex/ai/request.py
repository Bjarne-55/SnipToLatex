from pathlib import Path
from functools import lru_cache
from PyQt5.QtGui import QPixmap

class Request:
    """Abstract base class for prompt-driven image requests.

    Attributes:
        _prompt_file (Path): Resolved path to the prompt template file.
    """

    def __init__(self, prompt_file_name: str):
        """Initialize a request with a prompt file name.

        Args:
            prompt_file_name (str): File name within the `prompts` directory
                to load as the request prompt/template.

        Raises:
            FileNotFoundError: If the prompt file does not exist when read.
        """
        # Prompt file looked up relative to this package's prompts directory
        self._prompt_file = Path(__file__).parent / "prompts" / prompt_file_name

    @lru_cache
    def _read_prompt_from_file(self) -> str:
        """Read and cache the prompt content.

        Returns:
            str: Prompt contents loaded from disk.

        Raises:
            FileNotFoundError: If the prompt file path cannot be read.
        """
        return self._prompt_file.read_text(encoding="utf-8")

    def send_image(self, image: QPixmap) -> str:
        """Send an image to a concrete model implementation and return text.

        Args:
            image (QPixmap): Image to be processed by the model.

        Returns:
            str: Model-generated text.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError("Not implemented. Use a subclass for a specific model.")