import os
from pathlib import Path
from typing import Dict

ENV_FILE_NAME = ".env.client"

DEFAULT_ENV: Dict[str, str] = {
    "ES_HOST": "http://localhost:9200",
    "ES_USERNAME": "elasic",
    "ES_PASSWORD": "octopuspass",
    "ES_VERBOSE": "0",
    "ES_DEBUG": "0",
    "ES_EMBEDDING_MODEL": "sentence-transformers/all-MiniLM-L6-v2",
    "ES_EMBEDDING_MODEL_LEGACY": "sentence-transformers/all-MiniLM-L6-v2",
    "ES_CHATLLM_LLM_MODEL_ENABLE_API": "1",
    "ES_CHATLLM_LLM_CONTROLLER_DEBUG": "0",
    "ES_CHATGPT_API_MODEL_NAME": "gpt-4o-mini",
    "ES_CHATGPT_API_ENDPOINT": "http://localhost:18000/v1/chat_completions",
    "ES_CHATGPT_API_MODEL_ENDPOINT": "http://localhost:18000/v1/models",
}


def _parse_env_line(line: str) -> tuple[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if "=" not in line:
        return None
    key, value = line.split("=", 1)
    return key.strip(), value.strip()


def load_local_env() -> None:
    """Load .env.client if present and fall back to DEFAULT_ENV for missing keys."""
    env_path = Path(__file__).with_name(ENV_FILE_NAME)
    if env_path.exists():
        for raw_line in env_path.read_text().splitlines():
            parsed = _parse_env_line(raw_line)
            if parsed:
                key, value = parsed
                os.environ[key] = value

    for key, value in DEFAULT_ENV.items():
        os.environ.setdefault(key, value)


def print_heading(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_kv(label: str, value) -> None:
    print(f"{label:>24}: {value}")


def require_env(var_name: str) -> str:
    load_local_env()
    value = os.getenv(var_name)
    if not value:
        raise RuntimeError(f"Environment variable {var_name} is required for the client tests")
    return value
