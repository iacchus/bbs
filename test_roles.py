import asyncio
import os
import sys
from bbs_client.api import BBSClient
from bbs_client.auth import generate_identity
from bbs_server.core import BBS
import httpx

async def test_roles():
    # 1. Start Server
    instance_name = "test-roles"
    db_file = f"db-{instance_name}.sqlite"
    if os.path.exists(db_file):
        os.remove(db_file)

    bbs = BBS(instance=instance_name)
    # We'll run the Litestar app in a separate task or just use a mock client if possible.
    # But since we want to test the full flow, let's try to use httpx with the app.

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=bbs.api), base_url="http://testserver") as client:
        # 2. Register First User (Admin)
        admin_id = generate_identity("Admin")
        
        # Step 1: Request Challenge
        resp = await client.get(f"/user/request_challenge/{admin_id.public_key}")
        nonce = resp.json()["nonce"]
        
        # Step 2: Register
        signature = admin_id.sign(nonce)
        resp = await client.post("/user/register", json={
            "public_key": admin_id.public_key,
            "signature": signature
        })
        print(f"Admin Register Response: {resp.status_code}, Role: {resp.json().get('role')}")
        assert resp.status_code == 201
        assert resp.json()["role"] == "admin"
        
        admin_cookies = resp.cookies

        # 3. Register Second User (User)
        user_id = generate_identity("User")
        
        # Step 1: Request Challenge
        resp = await client.get(f"/user/request_challenge/{user_id.public_key}")
        nonce = resp.json()["nonce"]
        
        # Step 2: Register
        signature = user_id.sign(nonce)
        resp = await client.post("/user/register", json={
            "public_key": user_id.public_key,
            "signature": signature
        })
        print(f"User Register Response: {resp.status_code}, Role: {resp.json().get('role')}")
        assert resp.status_code == 201
        assert resp.json()["role"] == "user"
        
        user_cookies = resp.cookies

        # 4. Test Board Creation (Admin should succeed)
        resp = await client.post("/", json={
            "name": "Admin Board",
            "description": "Created by admin",
            "slug": "admin-board"
        }, cookies=admin_cookies)
        print(f"Admin Create Board: {resp.status_code}")
        assert resp.status_code == 201

        # 5. Test Board Creation (User should fail)
        resp = await client.post("/", json={
            "name": "User Board",
            "description": "Created by user",
            "slug": "user-board"
        }, cookies=user_cookies)
        print(f"User Create Board: {resp.status_code}, Detail: {resp.json().get('detail')}")
        assert resp.status_code == 401 # NotAuthorizedException defaults to 401
        assert resp.json()["detail"] == "Only admins can create boards"

    print("Role-based authorization test passed!")
    if os.path.exists(db_file):
        os.remove(db_file)

if __name__ == "__main__":
    asyncio.run(test_roles())
