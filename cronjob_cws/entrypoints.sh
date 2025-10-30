#!/usr/bin/env bash
set -e

# Save all current environment variables to /container.env
export -p \
| grep -Ev ' (BASHOPTS|BASH_VERSINFO|EUID|PPID|SHELLOPTS|UID)=' \
> /container.env

chmod 600 /container.env

# Now start cron (this keeps it running)
crond -f -l 8
