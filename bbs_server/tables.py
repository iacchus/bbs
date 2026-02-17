import datetime
from piccolo.table import Table
from piccolo.columns import Varchar, Timestamp, Text, Serial, ForeignKey

class User(Table):
    """
    Represents a user in the system.
    The Public Key (in Hex format) is the unique ID.
    """
    public_key = Varchar(length=64, unique=True, primary_key=True)
    username = Varchar(length=50, null=True) # Optional display name

class AuthChallenge(Table):
    """Stores temporary nonces to prevent replay attacks."""
    id = Serial(primary_key=True)
    public_key = Varchar(length=64)
    nonce = Varchar(length=64) # The random string they must sign
    created_at = Timestamp(default=datetime.datetime.now)

class Board(Table):
    """
    Represents a discussion board (category).
    """
    id = Serial(primary_key=True)
    slug = Varchar(length=50, unique=True)
    name = Varchar(length=100)
    description = Text()

class Post(Table):
    """
    Represents a post (either an OP or a reply).
    """
    id = Serial(primary_key=True)
    board_id = ForeignKey(references=Board)
    author_pubkey = ForeignKey(references=User)
    # Self-referential FK for replies
    reply_to_id = ForeignKey(references='Post', null=True)
    title = Varchar(length=200, null=True) # Nullable for replies
    content = Text()
    created_at = Timestamp(default=datetime.datetime.now)
