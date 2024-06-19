from typing import Optional

from litestar import Litestar
from litestar import Controller
from litestar import get
from litestar import post
from litestar.di import Provide

from sqlalchemy import engine, Engine
from sqlmodel import Field, Session, SQLModel, create_engine, select, table

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str

class BoardController(Controller):
    path = "/board"

    @get("/")
    #  async def read_root(self, site_uri: str) -> dict[str, str]:
    async def get_posts(self, site_uri: str) -> dict[str, str]:
        return {"instance": site_uri}

    @post("/")
    async def post(self, data: dict[str, str], db_engine: Engine) -> Post:
    #  async def post(self, data: dict[str, str], db_engine) -> dict[str, str]:

        session = Session(bind=db_engine)

        new_post = Post(text=data['text'])

        session.add(new_post)
        session.commit()
        session.close()

        #  return data
        return new_post

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

        self.api = Litestar(route_handlers=[BoardController],
                                      dependencies=dependencies)
        #  self.api = Litestar(route_handlers=[read_root, post_root],
        #                                dependencies=dependencies)

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
