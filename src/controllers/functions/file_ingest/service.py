import asyncio
import hashlib
import json
import logging
import os
from contextlib import suppress
from datetime import datetime
from urllib.parse import urlsplit

from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import TimeoutError as RedisTimeoutError

from src.controllers.functions._generic.fileutils import load_uploaded_file
from src.controllers.functions.file.file import on_upload_file
from src.models.master import File, FileIndexJob, FileProcessLog


logger = logging.getLogger(__name__)


FILE_STATUS_UPLOADING = "UPLOADING"
FILE_STATUS_UPLOADED = "UPLOADED"
FILE_STATUS_QUEUED = "QUEUED"
FILE_STATUS_INDEXING = "INDEXING"
FILE_STATUS_INDEXED = "INDEXED"
FILE_STATUS_ERROR = "ERROR"

FILE_INDEX_STATUS_NOT_INDEXED = "NOT_INDEXED"
FILE_INDEX_STATUS_QUEUED = "QUEUED"
FILE_INDEX_STATUS_INDEXING = "INDEXING"
FILE_INDEX_STATUS_INDEXED = "INDEXED"
FILE_INDEX_STATUS_ERROR = "ERROR"

INDEX_JOB_STATUS_QUEUED = "QUEUED"
INDEX_JOB_STATUS_RUNNING = "RUNNING"
INDEX_JOB_STATUS_SUCCESS = "SUCCESS"
INDEX_JOB_STATUS_ERROR = "ERROR"

INDEX_VERSION = os.getenv("FILE_INDEX_VERSION", "pdf-v1")

FILE_INGEST_QUEUE_KEY = os.getenv("FILE_INGEST_QUEUE_KEY", "km:file_ingest_queue")
FILE_STATUS_CHANNEL = os.getenv("FILE_STATUS_CHANNEL", "km:file_status_events")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
REDIS_RECONNECT_DELAY_SECONDS = max(
    float(os.getenv("REDIS_RECONNECT_DELAY_SECONDS", "5")),
    0.1,
)

REDIS_CONNECTION_ERRORS = (RedisConnectionError, RedisTimeoutError, OSError)


def _get_redis_client() -> Redis:
    return Redis.from_url(REDIS_URL, decode_responses=True)


def _redis_target_label() -> str:
    """Describe the Redis target without exposing credentials."""
    parsed = urlsplit(REDIS_URL)
    host = parsed.hostname or "localhost"
    port = parsed.port or 6379
    database = parsed.path.lstrip("/") or "0"
    return f"{host}:{port}/{database}"


async def _wait_for_redis(redis: Redis, component: str):
    waiting = False
    while True:
        try:
            await redis.ping()
            if waiting:
                logger.info("Redis is available again at %s", _redis_target_label())
            return
        except REDIS_CONNECTION_ERRORS:
            waiting = True
            logger.warning(
                "%s is waiting for Redis at %s. Start Redis or update REDIS_URL; "
                "retrying in %.1f seconds.",
                component,
                _redis_target_label(),
                REDIS_RECONNECT_DELAY_SECONDS,
            )
            await asyncio.sleep(REDIS_RECONNECT_DELAY_SECONDS)


def _serialize_datetime(value):
    return value.isoformat() if value is not None else None


def is_pdf_file(item: File) -> bool:
    filename = (item.filename or "").lower()
    mime_type = (item.mime_type or "").lower()
    return mime_type == "application/pdf" or filename.endswith(".pdf")


def _calculate_source_hash(item: File) -> str:
    digest = hashlib.sha256()
    with load_uploaded_file(item.filename) as raw_file:
        for chunk in iter(lambda: raw_file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
        "ingest_error": item.index_error or ("Indexing failed" if item.ingest_error else None),
        "index_status": item.index_status,
        "index_error": item.index_error,
        "index_attempt_count": item.index_attempt_count,
        "index_version": item.index_version,
        "source_hash": item.source_hash,
        "indexed_source_hash": item.indexed_source_hash,
        "indexed_at": _serialize_datetime(item.indexed_at),
        "document_tags_json": item.document_tags_json,
        "document_title": item.document_title,
        "document_summary": item.document_summary,
        "document_remarks": item.document_remarks,
        "document_userdata_json": item.document_userdata_json,
        "es_doc_ids": item.es_doc_ids,
        "created_at": _serialize_datetime(item.created_at),
        "modified_at": _serialize_datetime(item.modified_at),
    }


