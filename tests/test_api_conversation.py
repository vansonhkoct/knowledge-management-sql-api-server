from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from src.controllers.apis import api_conversation as conversation_api


class FakeQ:
    def __init__(self, **conditions):
        self.conditions = conditions

    def matches(self, item):
        for key, expected in self.conditions.items():
            if key.endswith("__icontains"):
                field_name = key[:-11]
                actual = getattr(item, field_name, None)
                if actual is None or str(expected).lower() not in str(actual).lower():
                    return False
                continue

            if getattr(item, key, None) != expected:
                return False

        return True

    def __and__(self, other):
        return FakePredicate(lambda item: self.matches(item) and other.matches(item))

    def __or__(self, other):
        return FakePredicate(lambda item: self.matches(item) or other.matches(item))


class FakePredicate(FakeQ):
    def __init__(self, predicate):
        self.predicate = predicate

    def matches(self, item):
        return self.predicate(item)


@dataclass
class FakeUser:
    id: str
    party_id: str


class FakeStore:
    def __init__(self):
        self.now = datetime(2026, 5, 23, 8, 0, tzinfo=timezone.utc)
        self.chat_counter = 0
        self.message_counter = 0
        self.chats = []
        self.messages = []

    def next_timestamp(self):
        value = self.now
        self.now = self.now + timedelta(seconds=1)
        return value

    def create_chat(self, **kwargs):
        self.chat_counter += 1
        created_at = kwargs.pop("created_at", self.next_timestamp())
        modified_at = kwargs.pop("modified_at", created_at)
        item = FakeChatRecord(
            store=self,
            id=kwargs.pop("id", f"chat-{self.chat_counter}"),
            name=kwargs.pop("name", ""),
            title_is_user_defined=kwargs.pop("title_is_user_defined", False),
            party_id=kwargs.pop("party_id", None),
            user_id=kwargs.pop("user_id", None),
            last_message_preview=kwargs.pop("last_message_preview", None),
            last_message_at=kwargs.pop("last_message_at", None),
            prompt_prefix=kwargs.pop("prompt_prefix", ""),
            created_at=created_at,
            modified_at=modified_at,
            is_disabled=kwargs.pop("is_disabled", False),
            is_deleted=kwargs.pop("is_deleted", False),
        )
        self.chats.append(item)
        return item

    def create_message(self, **kwargs):
        self.message_counter += 1
        created_at = kwargs.pop("created_at", self.next_timestamp())
        item = FakeChatMessageRecord(
            store=self,
            id=kwargs.pop("id", f"message-{self.message_counter}"),
            chat_id=kwargs.pop("chat_id", None),
            user_id=kwargs.pop("user_id", None),
            role=kwargs.pop("role", "USER"),
            body=kwargs.pop("body", ""),
            retrieval_enabled=kwargs.pop("retrieval_enabled", None),
            category_id_snapshot=kwargs.pop("category_id_snapshot", None),
            category_alias_snapshot=kwargs.pop("category_alias_snapshot", None),
            citations_json=kwargs.pop("citations_json", None),
            message_metadata_json=kwargs.pop("message_metadata_json", None),
            created_at=created_at,
            modified_at=kwargs.pop("modified_at", created_at),
            is_deleted=kwargs.pop("is_deleted", False),
        )
        self.messages.append(item)
        return item


@dataclass
class FakeChatRecord:
    store: FakeStore
    id: str
    name: str
    title_is_user_defined: bool
    party_id: str | None
    user_id: str | None
    last_message_preview: str | None
    last_message_at: datetime | None
    prompt_prefix: str
    created_at: datetime
    modified_at: datetime
    is_disabled: bool
    is_deleted: bool

    async def save(self):
        self.modified_at = self.store.next_timestamp()

    async def refresh_from_db(self):
        return self


@dataclass
class FakeChatMessageRecord:
    store: FakeStore
    id: str
    chat_id: str | None
    user_id: str | None
    role: str
    body: str
    retrieval_enabled: bool | None
    category_id_snapshot: str | None
    category_alias_snapshot: str | None
    citations_json: list | None
    message_metadata_json: dict | None
    created_at: datetime
    modified_at: datetime
    is_deleted: bool


class FakeQuerySet:
    def __init__(self, items):
        self.items = list(items)

    def _clone(self, items):
        return FakeQuerySet(items)

    def filter(self, *conditions, **kwargs):
        items = list(self.items)

        for condition in conditions:
            items = [item for item in items if condition.matches(item)]

        if kwargs:
            matcher = FakeQ(**kwargs)
            items = [item for item in items if matcher.matches(item)]

        return self._clone(items)

    def order_by(self, *fields):
        items = list(self.items)
        for field in reversed(fields):
            reverse = field.startswith("-")
            field_name = field[1:] if reverse else field
            items = sorted(
                items,
                key=lambda item: self._sort_value(item, field_name),
                reverse=reverse,
            )

        return self._clone(items)

    def _sort_value(self, item, field_name):
        value = getattr(item, field_name, None)
        if value is None:
            if field_name.endswith("_at"):
                return datetime.min.replace(tzinfo=timezone.utc)
            return ""
        return value

    def offset(self, value):
        return self._clone(self.items[value:])

    def limit(self, value):
        return self._clone(self.items[:value])

    async def first(self):
        return self.items[0] if self.items else None

    async def count(self):
        return len(self.items)

    def __await__(self):
        async def _resolve():
            return list(self.items)

        return _resolve().__await__()


