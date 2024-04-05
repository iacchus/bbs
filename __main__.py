import glob

from typing import Union

from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

import toml

from core import BBS

instance_names = ["one", "another"]

routes = list()

for name in instance_names:
    bbs_application = BBS(instance=name)
    mount_point = Mount(f"/{name}", bbs_application.api)
    routes.append(mount_point)

app = Starlette(debug=True, routes=routes)

uvicorn.run(app)
