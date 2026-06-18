
from mistralai import Mistral
import os 
from src.llm_connectors.abstract_connector import AbstractConnector

from openai import OpenAI
class MistralConnectorLOCAL(AbstractConnector):
    """
    Local LLM Studio connector using OpenAI-compatible API.
    """

    def __init__(self, provider_model: str):
        self.provider_model = provider_model

        self.client = OpenAI(
            base_url="http://127.0.0.1:1234/v1",
        )

    def send_prompt(self, prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.provider_model,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content
