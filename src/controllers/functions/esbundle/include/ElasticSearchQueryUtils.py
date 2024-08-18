
from . import ConfigParams
from .EmbeddingsBundle import EmbeddingsBundle
from typing import Dict
from .ElasticSearchDao.ESVo import ESVoDocSearch
from .ElasticSearchDao import _constants


class ESChatLLMSearchException(Exception):
    def __init__(
        self,
        status_code: str,
        detail: str | None = None,
    ) -> None:
        self.status_code = status_code
        self.detail = detail

    def __str__(self) -> str:
        return f"{self.status_code}: {self.detail}"

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        return f"{class_name}(status_code={self.status_code!r}, detail={self.detail!r})"




def generate_multi_vector_knn(
    embedding: EmbeddingsBundle,
    voDocSearch: ESVoDocSearch,
    ) -> Dict:
    """
    Performs a multi-vector field KNN query in Elasticsearch with additional term query criteria.
    
    Args:
        index_name (str): The name of the Elasticsearch index to search.
        query_vectors (dict): A dictionary containing the query vectors for each vector field.
            The keys should be the field names, and the values should be the vector values.
        knn_boosts (dict, optional): A dictionary containing the KNN boost values for each vector field.
            The keys should be the field names, and the values should be the boost values.
        document_category (str, optional): The document category to filter the search results.
        k (int): Specifies the number of nearest neighbors (k) to retrieve in the search results.
        num_candidates (int): Specifies the number of candidate documents to consider when performing the KNN search.
    
    Returns:
        dict: Elasticsearch Query
    """
    
    
    ConfigParams.es_dbg("[ElasticSearchQueryUtils] question", voDocSearch.question)
    ConfigParams.es_dbg("[ElasticSearchQueryUtils] query strings:", voDocSearch.query_strings)
    ConfigParams.es_dbg("[ElasticSearchQueryUtils] query vectors:", voDocSearch.query_vectors)
    
    
    
    
    if voDocSearch.query_vectors is None:
        if voDocSearch.query_strings is None:
            if voDocSearch.question is None:
                raise ESChatLLMSearchException(status_code="ESQU0001", detail="All missing: question, query_strings, query_vectors")



    embedding_function = None
    
    if voDocSearch.is_search_strategy_2():
        embedding_function = embedding.embed_query
    else:
        embedding_function = embedding.embed_query_legacy


    if voDocSearch.knn_boosts is None:
        voDocSearch.knn_boosts = {}



    query_texts = {}

    if voDocSearch.query_vectors is None:
        if voDocSearch.query_strings is None:
            
            query_strings = {}
            
            if voDocSearch.is_search_strategy_2():
                
                if voDocSearch.data_vector_query_strategy == 4:
                    
                    if voDocSearch.data_portion_type == "PAGE":

                        query_texts["page_content"] = voDocSearch.question
                        voDocSearch.knn_boosts["page_content"] = 0.03
                        
                        query_texts["document_header"] = voDocSearch.question
                        voDocSearch.knn_boosts["document_header"] = 0.018
                    
                    elif voDocSearch.data_portion_type == "CHUNK990":

                        query_texts["page_content"] = voDocSearch.question
                        voDocSearch.knn_boosts["page_content"] = 0.04
                        
                        query_texts["document_header"] = voDocSearch.question
                        voDocSearch.knn_boosts["document_header"] = 0.02
                    
                    else:

                        query_texts["page_content"] = voDocSearch.question
                        voDocSearch.knn_boosts["page_content"] = 0.07
                        
                        query_texts["document_header"] = voDocSearch.question
                        voDocSearch.knn_boosts["document_header"] = 0.03

                    query_strings["page_content_w_header_vector"] = voDocSearch.question
                    voDocSearch.knn_boosts["page_content_w_header_vector"] = 1.0
                    
                else:
                    query_strings["page_content_w_header_vector"] = voDocSearch.question
                    voDocSearch.knn_boosts["page_content_w_header_vector"] = 1.0
                # if voDocSearch.data_vector_query_strategy == 2:
                #     query_strings["page_content_vector"] = voDocSearch.question
                #     voDocSearch.knn_boosts["page_content_vector"] = 1.0

                # elif voDocSearch.data_vector_query_strategy == 3:

                # else:
                #     query_strings["page_content_vector"] = voDocSearch.question
                #     query_strings["document_header_vector"] = voDocSearch.question
                #     voDocSearch.knn_boosts["page_content_vector"] = 0.96
                #     voDocSearch.knn_boosts["document_header_vector"] = 0.04

            else:
                query_strings["vector"] = voDocSearch.question
                voDocSearch.knn_boosts["vector"] = 1.0
        
            voDocSearch.query_strings = query_strings

        
        query_vectors = {}
        for field_name, field_string in voDocSearch.query_strings.items():
            query_vectors[field_name] = embedding_function(field_string)
        
        voDocSearch.query_vectors = query_vectors
    

    
    
    print("Emergency debug", voDocSearch.data_vector_query_strategy, query_strings, query_texts, voDocSearch.knn_boosts)
    
    query = {}
    
    query["knn"] = [
        {
            "field": field_name,
            "query_vector": list(field_vector),
            "k": voDocSearch.k,
            "num_candidates": voDocSearch.num_candidates,
            "boost": voDocSearch.knn_boosts.get(field_name, 1.0),
        } for field_name, field_vector in voDocSearch.query_vectors.items()
    ]
    
    query["size"] = voDocSearch.k
    
    
    
    qbool = {}


    
    if (len(query_texts.keys()) > 0):
        qbool["should"] = [] if "should" not in qbool else qbool["should"]
        
        for field_name, field_text in query_texts.items():
            qbool["should"].append({
                "match": {
                    field_name: {
                        "query": field_text,
                        "boost": voDocSearch.knn_boosts.get(field_name, 1.0)
                    }
                }
            })
    


    if voDocSearch.is_search_strategy_2():
        qbool["must"] = [] if "must" not in qbool else qbool["must"]
        qbool["must"].append({
            "term": {
                "metadata.data_strategy.keyword": "2",
            }
        })
        
        if voDocSearch.has_search_portion_type():
            qbool["must"] = [] if "must" not in qbool else qbool["must"]
            qbool["must"].append({
                "term": {
                    "metadata.data_portion_type.keyword": voDocSearch.get_search_portion_type(),
                }
            })
            
    else:
        qbool["must"] = [] if "must" not in qbool else qbool["must"]
        qbool["must"].append({
            "term": {
                "metadata.data_strategy.keyword": "1",
            }
        })





    
    if (voDocSearch.must_match_document_category):
        qbool["must"] = [] if "must" not in qbool else qbool["must"]
        qbool["must"].append({
            "term": {
                "metadata.document_category.keyword": voDocSearch.document_category
            }
        })
    
    if (voDocSearch.document_file_ids is not None and len(voDocSearch.document_file_ids) > 0):
        qbool["must"] = [] if "must" not in qbool else qbool["must"]
        qbool["must"].append({
            "terms": {
                "metadata.document_file_id.keyword": voDocSearch.document_file_ids
            }
        })

    if (voDocSearch.should_match_document_tags > 0):
        qbool["should"] = [] if "should" not in qbool else qbool["should"]
        qbool["should"].append({
            "match": {
                "text": {
                    "query": voDocSearch.question,
                    "boost": voDocSearch.should_match_document_tags,
                }
            }
        })
    
    if (voDocSearch.should_match_document_title > 0):
        qbool["should"] = [] if "should" not in qbool else qbool["should"]
        qbool["should"].append({
            "match": {
                "text": {
                    "query": voDocSearch.question,
                    "boost": voDocSearch.should_match_document_title,
                }
            }
        })
    
    if (voDocSearch.should_match_document_summary > 0):
        qbool["should"] = [] if "should" not in qbool else qbool["should"]
        qbool["should"].append({
            "match": {
                "text": {
                    "query": voDocSearch.question,
                    "boost": voDocSearch.should_match_document_summary,
                }
            }
        })
    
    if (voDocSearch.should_match_document_text > 0):
        qbool["should"] = [] if "should" not in qbool else qbool["should"]
        qbool["should"].append({
            "match": {
                "text": {
                    "query": voDocSearch.question,
                    "boost": voDocSearch.should_match_document_text,
                }
            }
        })

    
    if (len(qbool) > 0):
        query["query"] = {} if "query" not in query else query["query"]
        query["query"]["bool"] = qbool

    # Expected format: Build the multi-vector field KNN query
    # query = {
    #     "query": {
    #         "bool": {
    #             "must": [
    #                 {
    #                     "term": {
    #                         "metadata.document_category.keyword": voDocSearch.document_category
    #                     }
    #                 }
    #             ]
    #         }
    #     },
    #     "knn": [
    #         {
    #             "field": field_name,
    #             "query_vector": list(field_vector),
    #             "k": voDocSearch.k,
    #             "num_candidates": voDocSearch.num_candidates,
    #             "boost": voDocSearch.knn_boosts.get(field_name, 1.0),
    #         } for field_name, field_vector in voDocSearch.query_vectors.items()
    #     ],
    #     "size": voDocSearch.k,
    # }
    
    ConfigParams.es_verb("[ElasticSearchQueryUtils] resulting query dict:", query)
    
    
    possible_max_score = 0
    
    for field_name, field_vector in voDocSearch.query_vectors.items():
        possible_max_score += voDocSearch.knn_boosts.get(field_name, 1.0)

    possible_max_score += voDocSearch.should_match_document_tags
    possible_max_score += voDocSearch.should_match_document_title
    possible_max_score += voDocSearch.should_match_document_summary
    possible_max_score += voDocSearch.should_match_document_text

    return query, possible_max_score





