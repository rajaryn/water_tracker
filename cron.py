"""
Hydration Companion - Standalone Cron Job Runner
Can be executed directly via system cron (crontab), Cloud Scheduler, or container jobs.

Usage Examples:
  python cron.py                    # Runs all scheduled tasks
  python cron.py daily_summary       # Runs daily summary calculations for yesterday
  python cron.py pacing             # Runs hourly hydration pacing & bottle empty checks
  python cron.py cleanup            # Runs stale record cleanup
"""

import sys
import json
from app import run_cron_job


def main():
    job_type = sys.argv[1] if len(sys.argv) > 1 else "all"
    date_arg = sys.argv[2] if len(sys.argv) > 2 else None

    print(f"[Cron] Executing scheduled job: '{job_type}' (target_date: {date_arg})")
    result = run_cron_job(job_type=job_type, date_str=date_arg)
    print(f"[Cron] Execution complete with status: {result.get('status')}")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
