

from elasticsearch import Elasticsearch
from . import _constants


def doc_update_document_metadata(
    es_client: Elasticsearch,
    index_name: str, 
    id: str,
    document_category: str,
    document_tags: list[str] = None,
    document_userdata = None,
):
    _index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{index_name}"
    
    metadata_to_update = {}

    if document_category is not None:
        metadata_to_update["document_category"] = document_category
    if document_tags is not None:
        metadata_to_update["document_tags"] = document_tags
    if document_userdata is not None:
        metadata_to_update["document_userdata"] = document_userdata

    return es_client.update(
        index=_index_name,
        id=id,
        body={
            'doc': {
                'metadata': {
                    "document_category": document_category,
                    "document_tags": document_tags,
                    "document_userdata": document_userdata,
                }
            }
        }
    )


def doc_update_document_metadata_free(
    es_client: Elasticsearch,
    index_name: str, 
    id: str,
    metadata: dict,
):
    _index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{index_name}"

    return es_client.update(
        index=_index_name,
        id=id,
        body={
            'doc': {
                'metadata': metadata,
            }
        }
    )
