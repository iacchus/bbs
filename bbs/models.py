from typing import Optional

from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig

from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select, table


#  ┌──────┐
#  │ site │
#  └──────┘

class Site(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uri: str

class SiteSendDTO(PydanticDTO[Site]):
    config: DTOConfig = DTOConfig()

class SiteReceiveDTO(PydanticDTO[Site]):
    config: DTOConfig = DTOConfig(exclude={"id"})


#  ┌───────┐
#  │ board │
#  └───────┘

class Board(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    uri: str
    #  id: str = Field(default=None, primary_key=True)
    #  posts: list["Post"] = Relationship(back_populates="board")


class BoardReceiveDTO(PydanticDTO[Board]):
    config: DTOConfig = DTOConfig(exclude={"id"})


class BoardSendDTO(PydanticDTO[Board]):
    config: DTOConfig = DTOConfig()


#  ┌──────┐
#  │ post │
#  └──────┘

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    board_id: int
    text: str
    reply_to_id: int = Field(foreign_key="post.id")
    # https://docs.sqlalchemy.org/en/20/orm/self_referential.html
    # https://stackoverflow.com/questions/73420018/how-do-i-construct-a-self-referential-recursive-sqlmodel
    replies = Relationship("Post", back_populates="reply_to" sa_relationship_kwargs=dict(remote_side=[id]))  # type: ignore
    #  replies = Relationship("Post", remote_side=[id])
    #  board_id: int = Field(default=None, foreign_key="board.id")
    #  board: Board = Relationship(back_populates="posts")
    reply_to = Relationship("Post", back_populates="replies")  # pyright: ignore



class PostReceiveDTO(PydanticDTO[Post]):
    config: DTOConfig = DTOConfig(exclude={"id"})

class TopicReceiveDTO(PydanticDTO[Post]):
    config: DTOConfig = DTOConfig(exclude={"id", "reply_to_id"})
    # `reply_to_id` for topics is always `0` (int zero)

class BoardTopicReceiveDTO(PydanticDTO[Post]):
    config: DTOConfig = DTOConfig(exclude={"id", "board_id", "reply_to_id"})
    # `reply_to_id` for topics is always `0` (int zero)
    # `board_id` is taken from http path

class ReplyReceiveDTO(PydanticDTO[Post]):
    config: DTOConfig = DTOConfig(exclude={"id", "reply_to_id", "board_id"})
    # `reply_to_id` is taken via http path
    # `board_id` for replies is always `0` (int zero)

class PostSendDTO(PydanticDTO[Post]):
    #  config: DTOConfig = DTOConfig(exclude={"id", "board_id"})
    config: DTOConfig = DTOConfig()


#  ┌──────┐
#  │ User │
#  └──────┘

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str  # FIXME: limit the characters allowed here
    password: str
    #  board_id: int = Field(default=None, foreign_key="board.id")
    #  board: Board = Relationship(back_populates="posts")

class UserReceiveDTO(PydanticDTO[User]):
    config: DTOConfig = DTOConfig(exclude={"id"})
    #  config: DTOConfig = DTOConfig(exclude={"id", "username"})

class UserSendDTO(PydanticDTO[User]):
    config: DTOConfig = DTOConfig()
