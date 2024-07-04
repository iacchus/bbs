from litestar.middleware import AbstractAuthenticationMiddleware
from litestar.middleware import AuthenticationResult

from litestar.connection import ASGIConnection

class AuthenticationMiddleware(AbstractAuthenticationMiddleware):
    async def authenticate_request(self, connection: ASGIConnection) -> AuthenticationResult:
        #  pass
        #  return await super().authenticate_request(connection)
