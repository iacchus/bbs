# BBS Client

This repository contains the server application for the client at
https://github.com/iacchus/bbs-client

Both should be developed together, this is, keeping the same pace, despite the
fact the client is a refence implementation as the protocol we're developing
will be open to diverse implementation.

This bbs is also the reference implementation to our bbs/forum protocol.

Its objective is to provide a forum-like experience  both with information
exchange and privacy in mind.

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

## Key concepts

### Components

We have, conceptually, components like (with short comments):

* server (entry python process server running on ip/port)
* sites - given `subject` inside server
* boards - organization of a size; boards like any forum
* board - list of topics, like any forum
* post - opening post plus replies and replies of replies, like any forum
* post\_item (or opening post or reply, both are post items; atomic) 
* user - identity represented by its public key

### API Endpoints

Endpoints can somewhat reflect the user experience in bbs-client :) 

We need to think in better names for some (or all) of these:

* login/register
* sites - server; if server has more than 1 site (as an example, this is like Stack Exchange which has various sites, about different subjects, "buddhism", "vim" etc.) This is disabled if the server has only 1 site.
* boards - list of boards inside a site,
* board
* post
* item

#### API Endpoints Longer Description...

... and further conceptual development

After the user connected to a server the first time and have credentials and
a server registered locally, it will automatically enter the server and not
be shown the `Login Screen` automatically as in the first tine.

## Screens

These are screens we have to develop in the app to begin with (we may change the
design later, as it goes):

* `Login Screen` - Already described in "Logging In"
* `Boards Screen` - Shows all the boards of the Site
* `Board Screen` - Shows the opening posts from a specific board, shows the
  posting date, the user who posted and the number of replies, both direct
  replies (replies to the OP) and thread replies (replies to replies)
* `Post Screen` - Shows the OP and replies and theads of replies (replies to
  replies), the discussion itself
* `User Screen` - Shows the user's profile screen, public info etc. Allows
  to change info if it's the own user's `User Screen`, just like a web forum
  or a social nerwork.

