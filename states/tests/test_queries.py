from copy import deepcopy
import uuid
from unittest.mock import patch

import pytest

from states import queries as qry
import countries.queries as country_qry


# Fixed test country code - uses 'ZZ' which is reserved/not a real ISO code
TEST_COUNTRY_CODE = 'ZZ'


def get_test_country_code():
    """Return the test country code."""
    return TEST_COUNTRY_CODE


def get_unique_state_code():
    """Generate a unique state code for testing."""
    return f'T{uuid.uuid4().hex[:2].upper()}'


def get_temp_rec():
    rec = deepcopy(qry.SAMPLE_STATE)
    # Use our test country code instead of 'US'
    rec[qry.COUNTRY_CODE] = get_test_country_code()
    # Use unique state code to avoid conflicts
    rec[qry.STATE_CODE] = get_unique_state_code()
    return rec


def ensure_test_country():
    """Create the test country if it doesn't exist."""
    code = get_test_country_code()
    if not country_qry.code_exists(code):
        country_qry.create({
            country_qry.NAME: 'Test Country',
            country_qry.CODE: code
        })


def cleanup_test_country():
    """Delete the test country."""
    code = get_test_country_code()
    try:
        country_qry.delete(code)
    except (KeyError, Exception):
        pass


def cleanup_state(state_code: str, country_code: str = None):
    """Helper to delete a state by code if it exists (for test cleanup)."""
    if country_code is None:
        country_code = get_test_country_code()
    try:
        qry.delete(state_code, country_code)
    except Exception:
        pass  # Ignore errors if state doesn't exist


@pytest.fixture(scope='module', autouse=True)
def setup_test_country():
    """Create test country before all tests in module, clean up after."""
    ensure_test_country()
    yield
    cleanup_test_country()


@pytest.fixture(scope='function')
def temp_state():
    """Create a temp state and return (state_code, country_code) tuple."""
    temp_rec = get_temp_rec()
    state_code = temp_rec[qry.STATE_CODE]
    country_code = temp_rec[qry.COUNTRY_CODE]
    # Clean up any existing state with same code before creating
    cleanup_state(state_code, country_code)
    qry.create(temp_rec)
    yield (state_code, country_code)
    try:
        qry.delete(state_code, country_code)
    except (ValueError, KeyError):
        print('The record was already deleted.')


def test_valid_state_code():
    """Test state code validation."""
    assert qry.is_valid_state_code('NY') is True
    assert qry.is_valid_state_code('CA') is True
    assert qry.is_valid_state_code('Tokyo') is True
    assert qry.is_valid_state_code('') is False
    assert qry.is_valid_state_code('X' * 20) is False
    assert qry.is_valid_state_code(123) is False


def test_valid_country_code():
    """Test country code validation."""
    assert qry.is_valid_country_code('US') is True
    assert qry.is_valid_country_code('USA') is True
    assert qry.is_valid_country_code('') is False
    assert qry.is_valid_country_code('ABCD') is False
    assert qry.is_valid_country_code('12') is False


def test_good_create():
    old_count = qry.num_states()
    temp_rec = get_temp_rec()
    state_code = temp_rec[qry.STATE_CODE]
    country_code = temp_rec[qry.COUNTRY_CODE]
    # Clean up any existing state with same code before creating
    cleanup_state(state_code, country_code)
    result = qry.create(temp_rec)
    # create() now returns tuple (state_code, country_code)
    assert result == (state_code.upper(), country_code.upper())
    assert qry.num_states() > old_count
    # Clean up
    qry.delete(state_code, country_code)


def test_create_no_name():
    with pytest.raises(ValueError):
        qry.create({
            qry.STATE_CODE: 'XX',
            qry.COUNTRY_CODE: get_test_country_code()
        })


def test_create_empty_name():
    with pytest.raises(ValueError):
        qry.create({
            qry.NAME: "",
            qry.STATE_CODE: 'XX',
            qry.COUNTRY_CODE: get_test_country_code()
        })


def test_create_missing_state_code():
    with pytest.raises(ValueError):
        qry.create({
            qry.NAME: "Test State",
            qry.COUNTRY_CODE: get_test_country_code()
        })


def test_create_missing_country_code():
    with pytest.raises(ValueError):
        qry.create({
            qry.NAME: "Test State",
            qry.STATE_CODE: 'XX'
        })


def test_create_bad_param_type():
    with pytest.raises(ValueError):
        qry.create(17)


def test_create_nonexistent_country():
    """Test creating state with non-existent country raises ValueError."""
    with pytest.raises(ValueError):
        qry.create({
            qry.NAME: "Test State",
            qry.STATE_CODE: 'XX',
            qry.COUNTRY_CODE: 'QQ'  # doesn't exist
        })


def test_create_preserves_extra_fields():
    state = get_temp_rec()
    state.update({"area": 54555})
    state_code = state[qry.STATE_CODE]
    country_code = state[qry.COUNTRY_CODE]
    cleanup_state(state_code, country_code)
    qry.create(state)
    stored = qry.get(state_code, country_code)
    assert stored["area"] == 54555
    # Clean up
    qry.delete(state_code, country_code)


def test_create_duplicate():
    """Test creating duplicate state raises ValueError."""
    temp_rec = get_temp_rec()
    state_code = temp_rec[qry.STATE_CODE]
    country_code = temp_rec[qry.COUNTRY_CODE]
    cleanup_state(state_code, country_code)
    qry.create(temp_rec)

    # Try to create duplicate
    with pytest.raises(ValueError):
        qry.create(temp_rec)

    qry.delete(state_code, country_code)


