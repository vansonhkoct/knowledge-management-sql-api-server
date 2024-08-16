
from .include.pymupdf.pymupdf import extract_pdf_file_to_text, async_extract_pdf_file_to_text
from .include import ConfigParams
from .include.EmbeddingsBundle import EmbeddingsBundle
from .include.ElasticSearchController import ElasticSearchController
from .include.ChatLLMController import ChatLLMController
from .include.ElasticSearchDao.ESVo import ESVoDocSearch, ESVoDocInsert
from .include.ChatLLMDao.LLMVo import LLMVoAskQuestion


import asyncio


embedding_instance: EmbeddingsBundle = None
es_controller: ElasticSearchController = None
llm_controller: ChatLLMController = None

        
# Init ChatLLM Controller
def _bot_initialize_chatllm():

    global llm_controller

    llm_controller = llm_controller if llm_controller is not None else ChatLLMController()




# Init ElasticSearch
def _bot_initialize_es():

    global embedding_instance
    global es_controller
    
    embedding_instance = embedding_instance if embedding_instance is not None else EmbeddingsBundle(
        model_path = ConfigParams.embedding_model, 
        model_path_legacy = ConfigParams.embedding_model_legacy,
    )
    
    es_controller = es_controller if es_controller is not None else ElasticSearchController(
        embedding = embedding_instance, 
    )






# ES - Insert

async def bot_es_add_document(
    vo: ESVoDocInsert,
):
    _bot_initialize_es()
    
    def fn():
        docs, ids, index_name = es_controller.doc_insert_text_data_strat_2(
            voDocInsert=vo,
        )

        return docs, ids, index_name

    docs, ids, index_name = await asyncio.get_running_loop().run_in_executor(None, fn)
    return docs, ids, index_name





# ES - Update

async def bot_es_update_document_metadata(
    index_name, 
    id,
    document_category,
    document_tags,
):
    _bot_initialize_es()
    
    def fn():
        res = es_controller.doc_update_document_metadata(
            index_name = index_name,
            id = id,
            document_category=document_category,
            document_tags=document_tags,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res







# ES - Get

async def bot_es_get_document_by_id(
    index_name, 
    id,
):
    _bot_initialize_es()
    
    def fn():
        res = es_controller.doc_get_document_by_id(
            index_name = index_name,
            id = id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_get_document_es_ids_by_document_file_id(
    index_name,
    document_file_id,
    data_strategy,
):
    _bot_initialize_es()
    
    def fn():
        res = es_controller.doc_get_document_es_ids_by_document_file_id(
            index_name = index_name,
            document_file_id = document_file_id,
            data_strategy = data_strategy,
        )
        return res
    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res








# ES - Delete

async def bot_es_delete_document_by_id(
    index_name, 
    id,
):
    _bot_initialize_es()
    
    def fn():
        res = es_controller.doc_delete_document_by_id(
            index_name = index_name,
            id = id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res







# ES - Search

async def bot_es_search_multi_vector(
    vo: ESVoDocSearch,
):
    _bot_initialize_es()
    
    def fn():
        res = es_controller.doc_search_multi_vector(
            voDocSearch = vo,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res





# ES - Migrate

async def bot_es_doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
    index_name: str,
):
    _bot_initialize_es()
    
    def fn():
        res = es_controller.doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
            index_name=index_name,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res







# CHATLLM - ask question

async def bot_llm_ask_question(
    vo: LLMVoAskQuestion
):
    _bot_initialize_chatllm()
    
    def fn():
        res = llm_controller.bot_ask_question(
            voAskQuestion = vo,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res




# CHATLLM - stop answering

async def bot_llm_stop_answering(
    api_uid: str | None = None,
):
    _bot_initialize_chatllm()
    
    def fn():
        llm_controller.bot_stop_answering(
            api_uid = api_uid,
        )
        return True

    res = await asyncio.get_running_loop().run_in_executor(None, fn)



