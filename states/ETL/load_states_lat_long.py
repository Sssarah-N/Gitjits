import sys
import csv


def extract(flnm: str) -> list:
    state_list = []
    try:
        with open(flnm) as f:
            reader = csv.reader(f, delimiter='\t')
            for row in reader:
                state_list.append(row)
    except Exception as e:
        print(f'Problem reading csv file: {str(e)}')
        exit(1)
    return state_list


def transform(state_list: list) -> list:
    rev_list = []
    col_names = state_list.pop(0)
    print(f'{col_names=}')
    for state in state_list:
        state_dict = {}
        for i, fld in enumerate(col_names):
            state_dict[fld] = state[i]
        print(f'{state_dict=}')
        rev_list.append(state_dict)
    return rev_list


def load(rev_list: list):
    pass


def main():
    if len(sys.argv) < 2:
        print('USAGE: load_states_lat_long.py [csvfile]')
        exit(1)
    state_list = extract(sys.argv[1])
    rev_list = transform(state_list)
    print(f'{rev_list=}')
    load(rev_list)


if __name__ == '__main__':
    main()