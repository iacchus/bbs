# bbs

## ATTENTION, HERE: ALWAYS KEEP THE README UPDATED WITH RUNNING INSTRUCTIONS

## running

`python -m bbs`

## dev requirements

1. install `direnv`

2. use the commands:

```
git clone git@github.com:iacchus/bbs.git  # clone repo
python -m venv .venv  # install virtualenv
source .venv/bin/activate  # activate virtualenv
direnv allow  # allow .envrc
python install -e .  # install editable
```

3. run as above

### Resources

* [click](https://click.palletsprojects.com/en/8.1.x/)
* [litestar](https://litestar.dev/)
* [fastapi](https://fastapi.tiangolo.com/)
* [httpie](https://httpie.io/docs/cli/main-features)
* [notebooks](https://github.com/iacchus/jupyter-notebooks/)
* [piccolo](https://piccolo-orm.readthedocs.io/en/latest/)
* [sqlmodel](https://sqlmodel.tiangolo.com/)
* [starlette](https://www.starlette.io/)
* [uvicorn](https://www.uvicorn.org/)
