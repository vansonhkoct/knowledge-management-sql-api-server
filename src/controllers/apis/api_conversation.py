import re
import traceback

from fastapi import APIRouter, HTTPException, Request
from tortoise.expressions import Q

from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info
from src.models.master import Chat, ChatMessage


router = APIRouter(prefix="/api/v1")


TAG_C001 = "C_CONVERSATION001"
TAG_E001 = "E_CONVERSATION001"
DEFAULT_EMPTY_CONVERSATION_TITLE = "New conversation"


def _serialize_datetime(value):
  return value.isoformat() if value is not None else None


def _normalize_whitespace(value: str | None) -> str:
  return re.sub(r"\s+", " ", (value or "")).strip()


def _build_preview(value: str | None, limit: int = 160) -> str:
  normalized = _normalize_whitespace(value)
  if len(normalized) <= limit:
    return normalized
  return f"{normalized[: limit - 3].rstrip()}..."


def _build_auto_title(value: str | None, limit: int = 80) -> str:
  preview = _build_preview(value, limit=limit)
  return preview or DEFAULT_EMPTY_CONVERSATION_TITLE


async def _serialize_conversation_message(item: ChatMessage) -> dict:
  return {
    "id": str(item.id),
    "conversation_id": str(item.chat_id) if item.chat_id else None,
    "user_id": str(item.user_id) if item.user_id else None,
    "role": item.role,
    "content": item.body,
    "retrieval_enabled": item.retrieval_enabled,
    "category_id_snapshot": str(item.category_id_snapshot) if item.category_id_snapshot else None,
    "category_alias_snapshot": item.category_alias_snapshot,
    "citations_json": item.citations_json,
    "message_metadata_json": item.message_metadata_json,
    "created_at": _serialize_datetime(item.created_at),
    "modified_at": _serialize_datetime(item.modified_at),
  }


async def _serialize_conversation(item: Chat, include_messages: bool = False, messages: list[ChatMessage] | None = None) -> dict:
  serialized_messages = []
  if include_messages:
    serialized_messages = [await _serialize_conversation_message(message) for message in (messages or [])]

  return {
    "id": str(item.id),
    "title": item.name or DEFAULT_EMPTY_CONVERSATION_TITLE,
    "title_is_user_defined": item.title_is_user_defined,
    "party_id": str(item.party_id) if item.party_id else None,
    "user_id": str(item.user_id) if item.user_id else None,
    "last_message_preview": item.last_message_preview,
    "last_message_at": _serialize_datetime(item.last_message_at),
    "prompt_prefix": item.prompt_prefix,
    "created_at": _serialize_datetime(item.created_at),
    "modified_at": _serialize_datetime(item.modified_at),
    "is_disabled": item.is_disabled,
    "is_deleted": item.is_deleted,
    "messages": serialized_messages,
  }


async def _fetch_conversation_messages(chat_id: str, message_limit: int) -> list[ChatMessage]:
  if message_limit <= 0:
    return []

  items = list(
    await ChatMessage
      .filter(chat_id=chat_id, is_deleted=False)
      .order_by("-created_at")
      .limit(message_limit)
  )

  items.reverse()
  return items


async def _update_conversation_summary(chat: Chat, content: str | None, last_message_at = None):
  chat.last_message_preview = _build_preview(content)
  chat.last_message_at = last_message_at or chat.modified_at
  await chat.save()


@router.get("/conversation")
async def fetch_conversations(
  request: Request,
  page: int = 0,
  limit: int = 20,
  search: str = None,
  include_deleted: int = 0,
  party_id: str = None,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    limit = max(1, min(limit, 100))
    offset = page * limit

    filters = Q(user_id=user.id, is_disabled=False)
    filters &= Q(is_deleted=(include_deleted == 1)) if include_deleted in (0, 1) else Q()

    if include_deleted == 0:
      filters &= Q(is_deleted=False)

    if party_id:
      filters &= Q(party_id=party_id)

    if search:
      filters &= (Q(name__icontains=search) | Q(last_message_preview__icontains=search))

    items = list(
      await Chat
        .filter(filters)
        .order_by("-last_message_at", "-modified_at")
        .offset(offset)
        .limit(limit)
    )

    total_count = await Chat.filter(filters).count()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "pagination": {
          "page": page,
          "limit": limit,
          "total_count": total_count,
        },
        "items": [await _serialize_conversation(item) for item in items],
      },
    }

  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.get("/conversation/single")
