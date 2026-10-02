
import os
import threading
import time

from dotenv import load_dotenv
from src.llm_connectors.anthropic_connector import AnthropicConnector
from src.llm_connectors.mistral_connector import MistralConnector
from src.llm_connectors.mistral_connectorLOCAL import MistralConnectorLOCAL
from src.llm_connectors.openai_connector import OpenAIConnector

# Load environment variables from a .env file
load_dotenv()

# Dictionary mapping our abstract model names to provider classes and their corresponding provider model identifiers.
MODEL_PROVIDER_MAP = {
    "claude-sonnet-4-6": (AnthropicConnector, "claude-sonnet-4-6"),
    "mistral-small-2603": (MistralConnector, "mistral-small-2603"),
    "gpt-4o": (OpenAIConnector, "gpt-4o"),
    # Add more mappings as needed.
    
    "LocalMistral": (MistralConnectorLOCAL, "mistralai/ministral-3-3b")
}

_RATE_LIMIT_LOCK = threading.Lock()
_LAST_REQUEST_AT = 0.0


def _parse_delay_seconds(value) -> float:
    """Parse delay from config/env into a non-negative float."""
    if value is None or value == "":
        return 0.0
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid request delay value: {value}") from exc
    if parsed < 0:
        raise ValueError("Request delay must be >= 0")
    return parsed


def _default_delay_from_env() -> float:
    return _parse_delay_seconds(os.getenv("FAIRGAME_REQUEST_DELAY_SECONDS", 0))


_REQUEST_DELAY_SECONDS = _default_delay_from_env()


def configure_request_delay(delay_seconds=None) -> None:
    """Configure minimum seconds to wait between prompt calls."""
    global _REQUEST_DELAY_SECONDS, _LAST_REQUEST_AT
    _REQUEST_DELAY_SECONDS = (
        _default_delay_from_env() if delay_seconds is None
        else _parse_delay_seconds(delay_seconds)
    )
    _LAST_REQUEST_AT = 0.0


def _wait_for_request_slot() -> None:
    """Ensure calls are spaced to reduce provider rate-limit errors."""
    global _LAST_REQUEST_AT
    if _REQUEST_DELAY_SECONDS <= 0:
        return

    with _RATE_LIMIT_LOCK:
        now = time.monotonic()
        remaining = _REQUEST_DELAY_SECONDS - (now - _LAST_REQUEST_AT)
        if remaining > 0:
            time.sleep(remaining)
        _LAST_REQUEST_AT = time.monotonic()

class ChatModelFactory:
    """
    Factory for creating chat model instances based on the model name.
    """

    @staticmethod
    def get_model(model_name: str):
        """
        Return an instance of ChatModel based on the provided model name.

        Parameters:
            model_name (str): The abstract model name (e.g., "MistralLarge", "GPT4", "Claude").

        Returns:
            ChatModel: An instance of the appropriate chat model.

        Raises:
            ValueError: If the model_name is unsupported.
        """
        provider_info = MODEL_PROVIDER_MAP.get(model_name)
        if not provider_info:
            raise ValueError(f"Unsupported model specified: {model_name}")
        model_class, provider_model = provider_info
        return model_class(provider_model)


def execute_prompt(model_name: str, prompt: str) -> str:
    """
    Execute a prompt using the specified model.

    Parameters:
        model_name (str): The abstract model name (e.g., "MistralLarge", "GPT4", "Claude").
        prompt (str): The prompt text to send to the API.

    Returns:
        str: The response text from the API.
    """
    _wait_for_request_slot()
    chat_model = ChatModelFactory.get_model(model_name)
    return chat_model.send_prompt(prompt)


if __name__ == "__main__":
    # Example usage:
    model_identifier = "claude-sonnet-4-6"
    prompt_text = "Tell me a programming joke."
    
    try:
        result = execute_prompt(model_identifier, prompt_text)
        print("API Response:", result)
    except Exception as e:
        print("An error occurred:", e)
