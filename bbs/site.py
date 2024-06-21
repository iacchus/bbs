from typing import Annotated, Sequence
#  from typing import Annotated
from typing import Optional

from litestar import Litestar
from litestar import Controller
from litestar import get
from litestar import post
from litestar.di import Provide
from litestar.contrib.pydantic import PydanticDTO
from litestar.dto import DTOConfig
from litestar.exceptions import NotFoundException

from sqlalchemy import engine, Engine
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select, table
from sqlmodel.sql.expression import SelectOfScalar

#  from .board import Board
#  from .board import BoardReceiveDTO
#  from .board import BoardSendDTO
from . import Board
from . import BoardReceiveDTO
from . import BoardSendDTO

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"


#  class Site(SQLModel, table=True):
#      id: Optional[int] = Field(default=None, primary_key=True)
#      uri: str
#
#  class SiteSendDTO(PydanticDTO[Site]):
#      config: DTOConfig = DTOConfig()
#
#  class SiteReceiveDTO(PydanticDTO[Site]):
#      config: DTOConfig = DTOConfig(exclude={"id"})

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

        session.add(new_board)
        session.commit()
        session.close()

        return new_board

