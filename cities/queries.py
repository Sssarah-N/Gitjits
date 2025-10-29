"""
This file deals with our city-level data.
"""
from random import randint

MIN_ID_LEN = 1

ID = 'id'
NAME = 'name'
STATE_CODE = 'state_code'

# Valid US state codes (50 states + DC + 5 territories)
VALID_STATE_CODES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
    'DC', 'PR', 'VI', 'GU', 'AS', 'MP'
}

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
    Validate if the state code is a valid US state/territory code.
    
    Args:
        state_code: Two-letter state code (e.g., 'NY', 'CA')
        
    Returns:
        True if valid, False otherwise
        
    Example:
        >>> is_valid_state_code('NY')
        True
        >>> is_valid_state_code('XX')
        False
    """
    if not isinstance(state_code, str):
        return False
    return state_code.upper() in VALID_STATE_CODES


def num_cities() -> int:
    return len(city_cache)


def create(flds: dict):
    """
    Create a new city with validation.
    
    Args:
        flds: Dictionary with 'name' (required) and 'state_code' (optional)
        
    Returns:
        New city ID as string
        
    Raises:
        ValueError: If validation fails (bad type, missing name, or invalid state code)
    """
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    
    # Validate state code if provided
    if STATE_CODE in flds and flds[STATE_CODE]:
        if not is_valid_state_code(flds[STATE_CODE]):
            raise ValueError(f'Invalid state code: {flds[STATE_CODE]}')
    
    new_id = str(len(city_cache) + 1)
    city_cache[new_id] = flds
    return new_id


def update(city_id: str, flds: dict):
    """
    Update an existing city with validation.
    
    Args:
        city_id: ID of the city to update
        flds: Dictionary with fields to update (name, state_code)
        
    Returns:
        The city ID
        
    Raises:
        ValueError: If validation fails (bad ID, bad type, or invalid state code)
        KeyError: If city not found
    """
    if not is_valid_id(city_id):
        raise ValueError(f'Invalid ID: {city_id}')
    if city_id not in city_cache:
        raise KeyError(f'City not found: {city_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    
    # Validate state code if being updated
    if STATE_CODE in flds and flds[STATE_CODE]:
        if not is_valid_state_code(flds[STATE_CODE]):
            raise ValueError(f'Invalid state code: {flds[STATE_CODE]}')
    
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
