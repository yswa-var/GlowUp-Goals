import bcrypt
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

def hash_password(password: str) -> Tuple[str, str]:
    """
    Hash a password using bcrypt.
    Returns a tuple of (hashed_password, salt).
    """
    try:
        # Generate a salt and hash the password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
        return hashed.decode('utf-8'), salt.decode('utf-8')
    except Exception as e:
        logger.error(f"Error hashing password: {str(e)}")
        raise

def verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.
    Returns True if the password matches, False otherwise.
    """
    try:
        return bcrypt.checkpw(
            password.encode('utf-8'),
            hashed_password.encode('utf-8')
        )
    except Exception as e:
        logger.error(f"Error verifying password: {str(e)}")
        return False 