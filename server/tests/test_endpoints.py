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
SAMPLE_CITY = {"name": "Seattle", "state_code": "WA"}

@pytest.fixture
def sample_city_id():
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}", json=SAMPLE_CITY)
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      yield city_id


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

def test_cities_post_with_state_code():
      """Test creating a city with state code."""
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                              json={"name": "Boston", "state_code": "MA"})
      resp_json = resp.get_json()
      assert ep.CITIES_RESP in resp_json
      assert "city_id" in resp_json[ep.CITIES_RESP]

def test_cities_post_missing_name():
      """Test creating city without required name field."""
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"state_code": "CA"})
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json

def test_cities_post_invalid_data_type():
      """Test creating city with non-dict data."""
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}", json="not a dict")
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json

def test_city_get_valid(sample_city_id):
      """Test getting a single city by ID."""
      # sample city inserted by fixture
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{sample_city_id}")
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.CITY_RESP in resp_json
      assert resp_json[ep.CITY_RESP]["name"] == SAMPLE_CITY["name"]

def test_city_get_not_found():
      """Test getting city that doesn't exist."""
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/nonexistent_id_999")
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json
      assert resp.status_code == NOT_FOUND

def test_city_put_valid():
      """Test updating a city by ID."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Austin", "state_code": "TX"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]

      # Now update it
      resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}",
                            json={"name": "Austin", "state_code": "TEX"})
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.CITY_RESP in resp_json
      assert ep.CITY_ID in resp_json[ep.CITY_RESP]
      
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{city_id}")
      resp_json = resp.get_json()
      assert resp_json[ep.CITY_RESP]["state_code"] == "TEX"

def test_city_put_not_found():
      """Test updating city that doesn't exist."""
      resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/nonexistent_id_999",
                            json={"name": "Nowhere", "state_code": "XX"})
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json
      assert resp.status_code == NOT_FOUND

def test_city_delete_not_found():
      """Test deleting city that doesn't exist."""
      resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/nonexistent_id_999")
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json
      assert resp.status_code == NOT_FOUND