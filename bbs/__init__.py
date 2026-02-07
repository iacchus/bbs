import click

from starlette.applications import Starlette
from starlette.routing import Mount

import uvicorn
#  import toml

from .core import BBS

#  instance_names: list[str] = ["one", "another"]
instance_names: list[str] = ["one"]

def app_factory(instance_names: list[str]) -> Starlette:

    routes = list()

    for name in instance_names:
        bbs_application = BBS(instance=name)
        # if there's only one site, let's put in it root (dev mode/mono mode)
        # if there are multiple sites, let's put them in "/uri” (multisite/multi
        #   mode)
        path = f"/{name}" if len(instance_names) > 1 else "/"
        mount_point: Mount = Mount(path, bbs_application.api)
        routes.append(mount_point)

    app: Starlette = Starlette(debug=True, routes=routes)

    return app

app = app_factory(instance_names=instance_names)

def run_uvicorn():
    uvicorn.run("bbs:app", host="0.0.0.0", port=8100, reload=True)


@click.group()
def cli() -> None:
    pass


@cli.command(epilog="Runs BBS")
def run():
    """Runs the BBS"""

    run_uvicorn()

