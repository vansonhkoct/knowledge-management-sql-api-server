import asyncio
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from tortoise import Tortoise

from src.controllers.functions._generic.secretutils import (
    decrypt_secret,
    encrypt_secret,
    migrate_legacy_ai_endpoint_secrets,
)
from src.controllers.functions.esbundle.include.ElasticSearchDao.ESVo import ESVoDocSearch
from src.controllers.functions.rag.profile import embedding_profile_id
from src.controllers.functions.user.setup import superadmin_exists
from src.controllers.functions.user.permissions import (
    PermissionCode,
    assign_role_permissions,
)
from src.apiapp.APIApplication import _sanitize_http_exception_detail
from src.controllers.functions.user.userauth_session import fetch_loggedin_user_info


def test_missing_authorization_header_is_forbidden():
    async def run():
        with pytest.raises(HTTPException) as error:
            await fetch_loggedin_user_info(headers={})
        assert error.value.status_code == 403
        assert error.value.detail == "Authentication required"

    asyncio.run(run())


def test_secret_round_trip(monkeypatch):
    monkeypatch.setenv("AI_ENDPOINT_SECRET_KEY", "test-only-high-entropy-master-key")
    encrypted = encrypt_secret("provider-secret")
    assert encrypted.startswith("enc:v1:")
    assert "provider-secret" not in encrypted
    assert decrypt_secret(encrypted) == "provider-secret"


def test_search_value_object_owns_filter_lists():
    category_ids = ["category-1"]
    tags = ["policy"]
    first = ESVoDocSearch(
        index_name="party-1",
        question="question",
        query_strings=None,
        query_vectors=None,
        document_category_ids=category_ids,
        document_tags=tags,
    )
    second = ESVoDocSearch(
        index_name="party-1",
        question="question",
        query_strings=None,
        query_vectors=None,
    )

    assert first.document_category_ids == category_ids
    assert first.document_tags == tags
    assert first.document_file_ids == []
    assert second.document_file_ids == []
    assert first.document_file_ids is not second.document_file_ids


def test_embedding_profile_changes_only_with_embedding_configuration():
    endpoint = SimpleNamespace(
        id="00000000-0000-0000-0000-000000000001",
        provider="openai-compatible",
        base_url="https://ai.example.com",
        api_path="/v1",
        model_name="bge-m3",
        headers_json={"X-Tenant": "shared"},
        options_json={"encoding_format": "float"},
    )
    profile_options = {
        "index_version": "pdf-v1",
        "chunk_size": 900,
        "chunk_overlap": 100,
    }
    original = embedding_profile_id(endpoint, **profile_options)
    endpoint.name = "Display name changes do not affect vectors"
    assert embedding_profile_id(endpoint, **profile_options) == original
    endpoint.model_name = "bge-m3-v2"
    assert embedding_profile_id(endpoint, **profile_options) != original


def test_production_http_errors_do_not_expose_stacktraces(monkeypatch):
    detail = {"message": "E_TEST", "error": "database password leaked", "stacktrace": "secret trace"}
    monkeypatch.setenv("APP_ENV", "production")
    assert _sanitize_http_exception_detail(500, detail) == {
        "message": "E_TEST",
        "error": "Internal server error",
    }
    assert _sanitize_http_exception_detail(400, detail) == detail


def test_sqlite_schema_and_legacy_secret_migration(tmp_path, monkeypatch):
    monkeypatch.setenv("AI_ENDPOINT_SECRET_KEY", "test-only-high-entropy-master-key")

    async def run():
        await Tortoise.init(
            config={
                "connections": {"default": f"sqlite://{tmp_path / 'application.sqlite3'}"},
                "apps": {
                    "models": {
                        "models": ["src.schemas.master", "aerich.models"],
                        "default_connection": "default",
                    }
                },
            }
        )
        try:
            await Tortoise.generate_schemas(safe=True)
            connection = Tortoise.get_connection("default")
            rows = await connection.execute_query_dict(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            table_names = {row["name"] for row in rows}
            assert {
                "file",
                "file_index_job",
                "ai_model_endpoint",
                "role_permission_assignment",
            } <= table_names
            assert "permission" not in table_names
            assert "_rel_role_permission" not in table_names

            assert await superadmin_exists() is False

            from src.models.master import AIModelEndpoint, Party, Role, User

            party = await Party.create(name="Test organization")
            role = await Role.create(code="superadmin", party=party)
            await User.create(
                name="Test superadmin",
                username="superadmin",
                party=party,
                role=role,
            )
            await assign_role_permissions(role, [PermissionCode.PARTY_MANAGE])
            await assign_role_permissions(role, [PermissionCode.PARTY_MANAGE])
            await role.fetch_related("permission_assignments")
            assert {
                item.permission_code for item in role.permission_assignments
            } == {PermissionCode.PARTY_MANAGE}
            assert await superadmin_exists() is True

            endpoint = await AIModelEndpoint.create(
                name="Legacy endpoint",
                model_type="LLM",
                base_url="https://example.com",
                model_name="example-model",
                api_key="legacy-plaintext-secret",
            )
            assert await migrate_legacy_ai_endpoint_secrets() == 1
            await endpoint.refresh_from_db()
            assert endpoint.api_key.startswith("enc:v1:")
            assert decrypt_secret(endpoint.api_key) == "legacy-plaintext-secret"
        finally:
            await Tortoise.close_connections()

    asyncio.run(run())
