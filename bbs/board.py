from typing import Annotated, Sequence
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

from .models import Board, BoardReceiveDTO, BoardSendDTO
from .models import Post

#  from .functions import uid_exists

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"


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

