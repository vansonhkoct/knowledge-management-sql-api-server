"""
This script creates an interactive web demo for the GLM-4-9B model using Gradio,
a Python library for building quick and easy UI components for machine learning models.
It's designed to showcase the capabilities of the GLM-4-9B model in a user-friendly interface,
allowing users to interact with the model through a chat-like interface.
"""

from pathlib import Path
from threading import Thread
from typing import Union, List, Optional
import opencc

import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    PreTrainedTokenizer,
    PreTrainedTokenizerFast,
    StoppingCriteria,
    StoppingCriteriaList,
    TextIteratorStreamer
)

ModelType = Union[PreTrainedModel]
TokenizerType = Union[PreTrainedTokenizer, PreTrainedTokenizerFast]

DEFAULT_MODEL_PATH = 'THUDM/chatglm3-6b'
DEFAULT_TOKENIZER_PATH = 'THUDM/chatglm3-6b'

_global_model: ModelType = None
_global_tokenizer: TokenizerType = None


class ChatGLM3AnswerResult:
    history: List[List[str]] = []
    new_token: str = None
    
    def llm_output(self):
      return {"answer": self.history[-1][1]}
    


class ChatGLM3():
    model_path = DEFAULT_MODEL_PATH
    model_gpu = False
    answer_result = ChatGLM3AnswerResult()
    
    def __init__(self, llm_model = DEFAULT_MODEL_PATH, llm_model_uses_gpu = False):
        super().__init__()
        self.model_path = llm_model
        self.model_gpu = llm_model_uses_gpu


    def load_llm(self):
        
        global _global_model
        global _global_tokenizer

        if _global_model is not None and _global_tokenizer is not None:
          return
        
        def load_model_and_tokenizer(
            model_dir: Union[str, Path], trust_remote_code: bool = True, is_gpu: bool = False,
        ) -> tuple[ModelType, TokenizerType]:
            model = AutoModelForCausalLM.from_pretrained(
                model_dir,
                torch_dtype=torch.bfloat16,
                trust_remote_code=True,
                low_cpu_mem_usage=True,
            )
            
            if is_gpu:
              model = model.half().cuda()
            
            tokenizer_dir = model_dir
            tokenizer = AutoTokenizer.from_pretrained(
                tokenizer_dir, trust_remote_code=trust_remote_code, use_fast=False
            )
            return model, tokenizer


        model, tokenizer = load_model_and_tokenizer(
          self.model_path, 
          trust_remote_code=True, 
          is_gpu=self.model_gpu,
          )
        
        _global_model = model
        _global_tokenizer = tokenizer


    def generator_answer(
      self,
      prompt,
      history: List[List[str]] = [],
      streaming: bool = True,
      system_prompt = "你是一個學校系統教職員，你的母語為中文，負責閱讀並分析來自系統中的香港教育局/教育統籌局的每年推出的通告或其他校務工作文件。", 
      max_length = 2500, 
      top_p = 0.92, 
      top_k = 3,
      repetition_penalty = 1.2,
      temperature = 0.01,
      converter: opencc.OpenCC = None,
      ):

        history.append([prompt, ""])
      
        self.load_llm()
      
        model = _global_model
        tokenizer = _global_tokenizer
      
        stop = StopOnTokens()
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

        model_inputs = tokenizer.apply_chat_template(messages,
                                                    add_generation_prompt=True,
                                                    tokenize=True,
                                                    return_tensors="pt").to(next(model.parameters()).device)
        streamer = TextIteratorStreamer(tokenizer, timeout=60, skip_prompt=True, skip_special_tokens=True)
        generate_kwargs = {
            "input_ids": model_inputs,
            "streamer": streamer,
            "max_new_tokens": max_length,
            "do_sample": True,
            "top_p": top_p,
            "top_k": top_k,
            "repetition_penalty": repetition_penalty,
            "temperature": temperature,
            "stopping_criteria": StoppingCriteriaList([stop]),
        }

        print("ChatGLM3 -> generate_kwargs", generate_kwargs)

        thread = Thread(target=model.generate, kwargs=generate_kwargs)
        thread.start()
        for new_token in streamer:
            print("N", new_token, converter)
            _new_token = new_token is not None and (
                converter.convert(new_token) if converter is not None else new_token
            )
            
            # if (converter is not None):
            #     print("convert", converter, new_token, _new_token)
            
            if _new_token:
                history[-1][1] += _new_token

            answer_result = ChatGLM3AnswerResult()
            answer_result.history = history
            answer_result.new_token = _new_token
            yield answer_result



class StopOnTokens(StoppingCriteria):
    def __call__(self, input_ids: torch.LongTensor, scores: torch.FloatTensor, **kwargs) -> bool:
        stop_ids = [0, 2]
        for stop_id in stop_ids:
            if input_ids[0][-1] == stop_id:
                return True
        return False


