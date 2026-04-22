"""
Tests for auth.jwt_utils module.
"""
from datetime import datetime, timedelta, timezone

import pytest
import jwt

from auth import jwt_utils


class TestGenerateToken:
    """Tests for JWT token generation."""

    def test_generate_token_returns_string(self):
        """generate_token should return a string."""
        token = jwt_utils.generate_token('testuser', 'user')
        assert isinstance(token, str)

    def test_generate_token_decodable(self):
        """Generated token should be decodable."""
        token = jwt_utils.generate_token('testuser', 'user')
        payload = jwt_utils.decode_token(token)
        assert payload['username'] == 'testuser'
        assert payload['role'] == 'user'

    def test_generate_token_contains_expiry(self):
        """Token should contain expiry time."""
        token = jwt_utils.generate_token('testuser', 'user')
        payload = jwt_utils.decode_token(token)
        assert 'exp' in payload

    def test_generate_token_contains_issued_at(self):
        """Token should contain issued at time."""
        token = jwt_utils.generate_token('testuser', 'user')
        payload = jwt_utils.decode_token(token)
        assert 'iat' in payload

    def test_generate_token_different_users(self):
        """Different users should get different tokens."""
        token1 = jwt_utils.generate_token('user1', 'user')
        token2 = jwt_utils.generate_token('user2', 'user')
        assert token1 != token2

    def test_generate_token_different_roles(self):
        """Different roles should get different tokens."""
        token1 = jwt_utils.generate_token('testuser', 'user')
        token2 = jwt_utils.generate_token('testuser', 'admin')
        assert token1 != token2


class TestDecodeToken:
    """Tests for JWT token decoding."""

    def test_decode_valid_token(self):
        """Should decode valid token successfully."""
        token = jwt_utils.generate_token('admin', 'admin')
        payload = jwt_utils.decode_token(token)

        assert payload['username'] == 'admin'
        assert payload['role'] == 'admin'

    def test_decode_invalid_token(self):
        """Should raise ValueError for invalid token."""
        with pytest.raises(ValueError, match='Invalid token'):
            jwt_utils.decode_token('not.a.valid.token')

    def test_decode_tampered_token(self):
        """Should raise ValueError for tampered token."""
        token = jwt_utils.generate_token('user', 'user')
        tampered = token[:-5] + 'xxxxx'

        with pytest.raises(ValueError, match='Invalid token'):
            jwt_utils.decode_token(tampered)

    def test_decode_expired_token(self):
        """Should raise ValueError for expired token."""
        payload = {
            'username': 'testuser',
            'role': 'user',
            'exp': datetime.now(timezone.utc) - timedelta(hours=1),
            'iat': datetime.now(timezone.utc) - timedelta(hours=2)
        }
        expired_token = jwt.encode(
            payload,
            jwt_utils.SECRET_KEY,
            algorithm=jwt_utils.ALGORITHM
        )

        with pytest.raises(ValueError, match='Token has expired'):
            jwt_utils.decode_token(expired_token)

    def test_decode_token_wrong_secret(self):
        """Token signed with wrong secret should fail."""
        payload = {
            'username': 'testuser',
            'role': 'user',
            'exp': datetime.now(timezone.utc) + timedelta(hours=1),
            'iat': datetime.now(timezone.utc)
        }
        wrong_secret_token = jwt.encode(
            payload,
            'wrong-secret-key',
            algorithm=jwt_utils.ALGORITHM
        )

        with pytest.raises(ValueError, match='Invalid token'):
            jwt_utils.decode_token(wrong_secret_token)


class TestTokenPayloadContent:
    """Tests for token payload content."""

    def test_username_in_payload(self):
        """Username should be in token payload."""
        token = jwt_utils.generate_token('myusername', 'user')
        payload = jwt_utils.decode_token(token)
        assert payload['username'] == 'myusername'

    def test_role_in_payload(self):
        """Role should be in token payload."""
        token = jwt_utils.generate_token('testuser', 'admin')
        payload = jwt_utils.decode_token(token)
        assert payload['role'] == 'admin'

    def test_expiry_is_future(self):
        """Token expiry should be in the future."""
        token = jwt_utils.generate_token('testuser', 'user')
        payload = jwt_utils.decode_token(token)
        exp_timestamp = payload['exp']
        now_timestamp = datetime.now(timezone.utc).timestamp()
        assert exp_timestamp > now_timestamp

    def test_issued_at_is_recent(self):
        """Token issued_at should be recent."""
        token = jwt_utils.generate_token('testuser', 'user')
        payload = jwt_utils.decode_token(token)
        iat_timestamp = payload['iat']
        now_timestamp = datetime.now(timezone.utc).timestamp()
        # Should be within 5 seconds
        assert abs(now_timestamp - iat_timestamp) < 5
