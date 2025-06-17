
from .ChatGPTAPI import ChatGPTAPI, ChatGPTAPIAnswerResult
from .ChatLLMDao.LLMVo import LLMVoAskQuestion
from typing import Union
import time
import opencc
from . import ConfigParams
import pkg_resources
converter = opencc.OpenCC('s2t.json')


ChatModelInterface = Union[ChatGPTAPI]
ChatModelAnswerResult = Union[ChatGPTAPIAnswerResult]

class ChatLLMController:

    llm_collections: dict[str, ChatModelInterface] = {}

    active_llm_generators_vs_api_uids = {}

    def __init__(self):
        pass



    def _get_python_package_version(self, package_name):
        try:
            return pkg_resources.get_distribution(package_name).version
        except pkg_resources.DistributionNotFound:
            return None


    def _get_llm_model_name(
        self,
        llm_model_name: str = "chatgpt_api",
    ):
        if llm_model_name == "chatgpt_api":
            return "chatgpt_api"

        return llm_model_name



    def _get_llm_model_by_name(
        self,
        llm_model_name: str = "chatgpt_api",
    ):
        # TODO: now have to distinguish transformers version
        llm_model_name = self._get_llm_model_name(llm_model_name=llm_model_name)

        if llm_model_name not in self.llm_collections:
            if llm_model_name == "chatgpt_api":
                chatgpt_api = ChatGPTAPI()
                self.llm_collections[llm_model_name] = chatgpt_api
                
        
        return self.llm_collections[llm_model_name]
    
    

    def bot_ask_question(
        self, 
        voAskQuestion: LLMVoAskQuestion,
    ):
        timestamp = str(time.time_ns())
        
        llm_model_name = self._get_llm_model_name(voAskQuestion.llm_model_name)

        answer_gen = self._llm_generate_answer(
            prompt = voAskQuestion.prompt,
            history = voAskQuestion.history,
            llm_model_name = llm_model_name,
            llm_max_token = voAskQuestion.llm_max_token,
            llm_temperature = voAskQuestion.llm_temperature,
            llm_top_p = voAskQuestion.llm_top_p,
            llm_top_k = voAskQuestion.llm_top_k,
            llm_repetition_penalty = voAskQuestion.llm_repetition_penalty,
        )
        
        answer_result = self._llm_answering_loop(
            question = voAskQuestion.prompt,
            answer_generator = answer_gen,
            timestamp = timestamp,
            api_uid = voAskQuestion.api_uid,
            emit_to_uid = voAskQuestion.emit_to_uid,
        )

        answer_result_dict = {}
        answer_result_dict[timestamp] = answer_result.llm_output()

        return {
            "answer_gen": answer_gen,
            "answer_result": answer_result_dict,
        }



    def bot_stop_answering(
        self, 
        api_uid: str | None = None,
    ):
        if (
            api_uid is not None 
            and api_uid in self.active_llm_generators_vs_api_uids
            and self.active_llm_generators_vs_api_uids[api_uid] is not None
        ):
            
            self.active_llm_generators_vs_api_uids[api_uid].close()
        







    # private functions



    def _llm_generate_answer(
        self, 
        prompt, 
        history,
        llm_model_name: str,
        llm_max_token,
        llm_temperature,
        llm_top_p,
        llm_top_k,
        llm_repetition_penalty,
        ):
        try:
            for answer_result in self._get_llm_model_by_name(llm_model_name=llm_model_name).generator_answer(
                prompt=prompt, 
                history=history, 
                streaming=True,
                max_length = llm_max_token, 
                top_p = llm_top_p, 
                top_k = llm_top_k,
                repetition_penalty = llm_repetition_penalty,
                temperature = llm_temperature,
                converter = converter,
                ):
                yield answer_result
        except Exception as e:
            del self.llm_collections[llm_model_name]
            ConfigParams.llm_dbg("bot_ask_question", f"Cleaning LLM for Exception! {e}")
            raise e
        finally:
            ConfigParams.llm_dbg("bot_ask_question", "End of _llm_generate_answer")
            pass




    def _llm_answering_loop(self, question, answer_generator, timestamp, api_uid, emit_to_uid):

        answer_result: ChatModelAnswerResult = None

        try:
            ConfigParams.llm_dbg("bot_ask_question", "Start")

            self.active_llm_generators_vs_api_uids[api_uid] = answer_generator

            
            while True:
                answer_result = next(answer_generator)
                
                history = answer_result.history

                answer_result.llm_output()["answer"] = converter.convert(
                    answer_result.llm_output()["answer"]
                )
                
                history[-1][0] = question
        
                ConfigParams.llm_verbose("bot_ask_question", f"llm_output: {answer_result.llm_output()}")

                if api_uid is not None:

                    dict = {}
                    dict[timestamp] = answer_result.llm_output()
                    
                    if emit_to_uid is not None:
                        emit_to_uid(
                            "ai_response", 
                            dict,
                            uid = api_uid,
                        ) 



        except StopIteration:
            ConfigParams.llm_dbg("bot_ask_question", "Done")
            self.active_llm_generators_vs_api_uids[api_uid] = None
            pass

        return answer_result
