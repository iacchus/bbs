from piccolo.table import Table, create_db_tables_sync
from piccolo.columns import Varchar, Text, Serial
from piccolo.engine.sqlite import SQLiteEngine
import os

DB_FILE = "client_data.sqlite"
engine = SQLiteEngine(path=DB_FILE)

class IdentityRecord(Table, db=engine, tablename="identities"):
    id = Serial(primary_key=True)
    name = Varchar(length=100)
    private_key = Varchar(length=128, unique=True) # Hex encoded
    public_key = Varchar(length=64, unique=True) # Hex encoded

class ServerRecord(Table, db=engine, tablename="servers"):
    id = Serial(primary_key=True)
    url = Varchar(length=200, unique=True)
    name = Varchar(length=100, null=True)

def init_db():
    try:
        create_db_tables_sync(IdentityRecord, ServerRecord, if_not_exists=True)
    except Exception as e:
        print(f"Error initializing DB: {e}")

# Convenience functions
async def get_all_identities():
    results = await IdentityRecord.objects()
    if results and isinstance(results[0], dict):
        return [IdentityRecord(**r) for r in results]
    return results

async def add_identity(name: str, private_key: str, public_key: str):
    await IdentityRecord(name=name, private_key=private_key, public_key=public_key).save()

async def get_all_servers():
    return await ServerRecord.objects()

async def add_server(url: str, name: str = None):
    # Check if exists
    exists = await ServerRecord.exists().where(ServerRecord.url == url)
    if not exists:
        await ServerRecord(url=url, name=name or url).save()
