from guillotina.api.service import _safe_int_or_float_cast
from openapi_spec_validator import validate_v3_spec

import os
import pytest
import unittest


pytestmark = pytest.mark.asyncio


SWAGGER_SETTINGS = {"applications": ["guillotina.contrib.swagger"]}


@pytest.mark.app_settings(SWAGGER_SETTINGS)
async def test_get_swagger_definition(container_requester):
    async with container_requester as requester:
        resp, status = await requester("GET", "/@swagger")
        assert status == 200
        assert "/" in resp["paths"]

    async with container_requester as requester:
        resp, status = await requester("GET", "/db/@swagger")
        assert status == 200
        assert "/db" in resp["paths"]

    async with container_requester as requester:
        resp, status = await requester("GET", "/db/guillotina/@swagger")
        assert status == 200
        assert "/db/guillotina" in resp["paths"]


@pytest.mark.app_settings(SWAGGER_SETTINGS)
async def test_get_swagger_index(container_requester):
    async with container_requester as requester:
        resp, status = await requester("GET", "/@docs")
        assert status == 200


@pytest.mark.app_settings(SWAGGER_SETTINGS)
async def test_validate_swagger_definition(container_requester):
    async with container_requester as requester:
        for path in ("/", "/db", "/db/guillotina"):
            resp, status = await requester("GET", os.path.join(path, "@swagger"))
            assert status == 200
            validate_v3_spec(resp)


async def test_validate_arrays_in_query_params(container_requester):
    async with container_requester as requester:
        _, status = await requester("GET", "@queryParamsValidation?numbers=1.0&numbers=2")
        assert status == 200

        _, status = await requester("GET", "@queryParamsValidation?users=u1&users=u2&users=u3")
        assert status == 200

        resp, status = await requester("GET", "@queryParamsValidation?users=u1&users=")
        assert status == 412
        assert resp["validator"] == "minLength"

        resp, status = await requester("GET", "@queryParamsValidation?users=u1")
        assert status == 412
        assert resp["validator"] == "minItems"

        resp, status = await requester(
            "GET", "@queryParamsValidation?users=u1&users=u2&users=u3&users=u4&users=u5&users=u6"
        )
        assert status == 412
        assert resp["validator"] == "maxItems"


@pytest.mark.app_settings(SWAGGER_SETTINGS)
async def test_validate_numbers_and_integers_in_query_params(container_requester):
    async with container_requester as requester:
        _, status = await requester("GET", "@queryParamsValidation?oranges=5")
        assert status == 200

        _, status = await requester("GET", "@queryParamsValidation?kilograms=60.3")
        assert status == 200

        resp, status = await requester("GET", "@queryParamsValidation?oranges=0")
        assert status == 412
        assert resp["validator"] == "minimum"

        resp, status = await requester("GET", "@queryParamsValidation?kilograms=3.2")
        assert status == 412
        assert resp["validator"] == "minimum"


class Test_SafeIntOrFloatCast(unittest.TestCase):
    def _makeOne(self, value):
        return _safe_int_or_float_cast(value)

    def test_with_integers(self):
        value = self._makeOne(2)
        self.assertIsInstance(value, int)
        self.assertEqual(2, value)

    def test_with_integers_from_string(self):
        value = self._makeOne("2")
        self.assertIsInstance(value, int)
        self.assertEqual(2, value)

    def test_with_floats(self):
        value = self._makeOne(3.3)
        self.assertIsInstance(value, float)
        self.assertEqual(3.3, value)

    def test_with_floats_from_string(self):
        value = self._makeOne("3.0")
        self.assertIsInstance(value, float)
        self.assertEqual(3.0, value)

    def test_returns_input_if_cannot_cast(self):
        for foo in ([], None, {}, set(), ""):
            self.assertIs(foo, self._makeOne(foo))
