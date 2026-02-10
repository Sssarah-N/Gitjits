"""
This file deals with our city-level data.
Uses MongoDB _id as the primary key (cities don't have a natural key).
"""
from bson import ObjectId
import data.db_connect as dbc

PARK_COLLECTION = 'parks'

MONGO_ID = '_id'
NAME = 'name'
STATE_CODE = 'state_code'
PARK_CODE = 'park_code'

# Maximum length for state/province/region codes
MAX_STATE_CODE_LENGTH = 10

SAMPLE_PARK = {
    NAME: 'Abraham Lincoln Birthplace National Historical Park',
    PARK_CODE: 'abli',  # park code is from our dataset
    STATE_CODE: 'KY'
}

park_cache = {}


def is_valid_id(_id: str) -> bool:
    """
    Validate MongoDB ObjectId format.
    """
    if not isinstance(_id, str):
        return False
    return ObjectId.is_valid(_id)


def read() -> list:
    """Get all parks."""
    return dbc.read(PARK_COLLECTION)


def create(flds: dict, reload=True):
    """Create a new park record."""
    dbc.connect_db()
    # TODO: validate flds
    # TODO: handle more fields (lat, long, url, activities, etc.)
    if reload:
        park_cache.clear()
    dbc.create(PARK_COLLECTION, flds)
    return flds[PARK_CODE]


def get(park_code: str) -> dict:
    """Get a park record by its park code."""
    dbc.connect_db()
    # TODO: validate park_code
    return dbc.read_one(PARK_COLLECTION, {PARK_CODE: park_code})


def delete(park_code: str):
    """Delete a park by park code."""
    dbc.connect_db()

    # Validate park_code
    if not park_code:
        raise ValueError('Park code is required')
    if not isinstance(park_code, str):
        raise ValueError(
            f'Park code must be a string, got {type(park_code).__name__}'
        )

    # Park codes are typically 2-6 lowercase alphanumeric characters
    park_code = park_code.strip().lower()
    if len(park_code) < 2 or len(park_code) > 10:
        raise ValueError(f'Invalid park code length: {park_code}')
    if not park_code.isalnum():
        raise ValueError(f'Park code must be alphanumeric: {park_code}')

    # Clear cache before deletion
    park_cache.clear()

    # Delete the park
    ret = dbc.delete(PARK_COLLECTION, {PARK_CODE: park_code})
    if ret < 1:
        raise KeyError(f'Park not found: {park_code}')

    return ret
