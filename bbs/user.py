from typing import Sequence

from litestar import Controller
from litestar import get
from litestar import post
from litestar.exceptions import NotFoundException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .models import User, UserReceiveDTO, UserSendDTO
from .functions import user_id_exists, username_exists


class UserController(Controller):
    path = "/user"

    @get("/{user_id:int}", dto=UserReceiveDTO, return_dto=UserSendDTO)
    async def get_user(self, site_uri: str, user_id: int,
                       db_engine: Engine) -> User:
                       #  db_engine: Engine) -> Sequence[User]:

        session = Session(bind=db_engine, expire_on_commit=False)
        statement = select(User).where(User.id == user_id)
        user: User | None = session.exec(statement=statement).first()

        if not user:
            raise NotFoundException(f'User id {user_id} does not exist')

        return user

    @post("/", dto=UserReceiveDTO, return_dto=UserSendDTO)
    async def create_user(self, data: User, db_engine: Engine) -> User | None:
        """Creates a new user"""

        session = Session(bind=db_engine, expire_on_commit=False)

        new_user: User = data

        if not username_exists(db_session=session, username=new_user.username):
            session.add(new_user)
            session.commit()
            session.close()

            return new_user

        else:
            raise NotFoundException(f'Username `{new_user.username}`'
                                    ' already exists')

