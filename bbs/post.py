from litestar import Controller
from litestar import get
from litestar import post
from litestar.exceptions import NotFoundException

from sqlalchemy import Engine
from sqlmodel import Session

from .models import Post, PostReceiveDTO, PostSendDTO
from .functions import board_id_exists


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


