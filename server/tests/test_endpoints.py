from http.client import (
    BAD_REQUEST,
    NOT_FOUND,
    OK,
    CREATED,
)

import uuid
import time

import pytest

import server.endpoints as ep
import cities.queries as cqry
import parks.queries as pqry

TEST_CLIENT = ep.app.test_client()

# Default test country/state for nested city routes
TEST_COUNTRY = 'US'
TEST_STATE = 'TX'

# Counter for unique codes
_code_counter = [0]


def get_unique_code(prefix=''):
    """Generate a unique 2-3 letter code for testing (letters only)."""
    _code_counter[0] += 1
    # Use counter + time to ensure uniqueness
    n = _code_counter[0] + int(time.time() * 1000) % 10000
    # Convert number to base-26 letters
    letters = ''
    for _ in range(3):
        letters = chr(ord('A') + (n % 26)) + letters
        n //= 26
    return letters[:3]


def ensure_test_country_exists(country_code=TEST_COUNTRY):
    """Ensure the test country exists for nested route tests."""
    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}/{country_code}")
    if resp.status_code == NOT_FOUND:
        TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json={
            "name": f"Test Country {country_code}",
            "code": country_code
        })


def ensure_test_state_exists(country_code=TEST_COUNTRY, state_code=TEST_STATE):
    """Ensure the test state exists for nested route tests."""
    ensure_test_country_exists(country_code)
    resp = TEST_CLIENT.get(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}")
    if resp.status_code == NOT_FOUND:
        TEST_CLIENT.post(
            f"{ep.COUNTRIES_EPS}/{country_code}/states",
            json={
                "name": f"Test State {state_code}",
                "state_code": state_code,
                "country_code": country_code
            }
        )


# fixtures

@pytest.fixture
def test_client():
    """Fixture to provide a test client."""
    return ep.app.test_client()


@pytest.fixture
def sample_city_data():
    """Fixture to provide sample city data."""
    return {"name": "Test City", "state_code": TEST_STATE}


@pytest.fixture
def create_test_city(test_client):
    """Fixture to create a test city via nested route and return its ID."""
    def _create_city(name="Fixture City", state_code=TEST_STATE,
                     country_code=TEST_COUNTRY):
        ensure_test_state_exists(country_code, state_code)
        resp = test_client.post(
            f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}/cities",
            json={"name": name}
        )
        return resp.get_json()[ep.CITY_RESP]["_id"]
    return _create_city


@pytest.fixture
def mock_city_cache():
    """Fixture to provide a mock city cache."""
    return {
        '1': {'name': 'New York', 'state_code': 'NY'},
        '2': {'name': 'Los Angeles', 'state_code': 'CA'},
    }


@pytest.fixture
def create_test_park(test_client):
    """Fixture to create a test park via
    API and return (park_id, park_code)."""
    def _create_park(name=None, state_code=TEST_STATE,
                     location="Somewhere", description="Test park"):
        park_data = {
            "name": name or f"Test Park {uuid.uuid4().hex[:6]}",
            "state_code": state_code,
            "location": location,
            "description": description,
            "park_code": f"P{uuid.uuid4().hex[:6]}"
        }
        resp = test_client.post(ep.PARKS_EPS, json=park_data)
        resp_json = resp.get_json()
        park_info = resp_json.get('Park') or resp_json.get('Parks')
        park_id = park_info['_id']
        park_code = park_info.get('park_code')  # might be None
        return park_id, park_code
    return _create_park


def test_hello():
    resp = TEST_CLIENT.get(ep.HELLO_EP)
    resp_json = resp.get_json()
    assert ep.HELLO_RESP in resp_json


def test_cities_get():
    """Test getting all cities."""
    resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}")
    resp_json = resp.get_json()
    assert ep.CITIES_RESP in resp_json
    assert isinstance(resp_json[ep.CITIES_RESP], list)


def test_cities_post_via_nested_route():
    """Test creating a city via nested route."""
    ensure_test_state_exists()
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json={"name": "Test City"}
    )
    resp_json = resp.get_json()
    assert resp.status_code == CREATED
    assert ep.CITY_RESP in resp_json
    assert "_id" in resp_json[ep.CITY_RESP]
    city_id = resp_json[ep.CITY_RESP]['_id']
    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_cities_post_with_state_code():
    """Test creating a city with state code via nested route."""
    ensure_test_state_exists(TEST_COUNTRY, "MA")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/MA/cities",
        json={"name": "Boston"}
    )
    resp_json = resp.get_json()
    assert resp.status_code == CREATED
    assert ep.CITY_RESP in resp_json
    assert "_id" in resp_json[ep.CITY_RESP]

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{resp_json[ep.CITY_RESP]['_id']}")


