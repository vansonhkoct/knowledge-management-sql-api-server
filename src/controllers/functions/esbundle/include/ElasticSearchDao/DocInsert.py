
from elasticsearch import Elasticsearch
from .. import EmbeddingsBundle
from .. import DocumentUtils
from . import _constants
from .ESVo import ESVoDocInsert

def doc_insert_text_data_strat_1(
    DocumentUtils: DocumentUtils,
    embedding: EmbeddingsBundle,
    es_client: Elasticsearch,
    voDocInsert: ESVoDocInsert,
    ):
    try:
        updated_text = DocumentUtils.parse_text(
            voDocInsert.text_data, 
            voDocInsert.text,
        )

        # load txt file as Langchain Document chunks
        docs = DocumentUtils.load_oc_text(updated_text, voDocInsert.chunk_size, voDocInsert.chunk_overlap, 
                                          extra_metadata={
                                              **voDocInsert.extra_metadata,
                                              "data_strategy": _constants.DATA_STRATEGY_1,
                                              "data_portion_type": _constants.DATA_PORTION_TYPE_CHUNK,
                                          })

        # add Langchain Document chunks to ElasticSearch instance
        ids = []
        
        index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{voDocInsert.index_name}"
        
        if not voDocInsert.is_testrun:
            for doc in docs:

                text = doc.page_content
                vector = embedding.embed_query(text)
                metadata = doc.metadata,

                objApiResponse = es_client.index(
                    index=index_name,
                    body={
                        "text": text,
                        "vector": vector,
                        "metadata": metadata,
                    },
                )
                ids.append(objApiResponse["_id"])

        return docs, ids, index_name
    except Exception as e:
        print(e)
        raise e



# doc_insert_text_data_strat_20240812 stores the text data by
# page content, document header, and combination of (page content + document header)
def doc_insert_text_data_strat_2(
    DocumentUtils: DocumentUtils,
    embedding: EmbeddingsBundle,
    es_client: Elasticsearch,
    voDocInsert: ESVoDocInsert,
    ):
    try:
        
        updated_text = DocumentUtils.parse_text(
            voDocInsert.text,
        )

        # load txt file as Langchain Document chunks
        print("processing docs_by_chunk...")
        docs_by_chunk = DocumentUtils.load_oc_text(updated_text,
                                          voDocInsert.chunk_size, voDocInsert.chunk_overlap, 
                                          use_text_splitter=True,
                                          extra_metadata={
                                              **voDocInsert.extra_metadata,
                                              "data_strategy": _constants.DATA_STRATEGY_2,
                                              "data_portion_type": _constants.DATA_PORTION_TYPE_CHUNK,
                                          })

        # load txt file as Langchain Document pages
        print("processing docs_by_page...")
        docs_by_page = DocumentUtils.load_oc_text(updated_text,
                                          use_text_splitter=False,
                                          extra_metadata={
                                              **voDocInsert.extra_metadata,
                                              "data_strategy": _constants.DATA_STRATEGY_2,
                                              "data_portion_type": _constants.DATA_PORTION_TYPE_PAGE,
                                          })

        index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{voDocInsert.index_name}"

        ids_by_chunk = []
        ids_by_page = []

        if not voDocInsert.is_testrun:
            
            document_header_candidates = []
            if ("document_remarks" in docs_by_page[0].metadata and docs_by_page[0].metadata["document_remarks"] is not None):
                document_header_candidates.append(docs_by_page[0].metadata["document_remarks"])
            if ("document_title" in docs_by_page[0].metadata and docs_by_page[0].metadata["document_title"] is not None):
                document_header_candidates.append(docs_by_page[0].metadata["document_title"])
            if ("document_summary" in docs_by_page[0].metadata and docs_by_page[0].metadata["document_summary"] is not None):
                document_header_candidates.append(docs_by_page[0].metadata["document_summary"])

            document_header = "\n".join(document_header_candidates)
            document_header_vector = embedding.embed_query(document_header)

            for doc in docs_by_chunk:
                print(f"vector `{index_name}` chunk vector")

                print(f"vector `{index_name}` page_content_vector")
                
                page_content = f"{doc.page_content}"
                page_content_vector = embedding.embed_query(page_content)
                
                print(f"vector `{index_name}` document header + page_content_vector")
                
                page_content_w_header = f"{document_header}\n\n\n{doc.page_content}"
                page_content_w_header_vector = embedding.embed_query(page_content_w_header)

                objApiResponse = es_client.index(
                    index=index_name,
                    body={
                        "document_header": document_header,
                        "document_header_vector": document_header_vector,
                        "page_content": page_content,
                        "page_content_vector": page_content_vector,
                        "page_content_w_header": page_content_w_header,
                        "page_content_w_header_vector": page_content_w_header_vector,
                        "metadata": doc.metadata,
                    },
                )
                ids_by_chunk.append(objApiResponse["_id"])

            for doc in docs_by_page:

                # create document page header, page content, page content winpaged
                print(f"vector `{index_name}` page_content_vector")
                
                page_content = f"{doc.page_content}"
                page_content_vector = embedding.embed_query(page_content)
                
                print(f"vector `{index_name}` document header + page_content_vector")
                
                page_content_w_header = f"{document_header}\n\n\n{doc.page_content}"
                page_content_w_header_vector = embedding.embed_query(page_content_w_header)
                
                print(f"indexing `{index_name}`")

                # ES Create Index and obtain new ID!
                objApiResponse = es_client.index(
                    index=f"{index_name}",
                    body={
                        "document_header": document_header,
                        "document_header_vector": document_header_vector,
                        "page_content": page_content,
                        "page_content_vector": page_content_vector,
                        "page_content_w_header": page_content_w_header,
                        "page_content_w_header_vector": page_content_w_header_vector,
                        "metadata": doc.metadata,
                    },
                )
                ids_by_page.append(objApiResponse["_id"])
        
        return docs_by_chunk + docs_by_page, ids_by_chunk + ids_by_page, index_name
    except Exception as e:
        print(e)
        raise e



