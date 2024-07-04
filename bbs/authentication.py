from litestar.middleware import AbstractAuthenticationMiddleware
from litestar.middleware import AuthenticationResult

from litestar.connection import ASGIConnection

from litestar.exceptions import NotAuthorizedException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .jwt import decode_jwt_token
from .models import User


API_KEY_HEADER = "X-API-KEY"


class AuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection,
                                   db_engine: Engine) -> AuthenticationResult:
        #  pass
        #  return await super().authenticate_request(connection)

        auth_header = connection.headers.get(API_KEY_HEADER)
        if not auth_header:
            raise NotAuthorizedException()

        token = decode_jwt_token(encoded_token=auth_header)
        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(User).where(User.id == token.sub)
        results = session.exec(statement=statement).all()