def test_cities_post_missing_name():
    """Test creating city without required name field."""
    ensure_test_state_exists()
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json={"population": 100000}
    )
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_cities_post_invalid_data_type():
    """Test creating city with non-dict data."""
    ensure_test_state_exists()
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json="not a dict"
    )
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_city_get_valid():
    """Test getting a single city by ID."""
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "WA")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/WA/cities",
        json={"name": "Seattle"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

    # Now get it via flat route
    resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{city_id}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.CITY_RESP in resp_json
    assert resp_json[ep.CITY_RESP]["name"] == "Seattle"

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_city_get_not_found():
    """Test getting city that doesn't exist."""
    # Use a valid ObjectId format that doesn't exist
    resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/507f1f77bcf86cd799439011")
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
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "OR")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/OR/cities",
        json={"name": "Portland"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

    # Update the city
    resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}",
                           json={"name": "Portland", "state_code": "ME"})
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.CITY_RESP in resp_json

    # Verify the update
    resp = TEST_CLIENT.get(f"{ep.CITIES_EPS}/{city_id}")
    resp_json = resp.get_json()
    assert resp_json[ep.CITY_RESP]["state_code"] == "ME"

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_city_put_not_found():
    """Test updating a city that doesn't exist."""
    resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/507f1f77bcf86cd799439011",
                           json={"name": "Ghost City"})
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_city_put_invalid_data_type():
    """Test updating a city with non-dict data."""
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "CO")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/CO/cities",
        json={"name": "Denver"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

    # Try to update with invalid data
    resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}", json="not a dict")
    assert resp.status_code == BAD_REQUEST
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_city_put_empty_body():
    """Test updating a city with empty dict."""
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "AZ")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/AZ/cities",
        json={"name": "Phoenix"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

    # Update with empty dict (should still work, just no changes)
    resp = TEST_CLIENT.put(f"{ep.CITIES_EPS}/{city_id}", json={})
    assert resp.status_code == OK

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


# DELETE Tests
def test_city_delete_valid():
    """Test deleting a city with valid ID."""
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "FL")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/FL/cities",
        json={"name": "Miami"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

    # Delete the city
    resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.MESSAGE in resp_json
    assert city_id in resp_json[ep.MESSAGE]


def test_city_delete_and_verify_removed():
    """Test that deleted city is actually removed."""
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "FL")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/FL/cities",
        json={"name": "Tampa"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

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
    resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/507f1f77bcf86cd799439011")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_city_delete_twice():
    """Test deleting the same city twice (should fail second time)."""
    # First create a city via nested route
    ensure_test_state_exists(TEST_COUNTRY, "FL")
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/FL/cities",
        json={"name": "Orlando"}
    )
    city_id = resp.get_json()[ep.CITY_RESP]["_id"]

    # Delete once
    resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
    assert resp.status_code == OK

    # Try to delete again
    resp = TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


# ============= CITIES IN STATE VIA NESTED ROUTE =============

def test_cities_in_state_via_nested_route():
    """Test getting cities in a state via nested route."""
    ensure_test_state_exists(TEST_COUNTRY, TEST_STATE)

    # Create cities in the state
    resp1 = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json={"name": "Houston"}
    )
    resp2 = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json={"name": "Dallas"}
    )
    resp3 = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json={"name": "Austin"}
    )

    city_id_1 = resp1.get_json()[ep.CITY_RESP]["_id"]
    city_id_2 = resp2.get_json()[ep.CITY_RESP]["_id"]
    city_id_3 = resp3.get_json()[ep.CITY_RESP]["_id"]

    # Get cities in Texas via nested route
    resp = TEST_CLIENT.get(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.CITIES_RESP in resp_json

    # Filter for cities we just created (in case DB has others)
    tx_cities = [city for city in resp_json[ep.CITIES_RESP]
                 if city.get('name') in ['Houston', 'Dallas', 'Austin']]
    assert len(tx_cities) >= 3

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id_1}")
    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id_2}")
    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id_3}")


# ============= TESTS USING FIXTURES =============

