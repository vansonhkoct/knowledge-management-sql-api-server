

from typing import Dict

class ElasticSearchQueryUtils:
    
    
    @staticmethod
    def default_knn_mapping(dims: int) -> Dict:
        """Generates a default index mapping for kNN search."""
        return {
            "properties": {
                "text": {"type": "text"},
                "vector": {
                    "type": "dense_vector",
                    "dims": dims,
                    "index": True,
                    "similarity": "cosine",
                },
            }
        }
    
    
    @staticmethod
    def generate_search_query(vec, size) -> Dict:
        query = {
            "query": {
                "script_score": {
                    "query": {
                        "match_all": {}
                    },
                    "script": {
                        "source": "cosineSimilarity(params.queryVector, 'vector') + 1.0",
                        "params": {
                            "queryVector": vec
                        }
                    }
                }
            },
            "size": size
        }
        return query
    
    
    @staticmethod
    def generate_knn_query(vec, size) -> Dict:
        query = {
            "knn": {
                "field": "vector",
                "query_vector": vec,
                "k": 10,
                "num_candidates": 100
            },
            "size": size
        }
        return query
    
    
    @staticmethod
    def generate_hybrid_query(text, vec, size, knn_boost, document_category) -> Dict:
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "metadata.document_category.keyword": document_category,
                            }
                        }
                    ],
                    "should": [
                        {
                            "match": {
                                "text": {
                                    "query": text,
                                    "boost": (1 - knn_boost) * 1.0,
                                }
                            }
                        },
                    ]
                }
            },
            
            "knn": {
                "field": "vector",
                "query_vector": vec,
                "k": 10,
                "num_candidates": 100,
                "boost": (knn_boost) * 1.0,
            },
            "size": size
        }
        return query
