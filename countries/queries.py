"""
This file deals with our country-level data.
Uses 'code' (ISO country code) as the natural primary key.
"""
import data.db_connect as dbc

COUNTRY_COLLECTION = 'countries'

# Primary key - ISO country code (e.g., 'US', 'CA', 'UK')
CODE = 'code'
NAME = 'name'
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

country_cache = {}


def is_valid_code(code: str) -> bool:
    """
    Validate country code format.
    ISO country codes are typically 2-3 uppercase letters.
    """
    if not isinstance(code, str):
        return False
    # Remove user input like spaces, tabs, newlines, etc.
    code = code.strip()
    if len(code) < 2 or len(code) > 3:
        return False
    # Check if the code is all letters 'A' to 'Z'"
    if not code.isalpha():
        return False
    return True


def num_countries() -> int:
    return len(read())


def create(flds: dict, reload=True):
    """
    Create a new country.

    Args:
        flds: Dictionary with 'name' and 'code' (both required) and optional:
            - capital: Capital city name
            - population: Country population
            - continent: Continent name
        reload: If True, reload the cache after creating (default: True)

    Returns:
        Country code as string (the natural primary key)

    Raises:
        ValueError: If validation fails
            (bad type, missing name/code, invalid fields)
    """
    dbc.connect_db()
    print(f'{flds=}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')
    if not flds.get(NAME):
        raise ValueError(f'Bad value for {flds.get(NAME)=}')
    if not flds.get(CODE):
        raise ValueError('Country code is required')
    if not is_valid_code(flds[CODE]):
        raise ValueError(f'Invalid country code format: {flds[CODE]}')

    # Normalize code to uppercase
    flds[CODE] = flds[CODE].upper()

    # Validate population if provided
    if POPULATION in flds and flds[POPULATION] is not None:
        if not isinstance(flds[POPULATION], int):
            raise ValueError(
                f'Population must be an integer, '
                f'got {type(flds[POPULATION]).__name__}'
            )

    # Check for duplicate country code
    if code_exists(flds[CODE]):
        raise ValueError(f'Country with code {flds[CODE]} already exists')

    dbc.create(COUNTRY_COLLECTION, flds)
    if reload:
        load_cache()
    return flds[CODE]


def update(code: str, flds: dict):
    """
    Update an existing country.

    Args:
        code: Country code (e.g., 'US', 'CA')
        flds: Dictionary with fields to update

    Returns:
        The country code

    Raises:
        ValueError: If validation fails (bad code or bad type)
        KeyError: If country not found
    """
    if not is_valid_code(code):
        raise ValueError(f'Invalid country code: {code}')
    if not isinstance(flds, dict):
        raise ValueError(f'Bad type for {type(flds)=}')

    # Validate population if provided
    if POPULATION in flds and flds[POPULATION] is not None:
        if not isinstance(flds[POPULATION], int):
            raise ValueError(
                f'Population must be an integer, '
                f'got {type(flds[POPULATION]).__name__}'
            )

    # Don't allow changing the primary key
    if CODE in flds:
        del flds[CODE]

    updated = dbc.update(COUNTRY_COLLECTION, {CODE: code.upper()}, flds)

    if not updated or getattr(updated, 'matched_count', 0) < 1:
        raise KeyError(f'Country not found: {code}')
    return code.upper()


def get(code: str) -> dict:
    """Retrieve a country by code."""
    if not is_valid_code(code):
        raise ValueError(f'Invalid country code: {code}')
    country = dbc.read_one(COUNTRY_COLLECTION, {CODE: code.upper()})
    if not country:
        raise KeyError(f'Country not found: {code}')
    return country


def delete(code: str):
    """Delete a country by code."""
    if not is_valid_code(code):
        raise ValueError(f'Invalid country code: {code}')
    ret = dbc.delete(COUNTRY_COLLECTION, {CODE: code.upper()})
    if ret < 1:
        raise KeyError(f'Country not found: {code}')
    return ret


def read() -> list:
    """Get all countries."""
    return dbc.read(COUNTRY_COLLECTION)


def code_exists(code: str) -> bool:
    """Check if a country code exists."""
    try:
        get(code)
        return True
    except (KeyError, ValueError):
        return False


def search(filt: dict) -> list:
    """General-purpose search on country fields."""
    return dbc.read_many(COUNTRY_COLLECTION, filt)


def load_cache():
    """Load countries from database into memory cache."""
    global country_cache
    country_cache = {}
    countries = dbc.read(COUNTRY_COLLECTION)
    for country in countries:
        if CODE in country:
            country_cache[country[CODE].upper()] = country


def main():
    print(read())
