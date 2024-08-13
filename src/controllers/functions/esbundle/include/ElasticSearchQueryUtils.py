

from typing import Dict

class ElasticSearchQueryUtils:

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

    
    @staticmethod
    def generate_multi_vector_knn(
        query_vectors: dict, 
        knn_boosts: dict = None, 
        document_category: str = None, 
        k: int = 10,
        num_candidates: int = 100,
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
        
        # Build the multi-vector field KNN query
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "metadata.document_category.keyword": document_category
                            }
                        }
                    ]
                }
            },
            "knn": [
                {
                    "field": field_name,
                    "query_vector": list(field_vector),
                    "k": k,
                    "num_candidates": num_candidates,
                    "boost": knn_boosts.get(field_name, 1.0),
                } for field_name, field_vector in query_vectors.items()
            ],
            "size": k,
        }
        return query



    @staticmethod
    def generate_multi_vector_knn_by_query_string_fields(
        embedding_function,
        query_strings: dict, 
        knn_boosts: dict = None, 
        document_category: str = None, 
        k: int = 10,
        num_candidates: int = 100,
        ) -> Dict:
        """
        Performs a multi-vector field KNN query in Elasticsearch with additional term query criteria.
        
        Args:
            index_name (str): The name of the Elasticsearch index to search.
            query_strings (dict): A dictionary containing the query strings for each vector field.
                The keys should be the field names, and the values should be the string values.
                They will be converted to vector values & passed to `generate_multi_vector_knn`.
            knn_boosts (dict, optional): A dictionary containing the KNN boost values for each vector field.
                The keys should be the field names, and the values should be the boost values.
            document_category (str, optional): The document category to filter the search results.
            k (int): Specifies the number of nearest neighbors (k) to retrieve in the search results.
            num_candidates (int): Specifies the number of candidate documents to consider when performing the KNN search.
        
        Returns:
            dict: Elasticsearch Query
        """
        
        print(query_strings)
        
        query_vectors = {}
        for field_name, field_string in query_strings.items():
            query_vectors[field_name] = embedding_function(field_string)
        
        return ElasticSearchQueryUtils.generate_multi_vector_knn(
            query_vectors = query_vectors,
            knn_boosts = knn_boosts,
            document_category = document_category,
            k = k,
            num_candidates = num_candidates,
        )
