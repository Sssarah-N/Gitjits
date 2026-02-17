"""
This file deals with our national parks data.
Uses park_code as the primary key (from NPS dataset).
"""
from bson import ObjectId
import data.db_connect as dbc

PARK_COLLECTION = 'parks'

# Field constants
MONGO_ID = '_id'
NAME = 'name'
FULL_NAME = 'full_name'
PARK_CODE = 'park_code'
STATE_CODE = 'state_code'
DESCRIPTION = 'description'
LATITUDE = 'latitude'
LONGITUDE = 'longitude'
URL = 'url'
ACTIVITIES = 'activities'
CONTACTS = 'contacts'
DIRECTIONS_INFO = 'directions_info'
DIRECTIONS_URL = 'directions_url'
OPERATING_HOURS = 'operating_hours'
ADDRESSES = 'addresses'
IMAGES = 'images'
WEATHER_INFO = 'weather_info'
DESIGNATION = 'designation'

# Maximum length for state/province/region codes
MAX_STATE_CODE_LENGTH = 10

SAMPLE_PARK = {
    NAME: 'Abraham Lincoln Birthplace',
    FULL_NAME: 'Abraham Lincoln Birthplace National Historical Park',
    PARK_CODE: 'abli',
    STATE_CODE: 'KY,IN',
    LATITUDE: 37.5858662,
    LONGITUDE: -85.67330523,
    DESIGNATION: 'National Historical Park'
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

    if not isinstance(flds, dict):
        raise ValueError(f'Expected dict, got {type(flds).__name__}')
    if not flds.get(PARK_CODE):
        raise ValueError('Park code is required')
    if not flds.get(NAME) and not flds.get(FULL_NAME):
        raise ValueError('Park name is required')

    # Normalize park_code to lowercase
    flds[PARK_CODE] = flds[PARK_CODE].strip().lower()

    # TODO: validate that each state exists

    if reload:
        park_cache.clear()

    dbc.create(PARK_COLLECTION, flds)
    return flds[PARK_CODE]


def get(park_code: str) -> dict:
    """Get a park record by its park code."""
    dbc.connect_db()
    # validate park_code
    if not park_code:
        raise ValueError('Park code is required')
    if not isinstance(park_code, str):
        raise ValueError(
            f'Park code must be a string, got {type(park_code).__name__}'
        )
    return dbc.read_one(PARK_COLLECTION, {PARK_CODE: park_code})


def get_by_state(state_code: str) -> list:
    """ Get all park records in a state"""
    dbc.connect_db()
    # validate state code
    if not state_code:
        raise ValueError('state code is required')
    if not isinstance(state_code, str):
        raise ValueError(
            f'state code must be a string, got {type(state_code).__name__}'
        )
    return dbc.read_many(PARK_COLLECTION, {STATE_CODE: state_code.upper()})


def get_by_name(park_name: str) -> dict:
    """ Get park record by name"""
    dbc.connect_db()
    # validate park_name
    if not park_name:
        raise ValueError('Park name is required')
    if not isinstance(park_name, str):
        raise ValueError(
            f'Park code must be a string, got {type(park_name).__name__}'
        )
    return dbc.read_one(PARK_COLLECTION, {NAME: park_name})


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
