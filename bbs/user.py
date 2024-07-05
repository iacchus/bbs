from typing import Sequence

from litestar import Controller
from litestar import get
from litestar import post
from litestar.exceptions import NotFoundException
from litestar.exceptions import NotAuthorizedException

from sqlalchemy import Engine
from sqlmodel import Session, select

from .jwt import Token
from .jwt import encode_jwt_token
from .models import User, UserReceiveDTO, UserSendDTO
from .functions import user_id_exists, username_exists


class UserController(Controller):
    path = "/user"

    @get("/{user_id:int}", dto=UserReceiveDTO, return_dto=UserSendDTO)
    async def get_user(self, site_uri: str, user_id: int,
                       db_engine: Engine) -> User:

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

    @post("/login", dto=UserReceiveDTO, return_dto=UserSendDTO,
          exclude_from_auth=True)
    async def get_user(self, data: User, site_uri: str,
                       db_engine: Engine) -> Token:

        login_user = data

        session = Session(bind=db_engine, expire_on_commit=False)
        #  if username_exists(db_session=session, username=user.username)
        statement = select(User).where(User.username == login_user.username)
        user: User | None = session.exec(statement=statement).first()

        if not user:
            raise NotFoundException(f'Username `{login_user.username}`'
                                    ' does not exist')

        if user.password == login_user.password:
            token = encode_jwt_token(user_id=user.id)
            #  token = encode_jwt_token(user_id=login_user.username)
            return token

        else:
            raise NotAuthorizedException("Invalid login credentials")


