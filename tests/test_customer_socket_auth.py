import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from src.controllers.functions.ws.auth import authenticate_party_socket


class CustomerSocketAuthTests(unittest.IsolatedAsyncioTestCase):
    async def test_prefixed_cookie_authenticates_the_matching_party(self):
        socket = SimpleNamespace(cookies={"party-1_access_token": "valid"}, query_params={})
        user = SimpleNamespace(party_id="party-1")
        authenticate = AsyncMock(return_value=user)
        self.assertIs(await authenticate_party_socket(socket, "party-1", authenticate), user)
        authenticate.assert_awaited_once_with(access_token="valid")

    async def test_another_partys_valid_session_is_rejected(self):
        socket = SimpleNamespace(cookies={"party-2_access_token": "other-token"}, query_params={})
        authenticate = AsyncMock(return_value=SimpleNamespace(party_id="party-2"))
        self.assertIsNone(await authenticate_party_socket(socket, "party-1", authenticate))

    async def test_admin_cookie_authenticates_without_exposing_tokens_in_the_url(self):
        socket = SimpleNamespace(cookies={"p9-docker_access_token": "admin-token"}, query_params={})
        user = SimpleNamespace(party_id="party-1")
        self.assertIs(await authenticate_party_socket(socket, "party-1", AsyncMock(return_value=user)), user)

    async def test_stale_cookie_does_not_override_a_valid_customer_session(self):
        socket = SimpleNamespace(cookies={"access_token": "stale", "party-2_access_token": "valid"}, query_params={})
        user = SimpleNamespace(party_id="party-1")
        authenticate = AsyncMock(side_effect=[ValueError("Expired"), user])
        self.assertIs(await authenticate_party_socket(socket, "party-1", authenticate), user)

    async def test_missing_and_invalid_tokens_are_rejected(self):
        authenticate = AsyncMock(side_effect=ValueError("Invalid"))
        for cookies in [{}, {"party-1_access_token": "invalid"}]:
            socket = SimpleNamespace(cookies=cookies, query_params={})
            self.assertIsNone(await authenticate_party_socket(socket, "party-1", authenticate))

    async def test_legacy_clients_remain_supported(self):
        user = SimpleNamespace(party_id="party-1")
        for cookies, query in [({"access_token": "valid"}, {}), ({}, {"access_token": "valid"})]:
            socket = SimpleNamespace(cookies=cookies, query_params=query)
            self.assertIs(await authenticate_party_socket(socket, "party-1", AsyncMock(return_value=user)), user)
