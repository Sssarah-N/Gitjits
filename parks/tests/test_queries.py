from copy import deepcopy

import pytest
import uuid
# from unittest.mock import patch
# from bson import ObjectId

from parks import queries as qry


def get_temp_rec():
    rec = deepcopy(qry.SAMPLE_PARK)
    # make unique park code for test to avoid duplicates
    rec["park_code"] = str(uuid.uuid4())[:6]
    return rec


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


def test_delete(temp_park):
    """Test deleting a park."""
    qry.delete(temp_park)
    # Verify park is deleted by trying to get it
    result = qry.get(temp_park)
    assert result is None


def test_delete_bad_park_code():
    """Test deleting with invalid park code raises ValueError."""
    with pytest.raises(ValueError):
        qry.delete('invalid park code!')  # Contains invalid characters


def test_delete_empty_park_code():
    """Test deleting with empty park code raises ValueError."""
    with pytest.raises(ValueError):
        qry.delete("")


def test_delete_wrong_type():
    """Test deleting with wrong type raises ValueError."""
    with pytest.raises(ValueError):
        qry.delete(123)  # Integer instead of string


def test_delete_missing_park():
    """Test deleting non-existent park raises KeyError."""
    # Valid format but doesn't exist
    fake_code = "fake"
    with pytest.raises(KeyError):
        qry.delete(fake_code)


def test_delete_removes_from_list(temp_park):
    """Test that delete actually removes park from the collection."""
    # Get initial count
    initial_count = len(qry.read())
    qry.delete(temp_park)
    # After delete, count should be one less
    assert len(qry.read()) == initial_count - 1


def test_delete_clears_cache(temp_park):
    """Test that delete clears the cache."""
    # Populate cache by getting the park
    qry.park_cache['test_key'] = 'test_value'
    qry.delete(temp_park)
    # Cache should be cleared after delete
    assert len(qry.park_cache) == 0


def test_get_missing_code():
    """Test get() raises ValueError if code is empty."""
    with pytest.raises(ValueError):
        qry.get("")


def test_get_wrong_type():
    """Test get() raises ValueError if code is not a string."""
    with pytest.raises(ValueError):
        qry.get(123)


def test_get_by_state_valid():
    """Test get_by_state returns parks in that state."""
    park = get_temp_rec()
    qry.create(park)

    results = qry.get_by_state("ky")

    assert isinstance(results, list)
    assert len(results) > 0
    assert "KY" in results[0][qry.STATE_CODE]


def test_get_by_state_missing():
    """Test get_by_state raises ValueError if missing."""
    with pytest.raises(ValueError):
        qry.get_by_state("")


def test_get_by_state_wrong_type():
    """Test get_by_state raises ValueError if wrong type."""
    with pytest.raises(ValueError):
        qry.get_by_state(999)


def test_get_by_name_valid():
    """Test get_by_name finds park by name."""
    park = get_temp_rec()
    park[qry.NAME] = "Acadia"
    qry.create(park)

    result = qry.get_by_name("Acadia")

    assert result[qry.NAME] == "Acadia"


def test_get_by_name_missing():
    """Test get_by_name raises ValueError if missing."""
    with pytest.raises(ValueError):
        qry.get_by_name("")


def test_get_by_name_wrong_type():
    """Test get_by_name raises ValueError if wrong type."""
    with pytest.raises(ValueError):
        qry.get_by_name(["Acadia"])

# TODO: add tests for update, get_by_state, and other park queries
