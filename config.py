import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-water-tracker-secret-key-2026")
    # DB connection is configured via env vars in database.py (TIDB_HOST, TIDB_PORT, etc.)
