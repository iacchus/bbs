from litestar import Controller
from litestar import post
from litestar import get
from litestar import patch
from litestar import delete
from litestar.exceptions import NotFoundException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import Post, PostReceiveDTO, PostSendDTO, ReplyReceiveDTO
from .models import PostPatchDTO
from .functions import board_id_exists, post_id_exists
from .functions import get_thread
from .functions import get_thread_flattened

class PostController(Controller):
    path = "/post"

    @get("/{post_id:int}", dto=PostReceiveDTO, return_dto=PostSendDTO)
    async def get_posts(self, site_uri: str, post_id: int,
                        db_engine: Engine, flat: bool = False) -> dict:
                        #  db_engine: Engine) -> Sequence[Post]:

        session = Session(bind=db_engine, expire_on_commit=False)

        post: Post | None = session.get(Post, post_id)

        if not post:
            raise NotFoundException(f'Post id {post_id} does not exist')
        if not flat:
            thread: dict = get_thread(post_obj=post, max_depth=4)
        else:
            thread: dict = get_thread_flattened(post_obj=post, max_depth=4)

        #  return results
        return thread

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
            raise NotFoundException(f"Board id {new_post.board_id} does not exist")

    @post("/{reply_to_id:int}", dto=ReplyReceiveDTO, return_dto=PostSendDTO)
    async def reply_to_post(self, reply_to_id: int, data: Post,
                            db_engine: Engine) -> Post | None:
        """Replies to post"""

        session = Session(bind=db_engine, expire_on_commit=False)

        post: Post | None = session.get(Post, reply_to_id)

        #  if post_id_exists(db_session=session, post_id=reply_to_id):
        if post:

            new_post: Post = data
            new_post.reply_to_id = reply_to_id
            new_post.board_id = 0

            session.add(new_post)
            session.commit()
            session.close()

            return new_post

        else:
            raise NotFoundException(f'Post id {reply_to_id} does not exist')


    @patch("/{post_id:int}", dto=PostPatchDTO, return_dto=PostSendDTO)
    async def edit_post(self, post_id: int, data: Post,
                            db_engine: Engine) -> Post | None:
        """Updates post"""

        session = Session(bind=db_engine, expire_on_commit=False)

        post: Post | None = session.get(Post, post_id)

        if post:
            post.text = data.text

            session.add(post)
            session.commit()
            session.close()

            return post

        else:
            raise NotFoundException(f'Post id {post_id} does not exist')

    @delete("/{post_id:int}")
    async def delete_post(self, post_id: int, db_engine: Engine) -> None:
        """Deletes post"""

        session = Session(bind=db_engine, expire_on_commit=False)

        post: Post | None = session.get(Post, post_id)

        if post:
            session.delete(post)
            # FIXME: delete children or just rewrite post/change owner

            session.commit()
            session.close()

            return None

        else:
            raise NotFoundException(f'Post id {post_id} does not exist')
