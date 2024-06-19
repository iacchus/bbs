from typing import Annotated, Sequence
#  from typing import Annotated
from typing import Optional

from litestar import Litestar
from litestar import Controller
from litestar import get
from litestar import post
from litestar.di import Provide
from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from sqlalchemy import engine, Engine
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select, table

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"

#  class Board(SQLModel, table=True):
#      id: Optional[int] = Field(default=None, primary_key=True)
#      #  id: str = Field(default=None, primary_key=True)
#      posts: list["Post"] = Relationship(back_populates="board")

class Board(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uri: str
    #  id: str = Field(default=None, primary_key=True)
    #  posts: list["Post"] = Relationship(back_populates="board")

BoardDTO = PydanticDTO[Board]
ReadBoardDTO = BoardDTO

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    board_id: int
    text: str
    #  board_id: int = Field(default=None, foreign_key="board.id")
    #  board: Board = Relationship(back_populates="posts")

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
    async def get_posts(self, site_uri: str, db_engine: Engine) -> Sequence[Post]:
    #  async def get_posts(self, site_uri: str, db_engine: Engine) -> dict[str, str]:
        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(Post)
        results = session.exec(statement=statement)
        #  return {"instance": site_uri}
        return results.all()

    @post("/", dto=PostDTO, return_dto=ReadPostDTO)
    async def post(self, data: Post, db_engine: Engine) -> Post:

        session = Session(bind=db_engine, expire_on_commit=False)

        #  new_post = Post(text=data['text'])
        new_post = data

        session.add(new_post)
        session.commit()
        session.close()

        return new_post

    @get("/{board_id:int}")
    async def get_board_posts(self, site_uri: str, board_id: int,
                        db_engine: Engine) -> Sequence[Post]:
    #  async def get_posts(self, site_uri: str, db_engine: Engine) -> dict[str, str]:
        session = Session(bind=db_engine, expire_on_commit=False)
        #  statement = select(Post)
        statement = select(Post).where(Post.board_id == board_id)
        results = session.exec(statement=statement).all()
        #  return {"instance": site_uri}
        return results

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
                                      #  dependencies=dependencies,
                                      #  pdb_on_exception=True)
        #  self.api = Litestar(route_handlers=[read_root, post_root],
        #                                dependencies=dependencies)

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
