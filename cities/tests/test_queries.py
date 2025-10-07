import pytest

from cities import queries as qry


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset city cache before each test to ensure test isolation."""
    qry.city_cache.clear()
    yield


def test_good_create():
    old_count = qry.num_cities()
    new_rec_id = qry.create(qry.SAMPLE_CITY)
    assert qry.is_valid_id(new_rec_id)
    assert qry.num_cities() > old_count


def test_create_bad_name():
    with pytest.raises(ValueError):
        qry.create({})


def test_create_bad_param_type():
    with pytest.raises(ValueError):
        qry.create(17)


def test_update():
    city_id = qry.create({qry.NAME: "Boston", qry.STATE_CODE: "MA"})
    update_data = {qry.NAME: "Boston City", qry.STATE_CODE: "MA"}
    result_id = qry.update(city_id, update_data)
    
    # Verify update worked
    assert result_id == city_id
    assert qry.city_cache[city_id][qry.NAME] == "Boston City"