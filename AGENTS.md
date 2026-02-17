# BBS Server

This repository contains the server  and client applications for our bbs forum
system

Server is at `bbs/`
Client is at `bbs_client/`

Both should be developed together.

## BBS Server

Its objective is to provide a forum-like experience both with information
exchange and privacy in mind to overcome censorship.

Users can easily change identity if necessary.

Python libraries and technologies useda for this server currently are:

* [python](https://www.python.org/) language
* [litestar](https://github.com/litestar-org/litestar) (handling the backend api)
* [piccolo orm](https://github.com/piccolo-orm/piccolo) (handling sqlite3 to persist data)
* [pynacl](https://github.com/pyca/pynacl) (handling user credentials)
* [click](https://github.com/pallets/click) (handling command-line options)
* sqlite (handling database)

### Key concepts

* User credentials will be self-created Ed25519 keys, using PyNaCl library.
* Registering an account will be based in Challenge-Response based on
  user's public key (provided by him to the server) and his signature
  of a Challenge provided the server by using his private key, 
* Login will be based on a similar fashion as registering.

#### Components & Terminology

* **Server:** The entry python process (Litestar app).
* **Site:** An instance of the BBS. A server may host multiple Sites (e.g., `/vim`, `/politics`) or just one at root (`/`).
* **Board:** A category within a Site (e.g., "General Discussion", "Announcements").
* **Thread:** A collection of posts starting with an Opening Post (OP).
* **Post:** An atomic piece of content. 
    * If `reply_to_id` is NULL, it is an Opening Post (start of a Thread).
    * If `reply_to_id` is set, it is a Reply.

#### Data Model

* Being implemented in `bbs_server/tables.py`

#### API Endpoints

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

4. **Real-time (WebSockets)**
   * `WS /ws`: WebSocket endpoint.
     * Clients connect to receive real-time JSON events (e.g., `{"type": "new_post", "board_id": 1}`).
     * Server broadcasts messages to connected clients when new content is created.

List endpoints (Boards, Threads) should support pagination (e.g., ``?page=1&limit=20`).

The API router handles the site context. If accessing https://bbs.org/vim/, the {site_slug} is 'vim'.

#### Implementation Notes for Agents

* **Core Patch:** `bbs/core.py` includes a runtime patch for `litestar.security.jwt.auth` to fix type hint evaluation issues. Do not remove this block unless the underlying Litestar dependency is updated to a version that resolves it.
* **Database Strategy:** The `BBS` class manages multi-tenancy by dynamically binding SQLite engines to tables using the naming convention `db-{uri}.sqlite`. Persistence is instance-specific.
* **Routing Logic:** The application uses an `app_factory`. If only one instance is configured, it mounts to root (`/`). If multiple exist, they are mounted at `/{instance_name}`.

#### Feature Status Tracker

* **Data Model:** Implemented as described in `bbs/tables.py`.
* **Auth Flow:** Implemented (Challenge-Response + JWT Cookies) in `bbs/routes.py` and `bbs/core.py`.
* **WebSockets:** Planned. Current client code references a notification endpoint that is not yet implemented on the server.
* **API Endpoints:** `GET /user/{public_key}` and pagination parameters are currently placeholders and require implementation in `BoardController` and `UserController`.

## BBS Client

This repository contains the client application for the server at https://github.com/iacchus/bbs

It is a TUI (text-user-interface) client written in python using Textual library.

Its objective is to provide a forum-like experience on the Linux terminal.

Python libraries and technologies used are:

* [python](https://www.python.org/) language
* [textual](https://github.com/textualize/textual/) (handling the text user interface)
* [httpx](https://github.com/encode/httpx/) (handling http, https requests)
* [websockets](https://github.com/python-websockets/websockets) (handling real-time updates)
* [piccolo orm](https://github.com/piccolo-orm/piccolo) (handling sqlite3 to persist data)
* sqlite3
* [pynacl](https://github.com/pyca/pynacl) (handling user credentials)
* [click](https://github.com/pallets/click) (handling command-line options)

### Key Concepts

* **Async Architecture:** The client uses `httpx` to communicate with the server asynchronously, ensuring the `Textual` UI never freezes during network operations.
* **Local Identity:** User credentials (Ed25519 keys) are generated and stored locally in the client's SQLite database.
* **Server Management:** The client can store multiple server addresses (bookmarks) and multiple identities (keys), allowing the user to switch between them.
* **Real-time UI Updates:** The client maintains a background WebSocket connection to the server's `/ws/notifications` endpoint. When the server broadcasts an event (like a new reply in the currently viewed thread), Textual reacts by showing a notification badge or auto-fetching the new data via REST.

### Screens & UI Flow

#### 1. Connection Manager (formerly Login Screen)
This is the entry point. It handles:
* **Server Selection:** Choose a saved server or add a new URL.
* **Identity Selection:** Choose an existing Profile (Keys) or generate a new one.
* *Action:* Once a Server and Identity are selected, the user enters the `Board List`.

#### 2. Board List (Home)
* Displays a list of all boards available on the selected server.
* *Navigation:* Select a board to enter the `Thread List`.

#### 3. Thread List (Board View)
* Displays the list of threads (Opening Posts) for the selected board.
* Shows metadata: Title, Author, Date, Reply Count.
* *Action:* Press `c` (or similar) to open the `Compose Modal` and create a new thread.

#### 4. Thread View (Post View)
* Displays the Opening Post (OP) followed by a tree/list of replies.
* *Action:* Press `r` on any post to open the `Compose Modal` and reply to that specific post.

#### 5. Compose Modal
* A pop-up dialog or dedicated screen for writing content (Markdown supported).
* Used for both creating new threads and writing replies.

