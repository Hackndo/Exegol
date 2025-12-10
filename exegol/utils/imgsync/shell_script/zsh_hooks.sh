#!/usr/bin/env zsh

# =========
# Shell logging hooks for zsh
# =========

# Global variables for cross function data access
typeset -g LAST_COMMAND_RAW=""
typeset -g LAST_COMMAND_RAW_FULL=""
typeset -g LAST_COMMAND_START_TIME=""

# Hook called BEFORE command execution
function shell_logging_preexec() {
  # $1 : command from the user that will be executed
  LAST_COMMAND_RAW="$1"
  # $3 : fully resolved command without alias
  LAST_COMMAND_RAW_FULL="$3"
  # Start timestamp UTC (ISO8601 ms)
  LAST_COMMAND_START_TIME="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"
}

# Hook called AFTER command execution and before PROMPT display
function shell_logging_precmd() {
  # Saving previous command returned code for later use
  local exit_code=$?

  # If no registered command, logger is skipped
  [[ -z "$LAST_COMMAND_RAW" ]] && return 0

  # End timestamp
  local end_ts
  end_ts="$(date -u +"%Y-%m-%dT%H:%M:%S.%3NZ")"

  local cmd_raw cmd
  cmd="$LAST_COMMAND_RAW"

  # shellcheck disable=SC2296 (zsh syntax not supported by shellcheck)
  cmd_raw="${(e)LAST_COMMAND_RAW_FULL}"

  # Send metadata and write in background
  LOG_CWD="$PWD" \
  LOG_SHELL_TYPE="zsh" \
  LOG_COMMAND_RAW="$cmd_raw" \
  LOG_COMMAND="$cmd" \
  LOG_START_TIME="$LAST_COMMAND_START_TIME" \
  LOG_END_TIME="$end_ts" \
  LOG_EXIT_CODE="$exit_code" \
    /.exegol/json_shell_logger.py &!

  # Reset for next command
  LAST_COMMAND_RAW=""
  LAST_COMMAND_RAW_FULL=""
  LAST_COMMAND_START_TIME=""
}

# =========
# Wiring hooks zsh
# =========

typeset -a preexec_functions
# append the function to our array of preexec functions
preexec_functions+=(shell_logging_preexec)

typeset -a precmd_functions
# append the function to our array of precmd functions
precmd_functions+=(shell_logging_precmd)