def test_city_post_with_fixture(test_client, sample_city_data):
    """Test creating a city using fixtures."""
    ensure_test_state_exists()
    resp = test_client.post(
        f"{ep.COUNTRIES_EPS}/{TEST_COUNTRY}/states/{TEST_STATE}/cities",
        json=sample_city_data
    )
    assert resp.status_code == CREATED
    resp_json = resp.get_json()
    assert ep.CITY_RESP in resp_json
    assert "_id" in resp_json[ep.CITY_RESP]

    city_id = resp_json[ep.CITY_RESP]['_id']
    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_city_get_with_fixture(test_client, create_test_city):
    """Test getting a city using create_test_city fixture."""
    ensure_test_state_exists(TEST_COUNTRY, "IL")
    city_id = create_test_city(name="Chicago", state_code="IL")

    resp = test_client.get(f"{ep.CITIES_EPS}/{city_id}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert resp_json[ep.CITY_RESP]["name"] == "Chicago"

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_city_update_with_fixture(test_client, create_test_city):
    """Test updating a city using fixtures."""
    ensure_test_state_exists(TEST_COUNTRY, "CA")
    city_id = create_test_city(name="San Francisco", state_code="CA")

    resp = test_client.put(
        f"{ep.CITIES_EPS}/{city_id}",
        json={"name": "San Francisco", "state_code": "OR"}
    )
    assert resp.status_code == OK

    TEST_CLIENT.delete(f"{ep.CITIES_EPS}/{city_id}")


def test_update_nonexistent_city():
    """Test if updating a non-existent city raises KeyError."""
    # Use a valid ObjectId format
    city_id = "507f1f77bcf86cd799439011"
    with pytest.raises(KeyError):
        cqry.update(city_id, {cqry.NAME: "Ghosttown"})


# ============= STATE ENDPOINT TESTS =============

def test_states_get():
    """Test getting all states."""
    resp = TEST_CLIENT.get(f"{ep.STATES_EPS}")
    resp_json = resp.get_json()
    assert ep.STATES_RESP in resp_json
    assert isinstance(resp_json[ep.STATES_RESP], list)


def test_states_post_via_nested_route():
    """Test creating a state via nested route."""
    # First create the country (use unique code to avoid conflicts)
    country_code = get_unique_code('S')
    TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json={
        "name": "Test Country SP", "code": country_code})

    state_code = get_unique_code('T')
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{country_code}/states",
        json={
            "name": "Test State",
            "state_code": state_code,
            "capital": "Test Capital",
            "population": 1000000
        }
    )
    resp_json = resp.get_json()
    assert resp.status_code == CREATED
    assert ep.STATE_RESP in resp_json
    assert "state_code" in resp_json[ep.STATE_RESP]
    assert "country_code" in resp_json[ep.STATE_RESP]

    # Cleanup using nested route
    TEST_CLIENT.delete(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}")
    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_state_get_via_nested_route():
    """Test getting a single state via nested route."""
    # First create the country
    country_code = get_unique_code('G')
    TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json={
        "name": "Test Country SG", "code": country_code})

    state_code = get_unique_code('T')
    TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{country_code}/states",
        json={
            "name": "Test State Get",
            "state_code": state_code,
            "capital": "Test Capital",
            "population": 12800000
        }
    )

    # Get via nested route
    resp = TEST_CLIENT.get(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.STATE_RESP in resp_json
    assert resp_json[ep.STATE_RESP]["name"] == "Test State Get"

    # Cleanup
    TEST_CLIENT.delete(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}")
    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_state_put_via_nested_route():
    """Test updating a state via nested route."""
    # First create the country
    country_code = get_unique_code('U')
    TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json={
        "name": "Test Country ZZ", "code": country_code})

    state_code = get_unique_code('Z')
    TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{country_code}/states",
        json={
            "name": "Test State Update",
            "state_code": state_code,
            "capital": "Old Capital",
            "population": 12800000
        }
    )

    update_resp = TEST_CLIENT.put(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}",
        json={
            "name": "Updated State",
            "capital": "New Capital",
            "population": 13000000
        }
    )

    assert update_resp.status_code == OK
    data = update_resp.get_json()[ep.STATE_RESP]
    assert data["name"] == "Updated State"
    assert data["capital"] == "New Capital"
    assert data["population"] == 13000000

    # Cleanup
    TEST_CLIENT.delete(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code}")
    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_states_by_country():
    """Test getting all states in a country."""
    # Create a country
    country_code = get_unique_code('C')
    TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json={
        "name": "Test Country BC", "code": country_code})

    # Create some states via nested route
    state_code1 = get_unique_code('A')
    state_code2 = get_unique_code('B')
    TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{country_code}/states",
        json={"name": "State A", "state_code": state_code1}
    )
    TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}/{country_code}/states",
        json={"name": "State B", "state_code": state_code2}
    )

    # Get states by country
    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}/{country_code}/states")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.STATES_RESP in resp_json
    assert len(resp_json[ep.STATES_RESP]) >= 2

    # Cleanup
    TEST_CLIENT.delete(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code1}")
    TEST_CLIENT.delete(
        f"{ep.COUNTRIES_EPS}/{country_code}/states/{state_code2}")
    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_state_get_not_found():
    """Test getting state that doesn't exist."""
    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}/US/states/XX")
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json
    assert resp.status_code == NOT_FOUND


