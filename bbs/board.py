from typing import Sequence

from litestar import Controller
from litestar import get, post
from litestar.exceptions import NotFoundException
from litestar.exceptions import ValidationException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import Board, BoardReceiveDTO, BoardSendDTO
#  from .models import Post, TopicReceiveDTO, PostSendDTO
from .models import Post
from .models import BoardTopicReceiveDTO
from .models import PostSendDTO

from .functions import board_id_exists, board_uri_exists


class BoardController(Controller):

    path = "/board"

    @get("/")
    async def get_boards(self, site_uri: str, db_engine: Engine) -> Sequence[Board]:

        session = Session(bind=db_engine, expire_on_commit=False)

        statement = select(Board)
        results = session.exec(statement=statement).all()

        return results

    @get("/{board_id:int}")
    async def get_board_posts(self, site_uri: str, board_id: int,
                        db_engine: Engine) -> Sequence[Post]:

        session = Session(bind=db_engine, expire_on_commit=False)
        if board_id_exists(db_session=session, board_id=board_id):
            statement = select(Post).where(Post.board_id == board_id)
            results = session.exec(statement=statement).all()

            return results
        else:
            raise NotFoundException(f'Board id {board_id} does not exist')

    @post("/{board_id:int}", dto=BoardTopicReceiveDTO, return_dto=PostSendDTO)
    async def post_to_board(self, board_id: int, data: Post,
                            db_engine: Engine) -> Post | None:
        """Posts a new topic to board"""

        session = Session(bind=db_engine, expire_on_commit=False)

        new_post: Post = data

        if board_id_exists(db_session=session, board_id=board_id):
            new_post.board_id = board_id
            new_post.reply_to_id = 0  # a topic isn't replying to anything

            session.add(new_post)
            session.commit()
            session.close()

            return new_post

        else:
            raise NotFoundException(f'Board id {board_id} does not exist')

    @post(path="/", dto=BoardReceiveDTO, return_dto=BoardSendDTO)
    def create_board(self, db_engine: Engine, data: Board) -> Board:
        session = Session(bind=db_engine, expire_on_commit=False)

        new_board: Board = data

        if not board_uri_exists(db_session=session, board_uri=new_board.uri):
            session.add(new_board)
            session.commit()
            session.close()

            return new_board

        else:
            raise ValidationException("Board uri already exists")

