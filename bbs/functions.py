from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select, table
from sqlmodel.sql.expression import SelectOfScalar

def board_id_exists(db_session, board_id: int) -> bool:
        statement: SelectOfScalar[Board] = \
            select(Board).where(Board.id == board_id)

        board_exists: Board | None = \
            db_session.exec(statement=statement).first()

        return bool(board_exists)

def post_id_exists(db_session, post_id: int) -> bool:
        statement: SelectOfScalar[Post] = \
            select(Post).where(Post.id == post_id)

        post_exists: Post | None = \
            db_session.exec(statement=statement).first()

        return bool(post_exists)
