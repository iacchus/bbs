import datetime
from litestar import Litestar
from litestar.di import Provide
from litestar.connection import ASGIConnection
from litestar.security.jwt import JWTCookieAuth, Token
from piccolo.engine.sqlite import SQLiteEngine
from litestar.datastructures import State

from .tables import User, AuthChallenge, Board, Post
from .routes import UserController, BoardController, ThreadController

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SESSION_SECRET = "super-secret-session-key-123"

class BBS:

    def __init__(self, instance: str):
        self.instance: str = instance
        db_file = SQLITE_FILE_NAME.format(uri=instance)
        self.engine = SQLiteEngine(path=db_file)

        # Create tables
        # We temporarily bind the table to this instance's engine to create tables.
        # This is safe because creation happens sequentially during startup.
        # For queries, we explicitly pass the engine to override this binding.
        for table_class in [User, AuthChallenge, Board, Post]:
            table_class._meta.db = self.engine
            table_class.create_table(if_not_exists=True).run_sync()

        async def retrieve_user_handler(token: Token, connection: ASGIConnection) -> User | None:
            # Get engine from app state

            # User might be bound to the last initialized engine, so we MUST override it.
            return await User.objects().get(User.public_key == token.sub).run()

        self.jwt_cookie_auth = JWTCookieAuth[User](
            retrieve_user_handler=retrieve_user_handler,
            token_secret=SESSION_SECRET,
            # Public endpoints: auth/register. All others require login.
            exclude=["/user/request_challenge", "/user/register", "/schema", "/favicon.ico"],
        )

        dependencies: dict[str, Provide] = {
            'db_engine': Provide(self.get_db_engine),
            'jwt_auth': Provide(lambda: self.jwt_cookie_auth),
        }

        self.api = Litestar(
            route_handlers=[UserController, BoardController, ThreadController],
            dependencies=dependencies,
            on_app_init=[self.jwt_cookie_auth.on_app_init],
            debug=True,
            state=State({'db_engine': self.engine})
        )

    async def get_db_engine(self) -> SQLiteEngine:
        return self.engine
