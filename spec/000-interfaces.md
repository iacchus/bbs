# interfaces

bbs can have different frontpage *interfaces*:

* **server**/sites
* site/**boards**
* board/post (post list)
  * topic list/**board** (link to *topic post* interface with it's  *replies*)
  * ~~*posts*/**announcements** post list (topic text list with no replies, open, *ie*., not links to another interface)~~ (not at first—maybe later.)
* **post**/topic (opening post and replies)

interface data is sent from the server via JSON so the clients know how to mount it:

```
{'interfaces': 'board'}
```


