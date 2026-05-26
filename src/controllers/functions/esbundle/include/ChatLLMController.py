import requests
import time
import opencc
from . import ConfigParams
from .ChatLLMDao.LLMVo import LLMVoAskQuestion

converter = opencc.OpenCC('s2t.json')


class ChatModelAnswerResult:
    history = []

    def __init__(self, history=None):
        self.history = history or []

    def llm_output(self):
        return {"answer": self.history[-1][1] if self.history else ""}

class ChatLLMController:
    active_llm_generators_vs_api_uids = {}

    def __init__(
        self,
        base_url,
        model_name,
        api_key=None,
        api_path="/v1",
        headers_json=None,
        options_json=None,
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.api_path = api_path or "/v1"
        self.headers_json = headers_json if isinstance(headers_json, dict) else {}
        self.options_json = options_json if isinstance(options_json, dict) else {}

    def _build_url(self, suffix):
        api_path = (self.api_path or "").strip()
        suffix = suffix.lstrip("/")

        if api_path in ["", "/"]:
            return f"{self.base_url}/{suffix}"

        normalized_api_path = api_path if api_path.startswith("/") else f"/{api_path}"
        if self.base_url.endswith(normalized_api_path):
            return f"{self.base_url}/{suffix}"

        return f"{self.base_url}{normalized_api_path}/{suffix}"

    def _build_headers(self):
        headers = {
            "Content-Type": "application/json",
            **self.headers_json,
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    def _extract_answer_text(self, response_body):
        choices = response_body.get("choices") or []
        if len(choices) > 0:
            message = choices[0].get("message") or {}
            if message.get("content") is not None:
                return message.get("content")

        output = response_body.get("output") or []
        for item in output:
            contents = item.get("content") or []
            for content in contents:
                if content.get("text") is not None:
                    return content.get("text")

        raise ValueError(f"Unable to extract answer text from LLM response: {response_body}")

    def _build_messages(self, prompt, history):
        messages = []
        for user_msg, model_msg in history:
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})

        messages.append({"role": "user", "content": prompt})
        return messages
    
    

    def bot_ask_question(
        self, 
        voAskQuestion: LLMVoAskQuestion,
    ):
        timestamp = str(time.time_ns())

        history = [list(item) for item in (voAskQuestion.history or [])]
        messages = self._build_messages(voAskQuestion.prompt, history)

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "temperature": voAskQuestion.llm_temperature,
            "top_p": voAskQuestion.llm_top_p,
            "max_tokens": voAskQuestion.llm_max_token,
            **self.options_json,
        }

        response = requests.post(
            self._build_url("chat/completions"),
            headers=self._build_headers(),
            json=payload,
            timeout=240,
        )
        response.raise_for_status()

        answer_text = self._extract_answer_text(response.json())
        answer_text = converter.convert(answer_text)

        history.append([voAskQuestion.prompt, answer_text])
        answer_result = ChatModelAnswerResult(history=history)

        answer_result_dict = {
            timestamp: answer_result.llm_output(),
        }

        if voAskQuestion.api_uid is not None and voAskQuestion.emit_to_uid is not None:
            voAskQuestion.emit_to_uid(
                "ai_response",
                answer_result_dict,
                uid=voAskQuestion.api_uid,
            )

        return answer_result_dict



    def bot_stop_answering(
        self, 
        api_uid: str | None = None,
    ):
        if api_uid is not None:
            self.active_llm_generators_vs_api_uids[api_uid] = None
