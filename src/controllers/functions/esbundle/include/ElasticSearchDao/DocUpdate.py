


def doc_update_document_metadata(
    es_client,
    index_name, 
    id,
    document_category,
    document_tags,
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
    es_client,
    index_name, 
    id,
    metadata,
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
