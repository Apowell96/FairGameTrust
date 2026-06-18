from mistralai import Mistral
import os 
from src.llm_connectors.abstract_connector import AbstractConnector
from mistralai.models.sdkerror import SDKError
import time

class MistralConnector(AbstractConnector):
    """
    Chat model implementation for the Mistral API.
    """

    def __init__(self, provider_model: str):
        self.api_key = os.getenv("API_KEY_MISTRAL")
        if not self.api_key:
            raise EnvironmentError("API_KEY_MISTRAL not found in environment variables.")
        self.provider_model = provider_model
        self.client = Mistral(api_key=self.api_key)
        self.base_delay = 0.1

    def send_prompt(self, prompt: str) -> str:
        max_retries = 5
        delay = 1

        for attempt in range(max_retries):
            try:
                
                time.sleep(self.base_delay)

                response = self.client.chat.complete(
                    model=self.provider_model,
                    messages=[{"role": "user", "content": prompt}]
                )

                return response.choices[0].message.content

            except SDKError as e:
                error_msg = str(e)

                # detect rate limit
                if "429" in error_msg or "Rate limit exceeded" in error_msg:
                    if attempt == max_retries - 1:
                        print("[ERROR] Max retries reached. Raising exception.")
                        raise

                    print(f"[WARN] Rate limit hit. Retrying in {delay}s... (attempt {attempt + 1})")
                    time.sleep(delay)
                    delay *= 2  
                    continue

                
                raise
