# bbs

## ATTENTION, HERE: ALWAYS KEEP THE README UPDATED WITH RUNNING INSTRUCTIONS

## running

```
bbs-cli run
```

or

```
python -m bbs run
```

or in debug mode with

```
LITESTAR_PDB=1 bbs-cli run
```

## dev requirements

1. install `direnv`

2. use the commands:

```
git clone git@github.com:iacchus/bbs.git
cd bbs/
python -m venv .venv
source .venv/bin/activate
direnv allow
python install -e .
```

3. run as above

### Resources

* [click](https://click.palletsprojects.com/en/8.1.x/)
* [litestar](https://litestar.dev/)
* [fastapi](https://fastapi.tiangolo.com/)
* [httpie](https://httpie.io/docs/cli/main-features)
* [jupyter notebooks](https://github.com/iacchus/jupyter-notebooks)
* [jwt claims](https://www.iana.org/assignments/jwt/jwt.xhtml)
* [jwt introduction](https://jwt.io/introduction)
* [notebooks](https://github.com/iacchus/jupyter-notebooks/)
* [piccolo](https://piccolo-orm.readthedocs.io/en/latest/)
* [pydantic](https://docs.pydantic.dev/latest/)
* [pyjwt](https://pyjwt.readthedocs.io/en/stable/index.html)
* [sqlmodel](https://sqlmodel.tiangolo.com/)
* [starlette](https://www.starlette.io/)
* [uvicorn](https://www.uvicorn.org/)
