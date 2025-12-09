from copy import deepcopy
from unittest.mock import patch, MagicMock
from bson import ObjectId

import pytest

from states import queries as qry

# In-memory storage for fast testing
_test_db = {}
_next_id = 1

def get_temp_rec():
    return deepcopy(qry.SAMPLE_STATE)


def cleanup_state(state_code: str, country_code: str = 'US'):
    """Helper to delete a state by code if it exists (for test cleanup)."""
    try:
        qry.delete_by_code(state_code, country_code)
    except Exception:
        pass  # Ignore errors if state doesn't exist


@pytest.fixture(scope='function')
def temp_state():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
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
    old_count = qry.num_states()
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    new_rec_id = qry.create(temp_rec)
    assert qry.is_valid_id(new_rec_id)
    assert qry.num_states() > old_count
    # Clean up
    qry.delete(new_rec_id)


def test_create_no_name():
    with pytest.raises(ValueError):
        qry.create({})
        
        
def test_create_empty_name():
    with pytest.raises(ValueError):
        qry.create({qry.NAME: ""})


def test_create_bad_param_type():
    with pytest.raises(ValueError):
        qry.create(17)
        

def test_create_preserves_extra_fields():
    state = get_temp_rec()
    state.update({"area": 54555})
    # Clean up any existing state with same code before creating
    cleanup_state(state.get(qry.STATE_CODE), state.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(state)
    stored = qry.get(state_id)
    assert stored["area"] == 54555
    # Clean up
    qry.delete(state_id)


def test_update():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(temp_rec)
    update_data = {qry.NAME: temp_rec[qry.NAME] + " Updated", qry.STATE_CODE: temp_rec[qry.STATE_CODE]}
    result_id = qry.update(state_id, update_data)
    
    # Verify update worked
    assert result_id == state_id
    updated_state = qry.get(state_id)
    assert updated_state[qry.NAME] == temp_rec[qry.NAME] + " Updated"
    # Clean up
    qry.delete(state_id)

def test_update_population():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(temp_rec)
    new_population = 12345678
    update_data = {qry.POPULATION: new_population}
    result_id = qry.update(state_id, update_data)
    assert result_id == state_id
    updated_state = qry.get(state_id)
    assert updated_state[qry.POPULATION] == new_population
    # Clean up
    qry.delete(state_id)
    

def test_update_population_bad_type():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(temp_rec)
    update_data = {qry.POPULATION: "a lot"}
    with pytest.raises(ValueError):
        qry.update(state_id, update_data)
    # Clean up
    qry.delete(state_id)

    
def test_update_bad_id():
    with pytest.raises(ValueError):
        qry.update(123, {qry.NAME: "California"})


def test_update_missing_id():
    with pytest.raises(KeyError):
        qry.update("CA", {qry.NAME: "California"})


def test_update_bad_fields_param_type():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(temp_rec)
    with pytest.raises(ValueError):
        qry.update(state_id, 123)
    # Clean up
    qry.delete(state_id)
        
     
def test_get():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(temp_rec)
    state = qry.get(state_id)
    assert state[qry.NAME] == temp_rec[qry.NAME]
    assert state[qry.STATE_CODE] == temp_rec[qry.STATE_CODE]
    # Clean up
    qry.delete(state_id)


def test_get_bad_id():
    with pytest.raises(ValueError):
        qry.get(123)


def test_get_missing_id():
    with pytest.raises(KeyError):
        qry.get("999")


def test_delete():
    temp_rec = get_temp_rec()
    # Clean up any existing state with same code before creating
    cleanup_state(temp_rec.get(qry.STATE_CODE), temp_rec.get(qry.COUNTRY_CODE, 'US'))
    state_id = qry.create(temp_rec)
    qry.delete(state_id)
    # Verify state is deleted by trying to get it
    with pytest.raises(KeyError):
        qry.get(state_id)
    

def test_delete_bad_id():
    with pytest.raises(ValueError):
        qry.delete(123)


def test_delete_missing_id():
    # Use a unique state code to avoid conflicts
    state_id = qry.create({qry.NAME: "TestState", qry.STATE_CODE: "TS", qry.COUNTRY_CODE: "US"})
    qry.delete(state_id)  # Delete it first
    with pytest.raises(KeyError):
        qry.delete(state_id)  # Try to delete again


def test_read_returns_list():
    """Test that read() returns a list."""
    states = qry.read()
    assert isinstance(states, list)


def test_read(temp_state):
    """Test that read() includes created state."""
    states = qry.read()
    assert isinstance(states, list)
    # Check if our temp_state is in the list
    state_ids = [state.get('id') for state in states]
    assert temp_state in state_ids


def test_delete_removes_from_list(temp_state):
    qry.delete(temp_state)
    states = qry.read()
    state_ids = [state.get('id') for state in states]
    assert temp_state not in state_ids


def test_delete_missing():
    with pytest.raises(KeyError):
        qry.delete("nonexistent entry")

def test_search_by_state_id():
    temp_state = {
        qry.NAME: "Test State",
        qry.STATE_CODE: "TS",
        qry.COUNTRY_CODE: "US",
        qry.CAPITAL: "Test City",
        qry.POPULATION: 500000
    }

    sid = qry.create(temp_state)
    results = qry.search({qry.STATE_CODE: "TS"})
    assert isinstance(results, list)
    assert any(r.get(qry.ID) == sid for r in results)
    qry.delete(sid)
    
    
@patch('data.db_connect.read', side_effect=Exception('Connection failed'))
@patch('data.db_connect.connect_db', return_value=True)
def test_read_connection_error(mock_connect, mock_read):
    with pytest.raises(Exception):
        countries = qry.read()
