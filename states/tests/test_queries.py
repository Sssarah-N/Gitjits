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


@pytest.fixture(autouse=True)
def mock_db_operations():
    """Mock all database operations to use in-memory storage for fast tests."""
    global _test_db, _next_id
    _test_db = {}
    _next_id = 1
    
    def mock_connect():
        pass
    
    def mock_create(collection, doc):
        new_obj_id = ObjectId()
        doc_id = str(new_obj_id)
        _test_db[doc_id] = {**doc, 'id': doc_id}
        return doc_id
    
    def mock_read(collection):
        return list(_test_db.values())
    
    def mock_read_one(collection, query):
        state_id = query.get('id')
        return _test_db.get(state_id)
    
    def mock_update(collection, query, fields):
        # Handle both ObjectId queries and id queries
        if '_id' in query:
            # This is the initial update to add 'id' field after creation
            # Extract the id from the fields being set
            state_id = fields.get('id')
            if state_id and state_id in _test_db:
                _test_db[state_id].update(fields)
                result = MagicMock()
                result.matched_count = 1
                return result
        else:
            state_id = query.get('id')
            if state_id in _test_db:
                _test_db[state_id].update(fields)
                result = MagicMock()
                result.matched_count = 1
                return result
        result = MagicMock()
        result.matched_count = 0
        return result
    
    def mock_delete(collection, query):
        state_id = query.get('id')
        if state_id in _test_db:
            del _test_db[state_id]
            return 1
        return 0
    
    with patch('data.db_connect.connect_db', mock_connect), \
         patch('data.db_connect.create', mock_create), \
         patch('data.db_connect.read', mock_read), \
         patch('data.db_connect.read_one', mock_read_one), \
         patch('data.db_connect.update', mock_update), \
         patch('data.db_connect.delete', mock_delete):
        yield


@pytest.fixture(scope='function')
def temp_state():
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
    old_count = qry.num_states()
    temp_rec = get_temp_rec()
    new_rec_id = qry.create(temp_rec)
    assert qry.is_valid_id(new_rec_id)
    assert qry.num_states() > old_count


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
    state_id = qry.create(state)
    stored = qry.get(state_id)
    assert stored["area"] == 54555


def test_update():
    temp_rec = get_temp_rec()  
    state_id = qry.create(temp_rec)
    update_data = {qry.NAME: temp_rec[qry.NAME] + " Updated", qry.STATE_CODE: temp_rec[qry.STATE_CODE]}
    result_id = qry.update(state_id, update_data)
    
    # Verify update worked
    assert result_id == state_id
    updated_state = qry.get(state_id)
    assert updated_state[qry.NAME] == temp_rec[qry.NAME] + " Updated"

def test_update_population():
    temp_rec = get_temp_rec()
    state_id = qry.create(temp_rec)
    new_population = 12345678
    update_data = {qry.POPULATION: new_population}
    result_id = qry.update(state_id, update_data)
    assert result_id == state_id
    updated_state = qry.get(state_id)
    assert updated_state[qry.POPULATION] == new_population
    

def test_update_population_bad_type():
    temp_rec = get_temp_rec()
    state_id = qry.create(temp_rec)
    update_data = {qry.POPULATION: "a lot"}
    with pytest.raises(ValueError):
        qry.update(state_id, update_data)

    
def test_update_bad_id():
    with pytest.raises(ValueError):
        qry.update(123, {qry.NAME: "California"})


def test_update_missing_id():
    with pytest.raises(KeyError):
        qry.update("CA", {qry.NAME: "California"})


def test_update_bad_fields_param_type():
    state_id = qry.create(get_temp_rec())
    with pytest.raises(ValueError):
        qry.update(state_id, 123)
        
     
def test_get():
    temp_rec = get_temp_rec()
    state_id = qry.create(temp_rec)
    state = qry.get(state_id)
    assert state[qry.NAME] == temp_rec[qry.NAME]
    assert state[qry.STATE_CODE] == temp_rec[qry.STATE_CODE]


def test_get_bad_id():
    with pytest.raises(ValueError):
        qry.get(123)


def test_get_missing_id():
    with pytest.raises(KeyError):
        qry.get("999")


def test_delete():
    temp_rec = get_temp_rec()
    state_id = qry.create(temp_rec)
    qry.delete(state_id)
    # Verify state is deleted by trying to get it
    with pytest.raises(KeyError):
        qry.get(state_id)
    

def test_delete_bad_id():
    with pytest.raises(ValueError):
        qry.delete(123)


def test_delete_missing_id():
    with pytest.raises(KeyError):
        qry.create({qry.NAME: "California", qry.STATE_CODE: "CA", qry.COUNTRY_CODE: "US"})
        qry.delete("CA")


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
