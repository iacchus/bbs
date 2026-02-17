# BBS Server

This repository contains the server application for the client at
https://github.com/iacchus/bbs-client

Both should be developed together, this is, keeping the same pace, despite the
fact the client is a refence implementation as the protocol we're developing
will be open to diverse implementations.

This bbs is also only the reference implementation to our bbs/forum protocol.

Its objective is to provide a forum-like experience both with information
exchange and privacy in mind to overcome censorship.

Users can easily change identity if necessary.

Python libraries and technologies useda for this server currently are:

* [python](https://www.python.org/) language
* [litestar](https://github.com/litestar-org/litestar) (handling the backend api)
* [piccolo orm](https://github.com/piccolo-orm/piccolo) (handling sqlite3 to persist data)
* [pynacl](https://github.com/pyca/pynacl) (handling user credentials)
* [click](https://github.com/pallets/click) (handling command-line options)

## Key concepts

* User credentials will be self-created Ed25519 keys, using PyNaCl library.
* Registering an account will be based in Challenge-Response based on
  user's public key (provided by him to the server) and his signature
  of a Challenge provided the server by using his private key, 
* Login will be based on a similar fashion as registering.

### Components & Terminology

* **Server:** The entry python process (Litestar app).
* **Site:** An instance of the BBS. A server may host multiple Sites (e.g., `/vim`, `/politics`) or just one at root (`/`).
* **Board:** A category within a Site (e.g., "General Discussion", "Announcements").
* **Thread:** A collection of posts starting with an Opening Post (OP).
* **Post:** An atomic piece of content. 
    * If `reply_to_id` is NULL, it is an Opening Post (start of a Thread).
    * If `reply_to_id` is set, it is a Reply.

### Data Model (Proposed)

* **User:** `public_key` (PK), `username` (optional).
* **Board:** `id`, `slug`, `name`, `description`.
* **Post:** `id`, `board_id` (FK), `author_pubkey` (FK), `reply_to_id` (FK, nullable), `content`, `created_at`.

### API Endpoints

The API should follow RESTful conventions where possible:

1. **Sites & Boards**
   * `GET /` (or `/{site_slug}/`): List available Boards.
   * `GET /boards/{board_id}`: List Threads (OPs) for a specific board.

2. **Threads & Posts**
   * `POST /boards/{board_id}`: Create a new Thread.
   * `GET /threads/{thread_id}`: View a Thread (OP + recursive replies).
   * `POST /threads/{thread_id}`: Reply to a thread.

3. **Users & Auth**
   * `GET /user/request_challenge/{public_key}`: Step 1 of auth.
   * `POST /user/register`: Step 2 of auth (Submit signed challenge).
   * `GET /user/me`: Get current session info.
   * `GET /user/{public_key}`: Get public profile of another user.
