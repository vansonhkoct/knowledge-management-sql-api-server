

from typing import Optional, List
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
from langchain.llms.base import LLM


class ChatLLMAnswerResult:
    history: List[List[str]] = []
    llm_output: Optional[dict] = None


class ChatLLM(LLM):
    max_token: int = 8192
    temperature: float = 0.95
    top_p = 0.8
    history_len = 10
    history = []
    model_type: str = "ChatGLM"
    model_path: str = None
    model_gpu: bool = None
    tokenizer: object = None
    model: object = None
    
    def __init__(self, config_params):
        super().__init__()
        self.model_path = config_params.llm_model
        self.model_gpu = config_params.llm_model_gpu

    @property
    def _llm_type(self) -> str:
        return "ChatLLM"

    def load_llm(self):
        print("A")
        if 'internlm' in self.model_path.lower():
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, device_map="auto", trust_remote_code=True,
                                                           torch_dtype=torch.float16)
            self.model = AutoModelForCausalLM.from_pretrained(self.model_path, device_map="auto",
                                                              trust_remote_code=True,
                                                              torch_dtype=torch.float16)
            self.model = self.model.eval()
            self.model_type = "InternLM"
        else:
            print("B")
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_path, trust_remote_code=True)
            print(f"B2 {self.model_path}, GPU: {self.model_gpu}")
            if self.model_gpu == True:
                self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True).cuda()
            else:
                self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True).float()
            print("B3")
            self.model = self.model.eval()
            print("B4")

    def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
        print(f"__call:{prompt}")
        response, _ = self.model.chat(
            self.tokenizer,
            prompt,
            history=[],
            max_length=self.max_token,
            temperature=self.temperature,
            top_p=self.top_p
        )
        print(f"response:{response}")
        print(f"+++++++++++++++++++++++++++++++++++")
        return response

    def generatorAnswer(self, prompt: str,
                        history: List[List[str]] = [],
                        streaming: bool = False):

        if streaming:
            history += [[]]
            if self.model_type == "InternLM":
                response = self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_new_tokens=self.max_token,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
            else:
                response = self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_length=self.max_token,
                    temperature=self.temperature,
                    top_p=self.top_p
                )
            for inum, (stream_resp, _) in enumerate(response):
                # self.checkPoint.clear_torch_cache()
                history[-1] = [prompt, stream_resp]
                answer_result = ChatLLMAnswerResult()
                answer_result.history = history
                answer_result.llm_output = {"answer": stream_resp}
                yield answer_result
        else:
            response, _ = self.model.chat(
                self.tokenizer,
                prompt,
                history=history[-self.history_len:] if self.history_len > 0 else [],
                max_length=self.max_token,
                temperature=self.temperature,
                top_p=self.top_p
            )
            self.clear_torch_cache()
            history += [[prompt, response]]
            answer_result = ChatLLMAnswerResult()
            answer_result.history = history
            answer_result.llm_output = {"answer": response}
            yield answer_result

