
from .include.py_any2text_parser.pdf2text import extract_pdf_file_to_text
from .include.ConfigParams import ConfigParams
from .include.ChatLLM import ChatLLMAnswerResult, ChatLLM
from .include.EmbeddingsBundle import EmbeddingsBundle
from .include.ElasticSearchController import ElasticSearchController
from .include.ElasticSearchQueryUtils import ElasticSearchQueryUtils
from .include.DocumentUtils import DocumentUtils


import asyncio

class _SingleTon:
    def __init__(self):
      
        self.config_params = None
        self.llm = None
        self.history = []
        self.embedding_instance = None
        self.es_controller = None
        self.active_llm_generators_vs_api_uids = {}


        # Init config 
        self.config_params = ConfigParams()
        self.config_params.username = "elastic"
        self.config_params.password = "octopuspass"
        self.config_params.host = "https://octopus-tech.com:16899"
        # self.config_params.index_name = index_name # Any new index name means new database. e.g. "oct_index_6"

        # self.config_params.embedding_model = "all-MiniLM-L6-v2"
        self.config_params.embedding_model = "moka-ai/m3e-small"

        # GPU
        self.config_params.llm_model = "THUDM/chatglm2-6b"
        self.config_params.llm_model_gpu = True

        self.bot_initialize_es()

          
    def bot_initialize_chatllm(self):


        # Init ChatLLM

        self.llm = ChatLLM(config_params = self.config_params)
        self.llm.load_llm()
        


    def bot_initialize_es(self):

        # Init ElasticSearch
        
        self.embedding_instance = EmbeddingsBundle(model_path = self.config_params.embedding_model)
        self.es_controller = ElasticSearchController(embedding = self.embedding_instance)



    async def bot_es_add_index(
        self,
        index_name, 
    ):
        def fn(index_name):
            res = self.es_controller.doc_insert_index(
                index_name = index_name,
            )
            return res

        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(None, fn, index_name)
        return res


    async def bot_es_add_document(
        self,
        index_name, 
        text_data,
        text,
        chunk_size = 300, 
        chunk_overlap = 10, 
    ):
        def fn(
            index_name,
            text_data,
            text,
            chunk_size = 300, 
            chunk_overlap = 10, 
            ):
            
            docs, ids = self.es_controller.doc_insert_text_data(
                index_name = index_name,
                text_data = text_data,
                text = text,
                chunk_size = chunk_size, 
                chunk_overlap = chunk_overlap,
            )

            return docs, ids

        loop = asyncio.get_running_loop()
        docs, ids = await loop.run_in_executor(
            None,
            fn,
            index_name,
            text_data,
            text,
            chunk_size,
            chunk_overlap,
            )
        
        return docs, ids



    async def bot_es_update_document_metadata(
        self,
        index_name, 
        id,
        document_category,
    ):
        def fn(
            index_name, 
            id, 
            document_category,
            ):
            res = self.es_controller.doc_update_document_metadata(
                index_name = index_name,
                id = id,
                document_category=document_category,
            )
            return res

        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(
            None, 
            fn, 
            index_name, 
            id, 
            document_category,
            )
        return res


    async def bot_es_get_document_by_id(
        self,
        index_name, 
        id,
    ):
        def fn(
            index_name, 
            id, 
            ):
            res = self.es_controller.doc_get_document_by_id(
                index_name = index_name,
                id = id,
            )
            return res

        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(
            None, 
            fn,
            index_name, 
            id, 
            )
        return res


    async def bot_es_delete_document_by_id(
        self,
        index_name, 
        id,
    ):
        def fn(
            index_name, 
            id, 
            ):
            res = self.es_controller.doc_delete_document_by_id(
                index_name = index_name,
                id = id,
            )
            return res

        loop = asyncio.get_running_loop()
        res = await loop.run_in_executor(
            None, 
            fn, 
            index_name, 
            id, 
            )
        return res



ESChatLLM = _SingleTon()


