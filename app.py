from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import json
import os

from config import Config
from database import db, User, Bottle, HydrationTarget, DrinkEvent, RefillEvent, NotificationPreference
from recommendation_engine import calculate_hydration_target, CALCULATION_VERSION, RESEARCH_BASIS

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.from_object(Config)
CORS(app)

db.init_app(app)

# Create tables if not present
with app.app_context():
    db.create_all()

# --- Static PWA Routes ---
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/sw.js')
def service_worker():
    return send_from_directory(app.static_folder, 'sw.js', mimetype='application/javascript')

@app.route('/manifest.json')
def manifest():
    return send_from_directory(app.static_folder, 'manifest.json', mimetype='application/json')

# --- API Endpoints ---
@app.route('/api/health', methods=['GET'])
def health():
    db_type = "TiDB" if Config.TIDB_HOST else "SQLite (Fallback)"
    return jsonify({
        "status": "online",
        "database": db_type,
        "engine_version": CALCULATION_VERSION,
        "research_basis": RESEARCH_BASIS
    })

@app.route('/api/recommendation', methods=['POST'])
def get_recommendation():
    profile = request.json or {}
    recommendation = calculate_hydration_target(profile)
    return jsonify(recommendation)

@app.route('/api/profile', methods=['POST'])
def save_profile():
    data = request.json or {}
    user_id = data.get("user_id")

    user = None
    if user_id:
        user = db.session.get(User, user_id)
    
    if not user:
        user = User()
        if user_id:
            user.id = user_id

    user.age = int(data.get("age", 25))
    user.sex = str(data.get("sex", "prefer_not_to_say"))
    user.activity_level = str(data.get("activity_level", "sedentary"))
    user.environment_preference = str(data.get("environment_preference", "indoors"))
    user.pregnancy_status = str(data.get("pregnancy_status", "neither"))

    db.session.add(user)

    # Calculate recommendation
    rec = calculate_hydration_target(user.to_dict())
    
    # Store Hydration Target snapshot
    target = HydrationTarget(
        user_id=user.id,
        target_ml=rec["target_ml"],
        calculation_version=rec["calculation_version"],
        research_basis=rec["research_basis"],
        profile_snapshot=json.dumps(rec["profile_snapshot"])
    )
    db.session.add(target)
    
    # Create default bottle if none exists
    bottle = Bottle.query.filter_by(user_id=user.id).first()
    if not bottle:
        bottle_cap = int(data.get("bottle_capacity_ml", 750))
        bottle = Bottle(
            user_id=user.id,
            capacity_ml=bottle_cap,
            current_volume_ml=bottle_cap,
            name="My Water Bottle"
        )
        db.session.add(bottle)

    db.session.commit()

    return jsonify({
        "user": user.to_dict(),
        "target": target.to_dict(),
        "recommendation": rec,
        "bottle": bottle.to_dict()
    })

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    target = HydrationTarget.query.filter_by(user_id=user_id).order_by(HydrationTarget.created_at.desc()).first()
    bottle = Bottle.query.filter_by(user_id=user_id).first()
    
    rec = calculate_hydration_target(user.to_dict()) if user else None
    
    return jsonify({
        "user": user.to_dict() if user else None,
        "target": target.to_dict() if target else None,
        "recommendation": rec,
        "bottle": bottle.to_dict() if bottle else None
    })

@app.route('/api/bottle', methods=['POST'])
def save_bottle():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    bottle = Bottle.query.filter_by(user_id=user_id).first()
    if not bottle:
        bottle = Bottle(user_id=user_id)
    
    if "capacity_ml" in data:
        new_cap = int(data["capacity_ml"])
        if bottle.current_volume_ml > new_cap:
            bottle.current_volume_ml = new_cap
        bottle.capacity_ml = new_cap

    if "current_volume_ml" in data:
        bottle.current_volume_ml = max(0, min(int(data["current_volume_ml"]), bottle.capacity_ml))

    if "name" in data:
        bottle.name = str(data["name"])

    if "theme" in data:
        bottle.theme = str(data["theme"])

    db.session.add(bottle)
    db.session.commit()

    return jsonify(bottle.to_dict())