async def fetch_single_conversation(
  request: Request,
  id: str,
  include_messages: int = 1,
  message_limit: int = 100,
  include_deleted: int = 0,
):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    filters = Q(id=id, user_id=user.id, is_disabled=False)
    if include_deleted == 0:
      filters &= Q(is_deleted=False)

    item = await Chat.filter(filters).first()
    if item is None:
      raise HTTPException(status_code=404, detail="Conversation not found")

    messages = []
    if include_messages == 1:
      messages = await _fetch_conversation_messages(chat_id=item.id, message_limit=max(1, min(message_limit, 500)))

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_conversation(item, include_messages=(include_messages == 1), messages=messages),
      },
    }

  except HTTPException as e:
    raise e
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.post("/conversation")
async def create_conversation(request: Request):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    data = await request.json()

    title = _normalize_whitespace(data.get("title"))

    item = await Chat.create(
      user_id=user.id,
      party_id=user.party_id,
      name=title,
      title_is_user_defined=bool(title),
      prompt_prefix=data.get("prompt_prefix") or "",
    )

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_conversation(item),
      },
    }

  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.post("/conversation/message")
async def create_conversation_message(request: Request):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    data = await request.json()

    conversation_id = data.get("conversation_id")
    if not conversation_id:
      raise HTTPException(status_code=400, detail="conversation_id is required")

    role = (data.get("role") or "USER").upper()
    if role not in ("USER", "AI"):
      raise HTTPException(status_code=400, detail="role must be USER or AI")

    content = data.get("content")
    if content is None or _normalize_whitespace(content) == "":
      raise HTTPException(status_code=400, detail="content is required")

    conversation = await Chat.filter(
      id=conversation_id,
      user_id=user.id,
      is_disabled=False,
      is_deleted=False,
    ).first()
    if conversation is None:
      raise HTTPException(status_code=404, detail="Conversation not found")

    message = await ChatMessage.create(
      chat_id=conversation.id,
      user_id=user.id,
      role=role,
      body=content,
      retrieval_enabled=data.get("retrieval_enabled"),
      category_id_snapshot=data.get("category_id_snapshot"),
      category_alias_snapshot=data.get("category_alias_snapshot"),
      citations_json=data.get("citations_json"),
      message_metadata_json=data.get("message_metadata_json"),
    )

    if role == "USER" and not conversation.title_is_user_defined and _normalize_whitespace(conversation.name) == "":
      conversation.name = _build_auto_title(content)

    await _update_conversation_summary(conversation, content, last_message_at=message.created_at)
    await conversation.refresh_from_db()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "conversation": await _serialize_conversation(conversation),
        "item": await _serialize_conversation_message(message),
      },
    }

  except HTTPException as e:
    raise e
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.patch("/conversation")
async def update_conversation(request: Request, id: str):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)
    data = await request.json()

    item = await Chat.filter(
      id=id,
      user_id=user.id,
      is_disabled=False,
      is_deleted=False,
    ).first()
    if item is None:
      raise HTTPException(status_code=404, detail="Conversation not found")

    if "title" in data:
      item.name = _normalize_whitespace(data.get("title"))
      item.title_is_user_defined = _normalize_whitespace(data.get("title")) != ""

    if "prompt_prefix" in data:
      item.prompt_prefix = data.get("prompt_prefix") or ""

    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_conversation(item),
      },
    }

  except HTTPException as e:
    raise e
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.delete("/conversation")
async def delete_conversation(request: Request, id: str):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    item = await Chat.filter(
      id=id,
      user_id=user.id,
      is_disabled=False,
      is_deleted=False,
    ).first()
    if item is None:
      raise HTTPException(status_code=404, detail="Conversation not found")

    item.is_deleted = True
    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_conversation(item),
      },
    }

  except HTTPException as e:
    raise e
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )


@router.post("/conversation/restore")
async def restore_conversation(request: Request, id: str):
  try:
    headers = request.headers
    user, access_token = await fetch_loggedin_user_info(headers=headers)

    item = await Chat.filter(
      id=id,
      user_id=user.id,
      is_disabled=False,
      is_deleted=True,
    ).first()
    if item is None:
      raise HTTPException(status_code=404, detail="Conversation not found")

    item.is_deleted = False
    await item.save()

    return {
      "success": True,
      "message": TAG_C001,
      "data": {
        "item": await _serialize_conversation(item),
      },
    }

  except HTTPException as e:
    raise e
  except Exception as e:
    stacktrace = traceback.format_exc()
    raise HTTPException(
      status_code=500,
      detail={
        "message": TAG_E001,
        "error": str(e),
        "stacktrace": stacktrace,
      }
    )