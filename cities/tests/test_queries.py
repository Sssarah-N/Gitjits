from copy import deepcopy

import pytest
from unittest.mock import patch
from bson import ObjectId

from cities import queries as qry


def get_temp_rec():
    return deepcopy(qry.SAMPLE_CITY)


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset city cache before each test to ensure test isolation."""
    qry.city_cache.clear()
    yield


@pytest.fixture(scope='function')
def temp_city():
    """Create a temp city and return its MongoDB ObjectId."""
    temp_rec = get_temp_rec()
    new_rec_id = qry.create(temp_rec)
    yield new_rec_id
    try:
        qry.delete(new_rec_id)
    except (ValueError, KeyError):
        print('The record was already deleted.')


def test_valid_id_format():
    """Test MongoDB ObjectId validation."""
    # Valid ObjectId format (24 hex characters)
    assert qry.is_valid_id('507f1f77bcf86cd799439011') is True

    # Invalid formats
    assert qry.is_valid_id('') is False
    assert qry.is_valid_id('invalid') is False
    assert qry.is_valid_id('123') is False
    assert qry.is_valid_id(123) is False


def test_good_create():
    old_count = qry.num_cities()
    temp_rec = get_temp_rec()
    new_rec_id = qry.create(temp_rec)
    assert qry.is_valid_id(new_rec_id)
    assert qry.num_cities() > old_count

    qry.delete(new_rec_id)
    # Verify the deleted city is gone and count returned to original
    assert qry.num_cities() == old_count


def test_create_no_name():
    with pytest.raises(ValueError):
        qry.create({})


def test_create_empty_name():
    with pytest.raises(ValueError):
        qry.create({qry.NAME: ""})


def test_create_bad_param_type():
    with pytest.raises(ValueError):
        qry.create(17)


def test_create_bad_keys():
    with pytest.raises(ValueError):
        invalid_key = qry.NAME + "2"
        qry.create({invalid_key: "CA"})


def test_create_preserves_extra_fields():
    city = get_temp_rec()
    city.update({"population": 12345})
    city_id = qry.create(city)
    stored = qry.get(city_id)
    assert stored["population"] == 12345

    qry.delete(city_id)


def test_create_normalizes_state_code():
    """Test that state_code is normalized to uppercase."""
    city = {
        qry.NAME: "Test City",
        qry.STATE_CODE: "ny"  # lowercase
    }
    city_id = qry.create(city)
    stored = qry.get(city_id)
    assert stored[qry.STATE_CODE] == "NY"  # should be uppercase

    qry.delete(city_id)


def test_update(temp_city):
    update_data = {
        qry.NAME: qry.SAMPLE_CITY[qry.NAME] + " Updated",
        qry.STATE_CODE: qry.SAMPLE_CITY[qry.STATE_CODE]
    }
    result_id = qry.update(temp_city, update_data)

    # Verify update worked
    assert result_id == temp_city
    updated_city = qry.get(temp_city)
    assert updated_city[qry.NAME] == update_data[qry.NAME]
    assert updated_city[qry.STATE_CODE] == update_data[qry.STATE_CODE].upper()


def test_update_bad_id():
    with pytest.raises(ValueError):
        qry.update('invalid_id', {qry.NAME: "New York"})


def test_update_missing_id():
    """Test updating non-existent city raises KeyError."""
    # Use a valid ObjectId format that doesn't exist
    fake_id = str(ObjectId())
    with pytest.raises(KeyError):
        qry.update(fake_id, {qry.NAME: "New York"})


def test_update_bad_fields_param_type(temp_city):
    with pytest.raises(ValueError):
        qry.update(temp_city, 123)


def test_get(temp_city):
    city = qry.get(temp_city)
    assert city[qry.NAME] == qry.SAMPLE_CITY[qry.NAME]
    assert city[qry.STATE_CODE] == qry.SAMPLE_CITY[qry.STATE_CODE].upper()


def test_get_bad_id():
    with pytest.raises(ValueError):
        qry.get('invalid_id')


def test_get_missing_id():
    """Test getting non-existent city raises KeyError."""
    fake_id = str(ObjectId())
    with pytest.raises(KeyError):
        qry.get(fake_id)


def test_delete(temp_city):
    qry.delete(temp_city)
    # Verify city is deleted by trying to get it
    with pytest.raises(KeyError):
        qry.get(temp_city)


def test_delete_bad_id():
    with pytest.raises(ValueError):
        qry.delete('invalid_id')


def test_delete_missing_id():
    with pytest.raises(ValueError):
        qry.delete("")
    # Valid format but doesn't exist
    fake_id = str(ObjectId())
    with pytest.raises(KeyError):
        qry.delete(fake_id)


def test_read(temp_city):
    cities = qry.read()
    assert isinstance(cities, list)
    # Note: read() removes _id by default (no_id=True)
    # So we can't check for temp_city in the list easily


def test_delete_removes_from_list(temp_city):
    # Get initial count
    initial_count = len(qry.read())
    qry.delete(temp_city)
    # After delete, count should be one less
    assert len(qry.read()) == initial_count - 1


def test_search_by_city():
    temp_city = {
        qry.NAME: "Paris",
        qry.STATE_CODE: "FR"
    }

    city_id = qry.create(temp_city)

    results = qry.search({qry.NAME: "Paris"})
    assert isinstance(results, list)
    assert any(city.get(qry.NAME) == "Paris" for city in results)

    qry.delete(city_id)


def test_get_by_state_code():
    """Test getting cities by state code."""
    city = {
        qry.NAME: "Buffalo",
        qry.STATE_CODE: "NY"
    }
    city_id = qry.create(city)

    results = qry.get_by_state_code("NY")
    assert isinstance(results, list)
    # Check if Buffalo is in the results
    assert any(c.get(qry.NAME) == "Buffalo" for c in results)

    # Test case-insensitive
    results_lower = qry.get_by_state_code("ny")
    assert any(c.get(qry.NAME) == "Buffalo" for c in results_lower)

    qry.delete(city_id)


@patch('data.db_connect.client', None)
@patch('data.db_connect.connect_db',
       side_effect=ConnectionError("Cannot connect to database"))
def test_read_connection_error(mock_connect):
    with pytest.raises(ConnectionError):
        qry.read()


# ============= STATE CODE VALIDATION TESTS =============

def test_valid_state_codes_accepted():
    """Test that various valid state/region codes are accepted."""
    # Test various formats that should all be valid
    assert qry.is_valid_state_code('NY') is True      # US state
    assert qry.is_valid_state_code('ON') is True      # Canadian province
    assert qry.is_valid_state_code('NSW') is True     # Australian state
    assert qry.is_valid_state_code('Tokyo') is True   # Full name


def test_invalid_state_codes_rejected():
    """Test that clearly invalid codes are rejected."""
    # Too long
    assert qry.is_valid_state_code('X' * 20) is False
    # Only numbers (no letters)
    assert qry.is_valid_state_code('123') is False
    # Empty
    assert qry.is_valid_state_code('') is False
    # Wrong type
    assert qry.is_valid_state_code(None) is False
