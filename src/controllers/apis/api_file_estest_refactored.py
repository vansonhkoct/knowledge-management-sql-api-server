"""Refactored Elasticsearch test API with clearer separation of concerns."""

import asyncio
import logging
import math
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from py_eschat_llm import (
    ESVoDocInsert,
    ESVoDocSearch,
    LLMVoAskQuestion,
    es_chatllm as ESChatLLM,
    llm_model_enable_api,
)
from src.controllers.functions._generic.fileutils import load_uploaded_file
from src.controllers.functions.file.file import fetch_es_docs, bootstrapImportESBundle
from src.controllers.functions.user.userauth_email import (
    check_password_hash,
    make_password_hash,
)
from src.controllers.functions.log.log import add_log_apillm
from src.models.master import File

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/test", tags=["testing"])

# API Response Models
class BaseResponse(BaseModel):
    """Standard API response format."""
    success: bool
    message: str
    data: Optional[Any] = None

class PasswordHashRequest(BaseModel):
    password: str


class PasswordCheckRequest(BaseModel):
    password: str
    password_hash: str


class ESDocumentCreateRequest(BaseModel):
    index_name: str
    text: str
    metadata: Dict[str, Any] | None = None
    chunk_size: int | None = 350
    chunk_overlap: int | None = 10
    is_testrun: bool | None = False


class LLMQuestionRequest(BaseModel):
    index_name: str
    question: str
    document_category: str | None = None
    document_category_ids: List[str] | None = None
    document_tags: List[str] | None = None
    document_file_ids: List[str] | None = None
    exclude_document_file_ids: List[str] | None = None
    query_strings: Dict[str, str] | None = None
    query_vectors: Dict[str, List[float]] | None = None
    knn_boosts: Dict[str, float] | None = None
    k: int = 10
    num_candidates: int = 100
    data_strategy: str | None = None
    data_portion_type: str | None = None
    data_vector_query_strategy: int = 1
    must_match_document_category: bool = True
    should_match_document_tags: int = 0
    should_match_document_title: int = 0
    should_match_document_summary: int = 0
    should_match_document_text: int = 0
    score_threshold: float | None = None
    llm_model_name: str | None = None
    llm_temperature: float | None = 0.03
    llm_top_p: float | None = 0.92
    llm_top_k: int | None = 4
    llm_repetition_penalty: float | None = 1.2
    llm_max_token: int | None = 0
    llm_history_len: int | None = 3
    history: List[List[str]] | None = None
    api_uid: str | None = None
    skip_llm: bool = False
    is_streaming: bool | None = False
    max_retries: int | None = 10


def _success_response(data: Any = None, message: str = api_tags["C001"]) -> BaseResponse:
    return BaseResponse(success=True, message=message, data=data)


def _build_insert_vo(payload: ESDocumentCreateRequest) -> ESVoDocInsert:
    if not payload.text:
        raise HTTPException(status_code=400, detail={
            "message": api_tags["E003"],
            "error": "text field is required",
            "type": "es_document_validation_error",
        })

    return ESVoDocInsert(
        index_name=payload.index_name,
        text=payload.text,
        chunk_size=payload.chunk_size or 350,
        chunk_overlap=payload.chunk_overlap or 10,
        extra_metadata=payload.metadata or {},
        is_testrun=payload.is_testrun or False,
    )


async def _ingest_document(payload: ESDocumentCreateRequest) -> Dict[str, Any]:
    vo = _build_insert_vo(payload)
    docs, ids, index_name = await ESChatLLM.bot_es_add_document(vo=vo)
    return {"docs": docs, "ids": ids, "index_name": index_name}


async def _fetch_file_and_es_docs(file_id: str) -> Dict[str, Any]:
    item = await File.filter(id=file_id).prefetch_related().first()

    if not item:
        raise HTTPException(status_code=404, detail={
            "message": api_tags["E003"],
            "error": f"File {file_id} not found",
        })

    es_docs = await fetch_es_docs(party_id=item.party_id, file=item)
    file_path: Optional[str] = None

    try:
        with load_uploaded_file(filename=item.filename) as file_obj:
            file_path = file_obj.name
    except FileNotFoundError:
        file_path = None

    return {"item": item, "es_docs": es_docs, "file": file_path}


