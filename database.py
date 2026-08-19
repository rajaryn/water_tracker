import os
import uuid
import pymysql
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()


def generate_uuid():
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# DB connection config - reads the same env vars as config.py
# ---------------------------------------------------------------------------
_host = os.getenv("TIDB_HOST") or os.getenv("DB_HOST", "localhost")
_port = int(os.getenv("TIDB_PORT") or os.getenv("DB_PORT", "3306"))
_user = os.getenv("TIDB_USER") or os.getenv("DB_USER", "root")
_password = os.getenv("TIDB_PASSWORD") or os.getenv("DB_PASSWORD", "")
_database = os.getenv("TIDB_DB") or os.getenv("DB_NAME", "water_tracker")
_ssl_ca = os.getenv("TIDB_SSL_CA", "")

DB_CONFIG = {
    "host": _host,
    "port": _port,
    "user": _user,
    "password": _password,
    "database": _database,
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}

if _ssl_ca:
    DB_CONFIG["ssl"] = {"ca": _ssl_ca}


def get_connection():
    return pymysql.connect(**DB_CONFIG)


def create_tables():
    connection = get_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(36) PRIMARY KEY,
                    age INT NOT NULL DEFAULT 25,
                    sex VARCHAR(20) NOT NULL DEFAULT 'prefer_not_to_say',
                    activity_level VARCHAR(30) NOT NULL DEFAULT 'sedentary',
                    environment_preference VARCHAR(30) NOT NULL DEFAULT 'indoors',
                    pregnancy_status VARCHAR(30) NOT NULL DEFAULT 'neither',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS bottles (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    name VARCHAR(50) DEFAULT 'My Water Bottle',
                    capacity_ml INT NOT NULL DEFAULT 750,
                    current_volume_ml INT NOT NULL DEFAULT 750,
                    theme VARCHAR(30) DEFAULT 'ocean_blue',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP,
                    CONSTRAINT fk_bottles_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS hydration_targets (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    target_ml INT NOT NULL,
                    calculation_version VARCHAR(20) NOT NULL DEFAULT 'v1',
                    research_basis VARCHAR(100) NOT NULL,
                    profile_snapshot JSON NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_hydration_targets_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS drink_events (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    bottle_id VARCHAR(36),
                    amount_ml INT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    source VARCHAR(30) DEFAULT 'quick_add',
                    CONSTRAINT fk_drink_events_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_drink_events_bottle
                        FOREIGN KEY (bottle_id)
                        REFERENCES bottles(id)
                        ON DELETE SET NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS refill_events (
                    id VARCHAR(36) PRIMARY KEY,
                    user_id VARCHAR(36) NOT NULL,
                    bottle_id VARCHAR(36) NOT NULL,
                    amount_added_ml INT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_refill_events_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE,
                    CONSTRAINT fk_refill_events_bottle
                        FOREIGN KEY (bottle_id)
                        REFERENCES bottles(id)
                        ON DELETE CASCADE
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS notification_preferences (
                    user_id VARCHAR(36) PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    start_time VARCHAR(10) DEFAULT '08:00',
                    end_time VARCHAR(10) DEFAULT '22:00',
                    frequency_minutes INT DEFAULT 120,
                    quiet_hours BOOLEAN DEFAULT TRUE,
                    CONSTRAINT fk_notification_preferences_user
                        FOREIGN KEY (user_id)
                        REFERENCES users(id)
                        ON DELETE CASCADE
                )
            """)

        connection.commit()
    finally:
        connection.close()


# ---------------------------------------------------------------------------
# Plain-Python model classes - no ORM, just data containers with helpers
# ---------------------------------------------------------------------------

class User:
    def __init__(self, id=None, age=25, sex="prefer_not_to_say",
                 activity_level="sedentary", environment_preference="indoors",
                 pregnancy_status="neither", created_at=None, updated_at=None):
        self.id = id or generate_uuid()
        self.age = age
        self.sex = sex
        self.activity_level = activity_level
        self.environment_preference = environment_preference
        self.pregnancy_status = pregnancy_status
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            age=row["age"],
            sex=row["sex"],
            activity_level=row["activity_level"],
            environment_preference=row["environment_preference"],
            pregnancy_status=row["pregnancy_status"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "age": self.age,
            "sex": self.sex,
            "activity_level": self.activity_level,
            "environment_preference": self.environment_preference,
            "pregnancy_status": self.pregnancy_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Bottle:
    def __init__(self, id=None, user_id=None, name="My Water Bottle",
                 capacity_ml=750, current_volume_ml=None, theme="ocean_blue",
                 created_at=None, updated_at=None):
        self.id = id or generate_uuid()
        self.user_id = user_id
        self.name = name
        self.capacity_ml = capacity_ml
        self.current_volume_ml = current_volume_ml if current_volume_ml is not None else capacity_ml
        self.theme = theme
        self.created_at = created_at
        self.updated_at = updated_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            capacity_ml=row["capacity_ml"],
            current_volume_ml=row["current_volume_ml"],
            theme=row["theme"],
            created_at=row.get("created_at"),
            updated_at=row.get("updated_at"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "capacity_ml": self.capacity_ml,
            "current_volume_ml": self.current_volume_ml,
            "theme": self.theme,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class HydrationTarget:
    def __init__(self, id=None, user_id=None, target_ml=None,
                 calculation_version="v1", research_basis="",
                 profile_snapshot="{}", created_at=None):
        self.id = id or generate_uuid()
        self.user_id = user_id
        self.target_ml = target_ml
        self.calculation_version = calculation_version
        self.research_basis = research_basis
        self.profile_snapshot = profile_snapshot
        self.created_at = created_at

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            target_ml=row["target_ml"],
            calculation_version=row["calculation_version"],
            research_basis=row["research_basis"],
            profile_snapshot=row["profile_snapshot"],
            created_at=row.get("created_at"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_ml": self.target_ml,
            "calculation_version": self.calculation_version,
            "research_basis": self.research_basis,
            "profile_snapshot": self.profile_snapshot,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class DrinkEvent:
    def __init__(self, id=None, user_id=None, bottle_id=None,
                 amount_ml=0, timestamp=None, source="quick_add"):
        self.id = id or generate_uuid()
        self.user_id = user_id
        self.bottle_id = bottle_id
        self.amount_ml = amount_ml
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.source = source

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            bottle_id=row.get("bottle_id"),
            amount_ml=row["amount_ml"],
            timestamp=row.get("timestamp"),
            source=row["source"],
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bottle_id": self.bottle_id,
            "amount_ml": self.amount_ml,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
        }


class RefillEvent:
    def __init__(self, id=None, user_id=None, bottle_id=None,
                 amount_added_ml=0, timestamp=None):
        self.id = id or generate_uuid()
        self.user_id = user_id
        self.bottle_id = bottle_id
        self.amount_added_ml = amount_added_ml
        self.timestamp = timestamp or datetime.now(timezone.utc)

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            bottle_id=row["bottle_id"],
            amount_added_ml=row["amount_added_ml"],
            timestamp=row.get("timestamp"),
        )

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bottle_id": self.bottle_id,
            "amount_added_ml": self.amount_added_ml,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class NotificationPreference:
    def __init__(self, user_id=None, enabled=True, start_time="08:00",
                 end_time="22:00", frequency_minutes=120, quiet_hours=True):
        self.user_id = user_id
        self.enabled = enabled
        self.start_time = start_time
        self.end_time = end_time
        self.frequency_minutes = frequency_minutes
        self.quiet_hours = quiet_hours

    @classmethod
    def from_row(cls, row):
        if not row:
            return None
        return cls(
            user_id=row["user_id"],
            enabled=bool(row["enabled"]),
            start_time=row["start_time"],
            end_time=row["end_time"],
            frequency_minutes=row["frequency_minutes"],
            quiet_hours=bool(row["quiet_hours"]),
        )

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "enabled": self.enabled,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "frequency_minutes": self.frequency_minutes,
            "quiet_hours": self.quiet_hours,
        }


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")
