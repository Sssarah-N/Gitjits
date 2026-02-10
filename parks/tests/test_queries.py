from copy import deepcopy

import pytest
# from unittest.mock import patch
# from bson import ObjectId

from parks import queries as qry


def get_temp_rec():
    return deepcopy(qry.SAMPLE_PARK)


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset parks cache before each test to ensure test isolation."""
    qry.park_cache.clear()
    yield


@pytest.fixture(scope='function')
def temp_park():
    """Create a temp park and return its MongoDB ObjectId."""
    temp_rec = get_temp_rec()
    new_rec_id = qry.create(temp_rec)
    yield new_rec_id
    try:
        qry.delete(new_rec_id)
    except (ValueError, KeyError):
        print('The record was already deleted.')


def test_create():
    """Test creating a park."""
    park = get_temp_rec()
    park_code = qry.create(park)
    retrieved = qry.get(park_code)
    # Compare fields (ignore mongo's internal _id)
    assert retrieved[qry.NAME] == park[qry.NAME]
    assert retrieved[qry.PARK_CODE] == park[qry.PARK_CODE]
    assert retrieved[qry.STATE_CODE] == park[qry.STATE_CODE]
    assert qry.MONGO_ID in retrieved  # Verify _id was added
    qry.delete(park_code)

# TODO: add tests for all parks queries
