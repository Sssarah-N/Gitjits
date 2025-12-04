from copy import deepcopy

import pytest
from unittest.mock import patch

from countries import queries as qry

def get_temp_rec():
    return deepcopy(qry.SAMPLE_COUNTRY)


@pytest.fixture(scope='function')
def temp_country_no_del():
    temp_rec = get_temp_rec()
    qry.create(temp_rec)
    return temp_rec

@pytest.fixture(autouse=True)
def reset_cache():
    """Reset country cache before each test to ensure test isolation."""
    qry.country_cache.clear()
    yield

@pytest.fixture(scope='function')
def temp_country():
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
    old_count = qry.num_countries()
    temp_rec = get_temp_rec()
    new_rec_id = qry.create(temp_rec)
    assert qry.is_valid_id(new_rec_id)
    assert qry.num_countries() > old_count

    qry.delete(new_rec_id)
    # Verify the deleted country is gone and count returned to original
    assert qry.num_countries() == old_count


def test_read(temp_country):
    """Test reading all countries."""
    countries = qry.read()
    assert isinstance(countries, list)
    assert len(countries) > 0


def test_create_bad_type():
    """Test creating with non-dict raises ValueError."""
    with pytest.raises(ValueError):
        qry.create('Not a dictionary')


def test_create_missing_name():
    """Test creating without name raises ValueError."""
    with pytest.raises(ValueError):
        qry.create({'code': 'XX'})


def test_create_with_all_fields():
    """Test creating a country with all fields."""
    country_data = {
        qry.NAME: 'Canada',
        qry.CODE: 'CA',
        qry.CAPITAL: 'Ottawa',
        qry.POPULATION: 38000000,
        qry.CONTINENT: 'North America'
    }
    country_id = qry.create(country_data)
    assert qry.is_valid_id(country_id)
    
    # Verify it was created
    country = qry.get(country_id)
    assert country[qry.NAME] == 'Canada'
    assert country[qry.CODE] == 'CA'
    
    qry.delete(country_id)


def test_get_valid(temp_country):
    """Test getting a country by ID."""
    country = qry.get(temp_country)
    assert isinstance(country, dict)
    assert qry.NAME in country


def test_get_not_found():
    """Test getting non-existent country raises KeyError."""
    with pytest.raises(KeyError):
        qry.get('nonexistent_id_12345')


def test_get_invalid_id():
    """Test getting with invalid ID raises ValueError."""
    with pytest.raises(ValueError):
        qry.get('')


def test_update_valid(temp_country):
    """Test updating a country."""
    update_data = {
        qry.NAME: 'Updated Country Name',
        qry.POPULATION: 50000000
    }
    result = qry.update(temp_country, update_data)
    assert result == temp_country
    
    # Verify update
    country = qry.get(temp_country)
    assert country[qry.NAME] == 'Updated Country Name'
    assert country[qry.POPULATION] == 50000000


def test_update_not_found():
    """Test updating non-existent country raises KeyError."""
    with pytest.raises(KeyError):
        qry.update('nonexistent_id_12345', {qry.NAME: 'Test'})


def test_update_invalid_id():
    """Test updating with invalid ID raises ValueError."""
    with pytest.raises(ValueError):
        qry.update('', {qry.NAME: 'Test'})


def test_update_bad_type():
    """Test updating with non-dict raises ValueError."""
    with pytest.raises(ValueError):
        qry.update('some_id', 'not a dict')


def test_update_invalid_population():
    """Test updating with non-integer population raises ValueError."""
    temp_rec = get_temp_rec()
    country_id = qry.create(temp_rec)
    
    with pytest.raises(ValueError):
        qry.update(country_id, {qry.POPULATION: 'not an integer'})
    
    qry.delete(country_id)


def test_delete_valid(temp_country):
    """Test deleting a country."""
    result = qry.delete(temp_country)
    assert result >= 1
    
    # Verify it's deleted
    with pytest.raises(KeyError):
        qry.get(temp_country)


def test_delete_not_found():
    """Test deleting non-existent country raises KeyError."""
    with pytest.raises(KeyError):
        qry.delete('nonexistent_id_12345')


def test_delete_invalid_id():
    """Test deleting with invalid ID raises ValueError."""
    with pytest.raises(ValueError):
        qry.delete('')


def test_get_by_code():
    """Test getting country by code."""
    country_data = {
        qry.NAME: 'Mexico',
        qry.CODE: 'MX',
        qry.CAPITAL: 'Mexico City',
        qry.POPULATION: 128000000
    }
    country_id = qry.create(country_data)
    
    # Get by code
    country = qry.get_by_code('MX')
    assert country[qry.NAME] == 'Mexico'
    assert country[qry.CODE] == 'MX'
    
    # Test case-insensitive
    country = qry.get_by_code('mx')
    assert country[qry.NAME] == 'Mexico'
    
    qry.delete(country_id)


def test_get_by_code_not_found():
    """Test getting by non-existent code raises KeyError."""
    with pytest.raises(KeyError):
        qry.get_by_code('NONEXISTENT')


def test_code_exists():
    """Test checking if country code exists."""
    country_data = {
        qry.NAME: 'Japan',
        qry.CODE: 'JP',
        qry.CAPITAL: 'Tokyo',
        qry.POPULATION: 126000000
    }
    country_id = qry.create(country_data)
    
    assert qry.code_exists('JP') is True
    assert qry.code_exists('jp') is True  # case-insensitive
    assert qry.code_exists('NONEXISTENT') is False
    
    qry.delete(country_id)


def test_num_countries():
    """Test counting countries."""
    initial_count = qry.num_countries()
    
    country_data = {
        qry.NAME: 'Test Country',
        qry.CODE: 'TC'
    }
    country_id = qry.create(country_data)
    
    assert qry.num_countries() == initial_count + 1
    
    qry.delete(country_id)
    assert qry.num_countries() == initial_count

def test_search_by_continent():
    rec = {
        qry.NAME: "France",
        qry.CODE: "FR",
        qry.CONTINENT: "Europe"
    }
    cid = qry.create(rec)

    results = qry.search({qry.CONTINENT: "Europe"})
    assert any(r[qry.CODE] == "FR" for r in results)

    qry.delete(cid)
    
@patch('data.db_connect.read', side_effect=Exception('Connection failed'))
@patch('data.db_connect.connect_db', return_value=True)
def test_read_connection_error(mock_connect, mock_read):
    with pytest.raises(Exception):
        countries = qry.read()