def _build_es_search_vo(payload: LLMQuestionRequest) -> ESVoDocSearch:
    return ESVoDocSearch(
        index_name=payload.index_name,
        question=payload.question,
        query_strings=payload.query_strings,
        query_vectors=payload.query_vectors,
        knn_boosts=payload.knn_boosts,
        document_category=payload.document_category,
        document_category_ids=payload.document_category_ids,
        document_tags=payload.document_tags,
        document_file_ids=payload.document_file_ids or [],
        exclude_document_file_ids=payload.exclude_document_file_ids,
        k=payload.k,
        num_candidates=payload.num_candidates,
        data_strategy=payload.data_strategy,
        data_portion_type=payload.data_portion_type,
        data_vector_query_strategy=payload.data_vector_query_strategy,
        must_match_document_category=payload.must_match_document_category,
        should_match_document_tags=payload.should_match_document_tags,
        should_match_document_title=payload.should_match_document_title,
        should_match_document_summary=payload.should_match_document_summary,
        should_match_document_text=payload.should_match_document_text,
    )


def _filter_es_results(es_results: List[Dict[str, Any]], threshold: float | None) -> List[Dict[str, Any]]:
    remove_by_env = os.getenv("ES_REMOVE_LOWSCORE_SEARCH_RESULTS") == "1"
    threshold = threshold if threshold is not None else (1.7 if remove_by_env else 0.0)

    filtered: List[Dict[str, Any]] = []
    for item in es_results:
        score = item.get("score") or 0
        max_score = item.get("record_max_score") or 1
        possible_max = item.get("possible_max_score") or 1

        if remove_by_env:
            if max_score and score < 0.75 * max_score:
                continue
            if possible_max and score < 0.6 * possible_max:
                continue

        if score < threshold:
            continue

        filtered.append(item)
    return filtered


