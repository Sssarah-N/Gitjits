"""
This file deals with our country-level data.
"""
from bson import ObjectId
import data.db_connect as dbc

MIN_ID_LEN = 1

COUNTRY_COLLECTION = 'countries'

ID = 'id'
NAME = 'name'
CODE = 'code'  # ISO country code (e.g., 'US', 'CA', 'UK')
CAPITAL = 'capital'
POPULATION = 'population'
CONTINENT = 'continent'

SAMPLE_COUNTRY = {
    NAME: 'United States',
    CODE: 'US',
    CAPITAL: 'Washington, D.C.',
    POPULATION: 331000000,
    CONTINENT: 'North America'
}

country_cache = {
    '1': SAMPLE_COUNTRY,
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


def num_countries() -> int:
    return len(read())


def create(flds: dict):
    """
    Create a new country.
    
    Args:
        flds: Dictionary with 'name' (required) and optional fields:
              - code: ISO country code (e.g., 'US', 'CA', 'UK')
              - capital: Capital city name
              - population: Country population
              - continent: Continent name
    
    Returns:
        New country ID as string
    
    Raises:
        ValueError: If validation fails (bad type, missing name, invalid fields)
    """
    dbc.connect_db()
    print(f'{flds=}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    
    # Validate population if provided
    if POPULATION in flds and flds[POPULATION] is not None:
        if not isinstance(flds[POPULATION], int):
            raise ValueError(f'Population must be an integer, got {type(flds[POPULATION]).__name__}')
    
    new_id = dbc.create(COUNTRY_COLLECTION, flds)
    print(f'{new_id=}')
    dbc.update(COUNTRY_COLLECTION, {'_id': ObjectId(new_id)}, {'id': new_id})
    return new_id


def update(country_id: str, flds: dict):
    """
    Update an existing country.
    
    Args:
        country_id: ID of the country to update
        flds: Dictionary with fields to update
        
    Returns:
        The country ID
        
    Raises:
        ValueError: If validation fails (bad ID or bad type)
        KeyError: If country not found
    """
    if not is_valid_id(country_id):
        raise ValueError(f'Invalid ID: {country_id}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    
    # Validate population if provided
    if POPULATION in flds and flds[POPULATION] is not None:
        if not isinstance(flds[POPULATION], int):
            raise ValueError(f'Population must be an integer, got {type(flds[POPULATION]).__name__}')

    updated = dbc.update(COUNTRY_COLLECTION, {ID: country_id}, flds)

    if not updated or getattr(updated, 'matched_count', 0) < 1:
        raise KeyError(f'Country not found: {country_id}')
    return country_id


def get(country_id: str) -> dict:
    """Retrieve a country by ID."""
    if not is_valid_id(country_id):
        raise ValueError(f'Invalid ID: {country_id}')
    country = dbc.read_one(COUNTRY_COLLECTION, {ID: country_id})
    if not country:
        raise KeyError(f'Country not found: {country_id}')
    return country


def delete(country_id: str):
    """Delete a country by ID."""
    if not is_valid_id(country_id):
        raise ValueError(f'Invalid ID: {country_id}')
    ret = dbc.delete(COUNTRY_COLLECTION, {ID: country_id})
    if ret < 1:
        raise KeyError(f'Country not found: {country_id}')
    return ret


def read() -> list:
    """Get all countries."""
    return dbc.read(COUNTRY_COLLECTION)


def get_by_code(code: str) -> dict:
    """
    Get a country by its country code.
    
    Args:
        code: Country code (e.g., 'US', 'CA', 'UK')
    
    Returns:
        Country dict
    
    Raises:
        KeyError: If country not found
    """
    country = dbc.read_one(COUNTRY_COLLECTION, {CODE: code.upper()})
    if not country:
        raise KeyError(f'Country not found with code: {code}')
    return country


def code_exists(code: str) -> bool:
    """Check if a country code exists."""
    try:
        get_by_code(code)
        return True
    except KeyError:
        return False


def main():
    print(read())

