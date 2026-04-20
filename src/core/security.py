import bcrypt
import jwt
import datetime
from typing import Optional, Tuple
from src.core.config import settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[datetime.timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.JWTError:
        raise Exception("Could not validate credentials")


def verify_payment_signature(keys: list, secret_key: str, signature: str) -> bool:
    """Verify payment webhook signature using SHA256 of sorted concatenated keys + secret_key."""
    import hashlib
    # Sort keys and concatenate
    sorted_keys = sorted(keys)
    concatenated = ''.join(sorted_keys) + secret_key
    # Calculate SHA256
    expected_signature = hashlib.sha256(concatenated.encode('utf-8')).hexdigest()
    # Compare signatures
    return expected_signature == signature