
from .include.py_any2text_parser.pdf2text import extract_pdf_file_to_text, async_extract_pdf_file_to_text
from .include.ConfigParams import ConfigParams
from .include.ChatLLM import ChatLLMAnswerResult, ChatLLM
from .include.EmbeddingsBundle import EmbeddingsBundle
from .include.ElasticSearchController import ElasticSearchController
from .include.ElasticSearchQueryUtils import ElasticSearchQueryUtils
from .include.DocumentUtils import DocumentUtils


import asyncio


config_params: ConfigParams = ConfigParams()
llm: ChatLLM = None
history = []
embedding_instance: EmbeddingsBundle = None
es_controller: ElasticSearchController = None
active_llm_generators_vs_api_uids = {}

        
def bot_initialize_chatllm():

    # Init ChatLLM
    global llm

    llm = ChatLLM(config_params = config_params)
    llm.load_llm()
    


def bot_initialize_es():

    # Init ElasticSearch
    global embedding_instance
    global es_controller
    
    embedding_instance = EmbeddingsBundle(
        model_path = config_params.embedding_model, 
        model_path_legacy = config_params.embedding_model_legacy,
    )
    es_controller = ElasticSearchController(
        embedding = embedding_instance, 
        config_params = config_params,
    )




async def bot_es_add_document(
    index_name, 
    text_data,
    text,
    chunk_size = 300, 
    chunk_overlap = 10, 
    extra_metadata = {},
    is_testrun = False,
):
    def fn():
        docs, ids, _index_name = es_controller.doc_insert_text_data(
            index_name = index_name,
            text_data = text_data,
            text = text,
            chunk_size = chunk_size, 
            chunk_overlap = chunk_overlap,
            extra_metadata = extra_metadata,
            is_testrun = is_testrun,
        )

        return docs, ids, _index_name

    docs, ids, _index_name = await asyncio.get_running_loop().run_in_executor(None, fn)
    return docs, ids, _index_name




async def bot_es_add_document_testraw(
    index_name, 
    text_data,
    text,
    chunk_size = 300, 
    chunk_overlap = 10, 
    use_text_splitter = False,
    extra_metadata = {},
    is_testrun = False,
):
    def fn():
        docs, ids, _index_name = es_controller.doc_insert_text_data_textraw(
            index_name = index_name,
            text_data = text_data,
            text = text,
            chunk_size = chunk_size, 
            chunk_overlap = chunk_overlap,
            use_text_splitter = use_text_splitter,
            extra_metadata = extra_metadata,
            is_testrun = is_testrun,
        )

        return docs, ids, _index_name

    docs, ids, _index_name = await asyncio.get_running_loop().run_in_executor(None, fn)
    return docs, ids, _index_name




async def bot_es_update_document_metadata(
    index_name, 
    id,
    document_category,
    document_tags,
):
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


async def bot_es_get_document_by_id(
    index_name, 
    id,
):
    def fn():
        res = es_controller.doc_get_document_by_id(
            index_name = index_name,
            id = id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_delete_document_by_id(
    index_name, 
    id,
):
    def fn():
        res = es_controller.doc_delete_document_by_id(
            index_name = index_name,
            id = id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_delete_all_documents(
    index_name, 
):
    def fn():
        res = es_controller.delete_all_documents(
            index_name = index_name,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_search_by_document_file_name(
    index_name,
    document_file_name,
):
    def fn():
        res = es_controller.doc_search_by_document_file_name(
            index_name = index_name,
            document_file_name = document_file_name,
        )
        return res
    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_search_multi_vector_string_fields(
    index_name,
    query_strings,
    knn_boosts,
    document_category,
    k = 10,
    num_candidates = 100,
):
    def fn():
        res = es_controller.doc_search_multi_vector_string_fields(
            index_name = index_name,
            query_strings = query_strings, 
            knn_boosts = knn_boosts, 
            document_category = document_category,
            k = k,
            num_candidates = num_candidates,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res



async def bot_get_es_doc_ids_document_es_ids_by_document_file_id(
    index_name,
    document_file_id,
):
    def fn():
        res = es_controller.doc_get_document_es_ids_by_document_file_id(
            index_name = index_name,
            document_file_id = document_file_id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res



# Initialize
bot_initialize_es()

