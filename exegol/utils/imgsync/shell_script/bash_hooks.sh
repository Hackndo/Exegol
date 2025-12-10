#!/usr/bin/env bash

# =========
# Shell logging hooks for bash
# =========
# Global variables for cross function data access
LAST_COMMAND_RAW=""
LAST_COMMAND_START_TIME=""

COMMANDS_BLACKLIST=("shell_logging_precmd" "__fzf_history__")

IS_INIT=""
INIT_OVER=""

# Function PREEXEC : called before each command or function execution
function shell_logging_preexec() {
  # Prevent recursive logging
  if [[ -n "$LAST_COMMAND_RAW" || -n "$IS_INIT" ]]; then
    return 0
  fi
  # Prevent internal or side-function logging
  for current in "${COMMANDS_BLACKLIST[@]}"; do
    if [[ $current = "$BASH_COMMAND" ]]; then
        return 0
    fi
  done
  # Detect .bashrc execution and skip it (this must be the first command of .bashrc)
  if [[ -z "$INIT_OVER" && "$BASH_COMMAND" = "source /opt/.exegol_shells_rc" ]]; then
    IS_INIT="Y"
    return 0
  fi

  # BASH_COMMAND variable contain the command to be executed (not the exact same as the user entered)
  LAST_COMMAND_RAW="$BASH_COMMAND"

  # Start timestamp UTC (ISO8601 ms)
  LAST_COMMAND_START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
}

# Function PRECMD : called before prompt display and after command execution
function shell_logging_precmd() {
  # Saving previous command returned code for later use
  local exit_code=$?

  # Reset init at the end of .bashrc loading
  if [[ -n "$IS_INIT" ]]; then
    IS_INIT=""
    INIT_OVER="Y"
    return 0
  fi

  # If no registered command, logger is skipped
  if [[ -z "$LAST_COMMAND_RAW" ]]; then
    return 0
  fi

  # End timestamp
  local end_ts
  end_ts="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"

  # Get last history command
  local histno hist_line
  histno=$HISTCMD
  hist_line=$(HISTTIMEFORMAT='' history 1 | sed 's/^ *[0-9]\+ *//')

  # Add a fail-safe in-case this function is called multiple time to avoid log duplication
  if [[ "$histno" -eq "$LAST_HISTNO" ]]; then
    return 0
  fi
  LAST_HISTNO=$histno

  local cmd cmd_raw
  cmd_raw="$LAST_COMMAND_RAW"

  # If the history line is empty fallback to $LAST_COMMAND_RAW
  [[ -z "$hist_line" ]] && cmd="$LAST_COMMAND_RAW" || cmd="$hist_line"

  # Running logger in background
  (LOG_CWD="$PWD" \
  LOG_SHELL_TYPE="bash" \
  LOG_COMMAND_RAW="$cmd_raw" \
  LOG_COMMAND="$cmd" \
  LOG_START_TIME="$LAST_COMMAND_START_TIME" \
  LOG_END_TIME="$end_ts" \
  LOG_EXIT_CODE="$exit_code" \
    /.exegol/json_shell_logger.py &)

  # Reset for next command
  LAST_COMMAND_RAW=""
  LAST_COMMAND_START_TIME=""
}

# =========
# Wiring hooks bash
# =========

# Trap DEBUG = "preexec" for bash
# This function is called before each interactive command
function bash_preexec_trap() {
  shell_logging_preexec
}

# PROMPT_COMMAND = "precmd" for bash
# We add our function to other PROMPT_COMMAND if already exist
function bash_precmd_inject() {
  # We set PROMPT_COMMAND to call our own precmd first and then others
  local old_pc="$PROMPT_COMMAND"
  if [[ -z "$old_pc" ]]; then
    PROMPT_COMMAND="shell_logging_precmd"
  else
    PROMPT_COMMAND="shell_logging_precmd; ${old_pc}"
  fi
}

# Enable trap DEBUG only for interactive shell
if [[ $- == *i* ]]; then
  # Setup precmd "hook"
  bash_precmd_inject
  # Setup preexec "hook"
  trap 'bash_preexec_trap' DEBUG
fi
