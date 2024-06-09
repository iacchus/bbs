from litestar import Litestar
from litestar import get

SQLITE_FILE_NAME = "db-{uri}.sqlite"
SQLITE_URL = "sqlite:///{sqlite_file_name}"

class BBS:

    def __init__(self, instance: str):

        self.instance: str = instance

        sqlite_file_name: str = SQLITE_FILE_NAME.format(uri=instance)
        self.sqlite_file_name: str = sqlite_file_name

        sqlite_url: str = SQLITE_URL.format(sqlite_file_name=sqlite_file_name)
        self.sqlite_url: str = sqlite_url

        @get("/")
        async def read_root() -> dict[str, str]:
            return {"instance": f"{self.instance}"}

        self.api = Litestar([read_root])

