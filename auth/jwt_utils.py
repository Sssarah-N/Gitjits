"""
JWT utilities for authentication.

This module now imports from security.security to use the centralized
security protocol implementation. Kept for backward compatibility.
"""

# Import all functions from the main security module
from security.security import (
    generate_token,
    decode_token,
    get_token_from_header,
    token_required,
    admin_required,
    SECRET_KEY,
    ALGORITHM,
    TOKEN_EXPIRY_HOURS,
)

# Re-export for backward compatibility
__all__ = [
    'generate_token',
    'decode_token',
    'get_token_from_header',
    'token_required',
    'admin_required',
    'SECRET_KEY',
    'ALGORITHM',
    'TOKEN_EXPIRY_HOURS',
]
