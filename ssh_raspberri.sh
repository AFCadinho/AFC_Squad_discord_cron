#!/bin/bash

set -a
. .env
set +a

if [[ -z "$SSH_USER" || -z "$IP" ]]; then
  echo "❌ SSH_USER or IP not set in .env"
  exit 1
fi

ssh "$SSH_USER@$IP"
