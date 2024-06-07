from litestar import Litestar
from litestar import get

class BBS:

    def __init__(self, instance: str):

        self.instance = instance

        @get("/")
        async def read_root() -> dict[str, str]:
            return {"instance": f"{self.instance}"}

        self.api = Litestar([read_root])

