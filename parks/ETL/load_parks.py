#!/usr/bin/env python3
"""
ETL script to load national parks data from JSON into MongoDB.

Usage:
    python load_parks.py [json_file]
    python load_parks.py  # defaults to natl_parks.json in project root

Data source: National Park Service API
https://www.nps.gov/subjects/developer/api-documentation.htm
"""
import sys
import json
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from parks.queries import (
    NAME,
    PARK_CODE,
    STATE_CODE,
    create,
    get,
    update
)

# Additional fields we want to store
FULL_NAME = 'full_name'
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
CITY = 'city'
IMAGES = 'images'
WEATHER_INFO = 'weather_info'
DESIGNATION = 'designation'

# JSON field mapping (source -> our schema)
FIELD_MAP = {
    'name': NAME,
    'parkCode': PARK_CODE,
    'states': STATE_CODE,
    'fullName': FULL_NAME,
    'description': DESCRIPTION,
    'latitude': LATITUDE,
    'longitude': LONGITUDE,
    'url': URL,
    'activities': ACTIVITIES,
    'contacts': CONTACTS,
    'directionsInfo': DIRECTIONS_INFO,
    'directionsUrl': DIRECTIONS_URL,
    'operatingHours': OPERATING_HOURS,
    'addresses': ADDRESSES,
    'images': IMAGES,
    'weatherInfo': WEATHER_INFO,
    'designation': DESIGNATION,
}


def extract(filename: str) -> list:
    """Extract park data from JSON file."""
    try:
        with open(filename, 'r') as f:
            data = json.load(f)

        # Handle NPS API format: {"total": N, "data": [...]}
        if isinstance(data, dict) and 'data' in data:
            parks = data['data']
        elif isinstance(data, list):
            parks = data
        else:
            raise ValueError(f'Unexpected JSON format: {type(data)}')

        print(f'Extracted {len(parks)} parks from {filename}')
        return parks

    except FileNotFoundError:
        print(f'Error: File not found: {filename}')
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f'Error: Invalid JSON in {filename}: {e}')
        sys.exit(1)


def transform(parks: list) -> list:
    """Transform raw park data to our schema."""
    transformed = []

    for park in parks:
        try:
            park_dict = {}

            # Map fields from source to our schema
            for src_field, dest_field in FIELD_MAP.items():
                if src_field in park:
                    value = park[src_field]

                    # Convert lat/long to float
                    if dest_field in (LATITUDE, LONGITUDE):
                        try:
                            value = float(value) if value else None
                        except (ValueError, TypeError):
                            value = None

                    # Extract activity names from activity objects
                    if dest_field == ACTIVITIES and isinstance(value, list):
                        value = [a.get('name') for a in value if 'name' in a]

                    # Normalize state codes to uppercase
                    if dest_field == STATE_CODE and value:
                        value = [state.strip().upper() for state in value.split(',') if state.strip()]

                    park_dict[dest_field] = value

            # Extract primary city from addresses (outside field mapping loop)
            addresses = park.get("addresses", [])
            city = None
            if isinstance(addresses, list):
                for addr in addresses:
                    if addr.get("type") == "Physical" and addr.get("city"):
                        city = addr["city"]
                        break
                if not city and addresses:
                    city = addresses[0].get("city")
            if city:
                park_dict[CITY] = city

            # Normalize operating hours (outside field mapping loop)
            if 'operatingHours' in park:
                operating_hours = park['operatingHours']
                cleaned_hours = {}
                for unit in operating_hours:
                    unit_name = unit.get('name', 'Unknown Unit')
                    cleaned_hours[unit_name] = {
                        'description': unit.get('description', ''),
                        'standardHours': unit.get('standardHours', {}),
                        'exceptions': unit.get('exceptions', [])
                    }
                park_dict[OPERATING_HOURS] = cleaned_hours

            # Validate required fields
            if not park_dict.get(PARK_CODE):
                print(f'  Skipping park without code: {park.get("name", "?")}')
                continue
            if not park_dict.get(NAME):
                park_dict[NAME] = park_dict.get(FULL_NAME, 'Unknown')

            transformed.append(park_dict)

        except Exception as e:
            print(f'  Error transforming park {park.get("name", "?")}: {e}')
            continue

    print(f'Transformed {len(transformed)} parks')
    return transformed


def load(parks: list, skip_existing: bool = True) -> dict:
    """Load parks into MongoDB."""
    stats = {'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0}

    for park in parks:
        try:
            park_code = park[PARK_CODE]
            # Check if park already exists
            existing = get(park_code)
            if existing:
                # Always update with new data
                update_fields = {k: v for k, v in park.items() if k != PARK_CODE}
                if update_fields:
                    update(existing['_id'], update_fields)
                    stats['updated'] += 1
                continue

            # If park doesn't exist, create it
            create(park)
            stats['created'] += 1
            print(f'  + {park_code}: {park[NAME]}')

        except Exception as e:
            stats['errors'] += 1
            print(f'  ! Error loading {park.get(PARK_CODE, "?")}: {e}')

    return stats


def main():
    # Default to natl_parks.json in project root
    if len(sys.argv) > 1:
        filename = sys.argv[1]
    else:
        # Find project root (where natl_parks.json is)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.join(script_dir, '../..')
        filename = os.path.join(project_root, 'natl_parks.json')

    print(f'=== Loading Parks from {filename} ===\n')

    # ETL Pipeline
    print('Step 1: Extract')
    raw_parks = extract(filename)

    print('\nStep 2: Transform')
    parks = transform(raw_parks)

    print('\nStep 3: Load')
    stats = load(parks)

    print(f'\n=== Complete ===')
    print(f'Created: {stats["created"]}')
    print(f'Skipped (existing): {stats["skipped"]}')
    print(f"Updated: {stats['updated']}")
    print(f'Errors: {stats["errors"]}')


if __name__ == '__main__':
    main()
