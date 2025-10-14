from http.client import (
    BAD_REQUEST,
    FORBIDDEN,
    NOT_ACCEPTABLE,
    NOT_FOUND,
    OK,
    SERVICE_UNAVAILABLE,
)

from unittest.mock import patch

import pytest

import server.endpoints as ep

TEST_CLIENT = ep.app.test_client()


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json

"""always returns True to avoid connection errors in tests"""
@patch('cities.queries.db_connect', return_value=True, autospec=True)
def test_cities_get(mock_db_connect):
    resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}")
    resp_json = resp.get_json()
    assert ep.CITIES_RESP in resp_json
    
def test_cities_post():
    resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}", json={"name": "Test City"})
    resp_json = resp.get_json()
    assert ep.CITIES_RESP in resp_json
    assert "city_id" in resp_json[ep.CITIES_RESP]