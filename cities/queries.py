"""
This file deals with our city-level data.
Uses MongoDB _id as the primary key (cities don't have a natural key).
"""
from bson import ObjectId
import data.db_connect as dbc

CITY_COLLECTION = 'cities'

MONGO_ID = '_id'
NAME = 'name'
STATE_CODE = 'state_code'
COUNTRY_CODE = 'country_code'

# Maximum length for state/province/region codes
MAX_STATE_CODE_LENGTH = 10

SAMPLE_CITY = {
    NAME: 'New York',
    STATE_CODE: 'NY',
    COUNTRY_CODE: 'US'
}

city_cache = {}


def is_valid_id(_id: str) -> bool:
    """
    Validate MongoDB ObjectId format.
    """
    if not isinstance(_id, str):
        return False
    return ObjectId.is_valid(_id)


def is_valid_state_code(state_code: str) -> bool:
    """
    Validate state/province/region code format (international-friendly).

    Accepts any alphanumeric code with reasonable length.
    Works for US states, Canadian provinces, Australian states, etc.
    """
    if not isinstance(state_code, str):
        return False

    # Remove whitespace for validation
    code = state_code.strip()

    # Check length (2-10 characters is reasonable for most regions)
    if len(code) < 1 or len(code) > MAX_STATE_CODE_LENGTH:
        return False

    # Allow alphanumeric, spaces, hyphens (for regions like "New South Wales")
    # But require at least one letter
    if not any(c.isalpha() for c in code):
        return False

    return True


def num_cities() -> int:
    return len(read())


def create(flds: dict):
    """
    Create a new city with validation (international support).

    Args:
        flds: Dictionary with 'name' (required) and 'state_code' (optional)
            state_code can be any region identifier
            (US state, Canadian province, etc.)

    Returns:
        New city ID as string (MongoDB ObjectId)

    Raises:
        ValueError: If validation fails
            (bad type, missing name, or invalid state_code format)

    Examples:
        >>> create({'name': 'New York', 'state_code': 'NY'})
        >>> create({'name': 'Toronto', 'state_code': 'ON'})
    """
    dbc.connect_db()
    print(f'{flds=}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')

    # Validate and normalize state_code if provided
    if flds.get(STATE_CODE):
        if not is_valid_state_code(flds[STATE_CODE]):
            raise ValueError(f'Invalid state code format: {flds[STATE_CODE]}')
        flds[STATE_CODE] = flds[STATE_CODE].upper()

    # Normalize country_code if provided
    if flds.get(COUNTRY_CODE):
        flds[COUNTRY_CODE] = flds[COUNTRY_CODE].upper()

    new_id = dbc.create(CITY_COLLECTION, flds)
    print(f'{new_id=}')
    return new_id


def update(city_id: str, flds: dict):
    """
    Update an existing city with validation (international support).

    Args:
        city_id: MongoDB ObjectId as string
        flds: Dictionary with fields to update (name, state_code)
            state_code can be any region identifier

    Returns:
        The city ID

    Raises:
        ValueError: If validation fails
            (bad ID, bad type, or invalid state_code format)
        KeyError: If city not found
    """
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')

    # Validate and normalize state_code if provided
    if flds.get(STATE_CODE):
        if not is_valid_state_code(flds[STATE_CODE]):
            raise ValueError(f'Invalid state code format: {flds[STATE_CODE]}')
        flds[STATE_CODE] = flds[STATE_CODE].upper()

    # Normalize country_code if provided
    if flds.get(COUNTRY_CODE):
        flds[COUNTRY_CODE] = flds[COUNTRY_CODE].upper()

    updated = dbc.update(
        CITY_COLLECTION, {MONGO_ID: ObjectId(city_id)}, flds
    )

    if not updated or getattr(updated, 'matched_count', 0) < 1:
        raise KeyError(f'City not found: {city_id}')
    return city_id


def get(city_id: str) -> dict:
    """Retrieve a city by MongoDB ObjectId."""
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    city = dbc.read_one(CITY_COLLECTION, {MONGO_ID: ObjectId(city_id)})
    if not city:
        raise KeyError(f'City not found: {city_id}')
    return city


def delete(city_id: str):
    """Delete a city by MongoDB ObjectId."""
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    ret = dbc.delete(CITY_COLLECTION, {MONGO_ID: ObjectId(city_id)})
    if ret < 1:
        raise KeyError(f'City not found: {city_id}')
    return ret


def read() -> list:
    return dbc.read(CITY_COLLECTION)


def get_cities_by_state(state_code: str) -> list:
    """
    Get all cities in a state (deprecated, use get_by_state instead).

    Args:
        state_code: State/province code (e.g., 'NY', 'ON')

    Returns:
        List of city dicts
    """
    return dbc.read_many(CITY_COLLECTION, {STATE_CODE: state_code})


def get_by_state(country_code: str, state_code: str) -> list:
    """
    Get all cities in a specific country+state combination.

    This is the canonical way to query cities by state,
    as state_code alone is not globally unique.

    Args:
        country_code: ISO country code (e.g., 'US', 'CA')
        state_code: State/province code (e.g., 'NY', 'ON')

    Returns:
        List of city dictionaries matching the country+state
    """
    query = {
        COUNTRY_CODE: country_code.upper(),
        STATE_CODE: state_code.upper()
    }
    return dbc.read_many(CITY_COLLECTION, query)


def get_by_state_code(state_code: str) -> list:
    """
    Get all cities in a state/province/region by state code (case-insensitive).

    Alias for get_cities_by_state for backwards compatibility.

    Args:
        state_code: State/province/region code
            (e.g., 'NY', 'ON', 'NSW', 'Tokyo')

    Returns:
        List of city dictionaries matching the state code
    """
    if not isinstance(state_code, str):
        raise ValueError(
            f'State code must be a string, got {type(state_code).__name__}'
        )
    all_cities = dbc.read(CITY_COLLECTION)
    return [
        city for city in all_cities
        if city.get(STATE_CODE, '').upper() == state_code.upper()
    ]


def search(filt: dict) -> list:
    """General-purpose search on city fields."""
    return dbc.read_many(CITY_COLLECTION, filt)


def main():
    print(read())
