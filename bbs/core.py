from fastapi import FastAPI

class BBS:

    def __init__(self, instance):
        self.api = FastAPI()

        self.instance = instance

        @self.api.get("/")
        def read_root():
            return {"instance": f"{self.instance}"}
