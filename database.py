import uuid
import pymysql
from datetime import datetime, timezone


def generate_uuid():
    return str(uuid.uuid4())


DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "your_password",
    "database": "water_tracker",
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.DictCursor,
}


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


if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully.")