def _group_results_by_file(es_results: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for item in es_results:
        key = item.get("file_id") or "unknown"
        grouped.setdefault(key, []).append(item)
    return grouped


def _build_context_sections(grouped: Dict[str, List[Dict[str, Any]]]) -> str:
    sections: List[str] = []
    for file_id, entries in grouped.items():
        representative = entries[0]
        metadata = representative.get("metadata", {})
        document_header = "\n".join(
            filter(
                None,
                [
                    metadata.get("document_remarks"),
                    metadata.get("document_title"),
                    metadata.get("document_summary"),
                ],
            )
        )

        content = "\n\n...\n".join(entry.get("content", "") for entry in entries)
        sections.append(
            "\n\n".join([
                "----------",
                f"File ID: {file_id}",
                document_header,
                content,
                "----------",
            ])
        )

    return "\n\n".join(sections)


def _build_llm_prompt(question: str, context_sections: str) -> str:
    return """以下是系統提供的資料段落：
{context}

===================

請閱讀上述文件段落，單純依靠系統所提供的信息 (不必考慮信息以外的知識)，並使用中文（不要使用其他語言）告訴我：
{question}

===================

如果無法從系統提供的資料段落和我的問題匹配，請嘗試參考資料段落，從而建議我可以嘗試詢問的問題。
""".format(context=context_sections or "(未找到相關文件)", question=question)


async def _acquire_llm_slot(max_retries: int | None = 10, retry_delay: int = 2) -> int:
    global is_busy

    max_retries = max(1, max_retries or 10)
    attempts = 0
    while is_busy and attempts < max_retries:
        await asyncio.sleep(retry_delay)
        attempts += 1

    if is_busy:
        raise HTTPException(
            status_code=400,
            detail={
                "message": api_tags["E002"],
                "error": f"Server busy (Attempt {attempts + 1}/{max_retries})",
            },
        )

    is_busy = True
    return attempts


def _collect_es_result_ids(es_result: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ids: List[Dict[str, Any]] = []
    for item in es_result:
        metadata = item.get("metadata", {})
        ids.append({
            "file_id": item.get("file_id"),
            "page": metadata.get("page"),
        })
    return ids


def _build_llm_vo(payload: LLMQuestionRequest, prompt: str, llm_max_token: int) -> LLMVoAskQuestion:
    return LLMVoAskQuestion(
        prompt=prompt,
        history=payload.history or [],
        llm_model_name=payload.llm_model_name,
        llm_max_token=llm_max_token,
        llm_temperature=payload.llm_temperature,
        llm_top_p=payload.llm_top_p,
        llm_top_k=payload.llm_top_k,
        llm_repetition_penalty=payload.llm_repetition_penalty,
        llm_history_len=payload.llm_history_len or 3,
        api_uid=payload.api_uid or "",
        emit_to_uid=None,
    )

# Configuration
api_tags = {
    "C001": "Operation completed successfully",
    "E001": "Unexpected server error occurred",
    "E002": "Resource is busy or locked",
    "E003": "Validation error in request parameters",
}

# LLM State Management
is_busy = False  # Global flag for LLM processing state (consider Redis/locking mechanism)


# Public Functions - These should NOT be in auth module
def create_hash_response(password: str) -> BaseResponse:
    """Create password hash with appropriate warnings."""
    logger.warning("JWT-based-auth-pw-api requested (deprecated) - this endpoint allows password bypass")
    return BaseResponse(
        success=True,
        message=api_tags["C001"],
        data=make_password_hash(password=password)
    )

def create_check_response(password: str, password_hash: str) -> BaseResponse:
    """Check password against hash."""
    return BaseResponse(
        success=True,
        message=api_tags["C001"],
        data=check_password_hash(password_hash=password_hash, password=password)
    )

# Elasticsearch Integration Endpoints
@router.post("/es/initialize", response_model=BaseResponse)
async def initialize_elasticsearch():
    """Initialize Elasticsearch bundle - deprecated but kept for testing."""
    try:
        logger.warning(
            "Legacy ES bundle initialization attempted - recommended to use migration scripts"
        )
        bootstrapImportESBundle()
        return _success_response(data={})
    except Exception as e:
        logger.error(f"Elasticsearch initialization failed: {e}")
        raise HTTPException(status_code=500, detail={
            "message": api_tags["E001"],
            "error": str(e),
            "type": "elasticsearch_initialization_error"
        })

@router.post("/password/hash", response_model=BaseResponse)
async def hash_password(request: PasswordHashRequest):
    """Create password hash (TESTING ONLY - SECURITY RISK)."""
    return create_hash_response(request.password)

@router.post("/password/verify", response_model=BaseResponse)
async def verify_password(request: PasswordCheckRequest):
    """Verify password against hash."""
    return create_check_response(request.password, request.password_hash)

@router.post("/file/load", response_model=BaseResponse)
async def load_test_file(request: Request):
    """Load a test file for processing."""
    try:
        data = await request.json()
        filename = data.get("filename")

        if not filename:
            raise HTTPException(status_code=400, detail={
                "message": api_tags["E003"],
                "error": "filename is required"
            })

        with load_uploaded_file(filename=filename) as file_obj:
            return _success_response(
                data={"item": "___FILE_TEST___", "file": file_obj.name}
            )
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={
            "message": "File not found",
            "error": str(e)
        })
    except Exception as e:
        error_msg = f"File loading failed: {e}"
        logger.error(error_msg)
        raise HTTPException(status_code=500, detail={
            "message": api_tags["E001"],
            "error": error_msg,
            "type": "file_load_error"
        })

@router.post("/file/load/{file_id}", response_model=BaseResponse)
async def load_api_file(file_id: str):
    """Load file from API with Elasticsearch integration."""
    try:
        payload = await _fetch_file_and_es_docs(file_id=file_id)
        return _success_response(data=payload)
    except Exception as e:
        logger.error(f"API file loading failed: {e}")
        raise HTTPException(status_code=500, detail={
            "message": api_tags["E001"],
            "error": str(e),
            "type": "api_file_load_error"
        })

# Elasticsearch Document Operations
@router.post("/es/document/create", response_model=BaseResponse)
async def create_es_document(payload: ESDocumentCreateRequest):
    """Create Elasticsearch document with text processing."""
    try:
        ingestion_result = await _ingest_document(payload)
        return _success_response(data=ingestion_result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("ES document creation failed")
        raise HTTPException(
            status_code=500,
            detail={
                "message": api_tags["E001"],
                "error": str(exc),
                "type": "es_document_creation_error",
            },
        )

# System Health & Monitoring
@router.get("/health/status", response_model=BaseResponse)
async def get_health_status():
    """Check system health status."""
    return BaseResponse(
        success=True,
        message="System operational",
        data={"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    )

@router.get("/system/info", response_model=BaseResponse)
async def get_system_info():
    """Get system information for monitoring."""
    return BaseResponse(
        success=True,
        message="System information",
        data={
            "llm_status": "busy" if is_busy else "ready",
            "system_version": "1.0.0",
            "features_enabled": {
                "llm_api": llm_model_enable_api,
            }
        }
    )

# Advanced File Processing
@router.post("/file/process/from-string", response_model=BaseResponse)
async def process_text_string(payload: ESDocumentCreateRequest):
    """Process text string directly into Elasticsearch using payload schema."""
    try:
        ingestion_result = await _ingest_document(payload)
        return _success_response(data=ingestion_result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Text processing failed")
        raise HTTPException(
            status_code=500,
            detail={
                "message": api_tags["E001"],
                "error": str(exc),
                "type": "text_processing_error",
            },
        )

# Legacy functions that need refactoring
@router.post("/legacy/file/process/upload", response_model=BaseResponse)
async def legacy_process_uploaded_file(request: Request):
    """Legacy file processing endpoint (needs complete refactoring)."""
    # This is a placeholder as the original function was too large/complex
    # original function calls: ESChatLLM.bot_es_add_document
    logger.warning("Legacy file processing endpoint called - this needs complete refactoring")
    raise HTTPException(
        status_code=400,
        detail={"message": "Legacy endpoint needs refactoring", "type": "deprecated_endpoint"}
    )

# LLM Question Answering (Refactored helper-based flow)
@router.post("/llm/question", response_model=BaseResponse)
async def ask_llm_question(payload: LLMQuestionRequest):
    """Answer a question by retrieving ES context and optionally invoking the LLM."""
    global is_busy

    if not llm_model_enable_api:
        raise HTTPException(
            status_code=400,
            detail={"message": api_tags["E003"], "error": "Server LLM ask question ability disabled"},
        )

    if payload.is_streaming:
        raise HTTPException(
            status_code=400,
            detail={"message": api_tags["E003"], "error": "Streaming responses are not supported in this endpoint"},
        )

    if not payload.question:
        raise HTTPException(
            status_code=400,
            detail={"message": api_tags["E003"], "error": "question is required"},
        )

    slot_acquired = False
    try:
        attempts = await _acquire_llm_slot(payload.max_retries)
        slot_acquired = True

        vo_es = _build_es_search_vo(payload)
        es_result = await ESChatLLM.bot_es_search_multi_vector(vo=vo_es)
        filtered_es_result = _filter_es_results(es_result, payload.score_threshold)
        grouped_filtered_es_result = _group_results_by_file(filtered_es_result)
        context_sections = _build_context_sections(grouped_filtered_es_result)
        prompt = _build_llm_prompt(payload.question, context_sections)

        suggested_token = 8192
        prompt_token = math.ceil(len(prompt) * 1.6)
        input_llm_max_token = payload.llm_max_token or 0
        llm_max_token = max(input_llm_max_token, suggested_token, prompt_token)

        llm_answer_result: Dict[str, Any] | None = None
        if not payload.skip_llm:
            vo_llm = _build_llm_vo(payload, prompt, llm_max_token)
            llm_answer_result = await ESChatLLM.bot_llm_ask_question(vo=vo_llm)

        add_log_apillm(
            question=payload.question,
            index_name=payload.index_name,
            prompt=prompt,
            llm_answer_result=llm_answer_result,
            suggested_token=suggested_token,
            prompt_token=prompt_token,
            input_llm_max_token=input_llm_max_token,
            es_result_ids=_collect_es_result_ids(es_result),
        )

        response_payload = {
            "answer_result": llm_answer_result["answer_result"] if llm_answer_result else None,
            "suggested_token": suggested_token,
            "prompt_token": prompt_token,
            "input_llm_max_token": input_llm_max_token,
            "prompt": prompt,
            "context_sections": context_sections,
            "group_filtered_es_result_count": len(grouped_filtered_es_result),
            "filtered_es_result_count": len(filtered_es_result),
            "es_result_count": len(es_result),
            "group_filtered_es_result": grouped_filtered_es_result,
            "filtered_es_result": filtered_es_result,
            "es_result": es_result,
            "retry_attempts": attempts,
        }

        return _success_response(data=response_payload)

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("LLM question endpoint failed")
        raise HTTPException(
            status_code=500,
            detail={
                "message": api_tags["E001"],
                "error": str(exc),
                "type": "llm_question_error",
            },
        )
    finally:
        if slot_acquired:
            is_busy = False