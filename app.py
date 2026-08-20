from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import json
import os
import uuid

from config import Config
from recommendation_engine import calculate_hydration_target, CALCULATION_VERSION, RESEARCH_BASIS

# ---------------------------------------------------------------------------
# DATABASE IMPORTS - commented out until MySQL is ready
# ---------------------------------------------------------------------------
# from database import (get_connection, create_tables,
#                       User, Bottle, HydrationTarget,
#                       DrinkEvent, RefillEvent, NotificationPreference)
# create_tables()
# ---------------------------------------------------------------------------

app = Flask(__name__, static_folder='static', static_url_path='')
app.config.from_object(Config)
CORS(app)

# ---------------------------------------------------------------------------
# IN-MEMORY STORES  (UX / design testing only - data resets on server restart)
# ---------------------------------------------------------------------------
_users = {}           # user_id -> dict
_bottles = {}         # bottle_id -> dict  (one per user, keyed by user_id too)
_bottle_by_user = {}  # user_id -> bottle_id
_hydration_targets = {}   # list per user_id
_drink_events = {}    # event_id -> dict
_refill_events = {}   # event_id -> dict
_daily_summaries = {} # user_id -> dict of date_str -> summary_dict
_cron_run_history = [] # list of recent cron execution logs


def _gen_id():
    return str(uuid.uuid4())


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


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
@app.route('/api/cron', methods=['GET', 'POST', 'HEAD'])
@app.route('/api/ping', methods=['GET', 'POST', 'HEAD'])
@app.route('/ping', methods=['GET', 'POST', 'HEAD'])
@app.route('/healthz', methods=['GET', 'HEAD'])
def cron_keep_alive():
    """
    Lightweight keep-alive endpoint for external cron jobs & pingers
    (e.g., cron-job.org, UptimeRobot, Render/Koyeb pingers) to keep the service awake.
    """
    if request.method == 'HEAD':
        return '', 200
    return jsonify({
        "status": "ok",
        "message": "service is awake",
        "timestamp": _now_iso()
    }), 200

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({
        "status": "online",
        "database": "in-memory (UX test mode)",
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
    user_id = data.get("user_id") or _gen_id()

    # Upsert user
    user = _users.get(user_id, {"id": user_id, "created_at": _now_iso()})
    user.update({
        "id": user_id,
        "age": int(data.get("age", 25)),
        "sex": str(data.get("sex", "prefer_not_to_say")),
        "activity_level": str(data.get("activity_level", "sedentary")),
        "environment_preference": str(data.get("environment_preference", "indoors")),
        "pregnancy_status": str(data.get("pregnancy_status", "neither")),
        "updated_at": _now_iso(),
    })
    _users[user_id] = user

    # Calculate and store hydration target
    rec = calculate_hydration_target(user)
    target = {
        "id": _gen_id(),
        "user_id": user_id,
        "target_ml": rec["target_ml"],
        "calculation_version": rec["calculation_version"],
        "research_basis": rec["research_basis"],
        "profile_snapshot": json.dumps(rec["profile_snapshot"]),
        "created_at": _now_iso(),
    }
    _hydration_targets.setdefault(user_id, []).append(target)

    # Create default bottle if none exists
    if user_id not in _bottle_by_user:
        bottle_cap = int(data.get("bottle_capacity_ml", 750))
        bottle = {
            "id": _gen_id(),
            "user_id": user_id,
            "name": "My Water Bottle",
            "capacity_ml": bottle_cap,
            "current_volume_ml": bottle_cap,
            "theme": "ocean_blue",
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
        }
        _bottles[bottle["id"]] = bottle
        _bottle_by_user[user_id] = bottle["id"]

    bottle = _bottles[_bottle_by_user[user_id]]
    return jsonify({
        "user": user,
        "target": target,
        "recommendation": rec,
        "bottle": bottle,
    })

@app.route('/api/profile/<user_id>', methods=['GET'])
def get_profile(user_id):
    user = _users.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    targets = _hydration_targets.get(user_id, [])
    target = targets[-1] if targets else None

    bottle_id = _bottle_by_user.get(user_id)
    bottle = _bottles.get(bottle_id) if bottle_id else None

    rec = calculate_hydration_target(user)
    return jsonify({
        "user": user,
        "target": target,
        "recommendation": rec,
        "bottle": bottle,
    })

@app.route('/api/bottle', methods=['POST'])
def save_bottle():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    bottle_id = _bottle_by_user.get(user_id)
    if bottle_id:
        bottle = _bottles[bottle_id]
    else:
        bottle = {
            "id": _gen_id(),
            "user_id": user_id,
            "name": "My Water Bottle",
            "capacity_ml": 750,
            "current_volume_ml": 750,
            "theme": "ocean_blue",
            "created_at": _now_iso(),
        }
        _bottles[bottle["id"]] = bottle
        _bottle_by_user[user_id] = bottle["id"]

    if "capacity_ml" in data:
        new_cap = int(data["capacity_ml"])
        if bottle["current_volume_ml"] > new_cap:
            bottle["current_volume_ml"] = new_cap
        bottle["capacity_ml"] = new_cap

    if "current_volume_ml" in data:
        bottle["current_volume_ml"] = max(0, min(int(data["current_volume_ml"]), bottle["capacity_ml"]))

    if "name" in data:
        bottle["name"] = str(data["name"])

    if "theme" in data:
        bottle["theme"] = str(data["theme"])

    bottle["updated_at"] = _now_iso()
    return jsonify(bottle)

@app.route('/api/drink-events', methods=['POST'])
def log_drink():
    data = request.json or {}
    user_id = data.get("user_id")
    amount_ml = int(data.get("amount_ml", 0))

    if not user_id or amount_ml <= 0:
        return jsonify({"error": "Invalid user_id or amount_ml"}), 400

    # Idempotency check
    event_id = data.get("id")
    if event_id and event_id in _drink_events:
        return jsonify(_drink_events[event_id])

    # Auto-provision user
    if user_id not in _users:
        _users[user_id] = {"id": user_id, "age": 25, "sex": "prefer_not_to_say",
                           "activity_level": "sedentary", "environment_preference": "indoors",
                           "pregnancy_status": "neither", "created_at": _now_iso()}

    # Auto-provision bottle
    if user_id not in _bottle_by_user:
        bottle = {"id": _gen_id(), "user_id": user_id, "name": "My Water Bottle",
                  "capacity_ml": 750, "current_volume_ml": 750, "theme": "ocean_blue",
                  "created_at": _now_iso(), "updated_at": _now_iso()}
        _bottles[bottle["id"]] = bottle
        _bottle_by_user[user_id] = bottle["id"]

    bottle = _bottles[_bottle_by_user[user_id]]

    source = data.get("source", "quick_add")
    is_external = source in ['glass', 'gulp', 'external']

    if not is_external:
        bottle["current_volume_ml"] = max(0, bottle["current_volume_ml"] - amount_ml)
        bottle["updated_at"] = _now_iso()

    ts = _now_iso()
    if "timestamp" in data:
        try:
            ts = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')).isoformat()
        except Exception:
            pass

    event = {
        "id": event_id or _gen_id(),
        "user_id": user_id,
        "bottle_id": bottle["id"],
        "amount_ml": amount_ml,
        "timestamp": ts,
        "source": source,
    }
    _drink_events[event["id"]] = event

    return jsonify({"event": event, "bottle": bottle})

@app.route('/api/refill-events', methods=['POST'])
def log_refill():
    data = request.json or {}
    user_id = data.get("user_id")
    if not user_id:
        return jsonify({"error": "user_id is required"}), 400

    # Idempotency check
    event_id = data.get("id")
    if event_id and event_id in _refill_events:
        return jsonify(_refill_events[event_id])

    # Auto-provision user & bottle
    if user_id not in _users:
        _users[user_id] = {"id": user_id, "age": 25, "sex": "prefer_not_to_say",
                           "activity_level": "sedentary", "environment_preference": "indoors",
                           "pregnancy_status": "neither", "created_at": _now_iso()}

    if user_id not in _bottle_by_user:
        bottle = {"id": _gen_id(), "user_id": user_id, "name": "My Water Bottle",
                  "capacity_ml": 750, "current_volume_ml": 750, "theme": "ocean_blue",
                  "created_at": _now_iso(), "updated_at": _now_iso()}
        _bottles[bottle["id"]] = bottle
        _bottle_by_user[user_id] = bottle["id"]

    bottle = _bottles[_bottle_by_user[user_id]]
    amount_added = bottle["capacity_ml"] - bottle["current_volume_ml"]
    bottle["current_volume_ml"] = bottle["capacity_ml"]
    bottle["updated_at"] = _now_iso()

    ts = _now_iso()
    if "timestamp" in data:
        try:
            ts = datetime.fromisoformat(data["timestamp"].replace('Z', '+00:00')).isoformat()
        except Exception:
            pass

    event = {
        "id": event_id or _gen_id(),
        "user_id": user_id,
        "bottle_id": bottle["id"],
        "amount_added_ml": amount_added,
        "timestamp": ts,
    }
    _refill_events[event["id"]] = event

    return jsonify({"event": event, "bottle": bottle})

@app.route('/api/sync', methods=['POST'])
def batch_sync():
    """Idempotent batch sync for offline queue."""
    try:
        data = request.json or {}
        user_id = data.get("user_id")
        if not user_id:
            return jsonify({"status": "ignored", "reason": "No user_id provided"}), 200

        user_data = data.get("user")
        bottle_data = data.get("bottle")

        # Auto-provision user
        if user_id not in _users:
            _users[user_id] = {
                "id": user_id,
                "age": int(user_data.get("age", 25)) if user_data else 25,
                "sex": str(user_data.get("sex", "prefer_not_to_say")) if user_data else "prefer_not_to_say",
                "activity_level": str(user_data.get("activity_level", "sedentary")) if user_data else "sedentary",
                "environment_preference": str(user_data.get("environment_preference", "indoors")) if user_data else "indoors",
                "pregnancy_status": str(user_data.get("pregnancy_status", "neither")) if user_data else "neither",
                "created_at": _now_iso(),
            }

        # Auto-provision or update bottle
        if user_id not in _bottle_by_user:
            cap_ml = int(bottle_data.get("capacity_ml", 750)) if bottle_data else 750
            bottle = {
                "id": bottle_data.get("id") if bottle_data else _gen_id(),
                "user_id": user_id,
                "capacity_ml": cap_ml,
                "current_volume_ml": int(bottle_data.get("current_volume_ml", cap_ml)) if bottle_data else cap_ml,
                "theme": bottle_data.get("theme", "ocean_blue") if bottle_data else "ocean_blue",
                "name": "My Water Bottle",
                "created_at": _now_iso(), "updated_at": _now_iso(),
            }
            _bottles[bottle["id"]] = bottle
            _bottle_by_user[user_id] = bottle["id"]
        elif bottle_data:
            bottle = _bottles[_bottle_by_user[user_id]]
            if "current_volume_ml" in bottle_data:
                bottle["current_volume_ml"] = int(bottle_data["current_volume_ml"])
            if "capacity_ml" in bottle_data:
                bottle["capacity_ml"] = int(bottle_data["capacity_ml"])
            if "theme" in bottle_data:
                bottle["theme"] = str(bottle_data["theme"])
            bottle["updated_at"] = _now_iso()

        bottle = _bottles[_bottle_by_user[user_id]]
        synced_drinks = []
        synced_refills = []

        for d in data.get("drink_events", []):
            eid = d.get("id")
            if eid and eid in _drink_events:
                continue
            ts = _now_iso()
            if d.get("timestamp"):
                try:
                    ts = datetime.fromisoformat(d["timestamp"].replace('Z', '+00:00')).isoformat()
                except Exception:
                    pass
            ev = {"id": eid or _gen_id(), "user_id": user_id, "bottle_id": bottle["id"],
                  "amount_ml": int(d.get("amount_ml", 0)), "source": d.get("source", "quick_add"), "timestamp": ts}
            _drink_events[ev["id"]] = ev
            if eid:
                synced_drinks.append(eid)

        for r in data.get("refill_events", []):
            eid = r.get("id")
            if eid and eid in _refill_events:
                continue
            ts = _now_iso()
            if r.get("timestamp"):
                try:
                    ts = datetime.fromisoformat(r["timestamp"].replace('Z', '+00:00')).isoformat()
                except Exception:
                    pass
            ev = {"id": eid or _gen_id(), "user_id": user_id, "bottle_id": bottle["id"],
                  "amount_added_ml": int(r.get("amount_added_ml", 0)), "timestamp": ts}
            _refill_events[ev["id"]] = ev
            if eid:
                synced_refills.append(eid)

        return jsonify({"status": "success", "synced_drinks": synced_drinks, "synced_refills": synced_refills})
    except Exception as e:
        app.logger.error(f"Sync error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/history/<user_id>', methods=['GET'])
def get_history(user_id):
    drinks = [e for e in _drink_events.values() if e["user_id"] == user_id]
    refills = [e for e in _refill_events.values() if e["user_id"] == user_id]

    grouped = {}

    for d in sorted(drinks, key=lambda x: x["timestamp"], reverse=True):
        dt_str = d["timestamp"][:10]
        grouped.setdefault(dt_str, {"date": dt_str, "total_ml": 0, "drink_count": 0, "refill_count": 0, "items": []})
        grouped[dt_str]["total_ml"] += d["amount_ml"]
        grouped[dt_str]["drink_count"] += 1
        grouped[dt_str]["items"].append({**d, "type": "drink"})

    for r in sorted(refills, key=lambda x: x["timestamp"], reverse=True):
        dt_str = r["timestamp"][:10]
        grouped.setdefault(dt_str, {"date": dt_str, "total_ml": 0, "drink_count": 0, "refill_count": 0, "items": []})
        grouped[dt_str]["refill_count"] += 1
        grouped[dt_str]["items"].append({**r, "type": "refill"})

    history_list = []
    for date_key in sorted(grouped.keys(), reverse=True):
        day = grouped[date_key]
        day["items"].sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        history_list.append(day)

    return jsonify({"history": history_list})

@app.route('/api/stats/<user_id>', methods=['GET'])
def get_stats(user_id):
    targets = _hydration_targets.get(user_id, [])
    target_ml = targets[-1]["target_ml"] if targets else 2500

    drinks = [e for e in _drink_events.values() if e["user_id"] == user_id]

    daily_map = {}
    for d in drinks:
        dt_str = d["timestamp"][:10]
        daily_map[dt_str] = daily_map.get(dt_str, 0) + d["amount_ml"]

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
    avg_events = round(len(drinks) / total_days, 1)
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


# ---------------------------------------------------------------------------
# CRON JOB & SCHEDULED TASKS
# ---------------------------------------------------------------------------

def generate_daily_summaries(target_date_str=None):
    """
    Cron Task: Computes daily hydration summary per user for target_date.
    Defaults to yesterday's date if not specified.
    """
    if not target_date_str:
        yesterday = datetime.now(timezone.utc).date() - timedelta(days=1)
        target_date_str = yesterday.strftime("%Y-%m-%d")

    summaries = []
    for user_id, user in _users.items():
        targets = _hydration_targets.get(user_id, [])
        target_ml = targets[-1]["target_ml"] if targets else 2500

        user_drinks = [
            e for e in _drink_events.values()
            if e["user_id"] == user_id and (e.get("timestamp") or "").startswith(target_date_str)
        ]
        user_refills = [
            e for e in _refill_events.values()
            if e["user_id"] == user_id and (e.get("timestamp") or "").startswith(target_date_str)
        ]

        total_consumed_ml = sum(d["amount_ml"] for d in user_drinks)
        total_refills = len(user_refills)
        total_refilled_ml = sum(r["amount_added_ml"] for r in user_refills)
        goal_met = total_consumed_ml >= target_ml
        pct_completed = round((total_consumed_ml / target_ml) * 100, 1) if target_ml > 0 else 0.0

        summary = {
            "id": _gen_id(),
            "user_id": user_id,
            "date": target_date_str,
            "target_ml": target_ml,
            "consumed_ml": total_consumed_ml,
            "percentage_completed": pct_completed,
            "goal_met": goal_met,
            "drink_count": len(user_drinks),
            "refill_count": total_refills,
            "refill_volume_ml": total_refilled_ml,
            "generated_at": _now_iso()
        }

        _daily_summaries.setdefault(user_id, {})[target_date_str] = summary
        summaries.append(summary)

    return {
        "task": "daily_summary",
        "target_date": target_date_str,
        "processed_users": len(summaries),
        "summaries": summaries
    }


def evaluate_pacing_reminders():
    """
    Cron Task: Evaluates active users for hydration pacing and empty bottle alerts.
    Identifies users behind expected daytime pacing or needing bottle refills.
    """
    now = datetime.now(timezone.utc)
    current_hour = now.hour
    today_str = now.strftime("%Y-%m-%d")

    # Waking hours window (08:00 to 22:00 UTC)
    is_waking_hours = (8 <= current_hour <= 22)

    reminders = []
    for user_id, user in _users.items():
        targets = _hydration_targets.get(user_id, [])
        target_ml = targets[-1]["target_ml"] if targets else 2500

        bottle_id = _bottle_by_user.get(user_id)
        bottle = _bottles.get(bottle_id)

        user_drinks_today = [
            e for e in _drink_events.values()
            if e["user_id"] == user_id and (e.get("timestamp") or "").startswith(today_str)
        ]
        consumed_today_ml = sum(d["amount_ml"] for d in user_drinks_today)

        # Skip reminder if goal already reached
        if consumed_today_ml >= target_ml:
            continue

        # Check pacing deficit during waking hours
        if is_waking_hours:
            day_progress_ratio = max(0.0, min(1.0, (current_hour - 8) / 14.0))
            expected_consumed_ml = target_ml * day_progress_ratio

            if (expected_consumed_ml - consumed_today_ml) > 400:
                reminders.append({
                    "user_id": user_id,
                    "type": "behind_pace",
                    "title": "Hydration Check",
                    "message": f"You're at {consumed_today_ml} ml of your {target_ml} ml target. Time for a glass of water!",
                    "consumed_ml": consumed_today_ml,
                    "target_ml": target_ml,
                    "deficit_ml": round(expected_consumed_ml - consumed_today_ml),
                    "created_at": _now_iso()
                })

        # Check low bottle alert (< 20% volume remaining)
        if bottle and bottle.get("capacity_ml", 0) > 0:
            cap = bottle["capacity_ml"]
            cur = bottle.get("current_volume_ml", cap)
            if (cur / cap) <= 0.20 and cur > 0:
                reminders.append({
                    "user_id": user_id,
                    "type": "refill_reminder",
                    "title": "Bottle Almost Empty",
                    "message": f"Your bottle only has {cur} ml left ({round((cur / cap) * 100)}%). Ready for a refill?",
                    "current_volume_ml": cur,
                    "capacity_ml": cap,
                    "created_at": _now_iso()
                })

    return {
        "task": "pacing_reminders",
        "current_hour": current_hour,
        "is_waking_hours": is_waking_hours,
        "reminders_generated": len(reminders),
        "reminders": reminders
    }


def purge_stale_records(retention_days=90):
    """
    Cron Task: Cleans up transient records older than retention period.
    """
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
    return {
        "task": "cleanup",
        "retention_days": retention_days,
        "cutoff_iso": cutoff_date.isoformat(),
        "purged_records": 0
    }


def run_cron_job(job_type="all", date_str=None):
    """
    Master cron job executor function.
    Can be invoked programmatically, via CLI, or by HTTP trigger.
    
    Supported job_type values:
      - 'all': Runs daily summary, pacing reminders, and cleanup
      - 'daily_summary' / 'daily_reset': Calculates daily metrics & summary
      - 'pacing' / 'reminders': Evaluates pacing deficits and bottle alerts
      - 'cleanup': Performs periodic record pruning
    """
    started_at = _now_iso()
    results = {}

    if job_type in ["all", "daily_summary", "daily_reset"]:
        results["daily_summary"] = generate_daily_summaries(date_str)

    if job_type in ["all", "pacing", "reminders"]:
        results["pacing_reminders"] = evaluate_pacing_reminders()

    if job_type in ["all", "cleanup"]:
        results["cleanup"] = purge_stale_records()

    execution_log = {
        "job_id": _gen_id(),
        "job_type": job_type,
        "status": "success",
        "started_at": started_at,
        "completed_at": _now_iso(),
        "results": results
    }

    _cron_run_history.append(execution_log)
    if len(_cron_run_history) > 50:
        _cron_run_history.pop(0)

    return execution_log


def _verify_cron_auth():
    """Verify CRON_SECRET if set in environment."""
    cron_secret = os.getenv("CRON_SECRET")
    if not cron_secret:
        return True

    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and auth_header[7:] == cron_secret:
        return True
    if request.headers.get("X-Cron-Secret") == cron_secret:
        return True
    if request.args.get("key") == cron_secret:
        return True
    return False


@app.route('/api/cron/run', methods=['GET', 'POST'])
@app.route('/api/cron/<job_type>', methods=['GET', 'POST'])
def trigger_cron(job_type="all"):
    """
    HTTP endpoint to trigger scheduled cron jobs via external schedulers.
    """
    if not _verify_cron_auth():
        return jsonify({"error": "Unauthorized. Invalid or missing CRON_SECRET."}), 401

    data = request.json if request.is_json else {}
    target_date = request.args.get("date") or (data.get("date") if isinstance(data, dict) else None)

    result = run_cron_job(job_type=job_type, date_str=target_date)
    return jsonify(result)


@app.route('/api/cron/history', methods=['GET'])
def get_cron_history():
    """Endpoint to inspect recent cron execution logs."""
    if not _verify_cron_auth():
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify({
        "total_runs": len(_cron_run_history),
        "history": list(reversed(_cron_run_history[-20:]))
    })


if __name__ == '__main__':
    import sys
    if '--cron' in sys.argv or 'cron' in sys.argv:
        job = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith('-') else 'all'
        print(f"Running cron job: {job}...")
        res = run_cron_job(job_type=job)
        print(json.dumps(res, indent=2))
    else:
        port = int(os.getenv("PORT", 5050))
        app.run(host='0.0.0.0', port=port, debug=True)

