"""
This file deals with our state-level data.
"""
from bson import ObjectId
import data.db_connect as dbc

MONGO_ID = '_id'

MIN_ID_LEN = 1

STATE_COLLECTION = 'states'

ID = 'id'
NAME = 'name'
STATE_CODE = 'state_code'  # Composite key with country_code (e.g., 'NY', 'CA', 'ON')
CAPITAL = 'capital'
POPULATION = 'population'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
COUNTRY_CODE = 'country_code'  # Composite key with state_code (e.g., 'US', 'CA', 'MX')

SAMPLE_STATE = {
    NAME: 'New York',
    STATE_CODE: 'NY',
    COUNTRY_CODE: 'US',
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
    return len(read())


def create(flds: dict, reload=True):
    """
    Create a new state.
    
    Raises:
        ValueError: If validation fails (bad type, missing name, invalid fields,
                    or state with same state_code and country_code already exists)
    """
    dbc.connect_db()
    print(f'{flds=}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    if LATITUDE in flds:
        lat = flds[LATITUDE]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError(f'Latitude must be a number between -90 and 90, got {lat}')
    if LONGITUDE in flds:
        lon = flds[LONGITUDE]
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            raise ValueError(f'Longitude must be a number between -180 and 180, got {lon}')
    
    # Check if state with same state_code and country_code already exists
    if STATE_CODE in flds and flds[STATE_CODE]:
        country_code = flds.get(COUNTRY_CODE, 'US')  # Default to 'US' if not provided
        # Read all states and check case-insensitively
        all_states = read()
        state_code_upper = flds[STATE_CODE].upper()
        country_code_upper = country_code.upper()
        for existing_state in all_states:
            existing_state_code = existing_state.get(STATE_CODE, '').upper()
            existing_country_code = existing_state.get(COUNTRY_CODE, 'US').upper()
            if existing_state_code == state_code_upper and existing_country_code == country_code_upper:
                raise ValueError(
                    f'State with state_code "{flds[STATE_CODE]}" and country_code "{country_code}" already exists'
                )
    
    new_id = dbc.create(STATE_COLLECTION, flds)
    if reload:
        load_cache()
    dbc.update(STATE_COLLECTION, {'_id': ObjectId(new_id)}, {'id': new_id})
    return new_id


def update(state_id: str, flds: dict):
    """
    Update an existing state.
    
    Args:
        state_id: ID of the state to update
        flds: Dictionary with fields to update
        
    Returns:
        The state ID
        
    Raises:
        ValueError: If validation fails (bad ID or bad type)
        KeyError: If state not found
    """
    if not is_valid_id(state_id):
        raise ValueError(f'Invalid ID: {state_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if POPULATION in flds and not isinstance(flds[POPULATION], int):
        raise ValueError(f'Population must be an integer, got {type(flds[POPULATION]).__name__}')
    if LATITUDE in flds:
        lat = flds[LATITUDE]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError(f'Latitude must be a number between -90 and 90, got {lat}')
    if LONGITUDE in flds:
        lon = flds[LONGITUDE]
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            raise ValueError(f'Longitude must be a number between -180 and 180, got {lon}')

    updated = dbc.update(STATE_COLLECTION, {ID: state_id}, flds)

    if not updated or getattr(updated, 'matched_count', 0) < 1:
        raise KeyError(f'State not found: {state_id}')
    return state_id


def get(state_id: str) -> dict:
    """Retrieve a state by ID."""
    if not is_valid_id(state_id):
        raise ValueError(f'Invalid ID: {state_id}')
    state = dbc.read_one(STATE_COLLECTION, {ID: state_id})
    if not state:
        raise KeyError(f'State not found: {state_id}')
    return state


def delete(state_id: str):
    """Delete a state by ID."""
    if not is_valid_id(state_id):
        raise ValueError(f'Invalid ID: {state_id}')
    ret = dbc.delete(STATE_COLLECTION, {ID: state_id})
    if ret < 1:
        raise KeyError(f'State not found: {state_id}')
    return ret


def delete_by_code(state_code: str, country_code: str = 'US'):
    """
    Delete a state by state_code and country_code if it exists.
    Useful for test cleanup.
    
    Args:
        state_code: State code to delete
        country_code: Country code (default: 'US')
    
    Returns:
        True if deleted, False if not found
    """
    try:
        dbc.connect_db()
        from data.db_connect import client, GEO_DB
        from bson.regex import Regex
        
        # Use regex for case-insensitive matching
        filter_query = {
            STATE_CODE: Regex(f'^{state_code}$', 'i'),
            COUNTRY_CODE: Regex(f'^{country_code}$', 'i')
        }
        
        # Delete all matching documents
        result = client[GEO_DB][STATE_COLLECTION].delete_many(filter_query)
        return result.deleted_count > 0
    except Exception as e:
        print(f'Error in delete_by_code: {e}')
        import traceback
        traceback.print_exc()
        return False


def read() -> list:
    return dbc.read(STATE_COLLECTION)

def search(filt: dict) -> list:
    """General-purpose search on state fields."""
    return dbc.read_many(STATE_COLLECTION, filt)

def load_cache():
    global cache
    cache = {}
    states = dbc.read(STATE_COLLECTION)
    for state in states:
        if STATE_CODE in state:
            country = state.get(COUNTRY_CODE, 'US')  
            cache[(state[STATE_CODE], country)] = state
    
def main():
    create(SAMPLE_STATE)
    print(read())

