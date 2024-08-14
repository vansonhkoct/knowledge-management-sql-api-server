
class LLMVoAskQuestion:
    prompt: str
    llm_max_token=8192
    llm_temperature=0.01
    llm_top_p=0.8
    llm_history_len=3
    api_uid: str | None = None
    emit_to_uid = None

    def __init__(
        self,
        prompt: str,
        llm_max_token=8192,
        llm_temperature=0.01,
        llm_top_p=0.8,
        llm_history_len=3,
        api_uid: str | None = None,
        emit_to_uid = None,
        ):
        self.prompt = prompt
        self.llm_max_token = llm_max_token
        self.llm_temperature = llm_temperature
        self.llm_top_p = llm_top_p
        self.llm_history_len = llm_history_len
        self.api_uid = api_uid
        self.emit_to_uid = emit_to_uid
        