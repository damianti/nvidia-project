import jwt
from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone

from app.utils.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.schemas.user import TokenData
from app.exceptions.domain import TokenExpiredError, InvalidTokenError


def create_access_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise InvalidTokenError("Missing username in token")
        return TokenData(username=username)

    except jwt.ExpiredSignatureError:
        raise TokenExpiredError("Token has expired")

    except jwt.PyJWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def _get_exp_from_token(token: str) -> Optional[float]:
    """Decode the exp claim without verifying the signature.

    Used only during logout to compute the remaining TTL for the blocklist entry.
    The token was already fully validated when it was issued — we just need the
    expiry timestamp here.
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        return payload.get("exp")
    except Exception:
        return None
