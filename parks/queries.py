"""
This file deals with our national parks data.
Uses park_code as the primary key (from NPS dataset).
"""
import math
from bson import ObjectId
import data.db_connect as dbc
from data.db_connect import update as db_update


def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Calculate distance in miles between two coordinates."""
    R = 3959  # Earth radius in miles
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = (math.sin(dlat/2)**2
         + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
    return 2 * R * math.asin(math.sqrt(a))


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
    STATE_CODE: ['KY', 'IN'],
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


def update(park_id: str, data: dict) -> dict:
    """Update park field"""

    dbc.connect_db()

    if not park_id:
        raise ValueError("Park ID is required")
    if not isinstance(park_id, str):
        raise ValueError(
            f"Park ID must be a string, got {type(park_id).__name__}")
    if not ObjectId.is_valid(park_id):
        raise ValueError(f"Invalid ObjectId format: {park_id}")

    obj_id = ObjectId(park_id)

    if not data or not isinstance(data, dict):
        raise ValueError("Update data must be a non-empty dictionary")

    ret = db_update(PARK_COLLECTION, {"_id": obj_id}, data)
    if ret.matched_count == 0:
        raise KeyError(f"Park not found: {park_id}")

    park_cache.clear()
    updated_park = dbc.read_one(PARK_COLLECTION, {"_id": obj_id})
    return updated_park


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


def search(filters: dict) -> list:
    """
    Search parks with multiple filter criteria.

    Args:
        filters: dict with optional keys:
            - name: str (partial match, case-insensitive)
            - state: str (state code, e.g., 'CA')
            - designation: str (exact match)
            - activity: str (parks containing this activity)

    Returns:
        List of matching parks
    """
    dbc.connect_db()

    query = {}

    # State filter
    if filters.get('state'):
        query[STATE_CODE] = filters['state'].upper()

    # Designation filter (exact match)
    if filters.get('designation'):
        query[DESIGNATION] = filters['designation']

    # Activity filter (parks containing this activity)
    if filters.get('activity'):
        query[ACTIVITIES] = filters['activity']

    # Execute query
    if query:
        parks = dbc.read_many(PARK_COLLECTION, query)
    else:
        parks = dbc.read(PARK_COLLECTION)

    # Name filter (applied in Python for partial matching)
    if filters.get('name'):
        name_query = filters['name'].lower()
        parks = [
            p for p in parks
            if name_query in p.get('name', '').lower()
            or name_query in p.get('full_name', '').lower()
        ]

    return parks


def get_all_activities() -> list:
    """Get all unique activities across all parks."""
    dbc.connect_db()
    return sorted(dbc.distinct(PARK_COLLECTION, ACTIVITIES))


def get_all_designations() -> list:
    """Get all unique park designations."""
    dbc.connect_db()
    designations = dbc.distinct(PARK_COLLECTION, DESIGNATION)
    return sorted([d for d in designations if d])


def get_random() -> dict:
    """Get a random park."""
    import random
    parks = read()
    if not parks:
        return None
    return random.choice(parks)


def get_nearby(lat: float, lon: float, radius: float = 100) -> list:
    """
    Get parks within radius miles of coordinates.

    Args:
        lat: Latitude of search center
        lon: Longitude of search center
        radius: Search radius in miles (default: 100)

    Returns:
        List of parks sorted by distance, each with distance_miles field
    """
    parks = read()
    nearby = []
    for p in parks:
        p_lat, p_lon = p.get(LATITUDE), p.get(LONGITUDE)
        if p_lat is not None and p_lon is not None:
            dist = haversine_distance(lat, lon, p_lat, p_lon)
            if dist <= radius:
                p['distance_miles'] = round(dist, 1)
                nearby.append(p)
    return sorted(nearby, key=lambda x: x['distance_miles'])
