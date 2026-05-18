import os
import requests
import json
from typing import Union, List, Optional
import opencc

CHATGPT_API_ENDPOINT = os.getenv("ES_CHATGPT_API_ENDPOINT")

class ChatGPTAPIAnswerResult:
    history: List[List[str]] = []
    new_token: str = None
    
    def llm_output(self):
      return {"answer": self.history[-1][1]}
    


class ChatGPTAPI():
    answer_result = ChatGPTAPIAnswerResult()
    
    def __init__(self, api_endpoint = CHATGPT_API_ENDPOINT):
        super().__init__()
        self.api_endpoint = api_endpoint



    def _remove_chars_before_first_occurrence(self, text, char):
        index = text.find(char)
        if index != -1:
            return text[index:]
        return text



    def _yield_stream_tokens(self, stream_url, messages = []):
        response = requests.post(stream_url, data=json.dumps({
          "stream": True,
          "model": os.getenv("ES_CHATGPT_API_MODEL_NAME"),
          "messages": messages,
        }), stream=True)

        try:
            if response.status_code == 200:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:

                        chunkStr = chunk.decode()
                        res = json.loads(self._remove_chars_before_first_occurrence(chunkStr, "{"))

                        new_token = res["choices"][0]["message"]["content"]
                        yield new_token
        finally:
            response.close()



    def generator_answer(
      self,
      prompt,
      history: List[List[str]] = [],
      streaming: bool = True,
      system_prompt = "你是一個學校教職員，負責閱讀並分析香港教育局/教育統籌局的每年推出的通告或其他工作文件。", 
      max_length = 2500, 
      top_p = 0.92, 
      top_k = 3,
      repetition_penalty = 1.2,
      temperature = 0.01,
      converter: opencc.OpenCC = None,
      ):



        history.append([prompt, ""])

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        for idx, (user_msg, model_msg) in enumerate(history):
            # if prompt and idx == 0:
            #     continue
            if idx == len(history) - 1 and not model_msg:
                messages.append({"role": "user", "content": user_msg})
                break
            if user_msg:
                messages.append({"role": "user", "content": user_msg})
            if model_msg:
                messages.append({"role": "assistant", "content": model_msg})


        for new_token in self._yield_stream_tokens(
            stream_url = self.api_endpoint,
            messages = messages,
        ):

            _new_token = new_token is not None and (
                converter.convert(new_token) if converter is not None else new_token
            )

            if _new_token:
                history[-1][1] += _new_token

            answer_result = ChatGPTAPIAnswerResult()
            answer_result.history = history
            answer_result.new_token = _new_token
            yield answer_result

