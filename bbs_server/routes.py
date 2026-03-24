import secrets
from typing import Any, List, Dict
from litestar import Controller, get, post, Request, Response
from litestar.exceptions import NotFoundException, NotAuthorizedException, HTTPException
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

class CreateBoardPayload(BaseModel):
    name: str
    description: str
    slug: str


# Controllers

class UpdateProfilePayload(BaseModel):
    username: str | None = None

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
            # First user becomes admin
            has_users = await User.exists().run()
            role = 'admin' if not has_users else 'user'
            user = User(public_key=data.public_key, role=role)
            await user.save().run()

        # 5. Issue Cookie
        response = jwt_auth.login(identifier=user.public_key)
        return Response(
            content={"message": "Logged in!", "user": user.public_key, "role": user.role},
            cookies=response.cookies,
            status_code=HTTP_201_CREATED
        )

    @get("/me")
    async def get_me(self, request: Request) -> dict[str, Any]:
        if not request.user:
            raise NotAuthorizedException()
        user = await User.objects().get(User.public_key == request.user.public_key).run()
        return {
            "public_key": user.public_key,
            "role": user.role,
            "username": user.username
        }

    @get("/{public_key:str}")
    async def get_user_profile(self, public_key: str) -> dict[str, Any]:
        user = await User.objects().get(User.public_key == public_key).run()
        if not user:
            raise NotFoundException("User not found")
        return {
            "public_key": user.public_key,
            "role": user.role,
            "username": user.username
        }

    @post("/me")
    async def update_profile(self, data: UpdateProfilePayload, request: Request) -> dict[str, Any]:
        if not request.user:
            raise NotAuthorizedException()
        
        user = await User.objects().get(User.public_key == request.user.public_key).run()
        if not user:
            raise NotFoundException("User not found")

        if data.username is not None:
            import re
            if data.username != "" and not re.match(r'^[a-zA-Z0-9\-_]+$', data.username):
                raise HTTPException(detail="Username can only contain ASCII alphanumeric characters, hyphens, and underscores.", status_code=400)
            
            if data.username == "":
                user.username = None
            else:
                # Check if username is taken by someone else
                existing = await User.objects().get(User.username == data.username).run()
                if existing and existing.public_key != user.public_key:
                    raise HTTPException(detail="Username is already taken.", status_code=409)
                
                user.username = data.username
        
        await user.save().run()
        return {
            "public_key": user.public_key,
            "role": user.role,
            "username": user.username
        }

class BoardController(Controller):
    path = "/"


    @post("/")
    async def create_board(self, data: CreateBoardPayload, request: Request) -> Dict[str, Any]:
        if not request.user or request.user.role != 'admin':
            raise NotAuthorizedException("Only admins can create boards")

        if await Board.exists().where(Board.slug == data.slug).run():
            raise HTTPException(detail="Board with this slug already exists", status_code=409)

        board = Board(
            name=data.name,
            description=data.description,
            slug=data.slug
        )
        await board.save().run()
        return board.to_dict()

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
        threads = await Post.select(
            Post.all_columns(),
            Post.author_pubkey.username.as_alias("author_username")
        ).where(
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

    #  @post("/boards/{board_id:int}")
    #  async def create_thread(self, board_id: int, data: CreateThreadPayload, request: Request) -> Dict[str, Any]:
    #      if not request.user:
    #           raise NotAuthorizedException()
    #
    #      if not await Board.exists().where(Board.id == board_id).run():
    #          raise NotFoundException("Board not found")
    #
    #      post = Post(
    #          board_id=board_id,
    #          author_pubkey=request.user.public_key,
    #          title=data.title,
    #          content=data.content
    #      )
    #      await post.save().run()
    #      return post.to_dict()

class ThreadController(Controller):
    path = "/threads"

    @get("/{thread_id:int}")
    async def view_thread(self, thread_id: int) -> List[Dict[str, Any]]:
        op = await Post.objects().get(Post.id == thread_id).run()
        if not op:
            raise NotFoundException("Thread not found")

        # Recursive query to fetch entire thread tree (no pagination for now)
        query = """WITH RECURSIVE thread_posts AS (
            SELECT p.*, u.username as author_username FROM post p JOIN "user" u ON p.author_pubkey = u.public_key WHERE p.id = {}
            UNION ALL
            SELECT p.*, u.username as author_username FROM post p JOIN thread_posts tp ON p.reply_to_id = tp.id JOIN "user" u ON p.author_pubkey = u.public_key
        ) SELECT * FROM thread_posts;""".format(thread_id)

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
