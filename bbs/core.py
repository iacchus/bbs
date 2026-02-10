import datetime
import secrets

from litestar import Controller, Litestar

from litestar.di import Provide
#  from litestar.middleware.base import DefineMiddlewareo

from piccolo.engine.sqlite import SQLiteEngine

from piccolo.table import Table
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

#  from .tables import User, AuthChallenge, db

#  from sqlmodel import SQLModel, create_engine

#  from .site import SiteController
#  from .board import BoardController
#  from .post import PostController
#  from .user import UserController

#  from .tables import (
#          User,
#          AuthChallenge,
#          )

#  from .routes import (
#          request_challenge,
#          register,
#          user_profile,
#          jwt_cookie_auth,
#          )

#  from .authentication import AuthenticationMiddleware

#  SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_FILE_NAME = "db-{uri}.sqlite"
#  SQLITE_URL = "sqlite:///{sqlite_file_name}"

# --- 1. Session Configuration (Same as before) ---
SESSION_SECRET = "super-secret-session-key-123"




#  DB_FILE = "whaT.sqlite"
#  db = SQLiteEngine(path=DB_FILE)

class User(Table, db=db):
    # The Public Key (in Hex format) is the unique ID
    public_key = Varchar(length=64, unique=True, primary_key=True)
    username = Varchar(length=50, null=True) # Optional display name

class AuthChallenge(Table, db=db):
    """Stores temporary nonces to prevent replay attacks."""
    id = Serial(primary_key=True)
    public_key = Varchar(length=64)
    nonce = Varchar(length=64) # The random string they must sign
    created_at = Timestamp(default=datetime.datetime.now)



SESSION_SECRET = "uh6yhgvcrddrrfgtg6thhu8uu8u878h8huhuhu"


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


@get("/request_challenge/{public_key:str}")
async def request_challenge(public_key: str,
                            db_engine: SQLiteEngine
                            ) -> dict[str, str]:

    nonce = secrets.token_hex(32)

    await AuthChallenge.insert(
            AuthChallenge(public_key=public_key, nonce=nonce)
            ).run()

    return {"nonce": nonce}

class RegisterData(BaseModel):
    public_key: str
    signature: str


@post("/register")
async def register(data: RegisterData,
                   db_engine: SQLiteEngine
                   ) -> Response:

    challenge = await AuthChallenge.objects().where(
            AuthChallenge.public_key == data.public_key
            ).order_by(
                    AuthChallenge.created_at, ascending=False
                    ).first().run()

    if not challenge:
        raise NotFoundException("Challenge not found")

# 2. Verify Cryptography
    try:
        # Convert hex strings back to bytes
        verify_key_bytes = bytes.fromhex(data.public_key)
        signature_bytes = bytes.fromhex(data.signature)
        message_bytes = challenge.nonce.encode('utf-8') # The nonce is the message

        # Verify using PyNaCl
        verify_key = VerifyKey(verify_key_bytes)
        verify_key.verify(message_bytes, signature_bytes)

    except (BadSignatureError, ValueError):
        raise NotAuthorizedException("Invalid Signature")

    # 3. Cleanup: Delete the used challenge (Prevent Replay Attacks)
    await AuthChallenge.delete().where(AuthChallenge.id == challenge.id)

    # 4. Check if User exists, if not, Register them automatically!
    user = await User.objects().get(User.public_key == data.public_key)
    if not user:
        user = User(public_key=data.public_key)
        await user.save().run()

    # 5. Issue Session Cookie
    #  response = jwt_cookie_auth.login(identifier=user.public_key)
    return Response(content={"message": "Logged in!", "user": user.public_key})
    return Response(content={"message": "Logged in!", "user": user.public_key}, cookies=response.cookies)


#  @get("/me")
#  async def user_profile(request: Request[User, Any, Any],
#                         db_engine: SQLiteEngine) -> dict[str, str]:
#      return {"my_public_key": request.user.public_key,
#              "current_db": db_engine.config.get("path")}


class BBS:

    def __init__(self, instance: str):
        self.instance: str = instance

        db_file = SQLITE_FILE_NAME.format(uri=instance)
        self.engine = SQLiteEngine(path=db_file)
        #  sqlite_file_name: str = SQLITE_FILE_NAME.format(uri=instance)
        #  self.sqlite_file_name: str = sqlite_file_name

        #  sqlite_url: str = SQLITE_URL.format(sqlite_file_name=sqlite_file_name)
        #  self.sqlite_url: str = sqlite_url

        #  engine = create_engine(url=sqlite_url, echo=True)
        #  self.engine = engine

        #  SQLModel.metadata.create_all(engine)
        #  class User(Table, db=db):
        class User(Table, db=self.engine):
            # The Public Key (in Hex format) is the unique ID
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
            'db_engine': Provide(self.get_db_engine)
        }

        self.User = User
        self.AuthChallenge = AuthChallenge

        async def on_startup():
            await User.create_table(if_not_exists=True)
            await AuthChallenge.create_table(if_not_exists=True)
            #  await User.create_table(if_not_exists=True,
            #                          engine=self.engine)
            #  await AuthChallenge.create_table(if_not_exists=True,
            #                                   engine=self.engine)

        route_handlers: list = [
                request_challenge,
                register,
                #  user_profile,
                #  BoardController,
                #  PostController,
                #  SiteController,
                #  UserController
        ]

        #  auth_mw = DefineMiddleware(middleware=AuthenticationMiddleware,
        #                             exclude="schema",
        #                             db_engine=self.engine)
        #  self.auth_mw = auth_mw

        #  middleware = [
        #          #  self.auth_mw
        #  ]

        self.api = Litestar(route_handlers=route_handlers,
                            on_startup=[on_startup],
                            dependencies=dependencies,
                            on_app_init=[jwt_cookie_auth.on_app_init],
                            debug=True
                            )
                            #  middleware=middleware)

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
