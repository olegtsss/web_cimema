from typing import Optional

from fastapi import HTTPException, Request, status
from fastapi.security import HTTPBearer
from jose import jwt

from core.config import PUBLIC_KEY, settings


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(
            token,
            PUBLIC_KEY,
            algorithms=["RS256"],
            audience=settings.app_name,
        )
    except Exception:
        return None


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> dict:
        credentials = await super().__call__(request)

        if not credentials:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid authorization code",
            )

        if not credentials.scheme == "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Only Bearer token might be accepted",
            )

        decoded_token = self.parse_token(credentials.credentials)
        if not decoded_token:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or expired token",
            )

        return decoded_token

    @staticmethod
    def parse_token(jwt_token: str) -> Optional[dict]:
        return decode_token(jwt_token)


security_jwt = JWTBearer()
