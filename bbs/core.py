from typing import Optional

from litestar import Litestar
from litestar import get
from litestar import post

from sqlmodel import Field, Session, SQLModel, create_engine, select, table

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"

@get("/")
async def read_root() -> dict[str, str]:
    return {"instance": 'oi'}

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str

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

        #  @get("/")
        #  async def read_root() -> dict[str, str]:
        #      return {"instance": self.instance}

        @post("/")
        async def post_root(data: dict[str, str]) -> dict[str, str]:
            return data

        self.api = Litestar([read_root, post_root])

