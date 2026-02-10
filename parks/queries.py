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
    # TODO: validate park_code
    if not park_code:
        raise ValueError('Park code is required')
    ret = dbc.delete(PARK_COLLECTION, {PARK_CODE: park_code})
    if ret < 1:
        raise KeyError(f'Park not found: {park_code}')
    return ret
