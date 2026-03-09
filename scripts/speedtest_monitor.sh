#!/bin/bash

LOGFILE="/mnt/media/monitoring/data/speedtest.csv"

# Ensure logfile exists
[ ! -f "$LOGFILE" ] && touch "$LOGFILE"


TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

for i in 1 2 3; do
  RESULT=$(timeout 180 /usr/bin/speedtest --json 2>&1)
  EXIT_CODE=$?
  if [[ $EXIT_CODE -eq 0 && -n "$RESULT" ]]; then
    break
  fi
  if [[ $i -lt 3 ]]; then sleep 10; fi
done

if [[ $EXIT_CODE -ne 0 || -z "$RESULT" ]]; then
  ERROR_MSG=$(echo "$RESULT" | tr ',' ' ' | head -n 1)
  echo "$TIMESTAMP,FAILED,,,,,,\"$ERROR_MSG\"" >> "$LOGFILE"
  exit 1
fi

PING=$(jq -r '.ping' <<< "$RESULT")
DOWNLOAD=$(jq -r '.download' <<< "$RESULT")
UPLOAD=$(jq -r '.upload' <<< "$RESULT")

SERVER_NAME=$(jq -r '.server.name' <<< "$RESULT")
SERVER_ID=$(jq -r '.server.id' <<< "$RESULT")
DISTANCE=$(jq -r '.server.d' <<< "$RESULT")

# Convert bits to Mbit
DOWNLOAD_MBIT=$(awk "BEGIN {printf \"%.2f\", $DOWNLOAD/1000000}")
UPLOAD_MBIT=$(awk "BEGIN {printf \"%.2f\", $UPLOAD/1000000}")

echo "$TIMESTAMP,ONLINE,$PING,$DOWNLOAD_MBIT,$UPLOAD_MBIT,$SERVER_NAME,$SERVER_ID,$DISTANCE" >> "$LOGFILE"

DEGRADED_FLAG="/tmp/speedtest_degraded"

if (( $(echo "$DOWNLOAD_MBIT < 75" | bc -l))); then
  touch "$DEGRADED_FLAG"
else
  rm -f "$DEGRADED_FLAG"
fi

