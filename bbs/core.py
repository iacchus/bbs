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
from litestar.exceptions import NotFoundException

from sqlalchemy import engine, Engine
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select, table
from sqlmodel.sql.expression import SelectOfScalar

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"


def board_id_exists(db_session, board_id: int) -> bool:
        statement: SelectOfScalar[Board] = \
            select(Board).where(Board.id == board_id)

        board_exists: Board | None = \
            db_session.exec(statement=statement).first()

        return bool(board_exists)

def post_id_exists(db_session, post_id: int) -> bool:
        statement: SelectOfScalar[Post] = \
            select(Post).where(Post.id == post_id)

        post_exists: Post | None = \
            db_session.exec(statement=statement).first()

        return bool(post_exists)

class Board(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uri: str
    #  id: str = Field(default=None, primary_key=True)
    #  posts: list["Post"] = Relationship(back_populates="board")

class BoardReceiveDTO(PydanticDTO[Board]):
    config: DTOConfig = DTOConfig(exclude={"id"})

class BoardSendDTO(PydanticDTO[Board]):
    config: DTOConfig = DTOConfig()


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    board_id: int
    text: str
    reply_to_id: int
    #  board_id: int = Field(default=None, foreign_key="board.id")
    #  board: Board = Relationship(back_populates="posts")


class PostReceiveDTO(PydanticDTO[Post]):
    config: DTOConfig = DTOConfig(exclude={"id", "board_id"})

class PostSendDTO(PydanticDTO[Post]):
    #  config: DTOConfig = DTOConfig(exclude={"id", "board_id"})
    config: DTOConfig = DTOConfig()

class PostController(Controller):
    path = "/post"

    @post("/", dto=PostReceiveDTO, return_dto=PostSendDTO)
    async def create_post(self, data: Post, db_engine: Engine) -> Post | None:

        session = Session(bind=db_engine, expire_on_commit=False)

        new_post: Post = data

        #  statement: SelectOfScalar[Board] = select(Board).where(Board.id == new_post.board_id)
        #  board_exists: Board | None = session.exec(statement=statement).first()

        #  if board_exists:
        if board_id_exists(db_session=session, board_id=new_post.board_id):
            session.add(new_post)
            session.commit()
            session.close()

            return new_post

        else:
            raise NotFoundException('Board id does not exist')

class SiteController(Controller):

    path = "/"

    @get("/")

    async def get_boards(self, site_uri: str, db_engine: Engine) -> Sequence[Board]:
    #  async def get_boards(self) -> Sequence[Board]:
        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(Board)
        results = session.exec(statement=statement).all()

        return results


    @post("/", dto=BoardReceiveDTO, return_dto=BoardSendDTO)
    async def create_board(self, data: Board, db_engine: Engine) -> Board:

        session = Session(bind=db_engine, expire_on_commit=False)

        new_board = data

        # TODO: check if board exists
        #  new_board.uri = board_uri

        session.add(new_board)
        session.commit()
        session.close()

        return new_board


class BoardController(Controller):
    path = "/board"

    @get("/")
    async def get_posts(self, site_uri: str, db_engine: Engine) -> Sequence[Post]:

        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(Post)
        results = session.exec(statement=statement).all()

        return results

    #  @post("/{board_id:int}", dto=PostReceiveDTO, return_dto=PostSendDTO)
    #  @post("/", dto=PostReceiveDTO, return_dto=PostSendDTO)
    #  async def create_post(self, data: Post, db_engine: Engine) -> Post | None:
    #      #  async def create_post(self, board_id: int, data: Post, db_engine: Engine) -> Post | None:
    #
    #      session = Session(bind=db_engine, expire_on_commit=False)
    #
    #      new_post: Post = data
    #
    #      statement: SelectOfScalar[Board] = select(Board).where(Board.id == new_post.board_id)
    #      board_exists: Board | None = session.exec(statement=statement).first()
    #
    #      if board_exists:
    #          session.add(new_post)
    #          session.commit()
    #          session.close()
    #
    #          return new_post
    #
    #      else:
    #          raise NotFoundException('Board id does not exist')

    @get("/{board_id:int}")
    async def get_board_posts(self, site_uri: str, board_id: int,
                        db_engine: Engine) -> Sequence[Post]:

        session = Session(bind=db_engine, expire_on_commit=False)
        #  statement = select(Post)
        statement = select(Post).where(Post.board_id == board_id)
        results = session.exec(statement=statement).all()

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

        route_handlers: list = [BoardController,
                                SiteController]

        self.api = Litestar(route_handlers=route_handlers,
                                      dependencies=dependencies)
                                      #  dependencies=dependencies,
                                      #  pdb_on_exception=True)

    async def get_uri(self) -> str:
        return self.instance

    async def get_db_engine(self):
        return self.engine
