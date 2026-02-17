# BBS Client

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

#### Components' Longer Description...

... and further conceptual development

##### `server`

A `server` runs at an IP address and a port. A server is a set of one or more
sites.

Any server can run:

1. one site only
2. multiple sites

As an example of multiple sites, this is like Stack Exchange which has various
sites, about different subjects, "buddhism", "vim" etc, that are independent
from each other.)

##### `site` or `sites`

A `site` is an instance of `BBS` class.

About the number of sites a server has:

1. If a `server` has only one `site`, that instance is mounted at its root
  path, `/`, for example, at `https://<SERVER_ADDRESS>:<SERVER_PORT>/`.
2. If a `server` has two or more `site`s, let's call them, as an example, by
  uris "site1" and "anothersite", they will be mounted at:
  * "site1" will be mounted at: `https://<SERVER_ADDRESS>:<SERVER_PORT>/site1/`
  * "anothersite" will be mounted at:
    `https://<SERVER_ADDRESS>:<SERVER_PORT>/anothersite/`
  Each will run it's own, independent, `BBS` instance, but in the same
  `server`.
  Each one is an independent bbs/forum/`site`.

##### `boards`

`boards` is the home of a `site`. Just like in any common forum, it lists the
boards existing on that site/bbs/forum.

##### `board`

The `board` component is also common to any forum: it is a list of
OPs (opening posts) in that board.

##### `post`

FIXME: we need to change the name of the `post` component because "post" should
be valid for "opening posts" as well as for "replies" (comments or
`post_item`s)

The `post` component is also common to any forum: it is a opening post with its
replies, comments.

##### `post_item`

Any opening post or reply item.

An opening post has the database column `reply_to` set to 0, while the reply
has the column `reply_to` set to parent post `id`. Maybe the name of this
column should be changed.

##### `user`

A `user` is represented by a registered public key, which registered by
replying correctly signing a Challenge-Response test providaded by the server
(`site`).

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
