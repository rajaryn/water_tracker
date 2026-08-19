import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-water-tracker-secret-key-2026")
    
    # TiDB Connection setup
    TIDB_HOST = os.getenv("TIDB_HOST")
    TIDB_PORT = int(os.getenv("TIDB_PORT", "4000"))
    TIDB_USER = os.getenv("TIDB_USER", "root")
    TIDB_PASSWORD = os.getenv("TIDB_PASSWORD", "")
    TIDB_DB = os.getenv("TIDB_DB", "water_tracker")
    TIDB_SSL_CA = os.getenv("TIDB_SSL_CA", "")

    if TIDB_HOST:
        # TiDB MySQL connection URI
        ssl_args = f"?ssl_ca={TIDB_SSL_CA}" if TIDB_SSL_CA else ""
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{TIDB_USER}:{TIDB_PASSWORD}@{TIDB_HOST}:{TIDB_PORT}/{TIDB_DB}{ssl_args}"
    else:
        # SQLite fallback for local development / testing
        SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///water_tracker.db")

    SQLALCHEMY_TRACK_MODIFICATIONS = False
