

def doc_insert_text_data_strat_1(
    DocumentUtils,
    embedding,
    es_client,
    index_name, 
    text_data, 
    text, 
    chunk_size, 
    chunk_overlap, 
    extra_metadata,
    is_testrun,
    ):
    try:
        index_page_prefix = ""

        text_data, updated_text = DocumentUtils.parse_text(
            text_data, text
        )

        # load txt file as Langchain Document chunks
        docs = DocumentUtils.load_oc_text(updated_text, chunk_size, chunk_overlap, 
                                          extra_metadata=extra_metadata)

        # add Langchain Document chunks to ElasticSearch instance
        ids = []
        
        composite_index_name = f"{index_page_prefix}{index_name}"
        
        if not is_testrun:
            for k in range(len(docs)):

                text = docs[k].page_content
                vector = embedding.embed_query(text)
                metadata = docs[k].metadata,

                id = es_client.index(
                    index=composite_index_name,
                    body={
                        "text": text,
                        "vector": vector,
                        "metadata": metadata,
                    },
                )
                ids.append(id)

        return {
            composite_index_name: {
                "ids": ids,
                "docs": docs,
            }
        }
    except Exception as e:
        print(e)
        raise e



# doc_insert_text_data_strat_20240812 stores the text data by
# page content, document header, and combination of (page content + document header)
def doc_insert_text_data_strat_2(
    DocumentUtils,
    embedding,
    es_client,
    index_name, 
    text_data, 
    text, 
    chunk_size, 
    chunk_overlap, 
    extra_metadata,
    is_testrun,
    ):
    try:
        text_data, updated_text = DocumentUtils.parse_text(
            text_data, text
        )

        # load txt file as Langchain Document chunks
        print("processing docs_by_chunk...")
        docs_by_chunk = DocumentUtils.load_oc_text(updated_text,
                                          chunk_size, chunk_overlap, 
                                          use_text_splitter=True,
                                          extra_metadata=extra_metadata)

        # load txt file as Langchain Document pages
        print("processing docs_by_chunk...")
        docs_by_page = DocumentUtils.load_oc_text(updated_text,
                                          use_text_splitter=False,
                                          extra_metadata=extra_metadata)

        index_page_prefix = "strat_2_mpage_"
        index_chunk_prefix = "strat_2_mchunk_"
        
        composite_index_chunk_name = f"{index_chunk_prefix}{index_name}"
        composite_index_page_name = f"{index_page_prefix}{index_name}"

        ids_by_chunk = []
        ids_by_page = []

        if not is_testrun:
            
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
                print(f"vector `{composite_index_chunk_name}` vector")

                text = f"{docs_by_page[k].page_content}"
                vector = embedding.embed_query(text)

                id = es_client.index(
                    index=composite_index_chunk_name,
                    body={
                        "prefix": index_chunk_prefix,
                        "text": text,
                        "vector": vector,
                        "document_header": document_header,
                        "document_header_vector": document_header_vector,
                        "page_content": page_content,
                        "page_content_vector": page_content_vector,
                        "page_content_w_header": page_content_w_header,
                        "page_content_w_header_vector": page_content_w_header_vector,
                        "metadata": docs_by_page[k].metadata,
                    },
                )
                ids_by_chunk.append(id)

            for k in range(len(docs_by_page)):

                # create document page header, page content, page content winpaged
                print(f"vector `{composite_index_page_name}` page_content_vector")
                
                page_content = f"{docs_by_page[k].page_content}"
                page_content_vector = embedding.embed_query(page_content)
                
                print(f"vector `{composite_index_page_name}` document header + page_content_vector")
                
                page_content_w_header = f"{document_header}\n\n\n{docs_by_page[k].page_content}"
                page_content_w_header_vector = embedding.embed_query(page_content_w_header)
                
                print(f"indexing `{composite_index_page_name}`")

                # ES Create Index and obtain new ID!
                id = es_client.index(
                    index=f"{composite_index_page_name}",
                    body={
                        "prefix": index_page_prefix,
                        "document_header": document_header,
                        "document_header_vector": document_header_vector,
                        "page_content": page_content,
                        "page_content_vector": page_content_vector,
                        "page_content_w_header": page_content_w_header,
                        "page_content_w_header_vector": page_content_w_header_vector,
                        "metadata": docs_by_page[k].metadata,
                    },
                )
                ids_by_page.append(id)
        
        return {
            composite_index_chunk_name: {
                "ids": ids_by_chunk,
                "docs": docs_by_chunk,
            },
            composite_index_page_name: {
                "ids": ids_by_page,
                "docs": docs_by_page,
            },
        }
    except Exception as e:
        print(e)
        raise e



