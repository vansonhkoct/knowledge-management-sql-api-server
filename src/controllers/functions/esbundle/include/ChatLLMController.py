
from .ChatLLM import ChatLLM
from .ElasticSearchQueryUtils import ElasticSearchQueryUtils
import time
import opencc
converter = opencc.OpenCC('s2t.json')


llm: ChatLLM = None


def bot_initialize(config_params):
    llm = ChatLLM(config_params = config_params)
    llm.load_llm()



def llm_answer(prompt, history):
    try:
        for answer_result in llm.generator_answer(prompt=prompt, history=history, streaming=True):
            yield answer_result
    finally:
        print("End of llm_answer")
        pass




def bot_ask_question(
    index_name,
    question,
    es_controller = None,
    es_disabled = False,
    es_query_top_k=7,
    es_query_knn_boost=0.9,
    es_query_document_category = "",
    llm_max_token=8192,
    llm_temperature=0.01,
    llm_top_p=0.8,
    llm_history_len=3,
    llm_prompt_template=None,
    api_uid=None,
):
    timestamp = str(time.time_ns())

    def query_body_fn(question, top_k, knn_boost, document_category):
        def fn(query_vector):
            query_body = ElasticSearchQueryUtils.generate_hybrid_query(
                text=question, 
                vec=query_vector, 
                size=top_k, 
                knn_boost=knn_boost, 
                document_category=document_category,
            )
            return query_body
        return fn
    
    search_results = []
    
    
    
    if (not es_disabled):
        try:
            search_results = es_controller.doc_search_custom_query(
                index_name = index_name, 
                query = question,
                query_body_fn = query_body_fn(
                    question = question,
                    top_k = es_query_top_k,  # 0 ~ 10, integer
                    knn_boost = es_query_knn_boost,  # 0 ~ 1.0, float(step = 0.1)
                    document_category = es_query_document_category,
                ),
            )
        
        except Exception as e:
            print(f"Exception: {e}, Fallback result = []")
            search_results = []


        search_results = [result for result in search_results if result['score'] >= 1.2]

    
    informed_context = ''
    for i in search_results:
        informed_context += i['content'] + '\n'

    
    
    if llm_prompt_template == None:
        
        PROMPT_TEMPLATE = """已知信息：
        {context} 
        
        根据上述已知信息，简洁和专业的来回答用户的问题。如果无法从中得到答案，请说 “根据已知信息无法回答该问题” 或 “没有提供足够的相关信息”，不允许在答案中添加编造成分，答案请使用中文。 问题是：{question}"""

    else:
        
        PROMPT_TEMPLATE = llm_prompt_template

    

    prompt = PROMPT_TEMPLATE.replace("{question}", question).replace("{context}", informed_context)

    
    
    llm.max_token = llm_max_token             # 0 ~ 32768  (integer)
    llm.temperature = llm_temperature         # 0 ~ 1  (float, step = 0.01)
    llm.top_p = llm_top_p                     # 0 ~ 1  (float, step = 0.01)
    llm.history_len = llm_history_len         # 0 ~ 10 (integer)



    global history
    history = []
    
    answer_gen = llm_answer(
        prompt=prompt,
        history=history,
    )
    
    try:
        print("Start")

        active_llm_generators_vs_api_uids[api_uid] = answer_gen

        
        while True:
            answer_result = next(answer_gen)
            
            history = answer_result.history
            llm_output = answer_result.llm_output

            answer_result.llm_output["answer"] = converter.convert(
                answer_result.llm_output["answer"]
            )
            
            history[-1][0] = question
    
            print(f"llm_output: {answer_result.llm_output}")

            if api_uid is not None:

                dict = {}
                dict[timestamp] = answer_result.llm_output
                
                emit_to_uid(
                    "ai_response", 
                    dict,
                    uid = api_uid,
                )


    except StopIteration:
        print("Done")
        active_llm_generators_vs_api_uids[api_uid] = None
        pass

    answer_result_dict = {}
    answer_result_dict[timestamp] = answer_result.llm_output

    return {
        "answer_gen": answer_gen,
        "answer_result": answer_result_dict,
        "search_results": search_results,
    }



def bot_stop_answering(
    api_uid = None,
):
    global active_llm_generators_vs_api_uids

    if (
        api_uid is not None 
        and api_uid in active_llm_generators_vs_api_uids
        and active_llm_generators_vs_api_uids[api_uid] is not None
       ):
        
        active_llm_generators_vs_api_uids[api_uid].close()
    

