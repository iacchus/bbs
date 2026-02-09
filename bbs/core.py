from litestar import Litestar
from litestar.di import Provide
#  from litestar.middleware.base import DefineMiddleware

from sqlmodel import SQLModel, create_engine

#  from .site import SiteController
#  from .board import BoardController
#  from .post import PostController
#  from .user import UserController

from .routes import (
        User,
        AuthChallenge,
        request_challenge,
        register,
        user_profile,
        jwt_cookie_auth,
        )

#  from .authentication import AuthenticationMiddleware

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"

# --- 1. Session Configuration (Same as before) ---
SESSION_SECRET = "super-secret-session-key-123"


# --- Lifecycle ---
async def startup():
    await User.create_table(if_not_exists=True)
    await AuthChallenge.create_table(if_not_exists=True)

#  app = Litestar(
#      route_handlers=[get_challenge, login_handler, user_profile],
#      on_startup=[startup],
#      on_app_init=[jwt_cookie_auth.on_app_init]
#  )

class BBS:

    def __init__(self, instance: str):

        self.instance: str = instance

        sqlite_file_name: str = SQLITE_FILE_NAME.format(uri=instance)
        self.sqlite_file_name: str = sqlite_file_name

        sqlite_url: str = SQLITE_URL.format(sqlite_file_name=sqlite_file_name)
        self.sqlite_url: str = sqlite_url

        engine = create_engine(url=sqlite_url, echo=True)
        self.engine = engine

        SQLModel.metadata.create_all(engine)

        dependencies: dict[str, Provide] = {
            'site_uri': Provide(self.get_uri),
            'db_engine': Provide(self.get_db_engine)
        }

        route_handlers: list = [
                request_challenge,
                register,
                user_profile,
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
                            on_startup=[startup],
                            dependencies=dependencies,
                            on_app_init=[jwt_cookie_auth.on_app_init]
                            )
                            #  middleware=middleware)

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
