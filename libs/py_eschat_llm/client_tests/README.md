# py_eschat_llm Client Smoke Tests

These lightweight scripts exercise the two external dependencies that the `py_eschat_llm` library talks to:

1. The Elasticsearch cluster used for document storage/search
2. The ChatLLM HTTP API that powers streamed completions

They live outside the main FastAPI app so you can validate connectivity (and credentials) in isolation before wiring the
library into other services.

## Quick start

1. (Recommended) create a virtual environment and install the library in editable mode so all dependencies (including
  `elasticsearch`) are available:

  ```bash
  cd libs/py_eschat_llm
  python3 -m venv .venv
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -e .
  ```

2. Copy the provided environment template and tweak it if your endpoints differ:

   ```bash
   cd libs/py_eschat_llm
   cp client_tests/.env.client.example client_tests/.env.client
   ```

3. (Optional) edit `client_tests/.env.client` to point to non-default hosts or credentials.

4. Run one or both tests (shown here using the local virtual environment):

   ```bash
  # Elasticsearch connectivity (cluster health + short-lived document roundtrip)
  .venv/bin/python -m client_tests.test_elasticsearch_connection

  # LLM connectivity (model listing + real completion through py_eschat_llm)
  .venv/bin/python -m client_tests.test_llm_api

  # Convenience wrapper that runs both sequentially
  .venv/bin/python -m client_tests.run_all
   ```

Each script prints high-level diagnostics (host, status, elapsed time, sample answer text) so you can quickly spot
misconfigurations.

## Environment variables

The tests rely on the same environment variables as the core library. They automatically load `client_tests/.env.client`
(if it exists) and fall back to the defaults listed below:

| Variable | Default | Purpose |
| --- | --- | --- |
| `ES_HOST` | `http://localhost:9200` | Elasticsearch base URL |
| `ES_USERNAME` | `elasic` | Elasticsearch username |
| `ES_PASSWORD` | `octopuspass` | Elasticsearch password |
| `ES_CHATGPT_API_ENDPOINT` | `http://localhost:18000/v1/chat_completions` | Chat completion endpoint |
| `ES_CHATGPT_API_MODEL_ENDPOINT` | `http://localhost:18000/v1/models` | Model listing endpoint |
| `ES_CHATGPT_API_MODEL_NAME` | `gpt-4o-mini` | Target model name for completions |
| `ES_CHATLLM_LLM_MODEL_ENABLE_API` | `1` | Enables ChatLLM calls in the library |

> **Note:** The scripts do not download embedding models or touch document embeddings. Only HTTP connectivity is
> validated, so you can run them on developer laptops without the heavier ML dependencies.

## What the tests cover

- `test_elasticsearch_connection.py`
  - Establishes a real connection using the official `elasticsearch` Python client
  - Prints cluster info/health
  - Creates a temporary index, indexes a document, fetches it back, and finally deletes the index

- `test_llm_api.py`
  - Hits the raw model listing endpoint to confirm the service is alive
  - Builds an `LLMVoAskQuestion` and routes it through `ESChatLLM.bot_llm_ask_question`, matching how the FastAPI layer
    will invoke the LLM controller
  - Prints latency plus a snippet of the generated answer

- `run_all.py`
  - Convenience orchestrator that executes both scripts in sequence for CI pipelines or manual smoke testing

These tests are intended as quick integration checks, not replacements for unit tests inside the main API. Feel free to
extend them with scenario-specific prompts or Elasticsearch queries to fit your deployment.
