import glob

from typing import Union

from starlette.applications import Starlette
from starlette.routing import Mount
import uvicorn

import toml

from core import BBS

#instance_names = ["one", "another"]
instance_names = ["one"]

routes = list()

#  # if there's only one site, let's put in it root (dev mode/mono mode)
#  if len(instance_names) == 1:
#      name = instance_names[0]
#      bbs_application = BBS(instance=name)
#      mount_point = Mount(f"/", bbs_application.api)
#      routes.append(mount_point)
#  # if there are multiple sites, let's put in it root (multisite/multi mode)
#  else:
#      for name in instance_names:
#          bbs_application = BBS(instance=name)
#          mount_point = Mount(f"/{name}", bbs_application.api)
#          routes.append(mount_point)

for name in instance_names:
    bbs_application = BBS(instance=name)
    # if there's only one site, let's put in it root (dev mode/mono mode)
    # if there are multiple sites, let's put in it root (multisite/multi mode)
    path = f"/{name}" if len(instance_names) > 1 else "/"
    mount_point = Mount(path, bbs_application.api)
    routes.append(mount_point)

app = Starlette(debug=True, routes=routes)

if __name__ == '__main__':
    #  uvicorn.run("bbs.__main__:app", host="0.0.0.0", port=8000, reload=True)
    uvicorn.run("bbs.__main__:app", host="0.0.0.0", port=8000, reload=True)
