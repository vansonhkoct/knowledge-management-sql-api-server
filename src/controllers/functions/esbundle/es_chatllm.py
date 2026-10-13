
from .include.pymupdf.pymupdf import extract_pdf_file_to_text, async_extract_pdf_file_to_text
from .include import ConfigParams
from .include.EmbeddingsBundle import EmbeddingsBundle
from .include.ChatLLMController import ChatLLMController
from .include.ElasticSearchDao.ESVo import ESVoDocSearch, ESVoDocInsert
from .include.ChatLLMDao.LLMVo import LLMVoAskQuestion
from .include.ElasticSearchDao import _constants
from src.schemas.master import Party, AIModelEndpoint
from src.controllers.functions._generic.secretutils import decrypt_secret
from src.controllers.functions._generic.endpointutils import validate_ai_endpoint_url


import asyncio


MODEL_TYPE_LLM = "LLM"
MODEL_TYPE_EMBEDDING = "EMBEDDING"


async def _resolve_party(party_id: str):
    party = await Party.filter(
        id=party_id,
        is_disabled=False,
        is_deleted=False,
    ).first()

    if party is None:
        raise ValueError(f"Party not found for model resolution: {party_id}")

    await party.fetch_related("default_llm_model", "default_embedding_model")
    return party


async def _resolve_model_endpoint(
    party_id: str,
    model_type: str,
    preferred_model_name: str | None = None,
):
    party = await _resolve_party(party_id)

    endpoint = party.default_llm_model if model_type == MODEL_TYPE_LLM else party.default_embedding_model

    if endpoint is None:
      raise ValueError(f"Party {party_id} is missing a default {model_type.lower()} model")

    if preferred_model_name not in [None, ""]:
      allowed_names = {str(endpoint.id), endpoint.name, endpoint.model_name}
      if preferred_model_name not in allowed_names:
        raise ValueError("The requested model is not assigned to this party")

    validate_ai_endpoint_url(endpoint.base_url)

    return endpoint


def _build_embedding_bundle(endpoint: AIModelEndpoint):
    return EmbeddingsBundle(
        base_url=endpoint.base_url,
        model_name=endpoint.model_name,
        api_key=decrypt_secret(endpoint.api_key),
        api_path=endpoint.api_path,
        headers_json=endpoint.headers_json,
        options_json=endpoint.options_json,
    )


def _build_llm_controller(endpoint: AIModelEndpoint):
    return ChatLLMController(
        base_url=endpoint.base_url,
        model_name=endpoint.model_name,
        api_key=decrypt_secret(endpoint.api_key),
        api_path=endpoint.api_path,
        headers_json=endpoint.headers_json,
        options_json=endpoint.options_json,
        assistant_alias=endpoint.assistant_alias,
    )


def _build_es_controller(embedding=None):
    # Keep the retired Elasticsearch path installable without making its heavy
    # dependencies part of the default PGlite runtime.
    from .include.ElasticSearchController import ElasticSearchController
    return ElasticSearchController(embedding=embedding)






# ES - Insert

async def bot_es_add_document(
    vo: ESVoDocInsert,
):
    embedding_endpoint = await _resolve_model_endpoint(
        party_id=vo.index_name,
        model_type=MODEL_TYPE_EMBEDDING,
    )
    es_controller = _build_es_controller(
        embedding=_build_embedding_bundle(embedding_endpoint),
    )
    
    def fn():
        docs, ids, index_name = es_controller.doc_insert_text_data_strat_2(
            voDocInsert=vo,
        )

        return docs, ids, index_name

    docs, ids, index_name = await asyncio.get_running_loop().run_in_executor(None, fn)
    return docs, ids, index_name





# ES - Update

