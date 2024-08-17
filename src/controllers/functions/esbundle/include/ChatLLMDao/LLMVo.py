
from typing import List

class LLMVoAskQuestion:
    prompt: str
    history: List[List[str]] = []
    llm_model_name=None
    llm_max_token=None
    llm_temperature=None
    llm_top_p=None
    llm_top_k=None
    llm_repetition_penalty=None
    llm_history_len=3
    api_uid: str | None = None
    emit_to_uid = None

    def __init__(
        self,
        prompt: str,
        history: List[List[str]] = [],
        llm_model_name=None,
        llm_max_token=None,
        llm_temperature=None,
        llm_top_p=None,
        llm_top_k=None,
        llm_repetition_penalty=None,
        llm_history_len=3,
        api_uid: str | None = None,
        emit_to_uid = None,
        ):
        self.prompt = prompt
        self.history = history
        self.llm_model_name = llm_model_name or None
        self.llm_max_token = llm_max_token or 8192
        self.llm_temperature = llm_temperature or 0.01
        self.llm_top_p = llm_top_p or 0.9
        self.llm_top_k = llm_top_k or 4
        self.llm_repetition_penalty = llm_repetition_penalty or 1.2
        self.llm_history_len = llm_history_len or 3
        self.api_uid = api_uid
        self.emit_to_uid = emit_to_uid
        