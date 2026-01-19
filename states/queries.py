"""
This file deals with our state-level data.
Uses composite key: state_code + country_code as the natural primary key.
"""
import data.db_connect as dbc

STATE_COLLECTION = 'states'

# Composite primary key
STATE_CODE = 'state_code'   # e.g., 'NY', 'CA', 'ON'
COUNTRY_CODE = 'country_code'  # e.g., 'US', 'CA', 'MX'

NAME = 'name'
CAPITAL = 'capital'
POPULATION = 'population'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'

SAMPLE_STATE = {
    NAME: 'New York',
    STATE_CODE: 'NY',
    COUNTRY_CODE: 'US',
    CAPITAL: 'Albany',
    POPULATION: 19450000
}

state_cache = {}


def is_valid_state_code(code: str) -> bool:
    """
    Validate state code format.
    State codes are typically 2-10 alphanumeric characters.
    """
    if not isinstance(code, str):
        return False
    code = code.strip()
    if len(code) < 1 or len(code) > 10:
        return False
    return True


def is_valid_country_code(code: str) -> bool:
    """Validate country code format."""
    if not isinstance(code, str):
        return False
    code = code.strip()
    if len(code) < 2 or len(code) > 3:
        return False
    if not code.isalpha():
        return False
    return True


def num_states() -> int:
    return len(read())


def create(flds: dict, reload=True):
    """
    Create a new state.

    Args:
        flds: Dictionary with required fields:
            - name: State name
            - state_code: State code (e.g., 'NY')
            - country_code: Country code (e.g., 'US')

    Returns:
        Tuple of (state_code, country_code) - the composite primary key

    Raises:
        ValueError: If validation fails (bad type, missing name,
            invalid fields, country doesn't exist, or
            duplicate state_code+country_code)
    """
    dbc.connect_db()
    print(f'{flds=}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    if not flds.get(STATE_CODE):
        raise ValueError('State code is required')
    if not flds.get(COUNTRY_CODE):
        raise ValueError('Country code is required')
    if not is_valid_state_code(flds[STATE_CODE]):
        raise ValueError(f'Invalid state code format: {flds[STATE_CODE]}')
    if not is_valid_country_code(flds[COUNTRY_CODE]):
        raise ValueError(f'Invalid country code format: {flds[COUNTRY_CODE]}')

    # Normalize codes to uppercase
    flds[STATE_CODE] = flds[STATE_CODE].upper()
    flds[COUNTRY_CODE] = flds[COUNTRY_CODE].upper()

    if LATITUDE in flds:
        lat = flds[LATITUDE]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError(
                f'Latitude must be a number between -90 and 90, got {lat}'
            )
    if LONGITUDE in flds:
        lon = flds[LONGITUDE]
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            raise ValueError(
                f'Longitude must be between -180 and 180, got {lon}'
            )

    # Validate country exists
    import countries.queries as countries_qry
    if not countries_qry.code_exists(flds[COUNTRY_CODE]):
        raise ValueError(
            f'Country with code {flds[COUNTRY_CODE]} does not exist'
        )

    # Check for duplicate state_code + country_code combination
    if state_exists(flds[STATE_CODE], flds[COUNTRY_CODE]):
        raise ValueError(
            f'State {flds[STATE_CODE]} already exists in '
            f'country {flds[COUNTRY_CODE]}'
        )

    dbc.create(STATE_COLLECTION, flds)
    if reload:
        load_cache()
    return (flds[STATE_CODE], flds[COUNTRY_CODE])


def update(state_code: str, country_code: str, flds: dict):
    """
    Update an existing state.

    Args:
        state_code: State code (e.g., 'NY')
        country_code: Country code (e.g., 'US')
        flds: Dictionary with fields to update

    Returns:
        Tuple of (state_code, country_code)

    Raises:
        ValueError: If validation fails
        KeyError: If state not found
    """
    if not is_valid_state_code(state_code):
        raise ValueError(f'Invalid state code: {state_code}')
    if not is_valid_country_code(country_code):
        raise ValueError(f'Invalid country code: {country_code}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if POPULATION in flds and not isinstance(flds[POPULATION], int):
        raise ValueError(
            f'Population must be an integer, '
            f'got {type(flds[POPULATION]).__name__}'
        )
    if LATITUDE in flds:
        lat = flds[LATITUDE]
        if not isinstance(lat, (int, float)) or not (-90 <= lat <= 90):
            raise ValueError(
                f'Latitude must be a number between -90 and 90, got {lat}'
            )
    if LONGITUDE in flds:
        lon = flds[LONGITUDE]
        if not isinstance(lon, (int, float)) or not (-180 <= lon <= 180):
            raise ValueError(
                f'Longitude must be between -180 and 180, got {lon}'
            )

    # Don't allow changing the primary key
    if STATE_CODE in flds:
        del flds[STATE_CODE]
    if COUNTRY_CODE in flds:
        del flds[COUNTRY_CODE]

    updated = dbc.update(
        STATE_COLLECTION,
        {STATE_CODE: state_code.upper(), COUNTRY_CODE: country_code.upper()},
        flds
    )

    if not updated or getattr(updated, 'matched_count', 0) < 1:
        raise KeyError(f'State not found: {state_code} in {country_code}')
    return (state_code.upper(), country_code.upper())


def get(state_code: str, country_code: str) -> dict:
    """Retrieve a state by composite key."""
    if not is_valid_state_code(state_code):
        raise ValueError(f'Invalid state code: {state_code}')
    if not is_valid_country_code(country_code):
        raise ValueError(f'Invalid country code: {country_code}')
    state = dbc.read_one(STATE_COLLECTION, {
        STATE_CODE: state_code.upper(),
        COUNTRY_CODE: country_code.upper()
    })
    if not state:
        raise KeyError(f'State not found: {state_code} in {country_code}')
    return state


def delete(state_code: str, country_code: str):
    """Delete a state by composite key."""
    if not is_valid_state_code(state_code):
        raise ValueError(f'Invalid state code: {state_code}')
    if not is_valid_country_code(country_code):
        raise ValueError(f'Invalid country code: {country_code}')
    ret = dbc.delete(STATE_COLLECTION, {
        STATE_CODE: state_code.upper(),
        COUNTRY_CODE: country_code.upper()
    })
    if ret < 1:
        raise KeyError(f'State not found: {state_code} in {country_code}')
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


def get_states_by_country(country_code: str) -> list:
    """
    Get all states in a country.

    Args:
        country_code: Country code (e.g., 'US', 'CA')

    Returns:
        List of state dicts
    """
    return dbc.read_many(
        STATE_COLLECTION, {COUNTRY_CODE: country_code.upper()}
    )


def main():
    create(SAMPLE_STATE)
    print(read())