@app.route('/api/drink-events', methods=['POST'])
def log_drink():
    data = request.json or {}
    user_id = data.get("user_id")
    amount_ml = int(data.get("amount_ml", 0))

    if not user_id or amount_ml <= 0:
        return jsonify({"error": "Invalid user_id or amount_ml"}), 400

    event_id = data.get("id")
    existing = db.session.get(DrinkEvent, event_id) if event_id else None
    if existing:
        return jsonify(existing.to_dict())

    # Ensure user exists
    user = db.session.get(User, user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)

    bottle = Bottle.query.filter_by(user_id=user_id).first()
    if not bottle:
        bottle = Bottle(user_id=user_id, capacity_ml=750, current_volume_ml=750)
        db.session.add(bottle)

    source = data.get("source", "quick_add")
    is_external = source in ['glass', 'gulp', 'external']

    if bottle and not is_external:
        bottle.current_volume_ml = max(0, bottle.current_volume_ml - amount_ml)
        db.session.add(bottle)

    drink_event = DrinkEvent(
        id=event_id or None,
        user_id=user_id,
        bottle_id=bottle.id if bottle else None,
        amount_ml=amount_ml,
        source=source
    )
    if "timestamp" in data:
        try:
            drink_event.timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except Exception:
            pass

    db.session.add(drink_event)
    db.session.commit()

    return jsonify({
        "event": drink_event.to_dict(),
        "bottle": bottle.to_dict() if bottle else None
    })

@app.route('/api/refill-events', methods=['POST'])
def log_refill():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    event_id = data.get("id")
    existing = db.session.get(RefillEvent, event_id) if event_id else None
    if existing:
        return jsonify(existing.to_dict())

    user = db.session.get(User, user_id)
    if not user:
        user = User(id=user_id)
        db.session.add(user)

    bottle = Bottle.query.filter_by(user_id=user_id).first()
    if not bottle:
        bottle = Bottle(user_id=user_id, capacity_ml=750, current_volume_ml=750)
        db.session.add(bottle)

    amount_added = bottle.capacity_ml - bottle.current_volume_ml
    bottle.current_volume_ml = bottle.capacity_ml
    db.session.add(bottle)

    refill_event = RefillEvent(
        id=event_id or None,
        user_id=user_id,
        bottle_id=bottle.id,
        amount_added_ml=amount_added
    )
    if "timestamp" in data:
        try:
            refill_event.timestamp = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00'))
        except Exception:
            pass

    db.session.add(refill_event)
    db.session.commit()

    return jsonify({
        "event": refill_event.to_dict(),
        "bottle": bottle.to_dict()
    })

@app.route('/api/sync', methods=['POST'])
def batch_sync():
    """
    Idempotent batch sync for offline queue.
    Accepts arrays of drink_events, refill_events, user profile, and latest bottle state.
    """
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        user_data = data.get("user")
        bottle_data = data.get("bottle")
        drink_events = data.get("drink_events", [])
        refill_events = data.get("refill_events", [])

        if not user_id:
            return jsonify({"status": "ignored", "reason": "No user_id provided"}), 200

        # Auto-provision User if missing
        user = db.session.get(User, user_id)
        if not user:
            user = User(id=user_id)
            if user_data:
                user.age = int(user_data.get("age", 25))
                user.sex = str(user_data.get("sex", "prefer_not_to_say"))
                user.activity_level = str(user_data.get("activity_level", "sedentary"))
                user.environment_preference = str(user_data.get("environment_preference", "indoors"))
                user.pregnancy_status = str(user_data.get("pregnancy_status", "neither"))
            db.session.add(user)

        # Auto-provision or update Bottle if missing
        bottle = Bottle.query.filter_by(user_id=user_id).first()
        if not bottle:
            bottle_id = bottle_data.get("id") if bottle_data else None
            cap_ml = int(bottle_data.get("capacity_ml", 750)) if bottle_data else 750
            cur_ml = int(bottle_data.get("current_volume_ml", cap_ml)) if bottle_data else cap_ml
            theme = bottle_data.get("theme", "ocean_blue") if bottle_data else "ocean_blue"
            bottle = Bottle(
                id=bottle_id or None,
                user_id=user_id,
                capacity_ml=cap_ml,
                current_volume_ml=cur_ml,
                theme=theme
            )
            db.session.add(bottle)
        elif bottle_data:
            if "current_volume_ml" in bottle_data:
                bottle.current_volume_ml = int(bottle_data["current_volume_ml"])
            if "capacity_ml" in bottle_data:
                bottle.capacity_ml = int(bottle_data["capacity_ml"])
            if "theme" in bottle_data:
                bottle.theme = str(bottle_data["theme"])
            db.session.add(bottle)

        synced_drinks = []
        synced_refills = []

        for d in drink_events:
            eid = d.get("id")
            if eid and db.session.get(DrinkEvent, eid):
                continue
            ev = DrinkEvent(
                id=eid or None,
                user_id=user_id,
                bottle_id=bottle.id,
                amount_ml=int(d.get("amount_ml", 0)),
                source=d.get("source", "quick_add")
            )
            if d.get("timestamp"):
                try:
                    ev.timestamp = datetime.fromisoformat(d["timestamp"].replace('Z', '+00:00'))
                except Exception:
                    pass
            db.session.add(ev)
            if eid:
                synced_drinks.append(eid)

        for r in refill_events:
            eid = r.get("id")
            if eid and db.session.get(RefillEvent, eid):
                continue
            ev = RefillEvent(
                id=eid or None,
                user_id=user_id,
                bottle_id=bottle.id,
                amount_added_ml=int(r.get("amount_added_ml", 0))
            )
            if r.get("timestamp"):
                try:
                    ev.timestamp = datetime.fromisoformat(r["timestamp"].replace('Z', '+00:00'))
                except Exception:
                    pass
            db.session.add(ev)
            if eid:
                synced_refills.append(eid)

        db.session.commit()

        return jsonify({
            "status": "success",
            "synced_drinks": synced_drinks,
            "synced_refills": synced_refills
        })
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Sync error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    drinks = DrinkEvent.query.filter_by(user_id=user_id).order_by(DrinkEvent.timestamp.desc()).all()
    refills = RefillEvent.query.filter_by(user_id=user_id).order_by(RefillEvent.timestamp.desc()).all()

    grouped = {}
    
    for d in drinks:
        dt_str = d.timestamp.strftime("%Y-%m-%d") if d.timestamp else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if dt_str not in grouped:
            grouped[dt_str] = {"date": dt_str, "total_ml": 0, "drink_count": 0, "refill_count": 0, "items": []}
        grouped[dt_str]["total_ml"] += d.amount_ml
        grouped[dt_str]["drink_count"] += 1
        item_dict = d.to_dict()
        item_dict["type"] = "drink"
        grouped[dt_str]["items"].append(item_dict)

    for r in refills:
        dt_str = r.timestamp.strftime("%Y-%m-%d") if r.timestamp else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if dt_str not in grouped:
            grouped[dt_str] = {"date": dt_str, "total_ml": 0, "drink_count": 0, "refill_count": 0, "items": []}
        grouped[dt_str]["refill_count"] += 1
        item_dict = r.to_dict()
        item_dict["type"] = "refill"
        grouped[dt_str]["items"].append(item_dict)

    history_list = []
    for date_key in sorted(grouped.keys(), reverse=True):
        day_data = grouped[date_key]
        day_data["items"].sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        history_list.append(day_data)

    return jsonify({"history": history_list})

