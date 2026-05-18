"""Connectivity smoke test for the ChatLLM HTTP API via ``py_eschat_llm``."""

from __future__ import annotations

import asyncio
import os
import textwrap
import time
from typing import Any, Iterable

import requests

from client_tests.test_utils import load_local_env, print_heading, print_kv, require_env

# Ensure ConfigParams sees the intended environment before importing the library.
load_local_env()

from py_eschat_llm import LLMVoAskQuestion, bot_llm_ask_question

PROMPT = (
    "You are assisting the knowledge management platform team. "
    "Give a concise 3-bullet overview of how the API ingests documents, builds embeddings, "
    "and answers natural language questions."
)


def _extract_model_names(payload: Any) -> list[str]:
    """Return a flat list of model identifiers from whatever the endpoint returns."""

    def _lookup(entry: Any) -> str | None:
        if isinstance(entry, dict):
            return (
                entry.get("id")
                or entry.get("model")
                or entry.get("name")
            )
        if isinstance(entry, str):
            return entry
        return None

    candidates: Iterable[Any]
    if isinstance(payload, list):
        candidates = payload
    elif isinstance(payload, dict):
        for key in ("data", "models"):
            value = payload.get(key)
            if isinstance(value, list):
                candidates = value
                break
        else:
            candidates = [payload]
    else:
        return []

    names: list[str] = []
    for candidate in candidates:
        name = _lookup(candidate)
        if name:
            names.append(str(name))
    return names


def _preview_answer(answer: str | None) -> str:
    if not answer:
        return "<empty>"
    flattened = " ".join(answer.split())
    return textwrap.shorten(flattened, width=320, placeholder="…")


def _extract_answer_text(result: Any) -> str:
    if not isinstance(result, dict):
        return "<unexpected response>"
    answer_payload = result.get("answer_result")
    if isinstance(answer_payload, dict):
        for payload in answer_payload.values():
            if isinstance(payload, dict):
                return _preview_answer(payload.get("answer"))
    return "<missing answer>"


def _check_model_endpoint() -> None:
    print_heading("Checking LLM model endpoint")
    url = require_env("ES_CHATGPT_API_MODEL_ENDPOINT")
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    names = _extract_model_names(response.json())
    print_kv("URL", url)
    print_kv("Models returned", len(names))
    if names:
        print_kv("First model", names[0])


async def _ask_question() -> None:
    print_heading("Sending ChatLLM request via py_eschat_llm")
    vo = LLMVoAskQuestion(
        prompt=PROMPT,
        history=[],
        llm_model_name=os.getenv("ES_CHATGPT_API_MODEL_NAME", "").strip(),
        api_uid="client-tests",
    )
    started = time.perf_counter()
    result = await bot_llm_ask_question(vo=vo)
    elapsed = time.perf_counter() - started
    print_kv("Latency (s)", f"{elapsed:.2f}")
    print_kv("Answer preview", _extract_answer_text(result))


async def main() -> None:
    load_local_env()
    _check_model_endpoint()
    await _ask_question()


if __name__ == "__main__":
    asyncio.run(main())
