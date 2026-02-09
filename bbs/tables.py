from piccolo.table import Table
from piccolo.columns import Varchar, Timestamp, Text, Serial
from piccolo.engine.sqlite import SQLiteEngine
import datetime

DB_FILE = "whaT.sqlite"
db = SQLiteEngine(path=DB_FILE)
#  db = SQLiteEngine(file=DB_FILE)

class User(Table, db=db):
    # The Public Key (in Hex format) is the unique ID
    public_key = Varchar(length=64, unique=True, primary_key=True)
    username = Varchar(length=50, null=True) # Optional display name

class AuthChallenge(Table, db=db):
    """Stores temporary nonces to prevent replay attacks."""
    #  id = Serial(primary_key=True)
    public_key = Varchar(length=64)
    nonce = Varchar(length=64) # The random string they must sign
    created_at = Timestamp(default=datetime.datetime.now)
