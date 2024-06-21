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
    reply_to_id: int
    #  board_id: int = Field(default=None, foreign_key="board.id")
    #  board: Board = Relationship(back_populates="posts")


class PostReceiveDTO(PydanticDTO[Post]):
    config: DTOConfig = DTOConfig(exclude={"id"})


class PostSendDTO(PydanticDTO[Post]):
    #  config: DTOConfig = DTOConfig(exclude={"id", "board_id"})
    config: DTOConfig = DTOConfig()
