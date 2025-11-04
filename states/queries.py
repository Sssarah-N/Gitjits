"""
This file deals with our state-level data.
"""
from bson import ObjectId
import data.db_connect as dbc

MIN_ID_LEN = 1

STATE_COLLECTION = 'states'

ID = 'id'
NAME = 'name'
ABBREVIATION = 'abbreviation'
CAPITAL = 'capital'
POPULATION = 'population'

SAMPLE_STATE = {
    NAME: 'New York',
    ABBREVIATION: 'NY',
    CAPITAL: 'Albany',
    POPULATION: 19450000
}

state_cache = {
    '1': SAMPLE_STATE,
}

def is_valid_id(_id: str) -> bool:
    """
    Validate ID format.
    """
    if not isinstance(_id, str):
        return False
    if len(_id) < MIN_ID_LEN:
        return False
    return True


def num_states() -> int:
    return len(read())


def read() -> list:
    return dbc.read(STATE_COLLECTION)


def main():
    print(read())

