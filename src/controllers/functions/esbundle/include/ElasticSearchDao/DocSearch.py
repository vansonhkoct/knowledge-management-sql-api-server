
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
        query_strings = voDocSearch.query_strings,
        knn_boosts = voDocSearch.knn_boosts,
        document_category = voDocSearch.document_category,
        k = voDocSearch.k,
        num_candidates = voDocSearch.num_candidates,
    )
    
    # Run query
    response = es_client.search(index=voDocSearch.index_name, body=query_body)
    

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
    


