from abc import ABC, abstractmethod
import re

VALID_EMAIL_RE = re.compile(
    r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-zA-Z]{2,}$'
)

MIN_EMAIL_LEN = 6   # shortest possible: a@b.co
MAX_EMAIL_LEN = 254


class Email(ABC):
    @abstractmethod
    def __init__(self, address: str):
        print("Can't init this class!")

    def __str__(self):
        return self.address


class StandardEmail(Email):
    """
    Validates a standard internet email address
    - Must be a string
    - Length between MIN_EMAIL_LEN and MAX_EMAIL_LEN
    - Exactly one '@' symbol
    - Local part (before '@'): letters, digits, and . _ % + -
    - Domain part (after '@'): letters, digits, hyphens, dots
    - TLD must be at least 2 characters
    Stores the address lowercased for normalisation.
    """

    def __init__(self, address: str):
        if not isinstance(address, str):
            raise TypeError(f'Bad type for address: {type(address)}')
        if len(address) < MIN_EMAIL_LEN or len(address) > MAX_EMAIL_LEN:
            raise ValueError(f'Bad length for {address=}')
        if address.count('@') != 1:
            raise ValueError(f'Must contain exactly one "@" in {address=}')
        if not VALID_EMAIL_RE.match(address):
            raise ValueError(f'{address=} is not a valid email format')
        self.address = address.lower()


TEST_GOOD_EMAIL = 'User.Name+tag@Example.COM'
TEST_GOOD_EMAIL_SIMPLE = 'hello@world.io'
TEST_GOOD_EMAIL_SUBDOMAIN = 'user@mail.example.co.uk'


def main():
    email = StandardEmail(TEST_GOOD_EMAIL)
    print(email)


if __name__ == '__main__':
    main()
