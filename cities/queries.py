"""
This file deals with our city-level data.
"""
from random import randint

MIN_ID_LEN = 1

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
    return len(city_cache)


def create(flds: dict):
    """
    Create a new city with validation (international support).
    
    Args:
        flds: Dictionary with 'name' (required) and 'state_code' (optional)
              state_code can be any region identifier (US state, Canadian province, etc.)
        
    Returns:
        New city ID as string
        
    Raises:
        ValueError: If validation fails (bad type, missing name, or invalid state_code format)
        
    Examples:
        >>> create({'name': 'New York', 'state_code': 'NY'})      # US
        >>> create({'name': 'Toronto', 'state_code': 'ON'})       # Canada
        >>> create({'name': 'Sydney', 'state_code': 'NSW'})       # Australia
        >>> create({'name': 'Tokyo', 'state_code': 'Tokyo'})      # Japan
    """
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    
    # Validate state code format if provided (length, characters, etc.)
    if STATE_CODE in flds and flds[STATE_CODE]:
        if not is_valid_state_code(flds[STATE_CODE]):
            raise ValueError(f'Invalid state code format: {flds[STATE_CODE]}')
    
    new_id = str(len(city_cache) + 1)
    city_cache[new_id] = flds
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
    if city_id not in city_cache:
        raise KeyError(f'City not found: {city_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    
    # Validate state code format if being updated
    if STATE_CODE in flds and flds[STATE_CODE]:
        if not is_valid_state_code(flds[STATE_CODE]):
            raise ValueError(f'Invalid state code format: {flds[STATE_CODE]}')
    
    city_cache[city_id].update(flds)
    return city_id


def get(city_id: str) -> dict:
    """Retrieve a city by ID."""
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    if city_id not in city_cache:
        raise KeyError(f'City not found: {city_id}')
    return city_cache[city_id]


def delete(city_id: str):
    """Delete a city by ID."""
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    if city_id not in city_cache:
        raise KeyError(f'City not found: {city_id}')
    del city_cache[city_id]

def read() -> dict:
    if not db_connect(3):
        raise ConnectionError('Could not connect to DB.')
    return city_cache

def main():
    print(read())
