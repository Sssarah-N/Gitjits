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
                    country doesn't exist, or duplicate state_code+country_code)
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

    # Validate country exists if country_code provided
    if flds.get(COUNTRY_CODE):
        import countries.queries as countries_qry
        if not countries_qry.code_exists(flds[COUNTRY_CODE]):
            raise ValueError(f'Country with code {flds[COUNTRY_CODE]} does not exist')

    # Check for duplicate state_code + country_code combination
    if flds.get(STATE_CODE) and flds.get(COUNTRY_CODE):
        if state_exists(flds[STATE_CODE], flds[COUNTRY_CODE]):
            raise ValueError(
                f'State {flds[STATE_CODE]} already exists in country {flds[COUNTRY_CODE]}'
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


def state_exists(state_code: str, country_code: str) -> bool:
    """
    Check if a state with given state_code exists in the country.

    Args:
        state_code: State/province code (e.g., 'NY', 'ON')
        country_code: Country code (e.g., 'US', 'CA')

    Returns:
        True if state exists, False otherwise
    """
    return dbc.exists(STATE_COLLECTION, {
        STATE_CODE: state_code.upper(),
        COUNTRY_CODE: country_code.upper()
    })


def get_by_code(state_code: str, country_code: str) -> dict:
    """
    Get a state by its state code and country code.

    Args:
        state_code: State/province code (e.g., 'NY', 'ON')
        country_code: Country code (e.g., 'US', 'CA')

    Returns:
        State dict

    Raises:
        KeyError: If state not found
    """
    state = dbc.read_one(STATE_COLLECTION, {
        STATE_CODE: state_code.upper(),
        COUNTRY_CODE: country_code.upper()
    })
    if not state:
        raise KeyError(f'State not found: {state_code} in {country_code}')
    return state


def get_states_by_country(country_code: str) -> list:
    """
    Get all states in a country.

    Args:
        country_code: Country code (e.g., 'US', 'CA')

    Returns:
        List of state dicts
    """
    return dbc.read_many(STATE_COLLECTION, {COUNTRY_CODE: country_code.upper()})


def main():
    create(SAMPLE_STATE)
    print(read())
