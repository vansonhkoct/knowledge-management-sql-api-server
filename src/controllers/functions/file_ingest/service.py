import asyncio
import json
import os
import traceback

from redis.asyncio import Redis

from src.controllers.functions._generic.fileutils import load_uploaded_file
from src.controllers.functions.file.file import on_upload_file
from src.models.master import File, FileProcessLog


FILE_STATUS_UPLOADING = "UPLOADING"
FILE_STATUS_QUEUED = "QUEUED"
FILE_STATUS_INDEXING = "INDEXING"
FILE_STATUS_INDEXED = "INDEXED"
FILE_STATUS_ERROR = "ERROR"

FILE_INGEST_QUEUE_KEY = os.getenv("FILE_INGEST_QUEUE_KEY", "km:file_ingest_queue")
FILE_STATUS_CHANNEL = os.getenv("FILE_STATUS_CHANNEL", "km:file_status_events")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

TEXT_FILE_EXTENSIONS = (
    ".txt",
    ".md",
    ".markdown",
    ".csv",
    ".json",
    ".log",
)


def _get_redis_client() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)


def _serialize_datetime(value):
    return value.isoformat() if value is not None else None


def _is_plaintext_file(item: File) -> bool:
    filename = (item.filename or "").lower()
    mime_type = (item.mime_type or "").lower()
    return mime_type.startswith("text/") or filename.endswith(TEXT_FILE_EXTENSIONS)


async def serialize_file_item(item: File) -> dict:
    return {
        "id": str(item.id),
        "alias": item.alias,
        "filename": item.filename,
        "mime_type": item.mime_type,
        "size_bytes": item.size_bytes,
        "category_id": str(item.category_id) if item.category_id else None,
        "party_id": str(item.party_id) if item.party_id else None,
        "status": item.status,
        "latest_process_message": item.latest_process_message,
        "ingest_error": item.ingest_error,
        "document_tags_json": item.document_tags_json,
        "document_title": item.document_title,
        "document_summary": item.document_summary,
        "document_remarks": item.document_remarks,
        "document_userdata_json": item.document_userdata_json,
        "es_doc_ids": item.es_doc_ids,
        "created_at": _serialize_datetime(item.created_at),
        "modified_at": _serialize_datetime(item.modified_at),
    }


async def serialize_file_process_log(item: FileProcessLog) -> dict:
    return {
        "id": str(item.id),
        "file_id": str(item.file_id),
        "stage": item.stage,
        "status": item.status,
        "message": item.message,
        "details_json": item.details_json,
        "created_at": _serialize_datetime(item.created_at),
        "modified_at": _serialize_datetime(item.modified_at),
    }


async def _publish_file_status_event(file_item: File, process_log: FileProcessLog | None = None):
    payload = {
        "topic": "file_status",
        "dict": {
            "party_id": str(file_item.party_id) if file_item.party_id else None,
            "item": await serialize_file_item(file_item),
            "process_log": await serialize_file_process_log(process_log) if process_log is not None else None,
        },
    }

    redis = _get_redis_client()
    try:
        await redis.publish(FILE_STATUS_CHANNEL, json.dumps(payload))
    finally:
        await redis.aclose()


async def create_file_process_log(
    file_item: File,
    stage: str,
    status: str,
    message: str,
    details_json=None,
):
    process_log = await FileProcessLog.create(
        file_id=file_item.id,
        stage=stage,
        status=status,
        message=message,
        details_json=details_json,
    )
    await _publish_file_status_event(file_item, process_log)
    return process_log


async def update_file_status(
    file_item: File,
    status: str,
    latest_process_message: str | None = None,
    ingest_error: str | None = None,
    clear_ingest_error: bool = False,
):
    file_item.status = status
    if latest_process_message is not None:
        file_item.latest_process_message = latest_process_message
    if clear_ingest_error:
        file_item.ingest_error = None
    elif ingest_error is not None:
        file_item.ingest_error = ingest_error
    await file_item.save()
    await _publish_file_status_event(file_item)
    return file_item


