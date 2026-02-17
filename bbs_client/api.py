import httpx
from typing import List, Dict, Any, Optional
from .auth import Identity

class BBSClient:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.identity: Optional[Identity] = None

    async def close(self):
        await self.client.aclose()

    async def login(self, identity: Identity) -> bool:
        """Perform challenge-response authentication."""
        self.identity = identity
        pub_key = identity.public_key

        try:
            # 1. Request Challenge
            resp = await self.client.get(f"/user/request_challenge/{pub_key}")
            resp.raise_for_status()
            nonce = resp.json().get("nonce")

            if not nonce:
                return False

            # 2. Sign Challenge
            signature = identity.sign(nonce)

            # 3. Submit Response
            payload = {"public_key": pub_key, "signature": signature}
            resp = await self.client.post("/user/register", json=payload)
            resp.raise_for_status()

            return True
        except Exception as e:
            print(f"Login failed: {e}")
            return False

    async def get_boards(self) -> List[Dict[str, Any]]:
        try:
            # Server lists boards at root "/"
            resp = await self.client.get("/")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Failed to get boards: {e}")
            return []

    async def create_board(self, name: str, description: str) -> Dict[str, Any]:
        try:
            payload = {"name": name, "description": description}
            # Attempt to create a board using a standard REST endpoint.
            # If the server endpoint is different, this needs to be updated.
            resp = await self.client.post("/boards", json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Failed to create board: {e}")
            # Raising exception to let the caller handle it (e.g. notify user)
            raise e

    async def get_threads(self, board_id: int) -> List[Dict[str, Any]]:
        try:
            resp = await self.client.get(f"/boards/{board_id}")
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            print(f"Failed to get threads: {e}")
            return []

    async def create_thread(self, board_id: int, title: str, content: str) -> Dict[str, Any]:
        # POST /boards/{board_id}
        payload = {"title": title, "content": content}
        resp = await self.client.post(f"/boards/{board_id}", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_thread(self, thread_id: int) -> Dict[str, Any]:
        try:
            # GET /threads/{thread_id} returns List[Dict] (recursive)
            resp = await self.client.get(f"/threads/{thread_id}")
            resp.raise_for_status()
            posts = resp.json()

            # Find the OP (id == thread_id)
            op = next((p for p in posts if p["id"] == thread_id), None)
            if not op:
                return {}

            # Remove OP from posts list
            replies = [p for p in posts if p["id"] != thread_id]

            return {"thread": op, "posts": replies}
        except Exception as e:
            print(f"Failed to get thread: {e}")
            return {}

    async def create_post(self, thread_id: int, content: str, parent_id: int = None) -> Dict[str, Any]:
        # POST /threads/{thread_id}
        # Note: server expects `thread_id` in path to be the `reply_to_id`.
        # So if we are replying to a specific post, `thread_id` argument here should be that post's ID.
        # If `parent_id` is provided, we should probably use that as the target.
        target_id = parent_id if parent_id else thread_id

        payload = {"content": content}
        resp = await self.client.post(f"/threads/{target_id}", json=payload)
        resp.raise_for_status()
        return resp.json()
