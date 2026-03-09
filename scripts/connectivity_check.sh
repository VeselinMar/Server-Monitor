#!/bin/bash

LOGFILE="/mnt/media/monitoring/data/connectivity.csv"

# Ensure logfile exists
[ ! -f "$LOGFILE" ] && touch "$LOGFILE"

TIMESTAMP=$(date "+%Y-%m-%d %H:%M:%S")

# Ping Google's DNS
PING_RESULT=$(ping -c 2 -W 2 8.8.8.8 2>/dev/null)
if echo "$PING_RESULT" | grep -q "100% packet loss"; then
    STATUS="NO INTERNET"
    LATENCY=""
else
    STATUS="ONLINE"
    LATENCY=$(echo "$PING_RESULT" | awk -F'=' '/rtt/ {split($2,a,"/"); print a[2]}')
fi

echo "$TIMESTAMP,$STATUS,$LATENCY" >> "$LOGFILE"
