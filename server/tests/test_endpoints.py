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
import cities.queries as cqry

TEST_CLIENT = ep.app.test_client()

# fixtures

@pytest.fixture
def test_client():
    """Fixture to provide a test client."""
    return ep.app.test_client()


@pytest.fixture
def sample_city_data():
    """Fixture to provide sample city data."""
    return {"name": "Test City", "state_code": "TC"}


@pytest.fixture
def create_test_city(test_client):
    """Fixture to create a test city and return its ID."""
    def _create_city(name="Fixture City", state_code="FC"):
        resp = test_client.post(
            f"{ep.CITIES_EPS}",
            json={"name": name, "state_code": state_code}
        )
        return resp.get_json()[ep.CITIES_RESP]["city_id"]
    return _create_city


@pytest.fixture
def mock_city_cache():
    """Fixture to provide a mock city cache."""
    return {
        '1': {'name': 'New York', 'state_code': 'NY'},
        '2': {'name': 'Los Angeles', 'state_code': 'CA'},
    }

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

def test_city_get_valid():
      """Test getting a single city by ID."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Seattle", "state_code": "WA"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]

      # Now get it
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.CITY_RESP in resp_json
      assert resp_json[ep.CITY_RESP]["name"] == "Seattle"

def test_city_get_not_found():
      """Test getting city that doesn't exist."""
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/nonexistent_id_999")
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json
      assert resp.status_code == NOT_FOUND


def test_endpoints_get():
      """Test that /endpoints returns a list of available endpoints."""
      resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.ENDPOINT_RESP in resp_json
      assert isinstance(resp_json[ep.ENDPOINT_RESP], list)


def test_endpoints_not_empty():
      """Test that /endpoints returns a non-empty list."""
      resp = TEST_CLIENT.get(ep.ENDPOINT_EP)
      resp_json = resp.get_json()
      endpoints_list = resp_json[ep.ENDPOINT_RESP]
      
      assert len(endpoints_list) > 0


# PUT (Update) Tests
def test_city_put_valid():
      """Test updating a city with valid data."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Portland", "state_code": "OR"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      
      # Update the city
      resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}",
                            json={"name": "Portland", "state_code": "ME"})
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.CITY_RESP in resp_json
      assert resp_json[ep.CITY_RESP][ep.CITY_ID] == city_id
      
      # Verify the update
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{city_id}")
      resp_json = resp.get_json()
      assert resp_json[ep.CITY_RESP]["state_code"] == "ME"

def test_city_put_not_found():
      """Test updating a city that doesn't exist."""
      resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/nonexistent_id_999",
                            json={"name": "Ghost City"})
      assert resp.status_code == NOT_FOUND
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json


def test_city_put_invalid_data_type():
      """Test updating a city with non-dict data."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Denver", "state_code": "CO"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      
      # Try to update with invalid data
      resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}", json="not a dict")
      assert resp.status_code == BAD_REQUEST
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json


def test_city_put_empty_body():
      """Test updating a city with empty dict."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Phoenix", "state_code": "AZ"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      
      # Update with empty dict (should still work, just no changes)
      resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}", json={})
      assert resp.status_code == OK


# DELETE Tests
def test_city_delete_valid():
      """Test deleting a city with valid ID."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Miami", "state_code": "FL"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      
      # Delete the city
      resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.MESSAGE in resp_json
      assert city_id in resp_json[ep.MESSAGE]


def test_city_delete_and_verify_removed():
      """Test that deleted city is actually removed."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Tampa", "state_code": "FL"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      
      # Delete the city
      resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == OK
      
      # Verify it's gone
      resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == NOT_FOUND
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json


def test_city_delete_not_found():
      """Test deleting a city that doesn't exist."""
      resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/nonexistent_id_999")
      assert resp.status_code == NOT_FOUND
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json


def test_city_delete_twice():
      """Test deleting the same city twice (should fail second time)."""
      # First create a city
      resp = TEST_CLIENT.post(f"{ep.CITIES_EPS}",
                             json={"name": "Orlando", "state_code": "FL"})
      city_id = resp.get_json()[ep.CITIES_RESP]["city_id"]
      
      # Delete once
      resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == OK
      
      # Try to delete again
      resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == NOT_FOUND
      resp_json = resp.get_json()
      assert ep.ERROR in resp_json


# ============= TESTS USING FIXTURES =============

def test_city_post_with_fixture(test_client, sample_city_data):
      """Test creating a city using fixtures."""
      resp = test_client.post(f"{ep.CITIES_EPS}", json=sample_city_data)
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert ep.CITIES_RESP in resp_json
      assert "city_id" in resp_json[ep.CITIES_RESP]


def test_city_get_with_fixture(test_client, create_test_city):
      """Test getting a city using create_test_city fixture."""
      city_id = create_test_city(name="Chicago", state_code="IL")
      
      resp = test_client.get(f"{ep.CITIES_EPS}/{city_id}")
      assert resp.status_code == OK
      resp_json = resp.get_json()
      assert resp_json[ep.CITY_RESP]["name"] == "Chicago"


def test_city_update_with_fixture(test_client, create_test_city):
      """Test updating a city using fixtures."""
      city_id = create_test_city(name="San Francisco", state_code="CA")
      
      resp = test_client.put(
          f"{ep.CITIES_EPS}/{city_id}",
          json={"name": "San Francisco", "state_code": "CAL"}
      )
      assert resp.status_code == OK
