from typing import Sequence

from litestar import Controller
from litestar import get, post
from litestar.exceptions import NotFoundException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import Board, BoardReceiveDTO, BoardSendDTO

from .functions import board_uri_exists

class SiteController(Controller):

    path = "/"

    @get("/")
    async def get_boards(self, site_uri: str, db_engine: Engine) -> Sequence[Board]:
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

        if not board_uri_exists(session, new_board.uri):
            session.add(new_board)
            session.commit()
            session.close()

        return new_board

