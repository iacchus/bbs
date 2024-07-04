from typing import Sequence

from litestar import Controller
from litestar import get
from litestar import post
from litestar.exceptions import NotFoundException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import Post, PostReceiveDTO, PostSendDTO
from .functions import board_id_exists


class PostController(Controller):
    path = "/post"

    @get("/{post_id:int}", dto=PostReceiveDTO, return_dto=PostSendDTO)
    async def get_posts(self, site_uri: str, post_id: int,
                        db_engine: Engine) -> Sequence[Post]:

        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(Post).where(Post.id == post_id)
        results = session.exec(statement=statement).all()

        return results

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
            raise NotFoundException(f'Board id {new_post.board_id} does not exist')