@app.route('/api/stats/<user_id>', methods=['GET'])
def get_stats(user_id):
    user = db.session.get(User, user_id)
    target_obj = HydrationTarget.query.filter_by(user_id=user_id).order_by(HydrationTarget.created_at.desc()).first()
    target_ml = target_obj.target_ml if target_obj else 2500

    drinks = DrinkEvent.query.filter_by(user_id=user_id).all()
    
    daily_map = {}
    for d in drinks:
        dt_str = d.timestamp.strftime("%Y-%m-%d") if d.timestamp else datetime.now(timezone.utc).strftime("%Y-%m-%d")
        daily_map[dt_str] = daily_map.get(dt_str, 0) + d.amount_ml

    if not daily_map:
        return jsonify({
            "seven_day_avg_ml": 0,
            "completion_rate_pct": 0,
            "target_reached_days": 0,
            "total_days_tracked": 0,
            "highest_intake_ml": 0,
            "lowest_intake_ml": 0,
            "avg_drink_events_per_day": 0,
            "daily_target_ml": target_ml,
            "chart_data": []
        })

    today = datetime.now(timezone.utc).date()
    chart_data = []
    last_7_total = 0
    target_reached_days = 0

    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_consumed = daily_map.get(day_str, 0)
        last_7_total += day_consumed
        if day_consumed >= target_ml:
            target_reached_days += 1
        chart_data.append({
            "date": day_str,
            "day_label": day.strftime("%a"),
            "consumed_ml": day_consumed,
            "target_ml": target_ml,
            "reached": day_consumed >= target_ml
        })

    total_days = len(daily_map)
    seven_day_avg = int(last_7_total / 7)
    highest_day = max(daily_map.values())
    lowest_day = min(daily_map.values())
    total_events = len(drinks)
    avg_events = round(total_events / total_days, 1)
    completion_rate = int((target_reached_days / 7) * 100)

    return jsonify({
        "seven_day_avg_ml": seven_day_avg,
        "completion_rate_pct": completion_rate,
        "target_reached_days": target_reached_days,
        "total_days_tracked": total_days,
        "highest_intake_ml": highest_day,
        "lowest_intake_ml": lowest_day,
        "avg_drink_events_per_day": avg_events,
        "daily_target_ml": target_ml,
        "chart_data": chart_data
    })

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5050))
    app.run(host='0.0.0.0', port=port, debug=True)
