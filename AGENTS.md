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

### Components

We have, conceptually, components like (with short comments):

* `server` - entry python process server running on ip/port
* `site` or `sites` - given `subject` inside server
* `boards` - organization of a size; list boards like any forum
* `board` - list of topics, like any forum
* `post` - opening post plus replies and replies of replies, like any forum
* `post_item` - or opening post or reply, both are post items; atomic
* `user` - identity represented by its public key
* `data` - bytes, number\_of\_bytes, name (uri) and a mimetype (optional) -
  **not to be implemented now**

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

Endpoints can somewhat reflect the user experience in bbs-client :) 

We need to think in better names for some (or all) of these:

* sites 
* boards
* board
* post
* item
* user
* login/register

#### API Endpoints Longer Description...

... and further conceptual development

##### sites 

The base of a site; 

###### `/`

if the `server` has only one `site`

###### `/<UNIQUE_SITE_ID>/`

if the `server` has multiple `site`s (multisite)

##### boards

`boards` is mounted on the root of each site, as it is its "home", so as above.

##### board

###### `/board`

Maybe there is a more fitting name than this, let's find out.

This lists all `post_item`s which `reply_to` is None (null, or 0) and
`board_id` is this boards `id`

##### posts

###### `/post`

Find a good name for this endpoint/component.

##### post item

##### users

###### `/user`

Own user.

###### `/user/{id:str}`

Another user.

##### login/register

###### `/login` endpoint

##### data or file

###### `/data` - **not to be implemented now**