async def enqueue_file_ingest(file_id: str):
    redis = _get_redis_client()
    try:
        await redis.rpush(FILE_INGEST_QUEUE_KEY, json.dumps({"file_id": str(file_id)}))
    finally:
        await redis.aclose()


async def process_file_ingest(file_id: str):
    file_item = await File.filter(
        id=file_id,
        is_disabled=False,
        is_deleted=False,
    ).first()

    if file_item is None:
        return None

    await update_file_status(
        file_item,
        FILE_STATUS_INDEXING,
        latest_process_message="Indexing in progress",
        clear_ingest_error=True,
    )
    await create_file_process_log(
        file_item,
        stage="INDEXING",
        status="STARTED",
        message="Indexing started",
    )

    try:
        if _is_plaintext_file(file_item):
            with load_uploaded_file(file_item.filename) as raw_file:
                plaintext = raw_file.read().decode("utf-8", errors="ignore")

            docs, es_doc_ids, index_name = await on_upload_file(
                party_id=str(file_item.party_id),
                filename=file_item.filename,
                file_id=str(file_item.id),
                plaintext=plaintext,
                category_id=str(file_item.category_id) if file_item.category_id else None,
                document_tags=file_item.document_tags_json or [],
                document_title=file_item.document_title,
                document_summary=file_item.document_summary,
                document_remarks=file_item.document_remarks,
                document_userdata=file_item.document_userdata_json,
            )
        else:
            with load_uploaded_file(file_item.filename) as raw_file:
                docs, es_doc_ids, index_name = await on_upload_file(
                    party_id=str(file_item.party_id),
                    filename=file_item.filename,
                    file_id=str(file_item.id),
                    file=raw_file,
                    category_id=str(file_item.category_id) if file_item.category_id else None,
                    document_tags=file_item.document_tags_json or [],
                    document_title=file_item.document_title,
                    document_summary=file_item.document_summary,
                    document_remarks=file_item.document_remarks,
                    document_userdata=file_item.document_userdata_json,
                )

        indexed_chunks = len(es_doc_ids or [])
        file_item.es_doc_ids = ",".join(es_doc_ids or [])
        file_item.status = FILE_STATUS_INDEXED
        file_item.latest_process_message = f"Indexed {indexed_chunks} chunks"
        file_item.ingest_error = None
        await file_item.save()
        await _publish_file_status_event(file_item)
        await create_file_process_log(
            file_item,
            stage="INDEXING",
            status="SUCCESS",
            message=f"Indexed {indexed_chunks} chunks successfully",
            details_json={
                "index_name": index_name,
                "indexed_chunks": indexed_chunks,
                "document_count": len(docs or []),
            },
        )
        return file_item

    except Exception as e:
        stacktrace = traceback.format_exc()
        file_item.status = FILE_STATUS_ERROR
        file_item.latest_process_message = str(e)
        file_item.ingest_error = stacktrace
        await file_item.save()
        await _publish_file_status_event(file_item)
        await create_file_process_log(
            file_item,
            stage="INDEXING",
            status="ERROR",
            message=str(e),
            details_json={
                "stacktrace": stacktrace,
            },
        )
        return file_item


async def run_file_ingest_worker():
    redis = _get_redis_client()
    try:
        while True:
            message = await redis.blpop(FILE_INGEST_QUEUE_KEY, timeout=5)
            if message is None:
                continue

            _, payload = message
            try:
                data = json.loads(payload)
                file_id = data.get("file_id")
                if file_id:
                    await process_file_ingest(file_id)
            except Exception:
                print(traceback.format_exc())
    finally:
        await redis.aclose()


async def listen_for_file_status_events(on_message):
    redis = _get_redis_client()
    pubsub = redis.pubsub()
    await pubsub.subscribe(FILE_STATUS_CHANNEL)
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None:
                await asyncio.sleep(0.1)
                continue

            try:
                payload = json.loads(message["data"])
                await on_message(payload)
            except Exception:
                print(traceback.format_exc())
    finally:
        await pubsub.unsubscribe(FILE_STATUS_CHANNEL)
        await pubsub.aclose()
        await redis.aclose()