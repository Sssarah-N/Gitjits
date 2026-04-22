"""
Tests for users.queries module.
"""
import uuid

import pytest

from users import queries as qry


def generate_unique_username():
    """Generate a unique username for testing."""
    return f'testuser_{uuid.uuid4().hex[:8]}'


def generate_unique_email():
    """Generate a unique email for testing."""
    return f'test_{uuid.uuid4().hex[:8]}@example.com'


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def test_hash_password_returns_string(self):
        """hash_password should return a string."""
        result = qry.hash_password('mypassword')
        assert isinstance(result, str)

    def test_hash_password_not_same_as_input(self):
        """Hash should not be the same as the original password."""
        password = 'mypassword123'
        result = qry.hash_password(password)
        assert result != password

    def test_hash_password_different_each_time(self):
        """Same password should produce different hashes (due to salt)."""
        password = 'mypassword123'
        hash1 = qry.hash_password(password)
        hash2 = qry.hash_password(password)
        assert hash1 != hash2

    def test_hash_password_empty_raises_error(self):
        """Empty password should raise ValueError."""
        with pytest.raises(ValueError):
            qry.hash_password('')

    def test_hash_password_none_raises_error(self):
        """None password should raise ValueError."""
        with pytest.raises(ValueError):
            qry.hash_password(None)

    def test_hash_password_non_string_raises_error(self):
        """Non-string password should raise ValueError."""
        with pytest.raises(ValueError):
            qry.hash_password(12345)


