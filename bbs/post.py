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

#  from .functions import board_id_exists
#  from . import board_id_exists


SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"


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


#  def post_id_exists(db_session, post_id: int) -> bool:
#          statement: SelectOfScalar[Post] = \
#              select(Post).where(Post.id == post_id)
#
#          post_exists: Post | None = \
#              db_session.exec(statement=statement).first()
#
        #  return bool(post_exists)


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


#  class BBS:
#
#      def __init__(self, instance: str):
#
#          self.instance: str = instance
#
#          sqlite_file_name: str = SQLITE_FILE_NAME.format(uri=instance)
#          self.sqlite_file_name: str = sqlite_file_name
#
#          sqlite_url: str = SQLITE_URL.format(sqlite_file_name=sqlite_file_name)
#          self.sqlite_url: str = sqlite_url
#
#          engine = create_engine(url=sqlite_url, echo=True)
#          self.engine = engine
#
#          SQLModel.metadata.create_all(engine)
#
#          dependencies: dict[str, Provide] = {
#              'site_uri': Provide(self.get_uri),
#              'db_engine': Provide(self.get_db_engine)
#          }
#
#          route_handlers: list = [BoardController,
#                                  SiteController]
#
#          self.api = Litestar(route_handlers=route_handlers,
#                                        dependencies=dependencies)
#                                        #  dependencies=dependencies,
#                                        #  pdb_on_exception=True)
#
#      async def get_uri(self) -> str:
#          return self.instance
#
#      async def get_db_engine(self):
#          return self.engine
