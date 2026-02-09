import secrets
#  import time
from typing import Any

from litestar import (
        get,
        post,
        Request,
        Response,
        )

from litestar.exceptions import NotAuthorizedException, NotFoundException

from litestar.security.jwt import JWTCookieAuth
from litestar.status_codes import HTTP_401_UNAUTHORIZED

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from piccolo.engine.sqlite import SQLiteEngine
from pydantic import BaseModel

from .tables import User, AuthChallenge, db

SESSION_SECRET = "uh6yhgvcrddrrfgtg6thhu8uu8u878h8huhuhu"


async def retrieve_user_handler(token: "Token", connection: "ASGIConnection") -> User | None:
    # 'token.sub' is now the public_key
    return await User.objects().get(User.public_key == token.sub)


jwt_cookie_auth = JWTCookieAuth[User](
    retrieve_user_handler=retrieve_user_handler,
    token_secret=SESSION_SECRET,
    exclude=["/request_challenge", "/register"], 
    #  exclude=["/auth/challenge", "/auth/login"],
)


@get("/request_challenge/{public_key:str}")
async def request_challenge(public_key: str,
                            db_engine: SQLiteEngine
                            ) -> dict[str, str]:

    nonce = secrets.token_hex(32)

    await AuthChallenge.insert(
            AuthChallenge(public_key=public_key, nonce=nonce)
            ).run(engine=db_engine)

    return {"nonce": nonce}

class RegisterData(BaseModel):
    public_key: str
    signature: str


@post("/register")
async def register(data: RegisterData, 
                   db_engine: SQLiteEngine
                   ) -> Response:

    challenge = await AuthChallenge.objects().where(
            AuthChallenge.public_key == data.public_key
            ).order_by(
                    AuthChallenge.created_at, ascending=False
                    ).first().run(engine=db_engine)

    if not challenge:
        raise NotFoundException("Challenge not found")

# 2. Verify Cryptography
    try:
        # Convert hex strings back to bytes
        verify_key_bytes = bytes.fromhex(data.public_key)
        signature_bytes = bytes.fromhex(data.signature)
        message_bytes = challenge.nonce.encode('utf-8') # The nonce is the message

        # Verify using PyNaCl
        verify_key = VerifyKey(verify_key_bytes)
        verify_key.verify(message_bytes, signature_bytes)

    except (BadSignatureError, ValueError):
        raise NotAuthorizedException("Invalid Signature")

    # 3. Cleanup: Delete the used challenge (Prevent Replay Attacks)
    await AuthChallenge.delete().where(AuthChallenge.id == challenge.id)

    # 4. Check if User exists, if not, Register them automatically!
    user = await User.objects().get(User.public_key == data.public_key)
    if not user:
        user = User(public_key=data.public_key)
        await user.save().run(engine=db_engine)

    # 5. Issue Session Cookie
    response = jwt_cookie_auth.login(identifier=user.public_key)
    return Response(content={"message": "Logged in!", "user": user.public_key}, cookies=response.cookies)


@get("/me")
async def user_profile(request: Request[User, Any, Any],
                       db_engine: SQLiteEngine) -> dict[str, str]:
    return {"my_public_key": request.user.public_key,
            "current_db": db_engine.config.get("path")}