def test_update(temp_state):
    state_code, country_code = temp_state
    update_data = {
        qry.NAME: "Updated State Name"
    }
    result = qry.update(state_code, country_code, update_data)

    # Verify update worked
    assert result == (state_code.upper(), country_code.upper())
    updated_state = qry.get(state_code, country_code)
    assert updated_state[qry.NAME] == "Updated State Name"


def test_update_population(temp_state):
    state_code, country_code = temp_state
    new_population = 12345678
    update_data = {qry.POPULATION: new_population}
    qry.update(state_code, country_code, update_data)
    updated_state = qry.get(state_code, country_code)
    assert updated_state[qry.POPULATION] == new_population


def test_update_population_bad_type(temp_state):
    state_code, country_code = temp_state
    update_data = {qry.POPULATION: "a lot"}
    with pytest.raises(ValueError):
        qry.update(state_code, country_code, update_data)


def test_update_bad_state_code():
    with pytest.raises(ValueError):
        qry.update('', 'US', {qry.NAME: "California"})


def test_update_bad_country_code():
    with pytest.raises(ValueError):
        qry.update('CA', '', {qry.NAME: "California"})


def test_update_not_found():
    with pytest.raises(KeyError):
        qry.update('XX', get_test_country_code(), {qry.NAME: "California"})


def test_update_bad_fields_param_type(temp_state):
    state_code, country_code = temp_state
    with pytest.raises(ValueError):
        qry.update(state_code, country_code, 123)


def test_get(temp_state):
    state_code, country_code = temp_state
    state = qry.get(state_code, country_code)
    assert qry.NAME in state
    assert state[qry.STATE_CODE] == state_code.upper()
    assert state[qry.COUNTRY_CODE] == country_code.upper()


def test_get_case_insensitive(temp_state):
    state_code, country_code = temp_state
    state_upper = qry.get(state_code.upper(), country_code.upper())
    state_lower = qry.get(state_code.lower(), country_code.lower())
    assert state_upper[qry.NAME] == state_lower[qry.NAME]


def test_get_bad_state_code():
    with pytest.raises(ValueError):
        qry.get('', 'US')


def test_get_bad_country_code():
    with pytest.raises(ValueError):
        qry.get('CA', '')


def test_get_not_found():
    with pytest.raises(KeyError):
        qry.get('XX', get_test_country_code())


def test_delete(temp_state):
    state_code, country_code = temp_state
    result = qry.delete(state_code, country_code)
    assert result >= 1
    # Verify state is deleted by trying to get it
    with pytest.raises(KeyError):
        qry.get(state_code, country_code)


def test_delete_bad_state_code():
    with pytest.raises(ValueError):
        qry.delete('', 'US')


def test_delete_bad_country_code():
    with pytest.raises(ValueError):
        qry.delete('CA', '')


def test_delete_not_found():
    with pytest.raises(KeyError):
        qry.delete('XX', get_test_country_code())


def test_read_returns_list():
    """Test that read() returns a list."""
    states = qry.read()
    assert isinstance(states, list)


def test_read(temp_state):
    """Test that read() includes created state."""
    state_code, country_code = temp_state
    states = qry.read()
    assert isinstance(states, list)
    # Check if our temp_state is in the list
    found = any(
        s.get(qry.STATE_CODE) == state_code.upper() and
        s.get(qry.COUNTRY_CODE) == country_code.upper()
        for s in states
    )
    assert found


def test_delete_removes_from_list(temp_state):
    state_code, country_code = temp_state
    qry.delete(state_code, country_code)
    states = qry.read()
    found = any(
        s.get(qry.STATE_CODE) == state_code.upper() and
        s.get(qry.COUNTRY_CODE) == country_code.upper()
        for s in states
    )
    assert not found


def test_get_states_by_country():
    """Test getting all states in a country."""
    test_country = get_test_country_code()
    # Create a test state
    state_code = get_unique_state_code()
    cleanup_state(state_code, test_country)
    qry.create({
        qry.NAME: "Test State",
        qry.STATE_CODE: state_code,
        qry.COUNTRY_CODE: test_country
    })

    results = qry.get_states_by_country(test_country)
    assert isinstance(results, list)
    found = any(s.get(qry.STATE_CODE) == state_code.upper() for s in results)
    assert found

    qry.delete(state_code, test_country)


def test_state_exists(temp_state):
    state_code, country_code = temp_state
    assert qry.state_exists(state_code, country_code) is True
    assert qry.state_exists('XX', country_code) is False


def test_search_by_state_code():
    test_country = get_test_country_code()
    state_code = get_unique_state_code()
    temp_state = {
        qry.NAME: "Test State",
        qry.STATE_CODE: state_code,
        qry.COUNTRY_CODE: test_country,
        qry.CAPITAL: "Test City",
        qry.POPULATION: 500000
    }
    cleanup_state(state_code, test_country)
    qry.create(temp_state)
    results = qry.search({qry.STATE_CODE: state_code.upper()})
    assert isinstance(results, list)
    assert any(
        r.get(qry.STATE_CODE) == state_code.upper()
        for r in results
    )
    qry.delete(state_code, test_country)


@patch('data.db_connect.read', side_effect=Exception('Connection failed'))
@patch('data.db_connect.connect_db', return_value=True)
def test_read_connection_error(mock_connect, mock_read):
    with pytest.raises(Exception):
        qry.read()
