import uuid
from datetime import datetime, timezone
import json
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    age = db.Column(db.Integer, nullable=False, default=25)
    sex = db.Column(db.String(20), nullable=False, default='prefer_not_to_say')
    activity_level = db.Column(db.String(30), nullable=False, default='sedentary')
    environment_preference = db.Column(db.String(30), nullable=False, default='indoors')
    pregnancy_status = db.Column(db.String(30), nullable=False, default='neither')
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "age": self.age,
            "sex": self.sex,
            "activity_level": self.activity_level,
            "environment_preference": self.environment_preference,
            "pregnancy_status": self.pregnancy_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class Bottle(db.Model):
    __tablename__ = 'bottles'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), default="My Water Bottle")
    capacity_ml = db.Column(db.Integer, nullable=False, default=750)
    current_volume_ml = db.Column(db.Integer, nullable=False, default=750)
    theme = db.Column(db.String(30), default="ocean_blue")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "capacity_ml": self.capacity_ml,
            "current_volume_ml": self.current_volume_ml,
            "theme": self.theme,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class HydrationTarget(db.Model):
    __tablename__ = 'hydration_targets'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    target_ml = db.Column(db.Integer, nullable=False)
    calculation_version = db.Column(db.String(20), nullable=False, default="v1")
    research_basis = db.Column(db.String(100), nullable=False)
    profile_snapshot = db.Column(db.Text, nullable=False) # JSON string
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "target_ml": self.target_ml,
            "calculation_version": self.calculation_version,
            "research_basis": self.research_basis,
            "profile_snapshot": json.loads(self.profile_snapshot) if self.profile_snapshot else {},
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class DrinkEvent(db.Model):
    __tablename__ = 'drink_events'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    bottle_id = db.Column(db.String(36), db.ForeignKey('bottles.id'), nullable=True)
    amount_ml = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    source = db.Column(db.String(30), default="quick_add") # quick_add, glass, custom

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bottle_id": self.bottle_id,
            "amount_ml": self.amount_ml,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source
        }

class RefillEvent(db.Model):
    __tablename__ = 'refill_events'

    id = db.Column(db.String(36), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    bottle_id = db.Column(db.String(36), db.ForeignKey('bottles.id'), nullable=False)
    amount_added_ml = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "bottle_id": self.bottle_id,
            "amount_added_ml": self.amount_added_ml,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None
        }

class NotificationPreference(db.Model):
    __tablename__ = 'notification_preferences'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), primary_key=True)
    enabled = db.Column(db.Boolean, default=True)
    start_time = db.Column(db.String(10), default="08:00")
    end_time = db.Column(db.String(10), default="22:00")
    frequency_minutes = db.Column(db.Integer, default=120)
    quiet_hours = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "enabled": self.enabled,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "frequency_minutes": self.frequency_minutes,
            "quiet_hours": self.quiet_hours
        }
