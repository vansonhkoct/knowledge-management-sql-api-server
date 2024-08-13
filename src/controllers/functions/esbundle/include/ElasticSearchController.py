
from elasticsearch import Elasticsearch, logger, logging
from langchain.vectorstores import ElasticsearchStore
from langchain.vectorstores import ElasticKnnSearch
from langchain.document_loaders import TextLoader
from langchain.text_splitter import CharacterTextSplitter
from typing import Dict

from .ConfigParams import ConfigParams
from .DocumentUtils import DocumentUtils
from .ElasticSearchQueryUtils import ElasticSearchQueryUtils
from .ElasticSearchDao import DocInsert, DocUpdate

es_logger = logger
es_logger.setLevel(logging.DEBUG)

class ElasticSearchController:
    def __init__(self, embedding, config_params: ConfigParams):
        
        self.config_params = config_params

        # init Elastic
        self.es_client = Elasticsearch(
            hosts=[
                self.config_params.host,
            ],
            basic_auth=(self.config_params.username, self.config_params.password),
            verify_certs=False,
        )

        self.embedding = embedding
        

    def doc_insert_text_data_legacy(
        self, 
        index_name, 
        text_data, 
        text, 
        chunk_size, 
        chunk_overlap, 
        extra_metadata,
        is_testrun,
        ):
        try:
            docs = DocInsert.doc_insert_text_data_legacy(
                DocumentUtils = DocumentUtils,
                embedding = self.embedding,
                es_client = self.es_client,
                index_name = index_name, 
                text_data = text_data, 
                text = text, 
                chunk_size = chunk_size, 
                chunk_overlap = chunk_overlap, 
                extra_metadata = extra_metadata,
                is_testrun = is_testrun,
            )
            return docs
        except Exception as e:
            print(e)
            raise e



    # doc_insert_text_data_strat_20240812 stores the text data by
    # page content, document header, and combination of (page content + document header)
    def doc_insert_text_data_strat_20240812(
        self, 
        index_name, 
        text_data, 
        text, 
        chunk_size,
        chunk_overlap,
        extra_metadata,
        is_testrun,
        ):
        try:
            docs = DocInsert.doc_insert_text_data_strat_20240812(
                DocumentUtils = DocumentUtils,
                embedding = self.embedding,
                es_client = self.es_client,
                index_name = index_name, 
                text_data = text_data, 
                text = text, 
                chunk_size = chunk_size, 
                chunk_overlap = chunk_overlap, 
                extra_metadata = extra_metadata,
                is_testrun = is_testrun,
            )
            return docs
        except Exception as e:
            print(e)
            raise e




    def doc_update_document_metadata(
        self,
        index_name, 
        id,
        document_category,
        document_tags,
    ):
        return DocUpdate.doc_update_document_metadata(
            es_client = self.es_client,
            index_name = index_name,
            id = id,
            document_category = document_category,
            document_tags = document_tags,
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



    def doc_get_document_es_ids_by_document_file_id(
        self,
        index_name,
        document_file_id,
    ):
        query = {
           "query": {
                "term": {
                    "metadata.document_file_id.keyword": document_file_id,
                },
            },
        }

        response = self.es_client.search(index=index_name, body=query)
        res_body = response.body
        res_body_hits_list = res_body["hits"]["hits"]

        result = []

        for i in res_body_hits_list:
            result.append(i["_id"])

        return result





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
    
    
    def doc_search_multi_vector_string_fields(self, index_name, query_strings, knn_boosts, document_category, k, num_candidates):
        result = []

        embedding_function = (
            self.embedding.embed_query if (str(index_name).startswith("t20240812_a_mbase_"))
            else self.embedding.embed_query_legacy
        )

        query_body = ElasticSearchQueryUtils.generate_multi_vector_knn_by_query_string_fields(
            embedding_function=embedding_function,
            query_strings=query_strings,
            knn_boosts=knn_boosts,
            document_category=document_category,
            k=k,
            num_candidates=num_candidates,
        )
        
        # Run query
        response = self.es_client.search(index=index_name, body=query_body)
        

        # Extract hits
        res_body = response.body
        res_body_hits_total_stats = res_body["hits"]["total"]
        res_body_hits_max_score = res_body["hits"]["max_score"]
        res_body_hits_list = res_body["hits"]["hits"]

        if (str(index_name).startswith("t20240812_a_mbase_")):
            for i in res_body_hits_list:
                result.append({
                    'score': i['_score'],
                    'header': i['_source']['document_header'],
                    'content': i['_source']['page_content'],
                    'metadata': i['_source']['metadata'],
                })
        else:
            for i in res_body_hits_list:
                result.append({
                    'score': i['_score'],
                    'content': i['_source']['text'],
                    'metadata': i['_source']['metadata'],
                })
            
        return result
        





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



    def delete_all_documents(self, index_name):
        """
        Deletes all documents inside the specified Elasticsearch index.
        """

        try:
            # Get the total number of documents in the index
            total_docs = self.es_client.count(index=index_name)['count']
            print(f"Total documents in '{index_name}' index: {total_docs}")

            # Delete all documents in batches of 1000
            batch_size = 1000
            num_batches = (total_docs + batch_size - 1) // batch_size

            for batch_num in range(num_batches):
                start = batch_num * batch_size
                end = min((batch_num + 1) * batch_size, total_docs)
                print(f"Deleting documents {start} to {end-1} in batch {batch_num+1}/{num_batches}")

                # Use the `delete_by_query` API to delete the documents in batches
                self.es_client.delete_by_query(
                    index=index_name,
                    body={
                        "query": {
                            "match_all": {}
                        }
                    },
                    size=batch_size,
                    from_=start
                )

            print(f"All documents in '{index_name}' index have been deleted.")
        except Exception as e:
            print(f"Error deleting documents: {e}")