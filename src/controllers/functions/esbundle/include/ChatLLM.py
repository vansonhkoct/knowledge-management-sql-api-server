

from typing import Optional, List
import torch
from transformers import AutoModel, AutoTokenizer, AutoModelForCausalLM
from langchain.llms.base import LLM


class ChatLLMAnswerResult:
    history: List[List[str]] = []
    _llm_output: Optional[dict] = None
    
    def llm_output(self):
        return self._llm_output



class ChatLLM(LLM):
    history_len = 10
    model_type: str = "ChatGLM"
    model_path: str = None
    model_gpu: bool = None
    tokenizer: object = None
    model: object = None
    
    
    
    def __init__(self, llm_model_uses_gpu = False):
        super().__init__()
        self.model_gpu = llm_model_uses_gpu
        self.model_path = "THUDM/chatglm2-6b" if llm_model_uses_gpu else "THUDM/chatglm2-6b-int4"

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
            if self.model_gpu is True:
                self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True).cuda()
            else:
                self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True).half().float()
                # self.model = AutoModel.from_pretrained(self.model_path, trust_remote_code=True).half()
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




    def generator_answer(self, prompt: str,
                        history: List[List[str]] = [],
                        streaming: bool = True,
                        max_length = 2500, 
                        top_p = 0.8, 
                        top_k = 1,
                        repetition_penalty = 1.0,
                        temperature = 0.01,
                        ):

        if streaming:
            history += [[]]
            if self.model_type == "InternLM":
                response = self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p
                )
            else:
                response = self.model.stream_chat(
                    self.tokenizer,
                    prompt,
                    history=history[-self.history_len:-1] if self.history_len > 1 else [],
                    max_length=max_length,
                    temperature=temperature,
                    top_p=top_p
                )
            for inum, (stream_resp, _) in enumerate(response):
                # self.checkPoint.clear_torch_cache()
                history[-1] = [prompt, stream_resp]
                answer_result = ChatLLMAnswerResult()
                answer_result.history = history
                answer_result._llm_output = {"answer": stream_resp}
                yield answer_result
        else:
            response, _ = self.model.chat(
                self.tokenizer,
                prompt,
                history=history[-self.history_len:] if self.history_len > 0 else [],
                max_length=max_length,
                temperature=temperature,
                top_p=top_p
            )
            self.clear_torch_cache()
            history += [[prompt, response]]
            answer_result = ChatLLMAnswerResult()
            answer_result.history = history
            answer_result._llm_output = {"answer": response}
            yield answer_result

