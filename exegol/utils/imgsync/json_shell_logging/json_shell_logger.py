#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

LOG_DIR = Path("/var/log/exegol")
LOG_FILE = LOG_DIR / "shell_commands.json"


def main() -> int:
    if not LOG_DIR.is_dir():
        try:
            LOG_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # In case of any error, write only to stderr
            sys.stderr.write(f"[command_logger] Failed to create log dir {LOG_DIR}: {e}\n")
            return 1

    # Récupération des champs transmis par zsh
    hostname = os.environ.get("HOSTNAME", "")
    container_name = os.environ.get("EXEGOL_NAME", hostname)
    cwd = os.environ.get("LOG_CWD", "")
    shell_type = os.environ.get("LOG_SHELL_TYPE", "")
    command_raw = os.environ.get("LOG_COMMAND_RAW", "")
    command = os.environ.get("LOG_COMMAND", "")

    start_time = os.environ.get("LOG_START_TIME")
    end_time = os.environ.get("LOG_END_TIME")

    exit_code_str = os.environ.get("LOG_EXIT_CODE")
    try:
        exit_code = int(exit_code_str) if exit_code_str is not None else None
    except ValueError:
        exit_code = None

    # backup datetime
    if not start_time:
        start_time = datetime.now(UTC).isoformat(timespec="milliseconds") + "Z"
    if not end_time:
        end_time = datetime.now(UTC).isoformat(timespec="milliseconds") + "Z"

    event = {
        "start_time": start_time,
        "end_time": end_time,
        "hostname": hostname,
        "container_name": container_name,
        "current_directory": cwd,
        "shell": shell_type,
        "user_command": command,
        "resolved_command": command_raw,
        "exit_code": exit_code,
    }

    try:
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except Exception as e:
        # In case of any error, write only to stderr
        sys.stderr.write(f"[command_logger] Failed to write log to {LOG_FILE}: {e}\n")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
