
from . import _constants
from elasticsearch import Elasticsearch


# Get
def doc_get_document_by_id(
    es_client: Elasticsearch,
    index_name: str, 
    id: str,
):
    try:
        _index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{index_name}"
  
        result = es_client.get(
            index=_index_name,
            id=id,
        )

        doc = result['_source']
        return doc
    
    except Exception as e:
        print(e)
        return None

