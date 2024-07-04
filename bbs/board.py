from typing import Sequence

from litestar import Controller
from litestar import get, post
from litestar.exceptions import ValidationException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import Board, BoardReceiveDTO, BoardSendDTO
from .models import Post

from .functions import board_uri_exists


class BoardController(Controller):

    path = "/board"

    @get("/")
    async def get_boards(self, site_uri: str, db_engine: Engine) -> Sequence[Board]:

        session = Session(bind=db_engine, expire_on_commit=False)
        #  statement = select(Post)
        statement = select(Board)
        results = session.exec(statement=statement).all()

        return results

    @get("/{board_id:int}")
    async def get_board_posts(self, site_uri: str, board_id: int,
                        db_engine: Engine) -> Sequence[Post]:

        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(Post).where(Post.board_id == board_id)
        results = session.exec(statement=statement).all()

        return results

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
            raise ValidationException("Board URI already exists")

