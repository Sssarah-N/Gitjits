from copy import deepcopy
import time

import pytest
from unittest.mock import patch

from countries import queries as qry

# Counter for unique codes
_code_counter = [0]


def get_unique_code():
    """Generate a unique 2-3 letter code (letters only)."""
    _code_counter[0] += 1
    # Use counter + time to ensure uniqueness
    n = _code_counter[0] + int(time.time() * 1000) % 10000
    # Convert number to base-26 letters
    letters = ''
    for _ in range(3):
        letters = chr(ord('A') + (n % 26)) + letters
        n //= 26
    return letters[:3]


def get_temp_rec():
    """Get a temp record with a unique code to avoid conflicts."""
    rec = deepcopy(qry.SAMPLE_COUNTRY)
    rec[qry.CODE] = get_unique_code()
    return rec


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset country cache before each test to ensure test isolation."""
    qry.country_cache.clear()
    yield


@pytest.fixture(scope='function')
def temp_country():
    """Create a temp country and return its code (the primary key)."""
    temp_rec = get_temp_rec()
    code = qry.create(temp_rec)
    yield code
    try:
        qry.delete(code)
    except (ValueError, KeyError):
        print('The record was already deleted.')


def test_valid_code_format():
    """Test country code validation."""
    # Valid codes (2-3 letters)
    assert qry.is_valid_code('US') is True
    assert qry.is_valid_code('USA') is True
    assert qry.is_valid_code('uk') is True  # lowercase ok

    # Invalid codes
    assert qry.is_valid_code('') is False       # empty
    assert qry.is_valid_code('A') is False      # too short
    assert qry.is_valid_code('ABCD') is False   # too long
    assert qry.is_valid_code('U1') is False     # contains number
    assert qry.is_valid_code(123) is False      # not a string


def test_good_create():
    old_count = qry.num_countries()
    temp_rec = get_temp_rec()
    code = qry.create(temp_rec)
    assert qry.is_valid_code(code)
    assert qry.num_countries() > old_count

    qry.delete(code)
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
        qry.create({qry.CODE: 'XX'})


def test_create_missing_code():
    """Test creating without code raises ValueError."""
    with pytest.raises(ValueError):
        qry.create({qry.NAME: 'Test Country'})


def test_create_invalid_code_format():
    """Test creating with invalid code format raises ValueError."""
    with pytest.raises(ValueError):
        qry.create({qry.NAME: 'Test', qry.CODE: 'TOOLONG'})


def test_create_with_all_fields():
    """Test creating a country with all fields."""
    unique_code = get_unique_code()
    country_data = {
        qry.NAME: 'Test Canada',
        qry.CODE: unique_code,
        qry.CAPITAL: 'Ottawa',
        qry.POPULATION: 38000000,
        qry.CONTINENT: 'North America'
    }
    code = qry.create(country_data)
    assert qry.is_valid_code(code)
    assert code == unique_code.upper()

    # Verify it was created
    country = qry.get(code)
    assert country[qry.NAME] == 'Test Canada'
    assert country[qry.CODE] == unique_code.upper()

    qry.delete(code)


def test_create_duplicate_code():
    """Test creating duplicate country code raises ValueError."""
    temp_rec = get_temp_rec()
    code = qry.create(temp_rec)

    # Try to create another with same code
    duplicate_rec = {
        qry.NAME: 'Another Country',
        qry.CODE: code
    }
    with pytest.raises(ValueError):
        qry.create(duplicate_rec)

    qry.delete(code)


def test_get_valid(temp_country):
    """Test getting a country by code."""
    country = qry.get(temp_country)
    assert isinstance(country, dict)
    assert qry.NAME in country


def test_get_case_insensitive(temp_country):
    """Test that get() is case-insensitive."""
    country_upper = qry.get(temp_country.upper())
    country_lower = qry.get(temp_country.lower())
    assert country_upper[qry.NAME] == country_lower[qry.NAME]


def test_get_not_found():
    """Test getting non-existent country raises KeyError."""
    with pytest.raises(KeyError):
        qry.get('ZZ')  # ZZ is not a real ISO code


def test_get_invalid_code():
    """Test getting with invalid code raises ValueError."""
    with pytest.raises(ValueError):
        qry.get('')


def test_update_valid(temp_country):
    """Test updating a country."""
    update_data = {
        qry.NAME: 'Updated Country Name',
        qry.POPULATION: 50000000
    }
    result = qry.update(temp_country, update_data)
    assert result == temp_country.upper()

    # Verify update
    country = qry.get(temp_country)
    assert country[qry.NAME] == 'Updated Country Name'
    assert country[qry.POPULATION] == 50000000


def test_update_cannot_change_code(temp_country):
    """Test that updating code field is ignored (primary key cannot change)."""
    original = qry.get(temp_country)
    qry.update(temp_country, {qry.CODE: 'ZZ', qry.NAME: 'New Name'})
    updated = qry.get(temp_country)
    # Code should not have changed
    assert updated[qry.CODE] == original[qry.CODE]
    # But name should have changed
    assert updated[qry.NAME] == 'New Name'


def test_update_not_found():
    """Test updating non-existent country raises KeyError."""
    with pytest.raises(KeyError):
        qry.update('ZZ', {qry.NAME: 'Test'})


def test_update_invalid_code():
    """Test updating with invalid code raises ValueError."""
    with pytest.raises(ValueError):
        qry.update('', {qry.NAME: 'Test'})


def test_update_bad_type():
    """Test updating with non-dict raises ValueError."""
    with pytest.raises(ValueError):
        qry.update('US', 'not a dict')


def test_update_invalid_population():
    """Test updating with non-integer population raises ValueError."""
    temp_rec = get_temp_rec()
    code = qry.create(temp_rec)

    with pytest.raises(ValueError):
        qry.update(code, {qry.POPULATION: 'not an integer'})

    qry.delete(code)


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
        qry.delete('ZZ')


def test_delete_invalid_code():
    """Test deleting with invalid code raises ValueError."""
    with pytest.raises(ValueError):
        qry.delete('')


def test_code_exists():
    """Test checking if country code exists."""
    unique_code = get_unique_code()
    country_data = {
        qry.NAME: 'Test Japan',
        qry.CODE: unique_code,
        qry.CAPITAL: 'Tokyo',
        qry.POPULATION: 126000000
    }
    code = qry.create(country_data)

    assert qry.code_exists(unique_code) is True
    assert qry.code_exists(unique_code.lower()) is True  # case-insensitive
    assert qry.code_exists('ZZ') is False

    qry.delete(code)


def test_num_countries():
    """Test counting countries."""
    initial_count = qry.num_countries()

    unique_code = get_unique_code()
    country_data = {
        qry.NAME: 'Test Country',
        qry.CODE: unique_code
    }
    code = qry.create(country_data)

    assert qry.num_countries() == initial_count + 1

    qry.delete(code)
    assert qry.num_countries() == initial_count


def test_search_by_continent():
    unique_code = get_unique_code()
    rec = {
        qry.NAME: "Test France",
        qry.CODE: unique_code,
        qry.CONTINENT: "Europe"
    }
    code = qry.create(rec)

    results = qry.search({qry.CONTINENT: "Europe"})
    assert any(r[qry.CODE] == unique_code.upper() for r in results)

    qry.delete(code)


@patch('data.db_connect.read', side_effect=Exception('Connection failed'))
@patch('data.db_connect.connect_db', return_value=True)
def test_read_connection_error(mock_connect, mock_read):
    with pytest.raises(Exception):
        qry.read()