class FakeChatModel:
    store = None

    @classmethod
    async def create(cls, **kwargs):
        return cls.store.create_chat(**kwargs)

    @classmethod
    def filter(cls, *conditions, **kwargs):
        return FakeQuerySet(cls.store.chats).filter(*conditions, **kwargs)


class FakeChatMessageModel:
    store = None

    @classmethod
    async def create(cls, **kwargs):
        return cls.store.create_message(**kwargs)

    @classmethod
    def filter(cls, *conditions, **kwargs):
        return FakeQuerySet(cls.store.messages).filter(*conditions, **kwargs)


@pytest.fixture
def conversation_harness(monkeypatch):
    store = FakeStore()
    user_one = FakeUser(id="user-1", party_id="party-1")
    user_two = FakeUser(id="user-2", party_id="party-2")

    async def fake_fetch_loggedin_user_info(headers):
        token = headers.get("authorization", "").replace("Bearer ", "")
        if token == "token-user-1":
            return user_one, token
        if token == "token-user-2":
            return user_two, token
        raise RuntimeError("Unexpected test token")

    FakeChatModel.store = store
    FakeChatMessageModel.store = store

    monkeypatch.setattr(conversation_api, "fetch_loggedin_user_info", fake_fetch_loggedin_user_info)
    monkeypatch.setattr(conversation_api, "Chat", FakeChatModel)
    monkeypatch.setattr(conversation_api, "ChatMessage", FakeChatMessageModel)
    monkeypatch.setattr(conversation_api, "Q", FakeQ)

    app = FastAPI()
    app.include_router(conversation_api.router)

    return {
        "client": TestClient(app),
        "store": store,
        "user_one": user_one,
        "user_two": user_two,
    }


def test_conversation_endpoints_enforce_user_ownership(conversation_harness):
    client = conversation_harness["client"]
    store = conversation_harness["store"]
    user_one = conversation_harness["user_one"]
    user_two = conversation_harness["user_two"]

    owned_chat = store.create_chat(user_id=user_one.id, party_id=user_one.party_id, name="Owned conversation")
    foreign_chat = store.create_chat(user_id=user_two.id, party_id=user_two.party_id, name="Foreign conversation")

    response = client.get(
        "/api/v1/conversation",
        headers={"authorization": "Bearer token-user-1"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["data"]["pagination"]["total_count"] == 1
    assert [item["id"] for item in payload["data"]["items"]] == [owned_chat.id]

    forbidden_response = client.get(
        "/api/v1/conversation/single",
        params={"id": foreign_chat.id},
        headers={"authorization": "Bearer token-user-1"},
    )

    assert forbidden_response.status_code == 404


def test_soft_deleted_conversations_only_appear_in_deleted_view(conversation_harness):
    client = conversation_harness["client"]
    store = conversation_harness["store"]
    user_one = conversation_harness["user_one"]

    chat = store.create_chat(user_id=user_one.id, party_id=user_one.party_id, name="Delete me")

    delete_response = client.delete(
        "/api/v1/conversation",
        params={"id": chat.id},
        headers={"authorization": "Bearer token-user-1"},
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["data"]["item"]["is_deleted"] is True

    active_list_response = client.get(
        "/api/v1/conversation",
        headers={"authorization": "Bearer token-user-1"},
    )

    assert active_list_response.status_code == 200
    assert active_list_response.json()["data"]["pagination"]["total_count"] == 0

    deleted_list_response = client.get(
        "/api/v1/conversation",
        params={"include_deleted": 1},
        headers={"authorization": "Bearer token-user-1"},
    )

    assert deleted_list_response.status_code == 200
    assert deleted_list_response.json()["data"]["pagination"]["total_count"] == 1
    assert deleted_list_response.json()["data"]["items"][0]["id"] == chat.id

    restore_response = client.post(
        "/api/v1/conversation/restore",
        params={"id": chat.id},
        headers={"authorization": "Bearer token-user-1"},
    )

    assert restore_response.status_code == 200
    assert restore_response.json()["data"]["item"]["is_deleted"] is False


def test_ai_messages_preserve_frozen_citation_payloads(conversation_harness):
    client = conversation_harness["client"]
    store = conversation_harness["store"]
    user_one = conversation_harness["user_one"]

    chat = store.create_chat(user_id=user_one.id, party_id=user_one.party_id, name="Citation conversation")

    citations_payload = [
        {
            "file_id": "file-1",
            "page": 3,
            "filename": "policy.pdf",
        },
        {
            "file_id": "file-1",
            "page": 5,
            "filename": "policy.pdf",
        },
    ]
    metadata_payload = {
        "citations_frozen": True,
        "answer_model": "test-model",
    }

    create_message_response = client.post(
        "/api/v1/conversation/message",
        json={
            "conversation_id": chat.id,
            "role": "AI",
            "content": "Frozen citation answer",
            "retrieval_enabled": True,
            "citations_json": citations_payload,
            "message_metadata_json": metadata_payload,
        },
        headers={"authorization": "Bearer token-user-1"},
    )

    assert create_message_response.status_code == 200
    created_message = create_message_response.json()["data"]["item"]
    assert created_message["citations_json"] == citations_payload
    assert created_message["message_metadata_json"] == metadata_payload

    single_response = client.get(
        "/api/v1/conversation/single",
        params={"id": chat.id, "include_messages": 1},
        headers={"authorization": "Bearer token-user-1"},
    )

    assert single_response.status_code == 200
    messages = single_response.json()["data"]["item"]["messages"]
    assert len(messages) == 1
    assert messages[0]["role"] == "AI"
    assert messages[0]["citations_json"] == citations_payload
    assert messages[0]["message_metadata_json"] == metadata_payload