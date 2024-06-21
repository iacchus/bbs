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

from .models import Post, PostReceiveDTO, PostSendDTO
from .functions import board_id_exists
#  from .functions import uid_exists

#  from .board import board_id_exists
#  from .board import board_id_exists
#  from . import board_id_exists

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"


#  class Post(SQLModel, table=True):
#      id: Optional[int] = Field(default=None, primary_key=True)
#      board_id: int
#      text: str
#      reply_to_id: int
#      #  board_id: int = Field(default=None, foreign_key="board.id")
#      #  board: Board = Relationship(back_populates="posts")
#
#
#  class PostReceiveDTO(PydanticDTO[Post]):
#      config: DTOConfig = DTOConfig(exclude={"id", "board_id"})
#
#  class PostSendDTO(PydanticDTO[Post]):
#      #  config: DTOConfig = DTOConfig(exclude={"id", "board_id"})
#      config: DTOConfig = DTOConfig()
#

#  def post_id_exists(db_session, post_id: int) -> bool:
#      post_exists: bool = uid_exists(db_session=db_session,
#                                      model=Post,
#                                      unique_id_field=Post.id,
#                                      unique_id_value=post_id)
#      return post_exists


class PostController(Controller):
    path = "/post"

    @post("/", dto=PostReceiveDTO, return_dto=PostSendDTO)
    async def create_post(self, data: Post, db_engine: Engine) -> Post | None:
        """Creates a new post"""

        session = Session(bind=db_engine, expire_on_commit=False)

        new_post: Post = data

        if board_id_exists(db_session=session, board_id=new_post.board_id):
            session.add(new_post)
            session.commit()
            session.close()

            return new_post

        else:
            raise NotFoundException('Board id does not exist')


