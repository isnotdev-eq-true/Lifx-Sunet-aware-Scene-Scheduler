#!/usr/bin/env python3
import time
from datetime import datetime, timedelta, time as dt_time
from astral import LocationInfo
from astral.sun import sun
from pytz import timezone
import requests
from pathlib import Path
import json
import sys
import subprocess
import os

# -----------------------------
# Load configuration
# -----------------------------
BASE_DIR = Path(__file__).parent
CONFIG_FILE = BASE_DIR / "lifx-theme-config.json"

try:
    with open(CONFIG_FILE) as f:
        config = json.load(f)
except Exception as e:
    print(f"Error loading config: {e}")
    sys.exit(1)

LIFX_TOKEN = config["token"]
LIGHTS = config["lights"]
SCENES = config["scenes"]
HEADERS = {"Authorization": f"Bearer {LIFX_TOKEN}"}

# -----------------------------
# Location for sunset calculation
# -----------------------------
city = LocationInfo("New York", "USA", "US/Eastern", 40.7128, -74.0060)
eastern = timezone("US/Eastern")

# -----------------------------
# Send cloud command
# -----------------------------
def send_request(url, data=None):
    try:
        # Requests.put is used for state/scene activation
        response = requests.put(url, headers=HEADERS, data=data, timeout=5) 
        if response.status_code >= 400:
            print(f"Error: {response.status_code} {response.text}")
    except requests.RequestException as e:
        print(f"Request error: {e}")

# -----------------------------
# Activate a scene by UUID
# -----------------------------
def activate_scene(scene_uuid):
    url = f"https://api.lifx.com/v1/scenes/scene_id:{scene_uuid}/activate"
    send_request(url)

# -----------------------------
# Function to execute a single scene change (called by 'at')
# -----------------------------
def set_stage(mode):
    """Activates the specified scene (Stage 1 or Stage 2) directly."""
    scene_uuid = SCENES.get(mode)
    if scene_uuid:
        print(f"[{datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')}] Executing switch to {mode.upper()}...")
        activate_scene(scene_uuid)
    else:
        print(f"Error: Scene UUID for {mode} not found in config.")

# -----------------------------
# Daily Scheduler Logic (called by crontab)
# -----------------------------
def schedule_daily_jobs():
    print(f"--- Daily Scheduler Running ({datetime.now(eastern).strftime('%Y-%m-%d %H:%M:%S')}) ---")
    
    # 1. Calculate Start Time (Sunset - 15 min) and End Time
    now = datetime.now(eastern)
    s = sun(city.observer, date=now.date(), tzinfo=eastern)
    
    stage1_schedule = config["schedules"]["stage1"]
    offset_minutes = stage1_schedule.get("start_offset_minutes", 0) 
    end_time_str = stage1_schedule.get("end", "23:59")
    
    # Calculate the precise Stage 1 Start Datetime
    start_dt = s['sunset'] + timedelta(minutes=offset_minutes)

    # Calculate the precise Stage 1 End Datetime
    try:
        hour, minute = map(int, end_time_str.split(':'))
        end_dt = eastern.localize(datetime.combine(now.date(), dt_time(hour, minute)))
    except:
        end_dt = eastern.localize(datetime.combine(now.date(), dt_time(23, 59)))

    # Handle schedules that cross midnight (like ending tomorrow morning)
    if end_dt < start_dt:
        end_dt += timedelta(days=1)
        
    # 2. Define the command to run the script itself
    # Use full paths for maximum reliability in cron/at environments
    venv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'venv')
    python_path = os.path.join(venv_path, 'bin', 'python') 
    script_path = os.path.abspath(__file__)
    
    # 3. Schedule or Execute Stage 1 (Christmas)
    
    # Check if the calculated start time is more than 5 minutes in the past
    # If it is, we execute immediately instead of trying to schedule it.
    if start_dt > now + timedelta(minutes=5):
        # Schedule the job for a time safely in the future
        start_at_time = start_dt.strftime("%H:%M %m/%d/%y")
        stage1_command = f"{python_path} {script_path} stage1"
        try:
            subprocess.run(f'echo "{stage1_command}" | at {start_at_time}', shell=True, check=True)
            print(f"  -> Scheduled Stage 1 (Christmas) for: {start_at_time}")
        except subprocess.CalledProcessError as e:
            print(f"Error scheduling Stage 1 with 'at': {e}")
            
    else:
        # If the start time has passed (or is very soon), execute Stage 1 immediately
        print("  -> Stage 1 Start Time has passed. Executing Stage 1 immediately.")
        set_stage("stage1") 

    # 4. Schedule Stage 2 (Neutral Warm)
    # This should always be in the future, given the daily cron run.
    end_at_time = end_dt.strftime("%H:%M %m/%d/%y")
    stage2_command = f"{python_path} {script_path} stage2"
    
    try:
        subprocess.run(f'echo "{stage2_command}" | at {end_at_time}', shell=True, check=True)
        print(f"  -> Scheduled Stage 2 (Neutral Warm) for: {end_at_time}")
    except subprocess.CalledProcessError as e:
        print(f"Error scheduling Stage 2 with 'at': {e}")
        
    print("-------------------------------------------------------------")


# -----------------------------
# Main entry point 
# -----------------------------
if __name__ == "__main__":
    # If the script receives an argument (stage1 or stage2), it's a scheduled job
    if len(sys.argv) > 1 and sys.argv[1] in ["stage1", "stage2"]:
        set_stage(sys.argv[1])
    else:
        # If no argument is present, this is the daily cron job - schedule the future events
        schedule_daily_jobs()
