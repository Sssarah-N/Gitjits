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
        qry.delete(temp_rec[qry.NAME], temp_rec[qry.STATE_CODE])
    except ValueError:
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


@pytest.mark.skip(reason='Currently adds duplicate cities as new entries')
def test_create_duplicate():
    with pytest.raises(ValueError, match="City already exists"):
        qry.create(qry.SAMPLE_CITY)


def test_update():
    temp_rec = get_temp_rec()  
    city_id = qry.create(temp_rec)
    update_data = {qry.NAME: temp_rec[qry.NAME] + " Updated", qry.STATE_CODE: temp_rec[qry.STATE_CODE]}
    result_id = qry.update(city_id, update_data)
    
    # Verify update worked
    assert result_id == city_id
    assert qry.city_cache[city_id][qry.NAME] == temp_rec[qry.NAME] + " Updated"
    
    
def test_update_bad_id():
    with pytest.raises(ValueError):
        qry.update(123, {qry.NAME: "New York"})


def test_update_missing_id():
    with pytest.raises(KeyError):
        qry.update("NYC", {qry.NAME: "New York"})


def test_update_bad_fields_param_type():
    city_id = qry.create(get_temp_rec())
    with pytest.raises(ValueError):
        qry.update(city_id, 123)
        
        
def test_get():
    temp_rec = get_temp_rec()
    city_id = qry.create(temp_rec)
    city = qry.get(city_id)
    assert city[qry.NAME] == temp_rec[qry.NAME]
    assert city[qry.STATE_CODE] == temp_rec[qry.STATE_CODE]


def test_get_bad_id():
    with pytest.raises(ValueError):
        qry.get(123)


def test_get_missing_id():
    with pytest.raises(KeyError):
        qry.get("999")


def test_delete():
    temp_rec = get_temp_rec()
    city_id = qry.create(temp_rec)
    qry.delete(temp_rec[qry.NAME], temp_rec[qry.STATE_CODE])
    assert city_id not in qry.city_cache
    

def test_delete_bad_id():
    with pytest.raises(ValueError):
        qry.delete(123)


def test_delete_missing_id():
    with pytest.raises(KeyError):
        qry.create({qry.NAME: "New York", qry.STATE_CODE: "NY"})
        qry.delete("NYC")

@patch('data.db_connect.read', return_value=True, autospec=True)
def test_read(mock_db_connect, temp_city):
    cities = qry.read()
    assert isinstance(cities, dict)
    assert temp_city in cities

@patch('data.db_connect.read', return_value=True, autospec=True)
def test_delete(mock_db_connect, temp_city):
    qry.delete(temp_city)
    assert temp_city not in qry.read()

@patch('data.db_connect.read', return_value=True, autospec=True)
def test_delete_missing(mock_db_connect):
    with pytest.raises(KeyError):
        qry.delete("nonexistent entry")

@patch('data.db_connect.read', return_value=False, autospec=True)
def test_read_connection_error(mock_db_connect):
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
