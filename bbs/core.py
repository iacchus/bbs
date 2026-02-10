import datetime
import secrets

from litestar import Controller, Litestar

from litestar.di import Provide
#  from litestar.middleware.base import DefineMiddlewareo

from piccolo.engine.sqlite import SQLiteEngine

from piccolo.table import Table, create_db_tables_sync
from piccolo.table import create_db_tables
from piccolo.columns import Varchar, Timestamp, Text, Serial
from piccolo.engine.sqlite import SQLiteEngine
#  import time
from typing import Any

from litestar import (
        get,
        post,
        Request,
        Response,
        )

from litestar.exceptions import NotAuthorizedException, NotFoundException

from litestar.security.jwt import JWTCookieAuth
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from piccolo.engine.sqlite import SQLiteEngine
from pydantic import BaseModel

SQLITE_FILE_NAME = "db-{uri}.sqlite"

SESSION_SECRET = "super-secret-session-key-123"


#  async def retrieve_user_handler(token: "Token", connection: "ASGIConnection") -> User | None:
#      # 'token.sub' is now the public_key
#      return await User.objects().get(User.public_key == token.sub)
#
#
#  jwt_cookie_auth = JWTCookieAuth[User](
#      retrieve_user_handler=retrieve_user_handler,
#      token_secret=SESSION_SECRET,
#      exclude=["/request_challenge", "/register"],
#      #  exclude=["/auth/challenge", "/auth/login"],
#  )


class UserController(Controller):

    path = "/user"

    @get("/request_challenge/{public_key:str}")
    async def request_challenge(self, public_key: str,
                                db_engine: SQLiteEngine,
                                bbs: "BBS"
                                ) -> dict[str, str]:

        nonce = secrets.token_hex(32)

        await bbs.AuthChallenge.insert(
                bbs.AuthChallenge(public_key=public_key, nonce=nonce),
                )

        return {"nonce": nonce}



class BBS:

    def __init__(self, instance: str):
        self.instance: str = instance

        #  self.db_file = db_file
        db_file = SQLITE_FILE_NAME.format(uri=instance)
        self.engine = SQLiteEngine(path=db_file)

        class User(Table, db=self.engine):
            public_key = Varchar(length=64, unique=True, primary_key=True)
            username = Varchar(length=50, null=True) # Optional display name

        class AuthChallenge(Table, db=self.engine):
            """Stores temporary nonces to prevent replay attacks."""
            id = Serial(primary_key=True)
            public_key = Varchar(length=64)
            nonce = Varchar(length=64) # The random string they must sign
            created_at = Timestamp(default=datetime.datetime.now)

        dependencies: dict[str, Provide] = {
            'site_uri': Provide(self.get_uri),
            'db_engine': Provide(self.get_db_engine),
            'bbs': Provide(self.get_self)
        }

        self.User = User
        self.AuthChallenge = AuthChallenge

        create_db_tables_sync(self.User, if_not_exists=True)
        create_db_tables_sync(self.AuthChallenge, if_not_exists=True)


        route_handlers: list = [
                UserController,
        ]

        #  def on_startup():
        #      User.create_table(if_not_exists=True)
        #      AuthChallenge.create_table(if_not_exists=True)

        self.api = Litestar(
                route_handlers=route_handlers,
                #  on_startup=[self.on_startup],
                #  on_startup=[on_startup],
                dependencies=dependencies,
                #  on_app_init=[jwt_cookie_auth.on_app_init],
                debug=True
        )

    async def get_self(self):
        return self

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
