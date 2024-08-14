
from . import _constants
from elasticsearch import Elasticsearch

# Delete 

def doc_delete_document_by_id(
    es_client: Elasticsearch,
    index_name: str, 
    id: str,
):
    try:
        _index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{index_name}"
      
        return es_client.delete(
            index=_index_name,
            id=id,
        )
      
    except Exception as e:
        print(e)
        return None
