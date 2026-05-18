
from elasticsearch import Elasticsearch
from .. import EmbeddingsBundle
from .. import ElasticSearchQueryUtils
from . import _constants
from .ESVo import ESVoDocSearch



def doc_search_multi_vector(
    embedding: EmbeddingsBundle,
    es_client: Elasticsearch,
    voDocSearch: ESVoDocSearch):
    
    result = []

    query_body, possible_max_score = ElasticSearchQueryUtils.generate_multi_vector_knn(
        embedding = embedding,
        voDocSearch = voDocSearch,
    )
    
    index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{voDocSearch.index_name}"
    
    # Run query
    response = es_client.search(index=index_name, body=query_body)
    

    # Extract hits
    res_body = response.body
    res_body_hits_total_stats = res_body["hits"]["total"]
    res_body_hits_max_score = res_body["hits"]["max_score"]
    res_body_hits_list = res_body["hits"]["hits"]

    for i in res_body_hits_list:
        result.append({
            'total': res_body_hits_total_stats,
            'possible_max_score': possible_max_score,
            'record_max_score': res_body_hits_max_score,
            'score': i['_score'],
            'header': (
                i['_source']['document_header'] if 'document_header' in i['_source'] else ""
            ),
            'content': (
                i['_source']['page_content'] if 'page_content' in i['_source'] else
                i['_source']['text'] if 'text' in i['_source'] else ""
            ),
            'metadata': (
                i['_source']['metadata'] if 'metadata' in i['_source'] else {}
            ),
            'file_id': (
                i['_source']['metadata']['document_file_id'] if 'metadata' in i['_source'] and 'document_file_id' in i['_source']['metadata'] else ""
            ),
        })

    return result
    



def doc_search_any_query(
    index_name: str,
    query: dict,
    es_client: Elasticsearch):
    
    _index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{index_name}"
    
    response = es_client.search(index=_index_name, body=query)
    return response
    


