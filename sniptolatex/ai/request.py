from sniptolatex.config import read_model_settings

class Request:
    """Abstract base class for prompt-driven image requests.

    Attributes:
        _prompt_file (Path): Resolved path to the prompt template file.
    """

    def __init__(self, model_name: str):
        """Initialize a request with the api_key and prompt
        """
        settings = read_model_settings(model_name)
        self._api_key = settings["api_key"]
        self._prompt = settings["prompt_override"]

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
