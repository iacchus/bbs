from typing import Annotated
from typing import Optional

from litestar import Litestar
from litestar import Controller
from litestar import get
from litestar import post
from litestar.di import Provide
from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from sqlalchemy import engine, Engine
from sqlmodel import Field, Session, SQLModel, create_engine, select, table

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    text: str

PostDTO = PydanticDTO[Post]
ReadPostDTO = PostDTO
#  config: DTOConfig = DTOConfig(exclude={"id"})
#  ReadPostDTO = PydanticDTO[Annotated[Post, config]]

#  PostDTO = PydanticDTO[Post]
#  class PostDTO(PydanticDTO[Post]):
#      config: DTOConfig = DTOConfig(exclude={"id"})

class BoardController(Controller):
    path = "/board"

    @get("/")
    async def get_posts(self, site_uri: str) -> dict[str, str]:
        return {"instance": site_uri}

    @post("/", dto=PostDTO, return_dto=ReadPostDTO)
    async def post(self, data: Post, db_engine: Engine) -> Post:

        session = Session(bind=db_engine, expire_on_commit=False)

        #  new_post = Post(text=data['text'])
        new_post = data

        session.add(new_post)
        session.commit()
        session.close()

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
                                        #  pdb_on_exception=True)
        #  self.api = Litestar(route_handlers=[read_root, post_root],
        #                                dependencies=dependencies)

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
