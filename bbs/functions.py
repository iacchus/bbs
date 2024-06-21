from sqlmodel import select

from .models import Site
from .models import Board
from .models import Post

def board_id_exists(db_session, board_id: int) -> bool:
    board_exists: bool = uid_exists(db_session=db_session,
                                    model=Board,
                                    unique_id_field=Board.id,
                                    unique_id_value=board_id)
    return board_exists


def board_uri_exists(db_session, board_uri: int) -> bool:
    board_exists: bool = uid_exists(db_session=db_session,
                                    model=Board,
                                    unique_id_field=Board.uri,
                                    unique_id_value=board_uri)
    return board_exists


def uid_exists(db_session, model,
               unique_id_field, unique_id_value: int | str) -> bool:

        statement = \
            select(model).where(unique_id_field == unique_id_value)

        does_uid_exist: model | None = \
            db_session.exec(statement=statement).first()

        return bool(does_uid_exist)

def post_id_exists(db_session, post_id: int) -> bool:
    post_exists: bool = uid_exists(db_session=db_session,
                                    model=Post,
                                    unique_id_field=Post.id,
                                    unique_id_value=post_id)
    return post_exists
