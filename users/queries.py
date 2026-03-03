"""
User management queries - STEP BY STEP VERSION.
Starting with just password hashing.
"""
import bcrypt
from datetime import datetime
import data.db_connect as dbc

USER_COLLECTION = 'users'

# Field names
USERNAME = 'username'
EMAIL = 'email'
PASSWORD_HASH = 'password_hash'
ROLE = 'role'

# Roles
ROLE_USER = 'user'
ROLE_ADMIN = 'admin'


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """
    if not password or not isinstance(password, str):
        raise ValueError('Password must be a non-empty string')
    
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its hash.
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    except Exception:
        return False


def create_user(username: str, email: str, password: str, 
                role: str = ROLE_USER) -> str:
    """
    Create a new user.
    Returns the username on success.
    """
    dbc.connect_db()
    
    # Basic validation
    if not username or not isinstance(username, str):
        raise ValueError('Username is required')
    if not email or not isinstance(email, str):
        raise ValueError('Email is required')
    if not password or not isinstance(password, str):
        raise ValueError('Password is required')
    
    # Clean up inputs
    username = username.strip().lower()
    email = email.strip().lower()
    
    # Check if username already exists
    if dbc.exists(USER_COLLECTION, {USERNAME: username}):
        raise ValueError(f'Username already exists: {username}')
    
    # Check if email already exists
    if dbc.exists(USER_COLLECTION, {EMAIL: email}):
        raise ValueError(f'Email already exists: {email}')
    
    # Hash the password
    password_hash = hash_password(password)
    
    # Create user document
    user_doc = {
        USERNAME: username,
        EMAIL: email,
        PASSWORD_HASH: password_hash,
        ROLE: role,
        'created_at': datetime.utcnow().isoformat()
    }
    
    dbc.create(USER_COLLECTION, user_doc)
    return username


def get_user(username: str) -> dict:
    """
    Get a user by username.
    Returns user dict or None if not found.
    """
    if not username:
        raise ValueError('Username is required')
    
    username = username.strip().lower()
    return dbc.read_one(USER_COLLECTION, {USERNAME: username})


def authenticate(username: str, password: str) -> dict:
    """
    Authenticate a user with username and password.
    Returns user dict (without password_hash) if successful.
    Raises ValueError if authentication fails.
    """
    if not username or not password:
        raise ValueError('Username and password are required')
    
    # Get the user
    user = get_user(username)
    if not user:
        raise ValueError('Invalid username or password')
    
    # Verify password
    if not verify_password(password, user[PASSWORD_HASH]):
        raise ValueError('Invalid username or password')
    
    # Return user without password hash
    user_safe = dict(user)
    user_safe.pop(PASSWORD_HASH, None)
    user_safe.pop('_id', None)
    return user_safe
