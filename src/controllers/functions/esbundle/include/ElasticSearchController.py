
from elasticsearch import Elasticsearch
from langchain.vectorstores import ElasticsearchStore
from langchain.vectorstores import ElasticKnnSearch
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from typing import Dict

from .ConfigParams import ConfigParams
from .DocumentUtils import DocumentUtils
from .ElasticSearchQueryUtils import ElasticSearchQueryUtils


class ElasticSearchController:
    def __init__(self, embedding):
        
        self.config_params = ConfigParams()

        # init Elastic
        self.es_client = Elasticsearch(
            hosts=[
                self.config_params.host,
            ],
            basic_auth=(self.config_params.username, self.config_params.password),
            verify_certs=False,
        )

        self.embedding = embedding
        

    def doc_insert_text_data(self, index_name, text_data, text, chunk_size, chunk_overlap):
        try:
            es = ElasticsearchStore(
                index_name=index_name, 
                embedding=self.embedding,
                es_connection=self.es_client,
            )
    
            text_data, updated_text = DocumentUtils.parse_text(
                text_data, text
            )

            # load txt file as Langchain Document chunks
            docs = DocumentUtils.load_oc_text(updated_text, chunk_size, chunk_overlap)

            # add Langchain Document chunks to ElasticSearch instance
            ids = es.add_documents(docs)
            
            return docs, ids
        except Exception as e:
            raise e


    def doc_update_document_metadata(
        self,
        index_name, 
        id,
        document_category,
    ):
        return self.es_client.update(
            index=index_name,
            id=id,
            body={
                'doc': {
                    'metadata': {
                        "document_category": document_category,
                    }
                }
            }
        )


    def doc_get_document_by_id(
        self,
        index_name, 
        id,
    ):
        try:
            result = self.es_client.get(
                index=index_name,
                id=id,
            )

            doc = result['_source']
            return doc
        
        except Exception as e:
            return None


    def doc_delete_document_by_id(
        self,
        index_name, 
        id,
    ):
        return self.es_client.delete(
            index=index_name,
            id=id,
        )

    def doc_search(self, index_name, method, query, top_k, knn_boost, document_category):
        result = []

        # use `embedding model` to convert `question` to embedding vector units
        query_vector = self.embedding.embed_query(query)

        # pick 1 method to prepare ES vector query
        if method == "knn":
            query_body = ElasticSearchQueryUtils.generate_knn_query(vec=query_vector, size=top_k)
        elif method == "hybrid":
            query_body = ElasticSearchQueryUtils.generate_hybrid_query(text=query, vec=query_vector, size=top_k, knn_boost=knn_boost, document_category=document_category)
        else:
            query_body = ElasticSearchQueryUtils.generate_search_query(vec=query_vector, size=top_k)

        # Run query
        response = self.es_client.search(index=index_name, body=query_body)

        # Extract hits
        hits = [hit for hit in response["hits"]["hits"]]
        for i in hits:
            result.append({
                'content': i['_source']['text'],
                'metadata': i['_source']['metadata'],
                'score': i['_score'],
            })
            
        return result


    def doc_search_custom_query(self, index_name, query, query_body_fn):
        result = []

        # use `embedding model` to convert `question` to embedding vector units
        query_vector = self.embedding.embed_query(query)

        # pick 1 method to prepare ES vector query
        query_body = query_body_fn(query_vector)

        # Run query
        response = self.es_client.search(index=index_name, body=query_body)

        # Extract hits
        hits = [hit for hit in response["hits"]["hits"]]
        for i in hits:
            result.append({
                'content': i['_source']['text'],
                'metadata': i['_source']['metadata'],
                'score': i['_score'],
            })
            
        return result
        
    def doc_search_simple_query(self, index_name, query_body):
        response = self.es_client.search(index=index_name, body=query_body)
        return response


    def index_get_mapping(self, index_name):
        res = self.es_client.indices.get_mapping(index=index_name)
        return res

    def index_get_settings(self, index_name):
        res = self.es_client.indices.get_settings(index=index_name)
        return res


    def index_put_mapping(self, index_name, body):
        self.es_client.indices.put_mapping(
            index=index_name,
            body = body,
        )