class TestPasswordVerification:
    """Tests for password verification."""

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = 'mypassword123'
        hashed = qry.hash_password(password)
        assert qry.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Wrong password should not verify."""
        password = 'mypassword123'
        hashed = qry.hash_password(password)
        assert qry.verify_password('wrongpassword', hashed) is False

    def test_verify_password_invalid_hash(self):
        """Invalid hash should return False, not raise."""
        result = qry.verify_password('password', 'not-a-valid-hash')
        assert result is False

    def test_verify_password_empty_hash(self):
        """Empty hash should return False."""
        result = qry.verify_password('password', '')
        assert result is False


class TestCreateUser:
    """Tests for user creation."""

    def test_create_user_success(self):
        """Should create user and return username."""
        username = generate_unique_username()
        email = generate_unique_email()

        result = qry.create_user(username, email, 'password123')
        assert result == username.lower()

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass

    def test_create_user_empty_username_raises(self):
        """Empty username should raise ValueError."""
        with pytest.raises(ValueError, match='Username is required'):
            qry.create_user('', 'test@example.com', 'password123')

    def test_create_user_empty_email_raises(self):
        """Empty email should raise ValueError."""
        with pytest.raises(ValueError, match='Email is required'):
            qry.create_user('testuser', '', 'password123')

    def test_create_user_empty_password_raises(self):
        """Empty password should raise ValueError."""
        with pytest.raises(ValueError, match='Password is required'):
            qry.create_user('testuser', 'test@example.com', '')

    def test_create_user_none_values_raise(self):
        """None values should raise ValueError."""
        with pytest.raises(ValueError):
            qry.create_user(None, 'test@example.com', 'password')
        with pytest.raises(ValueError):
            qry.create_user('testuser', None, 'password')
        with pytest.raises(ValueError):
            qry.create_user('testuser', 'test@example.com', None)

    def test_create_user_normalizes_username(self):
        """Username should be normalized to lowercase."""
        username = f'TESTUSER_{uuid.uuid4().hex[:6]}'
        email = generate_unique_email()

        result = qry.create_user(username, email, 'password123')
        assert result == username.lower()

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass

    def test_create_user_default_role(self):
        """Default role should be 'user'."""
        username = generate_unique_username()
        email = generate_unique_email()

        qry.create_user(username, email, 'password123')
        user = qry.get_user(username)
        assert user[qry.ROLE] == qry.ROLE_USER

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass


class TestGetUser:
    """Tests for getting users."""

    def test_get_user_exists(self):
        """Should return user dict when found."""
        username = generate_unique_username()
        email = generate_unique_email()
        qry.create_user(username, email, 'password123')

        user = qry.get_user(username)
        assert user is not None
        assert user[qry.USERNAME] == username.lower()
        assert user[qry.EMAIL] == email.lower()

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass

    def test_get_user_not_found(self):
        """Should return None when user not found."""
        result = qry.get_user('nonexistent_user_12345')
        assert result is None

    def test_get_user_empty_raises(self):
        """Empty username should raise ValueError."""
        with pytest.raises(ValueError, match='Username is required'):
            qry.get_user('')


class TestAuthenticate:
    """Tests for user authentication."""

    def test_authenticate_success(self):
        """Valid credentials should return user info."""
        username = generate_unique_username()
        email = generate_unique_email()
        password = 'testpassword123'

        qry.create_user(username, email, password)
        result = qry.authenticate(username, password)

        assert result[qry.USERNAME] == username.lower()
        assert qry.PASSWORD_HASH not in result  # Should not include hash
        assert '_id' not in result  # Should not include MongoDB _id

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass

    def test_authenticate_wrong_password(self):
        """Wrong password should raise ValueError."""
        username = generate_unique_username()
        email = generate_unique_email()

        qry.create_user(username, email, 'correctpassword')

        with pytest.raises(ValueError, match='Invalid username or password'):
            qry.authenticate(username, 'wrongpassword')

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass

    def test_authenticate_nonexistent_user(self):
        """Nonexistent user should raise ValueError."""
        with pytest.raises(ValueError, match='Invalid username or password'):
            qry.authenticate('nonexistent_user_xyz', 'password')

    def test_authenticate_empty_values(self):
        """Empty username/password should raise ValueError."""
        with pytest.raises(ValueError):
            qry.authenticate('', 'password')
        with pytest.raises(ValueError):
            qry.authenticate('username', '')


class TestSavedParks:
    """Tests for saved parks functionality."""

    @pytest.fixture
    def test_user(self):
        """Create a test user for saved parks tests."""
        username = generate_unique_username()
        email = generate_unique_email()
        qry.create_user(username, email, 'password123')
        yield username

        # Cleanup
        try:
            from data.db_connect import client, GEO_DB
            client[GEO_DB][qry.USER_COLLECTION].delete_one(
                {qry.USERNAME: username.lower()}
            )
        except Exception:
            pass

    def test_get_saved_parks_empty(self, test_user):
        """New user should have empty saved parks."""
        parks = qry.get_saved_parks(test_user)
        assert parks == []

    def test_add_saved_park(self, test_user):
        """Should add park to saved list."""
        result = qry.add_saved_park(test_user, 'yell')
        assert result is True

        parks = qry.get_saved_parks(test_user)
        assert 'yell' in parks

    def test_add_saved_park_duplicate(self, test_user):
        """Adding same park twice should return False."""
        qry.add_saved_park(test_user, 'grca')
        result = qry.add_saved_park(test_user, 'grca')
        assert result is False

    def test_remove_saved_park(self, test_user):
        """Should remove park from saved list."""
        qry.add_saved_park(test_user, 'yose')

        result = qry.remove_saved_park(test_user, 'yose')
        assert result is True

        parks = qry.get_saved_parks(test_user)
        assert 'yose' not in parks

    def test_remove_saved_park_not_in_list(self, test_user):
        """Removing non-saved park should return False."""
        result = qry.remove_saved_park(test_user, 'notinlist')
        assert result is False

    def test_saved_parks_nonexistent_user(self):
        """Operations on nonexistent user should raise."""
        with pytest.raises(ValueError, match='User not found'):
            qry.get_saved_parks('nonexistent_user_xyz')

    def test_add_park_empty_code(self, test_user):
        """Empty park code should raise ValueError."""
        with pytest.raises(ValueError, match='Park code is required'):
            qry.add_saved_park(test_user, '')

    def test_remove_park_empty_code(self, test_user):
        """Empty park code should raise ValueError."""
        with pytest.raises(ValueError, match='Park code is required'):
            qry.remove_saved_park(test_user, '')
