
from elasticsearch import Elasticsearch, logger, logging
from typing import Dict

from . import ConfigParams
from .DocumentUtils import DocumentUtils
from .ElasticSearchDao import DocInsert, DocUpdate, DocSearch, DocMigrate, DocGet, DocDelete
from .ElasticSearchDao.ESVo import ESVoDocSearch, ESVoDocInsert
from .ElasticSearchDao import _constants

import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

es_logger = logger
es_logger.setLevel(logging.DEBUG)

class ElasticSearchController:
    def __init__(self, embedding):

        # init Elastic
        self.es_client = Elasticsearch(
            hosts=[
                ConfigParams.host,
            ],
            basic_auth=(ConfigParams.username, ConfigParams.password),
            verify_certs=False,
        )

        self.embedding = embedding
        



    # Insert 
    @DeprecationWarning
    def doc_insert_text_data_strat_1(
        self, 
        voDocInsert: ESVoDocInsert,
    ):
        try:
            docs, ids, index_name = DocInsert.doc_insert_text_data_strat_1(
                DocumentUtils = DocumentUtils,
                embedding = self.embedding,
                es_client = self.es_client,
                voDocInsert = voDocInsert,
            )
            return docs, ids, index_name
        except Exception as e:
            print(e)
            raise e



    # doc_insert_text_data_strat_2 stores the text data by
    # page content, document header, and combination of (page content + document header)
    def doc_insert_text_data_strat_2(
        self, 
        voDocInsert: ESVoDocInsert,
    ):
        try:
            docs, ids, index_name = DocInsert.doc_insert_text_data_strat_2(
                DocumentUtils = DocumentUtils,
                embedding = self.embedding,
                es_client = self.es_client,
                voDocInsert = voDocInsert,
            )
            return docs, ids, index_name
        except Exception as e:
            print(e)
            raise e




    # Update
    def doc_update_document_metadata(
        self,
        index_name: str, 
        id: str,
        document_category: str,
        document_tags: list[str] = None,
        document_userdata = None,
    ):
        return DocUpdate.doc_update_document_metadata(
            es_client = self.es_client,
            index_name = index_name,
            id = id,
            document_category = document_category,
            document_tags = document_tags,
            document_userdata = document_userdata,
        )


    def doc_update_document_metadata_free(
        self,
        index_name, 
        id,
        metadata,
    ):
        return DocUpdate.doc_update_document_metadata_free(
            es_client = self.es_client,
            index_name = index_name,
            id = id,
            metadata = metadata,
        )






    # Get
    def doc_get_document_by_id(
        self,
        index_name: str, 
        id: str,
    ):
        try:
            return DocGet.doc_get_document_by_id(
                es_client=self.es_client,
                index_name=index_name,
                id=id,
            )
        
        except Exception as e:
            return None



    def doc_get_document_es_ids_by_document_file_id(
        self,
        index_name: str,
        document_file_id: str,
        data_strategy: str = _constants.DATA_STRATEGY_1,
    ):
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "metadata.document_file_id.keyword": document_file_id,
                            },
                        },
                        {
                            "term": {
                                "metadata.data_strategy.keyword": data_strategy,
                            },
                        },
                    ]
                }
            },
            "size": 10000,
        }

        response = DocSearch.doc_search_any_query(
            index_name=index_name, 
            query=query, 
            es_client=self.es_client)

        res_body = response.body
        res_body_hits_list = res_body["hits"]["hits"]

        result = []

        for i in res_body_hits_list:
            result.append(i["_id"])

        return result




    # Delete 

    def doc_delete_document_by_id(
        self,
        index_name: str, 
        id: str,
    ):
        try:
            return DocDelete.doc_delete_document_by_id(
                es_client=self.es_client,
                index_name=index_name,
                id=id,
            )
            
        except Exception as e:
            return None
        
        



    # Search 

    def doc_search_multi_vector(
        self, 
        voDocSearch: ESVoDocSearch,
    ):
        return DocSearch.doc_search_multi_vector(
            embedding=self.embedding,
            es_client=self.es_client,
            voDocSearch=voDocSearch,
        )








    # Migrate
    
    def doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
        self,
        index_name: str,
    ):
        return DocMigrate.doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
            es_client=self.es_client,
            index_name=index_name,
        )
        
        