# ============= STATISTICS ENDPOINT TESTS =============

def test_statistics_get():
    """Test getting database statistics."""
    resp = TEST_CLIENT.get(ep.STATISTICS_EP)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.STATISTICS_RESP in resp_json

    stats = resp_json[ep.STATISTICS_RESP]

    # Check required fields
    assert 'total_countries' in stats
    assert 'total_states' in stats
    assert 'total_cities' in stats
    assert 'database' in stats
    assert 'collections' in stats

    # Verify types
    assert isinstance(stats['total_countries'], int)
    assert isinstance(stats['total_states'], int)
    assert isinstance(stats['total_cities'], int)
    assert isinstance(stats['database'], str)
    assert isinstance(stats['collections'], list)

    # Verify collections list
    assert 'countries' in stats['collections']
    assert 'states' in stats['collections']
    assert 'cities' in stats['collections']

    # Check optional breakdown
    if 'states_by_country' in stats:
        assert isinstance(stats['states_by_country'], dict)


# ============= COUNTRY ENDPOINT TESTS =============

def test_countries_get():
    """Test getting all countries."""
    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}")
    resp_json = resp.get_json()
    assert ep.COUNTRIES_RESP in resp_json
    assert isinstance(resp_json[ep.COUNTRIES_RESP], list)


def test_countries_post():
    """Test creating a country."""
    code = get_unique_code('C')
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"name": "Canada",
                                  "code": code,
                                  "capital": "Ottawa",
                                  "population": 38000000,
                                  "continent": "North America"})
    resp_json = resp.get_json()
    assert resp.status_code == CREATED
    assert ep.COUNTRY_RESP in resp_json
    assert "code" in resp_json[ep.COUNTRY_RESP]

    country_code = resp_json[ep.COUNTRY_RESP]["code"]
    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_countries_post_missing_name():
    """Test creating country without required name field."""
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"code": "XX"})
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json
    assert resp.status_code == BAD_REQUEST


def test_countries_post_missing_code():
    """Test creating country without required code field."""
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"name": "Test Country"})
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json
    assert resp.status_code == BAD_REQUEST


def test_countries_post_invalid_data_type():
    """Test creating country with non-dict data."""
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json="not a dict")
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json
    assert resp.status_code == BAD_REQUEST


def test_country_get_valid():
    """Test getting a single country by code."""
    code = get_unique_code('J')
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}",
        json={
            "name": "Japan",
            "code": code,
            "capital": "Tokyo",
            "population": 126000000,
            "continent": "Asia"
        }
    )
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}/{country_code}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.COUNTRY_RESP in resp_json
    assert resp_json[ep.COUNTRY_RESP]["name"] == "Japan"

    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_country_get_not_found():
    """Test getting country that doesn't exist."""
    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}/ZZ")
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json
    assert resp.status_code == NOT_FOUND


def test_country_put_valid():
    """Test updating a country with valid data."""
    code = get_unique_code('Z')
    resp = TEST_CLIENT.post(
        f"{ep.COUNTRIES_EPS}",
        json={
            "name": "Test Country ZM",
            "code": code,
            "capital": "Test Capital",
            "population": 128000000
        }
    )
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    update_resp = TEST_CLIENT.put(
        f"{ep.COUNTRIES_EPS}/{country_code}",
        json={
            "name": "Updated Country ZM",
            "capital": "New Capital",
            "population": 130000000,
            "continent": "Test Continent"
        }
    )

    assert update_resp.status_code == OK
    data = update_resp.get_json()[ep.COUNTRY_RESP]
    assert data["name"] == "Updated Country ZM"
    assert data["population"] == 130000000
    assert data.get("continent") == "Test Continent"

    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_country_put_not_found():
    """Test updating a country that doesn't exist."""
    resp = TEST_CLIENT.put(f"{ep.COUNTRIES_EPS}/ZZ",
                           json={"name": "Ghost Country"})
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_country_put_invalid_data_type():
    """Test updating a country with non-dict data."""
    code = get_unique_code('T')
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"name": "Test Country", "code": code})
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    resp = TEST_CLIENT.put(
        f"{ep.COUNTRIES_EPS}/{country_code}", json="not a dict")
    assert resp.status_code == BAD_REQUEST
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json

    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_country_put_empty_body():
    """Test updating a country with empty dict."""
    code = get_unique_code('B')
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"name": "Brazil", "code": code})
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    resp = TEST_CLIENT.put(f"{ep.COUNTRIES_EPS}/{country_code}", json={})
    assert resp.status_code == OK

    TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")


