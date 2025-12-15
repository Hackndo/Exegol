#!/usr/bin/env python3
import json
import os
import sys
from datetime import datetime, UTC
from pathlib import Path

LOG_DIR = Path("/var/log/exegol")
LOG_FILE = LOG_DIR / "shell_commands.json"

import os
import re
from typing import Mapping

_VAR1 = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
_VAR2 = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

def expand_env_vars_safe(command: str, env: Mapping[str, str] | None = None) -> str:
    """
    Expand $VAR and ${VAR} safely:
      - No command execution (does NOT evaluate $(...) or backticks)
      - No expansion inside single quotes
      - Expansion inside double quotes and unquoted text
    This is NOT a full shell parser; it's a pragmatic safe expander.
    """
    if env is None:
        env = os.environ

    out: list[str] = []
    i = 0
    n = len(command)
    in_single = False
    in_double = False

    while i < n:
        ch = command[i]

        # Toggle quote states (only when not escaped)
        if ch == "'" and not in_double:
            in_single = not in_single
            out.append(ch)
            i += 1
            continue

        if ch == '"' and not in_single:
            in_double = not in_double
            out.append(ch)
            i += 1
            continue

        # Handle backslash escapes (keep behavior simple & safe)
        if ch == "\\" and i + 1 < n:
            out.append(ch)
            out.append(command[i + 1])
            i += 2
            continue

        # Never expand inside single quotes
        if in_single:
            out.append(ch)
            i += 1
            continue

        # Detect $() and backticks and leave them untouched (no parsing inside)
        if ch == "$" and i + 1 < n and command[i + 1] == "(":
            # copy "$(" then continue; we do not attempt to parse nested parentheses here
            out.append("$(")
            i += 2
            continue
        if ch == "`":
            out.append("`")
            i += 1
            continue

        # Expand ${VAR}
        if ch == "$" and i + 1 < n and command[i + 1] == "{":
            m = _VAR2.match(command, i)
            if m:
                name = m.group(1)
                out.append(env.get(name, ""))
                i = m.end()
                continue

        # Expand $VAR
        if ch == "$":
            m = _VAR1.match(command, i)
            if m:
                name = m.group(1)
                out.append(env.get(name, ""))
                i = m.end()
                continue

        out.append(ch)
        i += 1

    return "".join(out)

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
        "resolved_command": expand_env_vars_safe(command_raw),
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