async def bot_es_update_document_metadata(
    index_name, 
    id,
    document_category,
    document_tags,
    document_userdata,
):
    es_controller = _build_es_controller()
    
    def fn():
        res = es_controller.doc_update_document_metadata(
            index_name = index_name,
            id = id,
            document_category=document_category,
            document_tags=document_tags,
            document_userdata=document_userdata,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res







# ES - Get

async def bot_es_get_document_by_id(
    index_name, 
    id,
):
    es_controller = _build_es_controller()
    
    def fn():
        res = es_controller.doc_get_document_by_id(
            index_name = index_name,
            id = id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_get_document_es_ids_by_document_file_id(
    index_name,
    document_file_id,
    data_strategy,
):
    es_controller = _build_es_controller()
    
    def fn():
        res = es_controller.doc_get_document_es_ids_by_document_file_id(
            index_name = index_name,
            document_file_id = document_file_id,
            data_strategy = data_strategy,
        )
        return res
    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res








# ES - Delete

async def bot_es_delete_document_by_id(
    index_name, 
    id,
):
    es_controller = _build_es_controller()
    
    def fn():
        res = es_controller.doc_delete_document_by_id(
            index_name = index_name,
            id = id,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res







# ES - Search

async def bot_es_search_multi_vector(
    vo: ESVoDocSearch,
):
    embedding_endpoint = await _resolve_model_endpoint(
        party_id=vo.index_name,
        model_type=MODEL_TYPE_EMBEDDING,
    )
    es_controller = _build_es_controller(
        embedding=_build_embedding_bundle(embedding_endpoint),
    )
    
    def fn():
        res = es_controller.doc_search_multi_vector(
            voDocSearch = vo,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res





# ES - Migrate

async def bot_es_doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
    index_name: str,
):
    es_controller = _build_es_controller()
    
    def fn():
        res = es_controller.doc_migrate_update_all_data_without_data_strategy_to_become_1_chunk(
            index_name=index_name,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res


async def bot_es_reembed_index(
    index_name: str,
):
    embedding_endpoint = await _resolve_model_endpoint(
        party_id=index_name,
        model_type=MODEL_TYPE_EMBEDDING,
    )
    embedding = _build_embedding_bundle(embedding_endpoint)
    es_controller = _build_es_controller(embedding=embedding)

    def fn():
        total = 0
        updated = 0
        target_index_name = f"{_constants.ES_INDEX_ACTIVE_GLOBAL_PREFIX}{index_name}"
        scroll_id = None

        response = es_controller.es_client.search(
            index=target_index_name,
            body={
                "query": {
                    "match_all": {},
                },
                "size": 250,
            },
            scroll="2m",
        )

        try:
            while True:
                body = response.body
                scroll_id = body.get("_scroll_id")
                hits = body.get("hits", {}).get("hits", [])

                if len(hits) == 0:
                    break

                for hit in hits:
                    total += 1
                    source = hit.get("_source", {})
                    doc = {}

                    if "document_header" in source:
                        doc["document_header_vector"] = embedding.embed_query(source.get("document_header") or "")

                    if "page_content" in source:
                        doc["page_content_vector"] = embedding.embed_query(source.get("page_content") or "")

                    if "page_content_w_header" in source:
                        doc["page_content_w_header_vector"] = embedding.embed_query(source.get("page_content_w_header") or "")

                    if "text" in source:
                        doc["vector"] = embedding.embed_query(source.get("text") or "")

                    if len(doc.keys()) == 0:
                        continue

                    es_controller.es_client.update(
                        index=target_index_name,
                        id=hit.get("_id"),
                        body={
                            "doc": doc,
                        },
                    )
                    updated += 1

                if not scroll_id:
                    break

                response = es_controller.es_client.scroll(
                    scroll_id=scroll_id,
                    scroll="2m",
                )
        finally:
            if scroll_id:
                try:
                    es_controller.es_client.clear_scroll(scroll_id=scroll_id)
                except Exception:
                    pass

        return {
            "index_name": index_name,
            "updated_documents": updated,
            "visited_documents": total,
            "embedding_model_id": str(embedding_endpoint.id),
            "embedding_model_name": embedding_endpoint.model_name,
        }

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res







# CHATLLM - ask question

async def bot_llm_ask_question(
    vo: LLMVoAskQuestion
):
    llm_endpoint = await _resolve_model_endpoint(
        party_id=vo.party_id,
        model_type=MODEL_TYPE_LLM,
        preferred_model_name=vo.llm_model_name,
    )
    llm_controller = _build_llm_controller(llm_endpoint)
    
    def fn():
        res = llm_controller.bot_ask_question(
            voAskQuestion = vo,
        )
        return res

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
    return res




# CHATLLM - stop answering

async def bot_llm_stop_answering(
    api_uid: str | None = None,
):
    llm_controller = ChatLLMController(
        base_url="",
        model_name="",
    )
    
    def fn():
        llm_controller.bot_stop_answering(
            api_uid = api_uid,
        )
        return True

    res = await asyncio.get_running_loop().run_in_executor(None, fn)