def test_country_delete_valid():
    """Test deleting a country with valid code."""
    code = get_unique_code('D')
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}", json={
        "name": "Test Country to Delete", "code": code})
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    resp = TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.MESSAGE in resp_json
    assert country_code in resp_json[ep.MESSAGE]


def test_country_delete_and_verify_removed():
    """Test that deleted country is actually removed."""
    code = get_unique_code('T')
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"name": "Temporary Country", "code": code})
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    resp = TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")
    assert resp.status_code == OK

    resp = TEST_CLIENT.get(f"{ep.COUNTRIES_EPS}/{country_code}")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_country_delete_not_found():
    """Test deleting a country that doesn't exist."""
    resp = TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/ZZ")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_country_delete_twice():
    """Test deleting the same country twice (should fail second time)."""
    code = get_unique_code('O')
    resp = TEST_CLIENT.post(f"{ep.COUNTRIES_EPS}",
                            json={"name": "One-time Country", "code": code})
    country_code = resp.get_json()[ep.COUNTRY_RESP]["code"]

    resp = TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")
    assert resp.status_code == OK

    resp = TEST_CLIENT.delete(f"{ep.COUNTRIES_EPS}/{country_code}")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


# =============================================================================
# Parks Endpoints Tests (UNCHANGED)
# =============================================================================
def test_parks_get_all():
    """Test retrieving all parks."""
    resp = TEST_CLIENT.get(ep.PARKS_EPS)
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert 'Parks' in resp_json
    assert isinstance(resp_json['Parks'], list)


def test_park_get_by_id(test_client, create_test_park):
    """Test retrieving a park by its ID."""
    park_id, _ = create_test_park()
    resp = test_client.get(f"{ep.PARKS_EPS}/{park_id}")
    assert resp.status_code == OK
    data = resp.get_json()
    assert 'Park' in data
    # Cleanup
    test_client.delete(f"{ep.PARKS_EPS}/{park_id}")


def test_park_get_by_state(test_client, create_test_park):
    """Test retrieving parks by state."""
    park_id, park_code = create_test_park(state_code="TX")
    resp = test_client.get(f"{ep.PARKS_EPS}/state/TX")
    assert resp.status_code == OK
    data = resp.get_json()
    assert 'Parks' in data
    assert any(p['state_code'] == 'TX' for p in data['Parks'])
    # Cleanup
    test_client.delete(f"{ep.PARKS_EPS}/{park_id}")


def test_park_delete_valid():
    """Test deleting a park with valid park code."""
    park_code = f"test{uuid.uuid4().hex[:4]}"
    pqry.create({
        "name": "Park to Delete",
        "park_code": park_code,
        "state_code": "TX"
    })

    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/{park_code}")
    assert resp.status_code == OK
    resp_json = resp.get_json()
    assert ep.MESSAGE in resp_json
    assert park_code in resp_json[ep.MESSAGE]


def test_park_delete_and_verify_removed():
    """Test that deleted park is actually removed."""
    park_code = f"test{uuid.uuid4().hex[:4]}"
    pqry.create({
        "name": "Temporary Park",
        "park_code": park_code,
        "state_code": "FL"
    })

    # Delete the park
    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/{park_code}")
    assert resp.status_code == OK

    # Verify it's gone
    result = pqry.get(park_code)
    assert result is None


def test_park_delete_not_found():
    """Test deleting a park that doesn't exist."""
    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/fake")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_park_delete_twice():
    """Test deleting the same park twice (should fail second time)."""
    park_code = f"test{uuid.uuid4().hex[:4]}"
    pqry.create({
        "name": "One-time Park",
        "park_code": park_code,
        "state_code": "WA"
    })

    # Delete once
    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/{park_code}")
    assert resp.status_code == OK

    # Delete again - should fail
    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/{park_code}")
    assert resp.status_code == NOT_FOUND
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_park_delete_invalid_code():
    """Test deleting with invalid park code format."""
    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/invalid park!")
    assert resp.status_code == BAD_REQUEST
    resp_json = resp.get_json()
    assert ep.ERROR in resp_json


def test_park_delete_empty_code():
    """Test deleting with empty park code."""
    resp = TEST_CLIENT.delete(f"{ep.PARKS_EPS}/")
    # This hits the collection endpoint, not individual park
    assert resp.status_code in [BAD_REQUEST, NOT_FOUND, 405]
