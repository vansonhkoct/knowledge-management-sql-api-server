## py_eschat_llm

`py_eschat_llm` bundles the Elasticsearch + ChatLLM building blocks that powered the
original `src.controllers.functions.esbundle` module. The code now lives in a
stand-alone package so it can be re-used by the API server as well as notebooks
and integration tests without duplicating logic.

### Highlights

- Async-friendly façade (`py_eschat_llm.es_chatllm`) that exposes the document
	ingestion, metadata updates, search, and LLM helper methods used by the API
	server.
- Full copy of the existing Elasticsearch, embedding, PyMuPDF, and LLM helpers
	inside a distributable Python package.
- Clean module exports via `py_eschat_llm.__init__` so callers can import the
	existing value objects (`ESVoDocInsert`, `ESVoDocSearch`, `LLMVoAskQuestion`)
	without touching internal folders.
- Updated dependency metadata (see `pyproject.toml`) so installing the package
	pulls in `elasticsearch`, `sentence-transformers`, `langchain`, `pymupdf`,
	`pymupdf4llm`, and related runtime requirements.

### Local installation

From the repository root you can install the package in editable mode:

```bash
pip install -e libs/py_eschat_llm
```

or using venv:

```bash
cd libs/py_eschat_llm
python3 -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -e .
.venv/bin/python -m client_tests.test_elasticsearch_connection
.venv/bin/python -m client_tests.test_llm_api
.venv/bin/python -m client_tests.run_all
```

The FastAPI application now adds the `/libs` folder to `sys.path` when `src`
loads, so the package is also available automatically when you run
`python main_uvicorn.py`.

### Usage

```python
from py_eschat_llm import ESVoDocInsert, es_chatllm

payload = ESVoDocInsert(
		index_name="demo",
		text="<oc_document ...>",
		extra_metadata={"document_tags": ["demo"]},
)

docs, ids, index_name = await es_chatllm.bot_es_add_document(payload)
```

The original helper functions (`bot_es_search_multi_vector`,
`bot_llm_ask_question`, `extract_pdf_file_to_text`, etc.) continue to work
exactly as before—only the import path changed.

### Configuration

The library reads the same environment variables as the legacy module, e.g.:

- `ES_HOST`, `ES_USERNAME`, `ES_PASSWORD`
- `ES_EMBEDDING_MODEL`, `ES_EMBEDDING_MODEL_LEGACY`
- `ES_CHATGPT_API_ENDPOINT`, `ES_CHATGPT_API_MODEL_NAME`
- `ES_CHATLLM_LLM_MODEL_ENABLE_API`, `ES_CHATLLM_LLM_CONTROLLER_DEBUG`

Refer to `include/ConfigParams.py` for the complete list.
