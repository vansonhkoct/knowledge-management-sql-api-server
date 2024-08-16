
from .ChatLLM import ChatLLM, ChatLLMAnswerResult
from .ChatLLMDao.LLMVo import LLMVoAskQuestion
import time
import opencc
from . import ConfigParams
converter = opencc.OpenCC('s2t.json')



class ChatLLMController:

    llm: ChatLLM = None

    active_llm_generators_vs_api_uids = {}
    history = []

    def __init__(self):
        self.llm = ChatLLM(config_params = ConfigParams)
        self.llm.load_llm()


    def bot_ask_question(
        self, 
        voAskQuestion: LLMVoAskQuestion,
    ):
        timestamp = str(time.time_ns())

        prompt = voAskQuestion.prompt

        self._apply_llm_params(
            llm_max_token = voAskQuestion.llm_max_token,
            llm_temperature = voAskQuestion.llm_temperature,
            llm_top_p = voAskQuestion.llm_top_p,
            llm_history_len = voAskQuestion.llm_history_len,
        )


        # VANTODO: does not support history at the moment
        self._clear_history()
        
        
        answer_gen = self._llm_generate_answer(
            prompt=prompt,
            history=[],
        )
        
        answer_result = self._llm_answering_loop(
            question = prompt,
            answer_generator = answer_gen,
            timestamp = timestamp,
            api_uid=voAskQuestion.api_uid,
            emit_to_uid=voAskQuestion.emit_to_uid,
        )

        answer_result_dict = {}
        answer_result_dict[timestamp] = answer_result.llm_output

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





    def _apply_llm_params(
        self, 
        llm_max_token=8192,
        llm_temperature=0.01,
        llm_top_p=0.8,
        llm_history_len=3,
    ):
        self.llm.max_token = llm_max_token             # 0 ~ 32768  (integer)
        self.llm.temperature = llm_temperature         # 0 ~ 1  (float, step = 0.01)
        self.llm.top_p = llm_top_p                     # 0 ~ 1  (float, step = 0.01)
        self.llm.history_len = llm_history_len         # 0 ~ 10 (integer)


    def _clear_history(self):
        self.history = []
        




    def _llm_generate_answer(self, prompt, history):
        try:
            for answer_result in self.llm.generator_answer(prompt=prompt, history=history, streaming=True):
                yield answer_result
        finally:
            ConfigParams.llm_dbg("bot_ask_question", "End of _llm_generate_answer")
            pass




    def _llm_answering_loop(self, question, answer_generator, timestamp, api_uid, emit_to_uid):

        answer_result: ChatLLMAnswerResult = None

        try:
            ConfigParams.llm_dbg("bot_ask_question", "Start")

            self.active_llm_generators_vs_api_uids[api_uid] = answer_generator

            
            while True:
                answer_result = next(answer_generator)
                
                history = answer_result.history

                answer_result.llm_output["answer"] = converter.convert(
                    answer_result.llm_output["answer"]
                )
                
                history[-1][0] = question
        
                ConfigParams.llm_dbg("bot_ask_question", f"llm_output: {answer_result.llm_output}")

                if api_uid is not None:

                    dict = {}
                    dict[timestamp] = answer_result.llm_output
                    
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
