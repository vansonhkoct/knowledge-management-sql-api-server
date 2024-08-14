

from elasticsearch import Elasticsearch


def doc_update_document_metadata(
    es_client: Elasticsearch,
    index_name: str, 
    id: str,
    document_category: str,
    document_tags: list[str],
):
    return es_client.update(
        index=index_name,
        id=id,
        body={
            'doc': {
                'metadata': {
                    "document_category": document_category,
                    "document_tags": document_tags,
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
    return es_client.update(
        index=index_name,
        id=id,
        body={
            'doc': {
                'metadata': metadata,
            }
        }
    )
