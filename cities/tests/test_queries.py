from copy import deepcopy

import pytest
from unittest.mock import patch

from cities import queries as qry

def get_temp_rec():
    return deepcopy(qry.SAMPLE_CITY)


@pytest.fixture(scope='function')
def temp_city_no_del():
    temp_rec = get_temp_rec()
    qry.create(temp_rec)
    return temp_rec

@pytest.fixture(autouse=True)
def reset_cache():
    """Reset city cache before each test to ensure test isolation."""
    qry.city_cache.clear()
    yield

@pytest.fixture(scope='function')
def temp_city():
    temp_rec = get_temp_rec()
    new_rec_id = qry.create(temp_rec)
    yield new_rec_id
    try:
        qry.delete(new_rec_id)
    except (ValueError, KeyError):
        print('The record was already deleted.')


def test_valid_id_min_length():
    short_id = "."*(qry.MIN_ID_LEN - 1)
    result = qry.is_valid_id(short_id)
    assert not result


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
        qry.create({ invalid_key: "CA" })
        
        
def test_create_preserves_extra_fields():
    city = get_temp_rec()
    city.update({"population": 12345})
    city_id = qry.create(city)
    stored = qry.get(city_id)
    assert stored["population"] == 12345

    qry.delete(city_id)


@pytest.mark.skip(reason='Currently adds duplicate cities as new entries')
def test_create_duplicate():
    with pytest.raises(ValueError, match="City already exists"):
        qry.create(qry.SAMPLE_CITY)


def test_update(temp_city):
    update_data = {qry.NAME: qry.SAMPLE_CITY[qry.NAME] + " Updated", qry.STATE_CODE: qry.SAMPLE_CITY[qry.STATE_CODE]}
    result_id = qry.update(temp_city, update_data)
    
    # Verify update worked
    assert result_id == temp_city
    updated_city = qry.get(temp_city)
    assert updated_city[qry.NAME] == update_data[qry.NAME]
    assert updated_city[qry.STATE_CODE] == update_data[qry.STATE_CODE]
    
    
def test_update_bad_id():
    with pytest.raises(ValueError):
        qry.update(123, {qry.NAME: "New York"})


def test_update_missing_id():
    with pytest.raises(KeyError):
        qry.update("NYC", {qry.NAME: "New York"})


def test_update_bad_fields_param_type(temp_city):
    with pytest.raises(ValueError):
        qry.update(temp_city, 123)
        
        
def test_get(temp_city):
    city = qry.get(temp_city)
    assert city[qry.NAME] == qry.SAMPLE_CITY[qry.NAME]
    assert city[qry.STATE_CODE] == qry.SAMPLE_CITY[qry.STATE_CODE]


def test_get_bad_id():
    with pytest.raises(ValueError):
        qry.get(123)


def test_get_missing_id():
    with pytest.raises(KeyError):
        qry.get("999")


def test_delete(temp_city):
    qry.delete(temp_city)
    # Verify city is deleted by trying to get it
    with pytest.raises(KeyError):
        qry.get(temp_city)
    

def test_delete_bad_id():
    with pytest.raises(ValueError):
        qry.delete(123)


def test_delete_missing_id():
    with pytest.raises(ValueError):
        qry.delete("")
    with pytest.raises(KeyError):
        qry.delete("nonexistent_id_12345")


def test_read(temp_city):
    cities = qry.read()
    assert isinstance(cities, list)
    # Check if our temp_city is in the list
    city_ids = [city.get('id') for city in cities]
    assert temp_city in city_ids

def test_delete_removes_from_list(temp_city):
    qry.delete(temp_city)
    cities = qry.read()
    city_ids = [city.get('id') for city in cities]
    assert temp_city not in city_ids

def test_delete_missing():
    with pytest.raises(KeyError):
        qry.delete("nonexistent entry")
        
def test_search_by_city():
    temp_city = {
        qry.NAME: "Paris",
        qry.STATE_CODE: "FR"
    }

    city_id = qry.create(temp_city)
    
    results = qry.search({qry.NAME: "Paris"})
    assert isinstance(results, list)
    
    assert any(city.get(qry.ID) == city_id for city in results)
    qry.delete(city_id)

@patch('data.db_connect.client', None)
@patch('data.db_connect.connect_db', side_effect=ConnectionError("Cannot connect to database"))
def test_read_connection_error(mock_connect):
    with pytest.raises(ConnectionError):
        cities = qry.read()


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
