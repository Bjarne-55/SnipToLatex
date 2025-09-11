from pathlib import Path
from sniptolatex.config import read_model_settings

class Request:
    """Abstract base class for prompt-driven image requests.

    Provides per-model API key and prompt loading, with a fallback to a
    packaged default prompt file when no stored prompt is present.
    """

    def __init__(self, model_name: str):
        """Initialize a request with API key and prompt for a model.

        The prompt is loaded from per-model config key 'prompt'. If missing,
        falls back to the packaged default prompt file for the model.
        """
        self._model_name = model_name
        settings = read_model_settings(model_name)
        self._api_key = settings.get("api_key")
        stored_prompt = settings.get("prompt")
        self._prompt = (
            stored_prompt if (stored_prompt is not None and len(stored_prompt) > 0)
            else self._read_default_prompt_file(model_name)
        )

    def _read_default_prompt_file(self, model_name: str) -> str:
        """Read the shipped default prompt for a model.

        Returns empty string if prompt file is not found.
        """
        name = {
            "gemini": "gemini_image_to_latex.txt",
            "chatgpt": "chatgpt_image_to_latex.txt",
        }.get(model_name, "gemini_image_to_latex.txt")
        path = Path(__file__).parent / "prompts" / name
        return path.read_text(encoding="utf-8")

    def send_image(self, image: bytes) -> str:
        """Send an image to a concrete model implementation and return text.

        Args:
            image (bytes): Image to be processed by the model.

        Returns:
            str: Model-generated text.

        Raises:
            NotImplementedError: Must be overridden by subclasses.
        """
        raise NotImplementedError("Not implemented. Use a subclass for a specific model.")
