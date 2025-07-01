import os
import sqlite3
from dotenv import load_dotenv
from passlib.context import CryptContext

load_dotenv()


DB_PATH = os.environ.get("TICTAC_DB_PATH", "tic_tac_toe.db")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db():
    """Yields a SQLite connection (for simplicity). Substitute for other DBs as needed."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hashes a password."""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a given hash."""
    return pwd_context.verify(plain_password, hashed_password)
