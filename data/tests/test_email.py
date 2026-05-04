import pytest

import data.email as em

# ---------------------------------------------------------------------------
# Abstract base class
# ---------------------------------------------------------------------------


def test_abc_base():
    with pytest.raises(TypeError):
        em.Email('user@example.com')


# ---------------------------------------------------------------------------
# Successful construction
# ---------------------------------------------------------------------------

def test_construct_standard_email():
    email = em.StandardEmail(em.TEST_GOOD_EMAIL)
    assert isinstance(email, em.StandardEmail)


def test_construct_simple_email():
    email = em.StandardEmail(em.TEST_GOOD_EMAIL_SIMPLE)
    assert isinstance(email, em.StandardEmail)


def test_construct_subdomain_email():
    email = em.StandardEmail(em.TEST_GOOD_EMAIL_SUBDOMAIN)
    assert isinstance(email, em.StandardEmail)


# ---------------------------------------------------------------------------
# Normalisation: stored address must be lowercased
# ---------------------------------------------------------------------------

def test_email_stored_as_lowercase():
    email = em.StandardEmail('User@Example.COM')
    assert str(email) == 'user@example.com'


def test_str():
    email = em.StandardEmail(em.TEST_GOOD_EMAIL_SIMPLE)
    assert str(email) == em.TEST_GOOD_EMAIL_SIMPLE


# ---------------------------------------------------------------------------
# Type errors
# ---------------------------------------------------------------------------

def test_construct_bad_type_int():
    with pytest.raises(TypeError):
        em.StandardEmail(42)


def test_construct_bad_type_none():
    with pytest.raises(TypeError):
        em.StandardEmail(None)


def test_construct_bad_type_list():
    with pytest.raises(TypeError):
        em.StandardEmail(['user@example.com'])


# ---------------------------------------------------------------------------
# Length errors
# ---------------------------------------------------------------------------

def test_construct_too_short():
    with pytest.raises(ValueError):
        em.StandardEmail('a@b.')


def test_construct_empty_string():
    with pytest.raises(ValueError):
        em.StandardEmail('')


def test_construct_too_long():
    local = 'a' * 200
    domain = 'b' * 50 + '.com'
    with pytest.raises(ValueError):
        em.StandardEmail(f'{local}@{domain}')


# ---------------------------------------------------------------------------
# Missing or malformed '@'
# ---------------------------------------------------------------------------

def test_construct_no_at_sign():
    with pytest.raises(ValueError):
        em.StandardEmail('userexample.com')


def test_construct_multiple_at_signs():
    with pytest.raises(ValueError):
        em.StandardEmail('user@@example.com')


def test_construct_only_at_sign():
    with pytest.raises(ValueError):
        em.StandardEmail('@')


# ---------------------------------------------------------------------------
# Bad local part (before '@')
# ---------------------------------------------------------------------------

def test_construct_empty_local_part():
    with pytest.raises(ValueError):
        em.StandardEmail('@example.com')


def test_construct_local_part_with_spaces():
    with pytest.raises(ValueError):
        em.StandardEmail('user name@example.com')


# ---------------------------------------------------------------------------
# Bad domain part (after '@')
# ---------------------------------------------------------------------------

def test_construct_missing_domain():
    with pytest.raises(ValueError):
        em.StandardEmail('user@')


def test_construct_missing_tld():
    with pytest.raises(ValueError):
        em.StandardEmail('user@example')


def test_construct_tld_too_short():
    with pytest.raises(ValueError):
        em.StandardEmail('user@example.c')


def test_construct_domain_with_spaces():
    with pytest.raises(ValueError):
        em.StandardEmail('user@exam ple.com')


def test_construct_domain_starts_with_dot():
    with pytest.raises(ValueError):
        em.StandardEmail('user@.example.com')
