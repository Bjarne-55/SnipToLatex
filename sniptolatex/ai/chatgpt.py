"""ChatGPT model request placeholder.

This is a placeholder implementation to allow selecting ChatGPT in settings
and customizing its prompt. Actual API calls are not implemented.
"""

from .request import Request


class ChatGPTRequest(Request):
    """Placeholder request class for ChatGPT.

    Uses a default prompt file and returns a fixed message to indicate that
    the model is not yet implemented.
    """

    def __init__(self):
        super().__init__("chatgpt")

    def send_image(self, image: bytes) -> str:
        # In a future implementation, this would call the OpenAI API.
        # For now, we just return a placeholder message so the flow continues.
        return "[ChatGPT placeholder: not implemented]"

