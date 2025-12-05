# LIFX Sunset-aware Scene Scheduler

This project provides an efficient, sunset-aware scheduling solution for managing lighting scenes via the LIFX Cloud API. It utilizes the Unix `at` utility for precise, low-overhead scheduling, initiated by a single daily cron job.

## Features

* Sunset-Aware Scheduling:** Dynamically calculates scene start times based on your local sunset.
* Two-Stage Theming:** Switches lights between two predefined scenes (Stage 1 and Stage 2) at calculated times.
* Low Maintenance:** A single daily cron job runs the scheduler script, which in turn sets up two temporary `at` jobs for the actual scene switching.

---

## Setup and Configuration

### 1. The Script (`life-theme.py`)

This file contains the logic for time calculation, API communication, and setting up the scheduled `at` jobs.

**Usage Modes:**

| Execution | Command Used | Triggered By | Function |
| :--- | :--- | :--- | :--- |
| **Scheduler** | `/path/to/script/lifx-theme.py` | Daily Cron Job | Calculates sunset and schedules two scene-switching jobs. |
| **Scene Switch** | `/path/to/script/lifx-theme.py stage1` | `at` utility | Immediately activates the Stage 1 scene. |
| **Scene Switch** | `/path/to/script/lifx-theme.py stage2` | `at` utility | Immediately activates the Stage 2 scene. |

### 2. The Config File (`lifx-theme-config.json`)

This file stores your authentication and schedule parameters. You must populate the `token` and `scenes` UUIDs.

```json
{
  "token": "{Your LIFX Cloud API Token}",
  "lights": ["all", "group:{light name}"],
  "scenes": {
    "stage1": "{Scene 1 UUID}",
    "stage2": "{Scene 2 UUID}"
  },
  "schedules": {
    "stage1": {
      "start_offset_minutes": -15,
      "end": "21:45"
    }
  }
}

Key                   Value             Description
token                 Your API Token    Required for LIFX Cloud access.
scenes.stage1         Scene UUID.       The primary theme to run during the evening window.
scenes.stage2         Scene UUID        The default theme to switch to after the window ends.
start_offset_minutes  -15 (Example)     Starts 15 minutes before sunset. Use a positive number to start after sunset.
end.                  "21:45" (Example) The fixed local time when the primary scene ends (9:45 PM).


Scheduling with Crontab
The project requires a single daily cron job to run the scheduler script.

Prerequisites
1 at Utility: Ensure the at utility (the background scheduler) is installed and running on your system. 
Bash # On Debian/Ubuntu
	sudo apt install at
	sudo systemctl enable --now atd 	 
2 Full Paths: You must use the full absolute path to your Python executable and script file.

The Crontab Entry
Use crontab -e to edit your user's crontab and add the following single line.

IMPORTANT: Replace all bracketed placeholders with your actual, correct paths and file names.

Bash

# Runs the scheduler script every day at 6:00 AM (0 6 * * *)
0 6 * * * {/path/to/venv/bin/python} {/path/to/script/lifx-theme.py} >> {/path/to/logfile.log} 2>&1

Monitoring

The output of the daily job is redirected to a log file. You can check this file to verify the daily scheduling success:

Bash

cat {/path/to/logfile.log}

If the setup is correct, you will see output confirming the schedules being set every day at the cron time:

--- Daily Scheduler Running (YYYY-MM-DD HH:MM:SS) ---
  -> Scheduled Stage 1 for: HH:MM MM/DD/YY
  -> Scheduled Stage 2 for: 21:45 MM/DD/YY
-------------------------------------------------------------
