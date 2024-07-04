from typing import Sequence

from litestar import Controller
from litestar import get
from litestar import post
from litestar.exceptions import NotFoundException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import User, UserReceiveDTO, UserSendDTO, ReplyReceiveDTO
from .functions import board_id_exists, user_id_exists


class UserController(Controller):
    path = "/user"

    @get("/{user_id:int}", dto=UserReceiveDTO, return_dto=UserSendDTO)
    async def get_users(self, site_uri: str, user_id: int,
                        db_engine: Engine) -> Sequence[User]:

        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(User).where(User.id == user_id)
        results = session.exec(statement=statement).all()

        if not results:
            raise NotFoundException(f'User id {user_id} does not exist')

        return results

    @post("/", dto=UserReceiveDTO, return_dto=UserSendDTO)
    async def create_user(self, data: User, db_engine: Engine) -> User | None:
        """Creates a new user"""

        session = Session(bind=db_engine, expire_on_commit=False)

        new_user: User = data

        if board_id_exists(db_session=session, board_id=new_user.board_id):
            session.add(new_user)
            session.commit()
            session.close()

            return new_user

        else:
            raise NotFoundException(f'Board id {new_user.board_id} does not exist')

    #  @post("/{reply_to_id:int}", dto=ReplyReceiveDTO, return_dto=UserSendDTO)
    #  async def reply_to_user(self, reply_to_id: int, data: User,
    #                          db_engine: Engine) -> User | None:
    #      """Replies to user"""
    #
    #      session = Session(bind=db_engine, expire_on_commit=False)
    #
    #      if user_id_exists(db_session=session, user_id=reply_to_id):
    #          new_user: User = data
    #          new_user.reply_to_id = reply_to_id
    #          new_user.board_id = 0
    #
    #          session.add(new_user)
    #          session.commit()
    #          session.close()
    #
    #          return new_user
    #
    #      else:
    #          raise NotFoundException(f'User id {reply_to_id} does not exist')
    #
    #
