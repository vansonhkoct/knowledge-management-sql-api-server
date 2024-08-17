
from typing import List

class LLMVoAskQuestion:
    prompt: str
    history: List[List[str]] = []
    llm_max_token=8192
    llm_temperature=0.01
    llm_top_p=0.8
    llm_top_k=4,
    llm_repetition_penalty=1.2,
    llm_history_len=3
    api_uid: str | None = None
    emit_to_uid = None

    def __init__(
        self,
        prompt: str,
        history: List[List[str]] = [],
        llm_max_token=8192,
        llm_temperature=0.01,
        llm_top_p=0.8,
        llm_top_k=4,
        llm_repetition_penalty=1.2,
        llm_history_len=3,
        api_uid: str | None = None,
        emit_to_uid = None,
        ):
        self.prompt = prompt
        self.history = history
        self.llm_max_token = llm_max_token
        self.llm_temperature = llm_temperature
        self.llm_top_p = llm_top_p
        self.llm_top_k = llm_top_k
        self.llm_repetition_penalty = llm_repetition_penalty
        self.llm_history_len = llm_history_len
        self.api_uid = api_uid
        self.emit_to_uid = emit_to_uid
        