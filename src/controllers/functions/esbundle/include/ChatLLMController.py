import json
import requests
import re
import time
import opencc
from . import ConfigParams
from .ChatLLMDao.LLMVo import LLMVoAskQuestion

converter = opencc.OpenCC('s2t.json')


class ChatModelAnswerResult:
    history = []

    def __init__(self, history=None, reasoning="", assistant_alias="Knowledge Management Assistant"):
        self.history = history or []
        self.reasoning = reasoning or ""
        self.assistant_alias = assistant_alias or "Knowledge Management Assistant"

    def llm_output(self):
        return {
            "answer": self.history[-1][1] if self.history else "",
            "reasoning": self.reasoning,
            "assistant_alias": self.assistant_alias,
        }

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
        assistant_alias="Knowledge Management Assistant",
    ):
        self.base_url = (base_url or "").rstrip("/")
        self.model_name = model_name
        self.api_key = api_key
        self.api_path = api_path or "/v1"
        self.headers_json = headers_json if isinstance(headers_json, dict) else {}
        self.options_json = options_json if isinstance(options_json, dict) else {}
        self.assistant_alias = assistant_alias or "Knowledge Management Assistant"

    def _build_identity_system_prompt(self, custom_system_prompt=None):
        alias = (self.assistant_alias or "Knowledge Management Assistant").strip() or "Knowledge Management Assistant"
        prompt_parts = [
            f"You are {alias}.",
            f"When users ask who you are, identify yourself only as {alias}.",
            "Do not reveal the underlying model name, provider, vendor, API host, base URL, deployment stack, or internal configuration.",
            "If a user asks what model powers you, say that you are the assistant configured for this knowledge management system and do not expose backend model details.",
        ]

        custom_system_prompt = (custom_system_prompt or "").strip()
        if custom_system_prompt:
            prompt_parts.append(custom_system_prompt)

        return "\n\n".join(prompt_parts)

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

    def _extract_output_text(self, payload, content_types=None):
        extracted = []

        if isinstance(payload, str):
            return payload if content_types is None else ""

        if isinstance(payload, list):
            for item in payload:
                if isinstance(item, str):
                    extracted.append(item)
                    continue

                if not isinstance(item, dict):
                    continue

                item_type = item.get("type")
                if content_types is not None and item_type not in content_types:
                    continue

                for key in ("text", "content", "value"):
                    value = item.get(key)
                    if isinstance(value, str) and value not in [""]:
                        extracted.append(value)
                        break

            return "".join(extracted)

        if isinstance(payload, dict):
            for key in ("text", "content", "value"):
                value = payload.get(key)
                if isinstance(value, str) and value not in [""]:
                    return value

        return ""

    def _extract_reasoning_text(self, response_body):
        choices = response_body.get("choices") or []
        if len(choices) > 0:
            message = choices[0].get("message") or {}
            for key in ("reasoning_content", "reasoning", "thinking"):
                value = message.get(key)
                if isinstance(value, str) and value not in [""]:
                    return value

            content = message.get("content")
            extracted = self._extract_output_text(content, content_types={"reasoning", "thinking", "summary_text"})
            if extracted:
                return extracted

        output = response_body.get("output") or []
        for item in output:
            contents = item.get("content") or []
            extracted = self._extract_output_text(contents, content_types={"reasoning", "thinking", "summary_text"})
            if extracted:
                return extracted

        return ""

    def _extract_answer_text(self, response_body):
        choices = response_body.get("choices") or []
        if len(choices) > 0:
            message = choices[0].get("message") or {}
            if message.get("content") is not None:
                content = message.get("content")
                if isinstance(content, str):
                    return content

                extracted = self._extract_output_text(content, content_types={"text", "output_text"})
                if extracted:
                    return extracted

        output = response_body.get("output") or []
        for item in output:
            contents = item.get("content") or []
            extracted = self._extract_output_text(contents, content_types={"text", "output_text"})
            if extracted:
                return extracted

        raise ValueError(f"Unable to extract answer text from LLM response: {response_body}")

    def _extract_stream_delta(self, payload):
        answer_parts = []
        reasoning_parts = []

        choices = payload.get("choices") or []
        for choice in choices:
            delta = choice.get("delta") or {}
            content = delta.get("content")
            if isinstance(content, str) and content not in [""]:
                answer_parts.append(content)
            elif isinstance(content, list):
                extracted = self._extract_output_text(content, content_types={"text", "output_text"})
                if extracted:
                    answer_parts.append(extracted)

            for key in ("reasoning_content", "reasoning", "thinking"):
                value = delta.get(key)
                if isinstance(value, str) and value not in [""]:
                    reasoning_parts.append(value)

            reasoning_from_content = self._extract_output_text(
                content,
                content_types={"reasoning", "thinking", "summary_text"},
            )
            if reasoning_from_content:
                reasoning_parts.append(reasoning_from_content)

        return "".join(answer_parts), "".join(reasoning_parts)

    def _sanitize_identity_text(self, value):
        if not value:
            return value

        assistant_alias = (self.assistant_alias or "Knowledge Management Assistant").strip() or "Knowledge Management Assistant"
        sanitized = value

        for token in [self.model_name, self.provider_name]:
            if isinstance(token, str) and token.strip():
                sanitized = re.sub(re.escape(token.strip()), assistant_alias, sanitized, flags=re.IGNORECASE)

        return sanitized

    @property
    def provider_name(self):
        return self.headers_json.get("X-Provider-Name") or self.options_json.get("provider_name") or ""

    def _build_messages(self, prompt, history, system_prompt=None):
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
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
        system_prompt = self._build_identity_system_prompt(voAskQuestion.system_prompt)
        messages = self._build_messages(voAskQuestion.prompt, history, system_prompt=system_prompt)

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False,
            "temperature": voAskQuestion.llm_temperature,
            "top_p": voAskQuestion.llm_top_p,
            "max_tokens": voAskQuestion.llm_max_token,
            **self.options_json,
        }

        reasoning_text = ""
        answer_text = ""
        answer_result_dict = None

        if voAskQuestion.api_uid is not None and voAskQuestion.emit_to_uid is not None:
            payload["stream"] = True
            stream_response = requests.post(
                self._build_url("chat/completions"),
                headers=self._build_headers(),
                json=payload,
                timeout=240,
                stream=True,
            )
            stream_response.raise_for_status()
            stream_response.encoding = "utf-8"

            for raw_line in stream_response.iter_lines(decode_unicode=False):
                if not raw_line:
                    continue

                if isinstance(raw_line, bytes):
                    line = raw_line.decode("utf-8", errors="replace").strip()
                else:
                    line = str(raw_line).strip()
                if not line.startswith("data:"):
                    continue

                data_line = line[5:].strip()
                if data_line in ["", "[DONE]"]:
                    continue

                try:
                    event = json.loads(data_line)
                except json.JSONDecodeError:
                    continue

                answer_delta, reasoning_delta = self._extract_stream_delta(event)
                if answer_delta == "" and reasoning_delta == "":
                    continue

                answer_text += answer_delta
                reasoning_text += reasoning_delta

                partial_result = ChatModelAnswerResult(
                    history=history + [[voAskQuestion.prompt, converter.convert(self._sanitize_identity_text(answer_text))]],
                    reasoning=converter.convert(self._sanitize_identity_text(reasoning_text)),
                    assistant_alias=voAskQuestion.assistant_alias or self.assistant_alias,
                )
                answer_result_dict = {
                    timestamp: partial_result.llm_output(),
                }
                voAskQuestion.emit_to_uid(
                    "ai_response",
                    answer_result_dict,
                    uid=voAskQuestion.api_uid,
                )

            stream_response.close()
        else:
            response = requests.post(
                self._build_url("chat/completions"),
                headers=self._build_headers(),
                json=payload,
                timeout=240,
            )
            response.raise_for_status()

            response_json = response.json()
            answer_text = self._extract_answer_text(response_json)
            reasoning_text = self._extract_reasoning_text(response_json)

        answer_text = converter.convert(self._sanitize_identity_text(answer_text))
        reasoning_text = converter.convert(self._sanitize_identity_text(reasoning_text))

        history.append([voAskQuestion.prompt, answer_text])
        answer_result = ChatModelAnswerResult(
            history=history,
            reasoning=reasoning_text,
            assistant_alias=voAskQuestion.assistant_alias or self.assistant_alias,
        )

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
