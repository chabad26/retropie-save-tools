#!/usr/bin/env bash

export DISPLAY="${DISPLAY:-:0}"
export XAUTHORITY="${XAUTHORITY:-/home/retropie/.Xauthority}"

LOG="/tmp/retropie-force-fullscreen.log"

sleep 2

for i in $(seq 1 20); do
  WIN="$(xdotool search --onlyvisible --class RetroArch 2>/dev/null | tail -n 1)"

  if [ -n "$WIN" ]; then
    echo "$(date) | RetroArch window=$WIN" >> "$LOG"

    wmctrl -ir "$WIN" -b remove,maximized_vert,maximized_horz
    sleep 0.1
    wmctrl -ir "$WIN" -b add,fullscreen

    exit 0
  fi

  sleep 0.2
done

echo "$(date) | RetroArch introuvable" >> "$LOG"
