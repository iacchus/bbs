from litestar.middleware import AbstractAuthenticationMiddleware
from litestar.middleware import AuthenticationResult

from litestar.connection import ASGIConnection

from litestar.exceptions import NotAuthorizedException


API_KEY_HEADER = "X-API-KEY"


class AuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        #  pass
        #  return await super().authenticate_request(connection)

        auth_header = connection.headers.get(API_KEY_HEADER)
        if not auth_header:
            raise NotAuthorizedException()
