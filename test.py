from dotenv import load_dotenv, dotenv_values
import os
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent / ".env"
print("Loading .env from:", ENV_PATH)
print("Exists:", ENV_PATH.exists())

# Read raw values from file without relying on os.environ
raw_env = dotenv_values(ENV_PATH)
print("Raw .env entries:")
for k, v in raw_env.items():
    if "MISTRAL" in k.upper() or "OPENAI" in k.upper() or "ANTHROP" in k.upper():
        print(f"{k} = {v}")

load_dotenv(dotenv_path=ENV_PATH, override=True)

print("os.getenv('API_KEY_MISTRAL'):", os.getenv("API_KEY_MISTRAL"))
print("os.getenv('API_KEY_OPENAI'):", os.getenv("API_KEY_OPENAI"))
print("os.getenv('API_KEY_ANTHROPIC'):", os.getenv("API_KEY_ANTHROPIC"))