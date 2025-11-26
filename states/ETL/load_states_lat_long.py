import sys
import csv

from states.queries import (
    NAME,
    ABBREVIATION,
    LATITUDE,
    LONGITUDE,
    COUNTRY_CODE,
    create,
)

CURR_COUNTRY = 'USA'

# CSV field mapping
CSV_CODE = 'code'
CSV_NAME = 'name'
CSV_LATITUDE = 'latitude'
CSV_LONGITUDE = 'longitude'

def extract(flnm: str) -> list:
    state_list = []
    try:
        with open(flnm) as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                state_list.append(row)
    except Exception as e:
        print(f'Problem reading csv file: {str(e)}')
        exit(1)
    return state_list


def transform(state_list: list) -> list:
    rev_list = []
    for state in state_list:
        try:
            # Map CSV fields to database fields
            state_dict = {
                NAME: state[CSV_NAME],
                ABBREVIATION: state[CSV_CODE],  # Map 'code' to 'abbreviation'
                LATITUDE: float(state[CSV_LATITUDE]),
                LONGITUDE: float(state[CSV_LONGITUDE]),
                COUNTRY_CODE: CURR_COUNTRY
            }
            rev_list.append(state_dict)
        except Exception as e:
            print(f'Problem transforming state {state[CSV_NAME]}: {str(e)}')
            continue
    return rev_list


def load(rev_list: list):
    for state in rev_list:
        try:
            create(state, reload=False)
        except Exception as e:
            print(f'Problem loading state {state[NAME]}: {str(e)}')
            continue


def main():
    if len(sys.argv) < 2:
        print('USAGE: load_states_lat_long.py [csvfile]')
        exit(1)
    state_list = extract(sys.argv[1])
    rev_list = transform(state_list)
    load(rev_list)


if __name__ == '__main__':
    main()