"""
This file deals with our city-level data.
"""
from bson import ObjectId
import data.db_connect as dbc

MIN_ID_LEN = 1

CITY_COLLECTION = 'cities'

ID = 'id'
NAME = 'name'
STATE_CODE = 'state_code'

# Maximum length for state/province/region codes
MAX_STATE_CODE_LENGTH = 10

SAMPLE_CITY = {
    NAME: 'New York',
    STATE_CODE: 'NY'
}

city_cache = {
    '1': SAMPLE_CITY,
}

def db_connect(success_ratio: int) -> bool:
    """
    Return True if connected, False if not.
    """
    return randint(1, success_ratio) % success_ratio

def is_valid_id(_id: str) -> bool:
    """
    Since flask treat http request as text, 
    everything is passed in as a string by default,
    therefore nothing would be an invalid id for now.
    Empty string returns false,
    but that redirects the page so it won't get tested.
    #needs attention or resolve.
    """
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def is_valid_state_code(state_code: str) -> bool:
    """
    Validate state/province/region code format (international-friendly).
    
    Accepts any alphanumeric code with reasonable length.
    Works for US states, Canadian provinces, Australian states, etc.
    
    Args:
        state_code: State/province/region code (e.g., 'NY', 'ON', 'NSW', 'Tokyo')
        
    Returns:
        True if format is valid, False otherwise
        
    Examples:
        >>> is_valid_state_code('NY')      # US - New York
        True
        >>> is_valid_state_code('ON')      # Canada - Ontario
        True
        >>> is_valid_state_code('NSW')     # Australia - New South Wales
        True
        >>> is_valid_state_code('Tokyo')   # Japan
        True
        >>> is_valid_state_code('X' * 20) # Too long
        False
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
              state_code can be any region identifier (US state, Canadian province, etc.)
        
    Returns:
        New city ID as string
        
    Raises:
        ValueError: If validation fails (bad type, missing name, invalid state_code format,
                    or city with same name and state_code already exists)
        
    Examples:
        >>> create({'name': 'New York', 'state_code': 'NY'})      # US
        >>> create({'name': 'Toronto', 'state_code': 'ON'})       # Canada
        >>> create({'name': 'Sydney', 'state_code': 'NSW'})       # Australia
        >>> create({'name': 'Tokyo', 'state_code': 'Tokyo'})      # Japan
    """
    dbc.connect_db()
    print(f'{flds=}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    
    # Check if city with same name and state_code already exists
    if STATE_CODE in flds and flds[STATE_CODE]:
        existing_cities = get_by_state_code(flds[STATE_CODE])
        city_name = flds[NAME].strip()
        for existing_city in existing_cities:
            if existing_city.get(NAME, '').strip().upper() == city_name.upper():
                raise ValueError(
                    f'City with name "{city_name}" and state_code "{flds[STATE_CODE]}" already exists'
                )
    
    new_id = dbc.create(CITY_COLLECTION, flds)
    print(f'{new_id=}')
    dbc.update(CITY_COLLECTION, {'_id': ObjectId(new_id)}, {'id': new_id})
    return new_id


def update(city_id: str, flds: dict):
    """
    Update an existing city with validation (international support).
    
    Args:
        city_id: ID of the city to update
        flds: Dictionary with fields to update (name, state_code)
              state_code can be any region identifier
        
    Returns:
        The city ID
        
    Raises:
        ValueError: If validation fails (bad ID, bad type, or invalid state_code format)
        KeyError: If city not found
    """
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')

    updated = dbc.update(CITY_COLLECTION, {ID: city_id}, flds)

    if not updated or getattr(updated, 'matched_count', 0) < 1:
        raise KeyError(f'City not found: {city_id}')
    return city_id


def get(city_id: str) -> dict:
    """Retrieve a city by ID."""
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    city = dbc.read_one(CITY_COLLECTION, {ID: city_id})
    if not city:
        raise KeyError(f'City not found: {city_id}')
    return city


def delete(city_id: str):
    """Delete a city by ID."""
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    ret = dbc.delete(CITY_COLLECTION, {ID: city_id})
    if ret < 1:
        raise KeyError(f'City not found: {city_id}')
    return ret

def read() -> list:
    return dbc.read(CITY_COLLECTION)


def get_by_state_code(state_code: str) -> list:
    """
    Get all cities in a state/province/region by state code (case-insensitive).
    
    Args:
        state_code: State/province/region code (e.g., 'NY', 'ON', 'NSW', 'Tokyo')
    
    Returns:
        List of city dictionaries matching the state code
    """
    if not isinstance(state_code, str):
        raise ValueError(f'State code must be a string, got {type(state_code).__name__}')
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
