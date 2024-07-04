from litestar.middleware import AbstractAuthenticationMiddleware
from litestar.middleware import AuthenticationResult

from litestar.connection import ASGIConnection

from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .jwt import decode_jwt_token
from .models import User


API_KEY_HEADER = "X-API-KEY"


class AuthenticationMiddleware(AbstractAuthenticationMiddleware):

    def __init__(self, db_engine: Engine, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.db_engine = db_engine

    #  async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
                                   #  db_engine: Engine) -> AuthenticationResult:
        #  pass
        #  return await super().authenticate_request(connection)

        auth_header = connection.headers.get(API_KEY_HEADER)
        if not auth_header:
            raise NotAuthorizedException(f"No `{API_KEY_HEADER}` header")

        token = decode_jwt_token(encoded_token=auth_header)

        db_engine = self.db_engine
        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(User).where(User.id == token.sub)
        user = session.exec(statement=statement).first()
        #  results = session.exec(statement=statement).all()

        if not user:
            raise NotAuthorizedException()

        return AuthenticationResult(user=user, auth=token)
        #  return AuthenticationResult(user=1, auth=token)

