
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
        _, updated_text = DocumentUtils.parse_text(
            voDocInsert.text_data, 
            voDocInsert.text,
        )

        # load txt file as Langchain Document chunks
        docs = DocumentUtils.load_oc_text(updated_text, voDocInsert.chunk_size, voDocInsert.chunk_overlap, 
                                          extra_metadata=voDocInsert.extra_metadata)

        # add Langchain Document chunks to ElasticSearch instance
        ids = []
        
        index_name = f"{voDocInsert.index_name}"
        
        if not voDocInsert.is_testrun:
            for k in range(len(docs)):

                text = docs[k].page_content
                vector = embedding.embed_query(text)
                metadata = docs[k].metadata,

                id = es_client.index(
                    index=index_name,
                    body={
                        "text": text,
                        "vector": vector,
                        "metadata": {
                            **metadata,
                            "data_strategy": "1",
                        }
                    },
                )
                ids.append(id)

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
        
        _, updated_text = DocumentUtils.parse_text(
            voDocInsert.text_data, 
            voDocInsert.text,
        )

        # load txt file as Langchain Document chunks
        print("processing docs_by_chunk...")
        docs_by_chunk = DocumentUtils.load_oc_text(updated_text,
                                          voDocInsert.chunk_size, voDocInsert.chunk_overlap, 
                                          use_text_splitter=True,
                                          extra_metadata=voDocInsert.extra_metadata)

        # load txt file as Langchain Document pages
        print("processing docs_by_chunk...")
        docs_by_page = DocumentUtils.load_oc_text(updated_text,
                                          use_text_splitter=False,
                                          extra_metadata=voDocInsert.extra_metadata)

        index_name = f"{voDocInsert.index_name}"

        ids_by_chunk = []
        ids_by_page = []

        if not voDocInsert.is_testrun:
            
            document_header_candidates = []
            if ("document_remarks" in docs_by_page[0].metadata):
                document_header_candidates.append(docs_by_page[0].metadata["document_remarks"])
            if ("document_title" in docs_by_page[0].metadata):
                document_header_candidates.append(docs_by_page[0].metadata["document_title"])
            if ("document_summary" in docs_by_page[0].metadata):
                document_header_candidates.append(docs_by_page[0].metadata["document_summary"])

            document_header = "\n".join(document_header_candidates)
            document_header_vector = embedding.embed_query(document_header)

            for k in range(len(docs_by_chunk)):
                print(f"vector `{index_name}` chunk vector")

                text = f"{docs_by_page[k].page_content}"
                vector = embedding.embed_query(text)

                id = es_client.index(
                    index=index_name,
                    body={
                        "text": text,
                        "vector": vector,
                        "document_header": document_header,
                        "document_header_vector": document_header_vector,
                        "page_content": page_content,
                        "page_content_vector": page_content_vector,
                        "page_content_w_header": page_content_w_header,
                        "page_content_w_header_vector": page_content_w_header_vector,
                        "metadata": {
                            **docs_by_page[k].metadata,
                            "data_strategy": "2",
                            "data_portion_type": _constants.DATA_PORTION_CHUNK,
                        }
                    },
                )
                ids_by_chunk.append(id)

            for k in range(len(docs_by_page)):

                # create document page header, page content, page content winpaged
                print(f"vector `{index_name}` page_content_vector")
                
                page_content = f"{docs_by_page[k].page_content}"
                page_content_vector = embedding.embed_query(page_content)
                
                print(f"vector `{index_name}` document header + page_content_vector")
                
                page_content_w_header = f"{document_header}\n\n\n{docs_by_page[k].page_content}"
                page_content_w_header_vector = embedding.embed_query(page_content_w_header)
                
                print(f"indexing `{index_name}`")

                # ES Create Index and obtain new ID!
                id = es_client.index(
                    index=f"{index_name}",
                    body={
                        "document_header": document_header,
                        "document_header_vector": document_header_vector,
                        "page_content": page_content,
                        "page_content_vector": page_content_vector,
                        "page_content_w_header": page_content_w_header,
                        "page_content_w_header_vector": page_content_w_header_vector,
                        "metadata": {
                            **docs_by_page[k].metadata,
                            "data_strategy": "2",
                            "data_portion_type": _constants.DATA_PORTION_PAGE,
                        }
                    },
                )
                ids_by_page.append(id)
        
        return docs_by_chunk + docs_by_page, ids_by_chunk + ids_by_page, index_name
    except Exception as e:
        print(e)
        raise e



