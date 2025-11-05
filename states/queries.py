"""
This file deals with our state-level data.
"""
from bson import ObjectId
import data.db_connect as dbc

MIN_ID_LEN = 1

STATE_COLLECTION = 'states'

ID = 'id'
NAME = 'name'
ABBREVIATION = 'abbreviation'
CAPITAL = 'capital'
POPULATION = 'population'

SAMPLE_STATE = {
    NAME: 'New York',
    ABBREVIATION: 'NY',
    CAPITAL: 'Albany',
    POPULATION: 19450000
}

state_cache = {
    '1': SAMPLE_STATE,
}

def is_valid_id(_id: str) -> bool:
    """
    Validate ID format.
    """
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def num_states() -> int:
    return len(state_cache)


def create(flds: dict):
    """
    Create a new state.
    
    Raises:
        ValueError: If validation fails (bad type, missing name, invalid fields)
    """
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    
    new_id = str(len(state_cache) + 1)
    state_cache[new_id] = flds
    return new_id


def update(state_id: str, flds: dict):
    """Update an existing state."""
    if not is_valid_id(state_id):
        raise ValueError(f'Invalid ID: {state_id}')
    if state_id not in state_cache:
        raise KeyError(f'State not found: {state_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    
    state_cache[state_id].update(flds)
    return state_id


def get(state_id: str) -> dict:
    """Retrieve a state by ID."""
    if not is_valid_id(state_id):
        raise ValueError(f'Invalid ID: {state_id}')
    if state_id not in state_cache:
        raise KeyError(f'State not found: {state_id}')
    return state_cache[state_id]


def delete(state_id: str):
    """Delete a state by ID."""
    if not is_valid_id(state_id):
        raise ValueError(f'Invalid ID: {state_id}')
    if state_id not in state_cache:
        raise KeyError(f'State not found: {state_id}')
    del state_cache[state_id]


def read() -> dict:
    return state_cache


def create(flds: dict):
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    new_id = dbc.create(STATE_COLLECTION, flds)
    dbc.update(STATE_COLLECTION, {'_id': ObjectId(new_id)}, {'id': new_id})
    return new_id


def update(_id: str, flds: dict):
    if not is_valid_id(_id):
        raise ValueError(f'Invalid ID: {_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    dbc.update(STATE_COLLECTION, {ID: _id}, flds)
    return _id
    
def main():
    print(read())

