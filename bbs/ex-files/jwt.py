from datetime import datetime, timedelta

from litestar.exceptions import NotAuthorizedException

from pydantic import BaseModel
from pydantic import UUID4

import jwt

# https://docs.litestar.dev/2/usage/security/abstract-authentication-middleware.html

ALGORITHM = "HS256"
DEFAULT_TIME_DELTA = timedelta(days=1)

settings = {'JWT_SECRET': 'abc123'}


class Token(BaseModel):

    exp: datetime
    iat: datetime
    sub: int
    #  sub: UUID4


def decode_jwt_token(encoded_token: str) -> Token:
    try:
        payload = jwt.decode(jwt=encoded_token, key=settings['JWT_SECRET'],
                             algorithms=[ALGORITHM])
        return Token(**payload)

    #  except JWTError as e:
    except:
        raise NotAuthorizedException(f"Invalid token")


def encode_jwt_token(user_id: int, expiration: timedelta = DEFAULT_TIME_DELTA) -> str:
    token = Token(
                exp=datetime.now() + expiration,
                iat=datetime.now(),
                sub=user_id
            )

    return jwt.encode(token.dict(), key=settings['JWT_SECRET'], algorithm=ALGORITHM)
