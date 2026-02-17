import secrets
from typing import Any, List, Dict
from litestar import Controller, get, post, Request, Response
from litestar.exceptions import NotFoundException, NotAuthorizedException
from litestar.status_codes import HTTP_201_CREATED
from litestar.security.jwt import JWTCookieAuth
from pydantic import BaseModel
from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

from .tables import User, AuthChallenge, Board, Post

# Pydantic Models

class LoginPayload(BaseModel):
    public_key: str
    signature: str

class CreateThreadPayload(BaseModel):
    title: str
    content: str

class CreateReplyPayload(BaseModel):
    content: str

# Controllers

class UserController(Controller):
    path = "/user"

    @get("/request_challenge/{public_key:str}")
    async def request_challenge(self, public_key: str) -> dict[str, str]:
        nonce = secrets.token_hex(32)
        await AuthChallenge.insert(
            AuthChallenge(public_key=public_key, nonce=nonce)
        ).run()
        return {"nonce": nonce}

    @post("/register")
    async def register(self, data: LoginPayload, jwt_auth: JWTCookieAuth) -> Response:
        # 1. Retrieve the pending challenge
        challenge = await AuthChallenge.objects().where(
            AuthChallenge.public_key == data.public_key
        ).order_by(AuthChallenge.created_at, ascending=False).first().run()

        if not challenge:
            raise NotFoundException("No pending challenge found. Request one first.")

        # 2. Verify Cryptography
        try:
            verify_key_bytes = bytes.fromhex(data.public_key)
            signature_bytes = bytes.fromhex(data.signature)
            message_bytes = challenge.nonce.encode('utf-8')

            verify_key = VerifyKey(verify_key_bytes)
            verify_key.verify(message_bytes, signature_bytes)
        except (BadSignatureError, ValueError):
            raise NotAuthorizedException("Invalid Signature")

        # 3. Cleanup
        await AuthChallenge.delete().where(AuthChallenge.id == challenge.id).run()

        # 4. Check/Create User
        user = await User.objects().get(User.public_key == data.public_key).run()
        if not user:
            user = User(public_key=data.public_key)
            await user.save().run()

        # 5. Issue Cookie
        response = jwt_auth.login(identifier=user.public_key)
        return Response(
            content={"message": "Logged in!", "user": user.public_key},
            cookies=response.cookies,
            status_code=HTTP_201_CREATED
        )

    @get("/me")
    async def user_profile(self, request: Request) -> dict[str, Any]:
        if not request.user:
             raise NotAuthorizedException()
        return {
            "my_public_key": request.user.public_key,
        }

class BoardController(Controller):
    path = "/"

    @get("/")
    async def list_boards(self, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        offset = (page - 1) * limit
        boards = await Board.select().limit(limit).offset(offset).run()
        return boards

    @get("/boards/{board_id:int}")
    async def list_threads(self, board_id: int, page: int = 1, limit: int = 20) -> List[Dict[str, Any]]:
        if not await Board.exists().where(Board.id == board_id).run():
             raise NotFoundException("Board not found")

        offset = (page - 1) * limit
        threads = await Post.select().where(
            (Post.board_id == board_id) & (Post.reply_to_id.is_null())
        ).order_by(Post.created_at, ascending=False).limit(limit).offset(offset).run()
        return threads

    @post("/boards/{board_id:int}")
    async def create_thread(self, board_id: int, data: CreateThreadPayload, request: Request) -> Dict[str, Any]:
        if not request.user:
             raise NotAuthorizedException()

        if not await Board.exists().where(Board.id == board_id).run():
            raise NotFoundException("Board not found")

        post = Post(
            board_id=board_id,
            author_pubkey=request.user.public_key,
            title=data.title,
            content=data.content
        )
        await post.save().run()
        return post.to_dict()

class ThreadController(Controller):
    path = "/threads"

    @get("/{thread_id:int}")
    async def view_thread(self, thread_id: int) -> List[Dict[str, Any]]:
        op = await Post.objects().get(Post.id == thread_id).run()
        if not op:
            raise NotFoundException("Thread not found")

        # Recursive query to fetch entire thread tree (no pagination for now)
        query = "WITH RECURSIVE thread_posts AS ( SELECT * FROM post WHERE id = {} UNION ALL SELECT p.* FROM post p JOIN thread_posts tp ON p.reply_to_id = tp.id ) SELECT * FROM thread_posts;".format(thread_id)

        results = await Post.raw(query).run()
        return results

    @post("/{thread_id:int}")
    async def reply_to_thread(self, thread_id: int, data: CreateReplyPayload, request: Request) -> Dict[str, Any]:
        if not request.user:
             raise NotAuthorizedException()

        parent_post = await Post.objects().get(Post.id == thread_id).run()
        if not parent_post:
            raise NotFoundException("Thread/Post not found")

        reply = Post(
            board_id=parent_post.board_id,
            author_pubkey=request.user.public_key,
            reply_to_id=thread_id,
            content=data.content
        )
        await reply.save().run()
        return reply.to_dict()
