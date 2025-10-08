import pytest

from cities import queries as qry


@pytest.fixture(autouse=True)
def reset_cache():
    """Reset city cache before each test to ensure test isolation."""
    qry.city_cache.clear()
    yield


def test_valid_id_min_length():
    short_id = "."*(qry.MIN_ID_LEN - 1)
    result = qry.is_valid_id(short_id)
    assert not result
    

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
        

def test_create_bad_keys():
    with pytest.raises(ValueError):
        invalid_key = qry.NAME + "2"
        qry.create({ invalid_key: "CA" })


def test_update():
    city_id = qry.create({qry.NAME: "Boston", qry.STATE_CODE: "MA"})
    update_data = {qry.NAME: "Boston City", qry.STATE_CODE: "MA"}
    result_id = qry.update(city_id, update_data)
    
    # Verify update worked
    assert result_id == city_id
    assert qry.city_cache[city_id][qry.NAME] == "Boston City"
    
    
def test_update_bad_id():
    with pytest.raises(ValueError):
        qry.update(123, {qry.NAME: "New York"})


def test_update_missing_id():
    with pytest.raises(KeyError):
        qry.update("NYC", {qry.NAME: "New York"})


def test_update_bad_fields_param_type():
    with pytest.raises(ValueError):
        city_id = qry.create({qry.NAME: "New York", qry.STATE_CODE: "NY"})
        qry.update(city_id, 123)
        
        
def test_delete():
    city_id = qry.create({qry.NAME: "New York", qry.STATE_CODE: "NY"})
    qry.delete(city_id)
    
    assert city_id not in qry.city_cache
    

def test_delete_bad_id():
    with pytest.raises(ValueError):
        qry.delete(123)


def test_delete_missing_id():
    with pytest.raises(KeyError):
        qry.create({qry.NAME: "New York", qry.STATE_CODE: "NY"})
        qry.delete("NYC")