async def serialize_file_index_job(item: FileIndexJob) -> dict:
    return {
        "id": str(item.id),
        "file_id": str(item.file_id),
        "party_id": str(item.party_id),
        "requested_by_id": str(item.requested_by_id) if item.requested_by_id else None,
        "status": item.status,
        "attempt": item.attempt,
        "error": item.error,
        "source_hash": item.source_hash,
        "index_version": item.index_version,
        "started_at": _serialize_datetime(item.started_at),
        "completed_at": _serialize_datetime(item.completed_at),
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
        "details_json": {
            key: value
            for key, value in (item.details_json or {}).items()
            if key != "stacktrace"
        },
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


async def enqueue_file_ingest(file_id: str, requested_by_user_id: str | None = None):
    file_item = await File.filter(
        id=file_id,
        is_disabled=False,
        is_deleted=False,
    ).first()
    if file_item is None:
        raise ValueError("File not found")
    if not is_pdf_file(file_item):
        raise ValueError("Only PDF files can be indexed")
    if file_item.index_status == FILE_INDEX_STATUS_INDEXED:
        raise ValueError("File is already indexed")

    existing_job = await FileIndexJob.filter(
        file_id=file_item.id,
        status__in=[INDEX_JOB_STATUS_QUEUED, INDEX_JOB_STATUS_RUNNING],
    ).order_by("created_at").first()
    if existing_job is not None:
        return existing_job

    source_hash = _calculate_source_hash(file_item)
    job = await FileIndexJob.create(
        file_id=file_item.id,
        party_id=file_item.party_id,
        requested_by_id=requested_by_user_id,
        status=INDEX_JOB_STATUS_QUEUED,
        source_hash=source_hash,
        index_version=INDEX_VERSION,
    )
    file_item.status = FILE_STATUS_QUEUED
    file_item.latest_process_message = "Queued for indexing"
    file_item.ingest_error = None
    file_item.index_status = FILE_INDEX_STATUS_QUEUED
    file_item.index_error = None
    file_item.source_hash = source_hash
    file_item.index_version = INDEX_VERSION
    await file_item.save()

    redis = _get_redis_client()
    try:
        await redis.rpush(
            FILE_INGEST_QUEUE_KEY,
            json.dumps({"job_id": str(job.id), "file_id": str(file_item.id)}),
        )
    except Exception as error:
        public_error = "Unable to queue indexing job"
        logger.exception("Unable to queue file indexing job for file %s", file_item.id)
        job.status = INDEX_JOB_STATUS_ERROR
        job.error = public_error
        job.completed_at = datetime.utcnow()
        await job.save()
        file_item.status = FILE_STATUS_ERROR
        file_item.index_status = FILE_INDEX_STATUS_ERROR
        file_item.index_error = public_error
        file_item.latest_process_message = public_error
        await file_item.save()
        raise
    finally:
        await redis.aclose()

    await create_file_process_log(
        file_item,
        stage="QUEUE",
        status="QUEUED",
        message="File queued for indexing",
        details_json={"job_id": str(job.id)},
    )
    return job


async def process_file_ingest(file_id: str, job_id: str | None = None):
    file_item = await File.filter(
        id=file_id,
        is_disabled=False,
        is_deleted=False,
    ).first()

    if file_item is None:
        return None

    job = None
    if job_id:
        job = await FileIndexJob.filter(id=job_id, file_id=file_item.id).first()
        if job is None or job.status not in [INDEX_JOB_STATUS_QUEUED, INDEX_JOB_STATUS_RUNNING]:
            return file_item
    if job is None:
        job = await FileIndexJob.create(
            file_id=file_item.id,
            party_id=file_item.party_id,
            status=INDEX_JOB_STATUS_QUEUED,
            source_hash=_calculate_source_hash(file_item),
            index_version=INDEX_VERSION,
        )

    job.status = INDEX_JOB_STATUS_RUNNING
    job.attempt += 1
    job.started_at = datetime.utcnow()
    job.error = None
    await job.save()

    await update_file_status(
        file_item,
        FILE_STATUS_INDEXING,
        latest_process_message="Indexing in progress",
        clear_ingest_error=True,
    )
    file_item.index_status = FILE_INDEX_STATUS_INDEXING
    file_item.index_error = None
    file_item.index_attempt_count += 1
    await file_item.save()
    await create_file_process_log(
        file_item,
        stage="INDEXING",
        status="STARTED",
        message="Indexing started",
    )

    try:
        if not is_pdf_file(file_item):
            raise ValueError("Only PDF files can be indexed")

        with load_uploaded_file(file_item.filename) as raw_file:
            upload_result = await on_upload_file(
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
            docs, es_doc_ids, index_name = upload_result[:3]
            completed_index_version = (
                upload_result[3] if len(upload_result) > 3 else INDEX_VERSION
            )

        indexed_chunks = len(es_doc_ids or [])
        file_item.es_doc_ids = ",".join(es_doc_ids or [])
        file_item.status = FILE_STATUS_INDEXED
        file_item.latest_process_message = f"Indexed {indexed_chunks} chunks"
        file_item.ingest_error = None
        file_item.index_status = FILE_INDEX_STATUS_INDEXED
        file_item.index_error = None
        file_item.index_version = completed_index_version
        file_item.indexed_source_hash = job.source_hash
        file_item.indexed_at = datetime.utcnow()
        await file_item.save()
        job.status = INDEX_JOB_STATUS_SUCCESS
        job.index_version = completed_index_version
        job.completed_at = datetime.utcnow()
        await job.save()
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
        public_error = str(e) if isinstance(e, ValueError) else "Indexing failed; review server logs"
        logger.exception("File indexing failed for file %s", file_item.id)
        file_item.status = FILE_STATUS_ERROR
        file_item.latest_process_message = public_error
        file_item.ingest_error = public_error
        file_item.index_status = FILE_INDEX_STATUS_ERROR
        file_item.index_error = public_error
        await file_item.save()
        job.status = INDEX_JOB_STATUS_ERROR
        job.error = public_error
        job.completed_at = datetime.utcnow()
        await job.save()
        await _publish_file_status_event(file_item)
        await create_file_process_log(
            file_item,
            stage="INDEXING",
            status="ERROR",
            message=public_error,
            details_json={"error_type": type(e).__name__},
        )
        return file_item


async def run_file_ingest_worker():
    redis = _get_redis_client()
    try:
        while True:
            await _wait_for_redis(redis, "File ingest worker")
            try:
                recoverable_jobs = await FileIndexJob.filter(
                    status__in=[INDEX_JOB_STATUS_QUEUED, INDEX_JOB_STATUS_RUNNING],
                )
                for job in recoverable_jobs:
                    if job.status == INDEX_JOB_STATUS_RUNNING:
                        job.status = INDEX_JOB_STATUS_QUEUED
                        await job.save()
                    await redis.rpush(
                        FILE_INGEST_QUEUE_KEY,
                        json.dumps({"job_id": str(job.id), "file_id": str(job.file_id)}),
                    )

                while True:
                    message = await redis.blpop(FILE_INGEST_QUEUE_KEY, timeout=5)
                    if message is None:
                        continue

                    _, payload = message
                    try:
                        data = json.loads(payload)
                        file_id = data.get("file_id")
                        if file_id:
                            await process_file_ingest(file_id, job_id=data.get("job_id"))
                    except Exception:
                        logger.exception("Unable to process a file ingest queue message")
            except REDIS_CONNECTION_ERRORS:
                logger.warning(
                    "File ingest worker lost its Redis connection at %s; reconnecting.",
                    _redis_target_label(),
                )
    finally:
        await redis.aclose()


async def listen_for_file_status_events(on_message):
    redis = _get_redis_client()
    try:
        while True:
            await _wait_for_redis(redis, "File status listener")
            pubsub = redis.pubsub()
            try:
                await pubsub.subscribe(FILE_STATUS_CHANNEL)
                while True:
                    message = await pubsub.get_message(
                        ignore_subscribe_messages=True,
                        timeout=1.0,
                    )
                    if message is None:
                        await asyncio.sleep(0.1)
                        continue

                    try:
                        payload = json.loads(message["data"])
                        await on_message(payload)
                    except Exception:
                        logger.exception("Unable to handle a file status event")
            except REDIS_CONNECTION_ERRORS:
                logger.warning(
                    "File status listener lost its Redis connection at %s; reconnecting.",
                    _redis_target_label(),
                )
            finally:
                with suppress(*REDIS_CONNECTION_ERRORS):
                    await pubsub.unsubscribe(FILE_STATUS_CHANNEL)
                await pubsub.aclose()
    finally:
        await redis.aclose()
