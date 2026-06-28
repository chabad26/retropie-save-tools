#!/usr/bin/env bash

export DISPLAY="${DISPLAY:-:1}"
export XAUTHORITY="${XAUTHORITY:-/home/retropie/.Xauthority}"

CURRENT="/tmp/retropie-current-manual.txt"
LOG="/tmp/retropie-open-manual.log"
PDF_LOG="/tmp/retropie-pdf-viewer.log"

GAMEPAD_DEVICE="$(/home/retropie/Documents/save_retropie/Manuels/scripts/controller-detect.py --first 2>/dev/null || true)"

if [ -z "$GAMEPAD_DEVICE" ]; then
  GAMEPAD_DEVICE="$(/home/retropie/Documents/save_retropie/Manuels/scripts/controller-detect.py --first 2>/dev/null || true)"

if [ -z "$GAMEPAD_DEVICE" ]; then
  GAMEPAD_DEVICE="/dev/input/by-id/usb-PowerA_NSW_wired_controller-event-joystick"
fi
fi
GAMEPAD_CONTROLLER="/home/retropie/Documents/save_retropie/Manuels/scripts/manual-pdf-gamepad-controller.py"

MANUAL=""

if [ -f "$CURRENT" ]; then
  MANUAL="$(cat "$CURRENT" 2>/dev/null | head -n 1)"
fi

if [ -z "$MANUAL" ] || [ ! -f "$MANUAL" ]; then
  echo "$(date) | Aucun manuel à ouvrir : $MANUAL" >> "$LOG"

  notify-send \
    --app-name="RetroPie" \
    --expire-time=2500 \
    "📕 Aucun manuel disponible" \
    "Aucune notice liée à ce jeu" \
    2>/dev/null || true

  exit 0
fi

echo "$(date) | Ouverture manuel : $MANUAL" >> "$LOG"

# Si un xpdf est déjà ouvert, on le ferme pour éviter l'empilement.
pkill -f "xpdf.*$MANUAL" 2>/dev/null || true

MAPPER_PID=""

if [ -e "$GAMEPAD_DEVICE" ] && [ -x "$GAMEPAD_CONTROLLER" ]; then
  "$GAMEPAD_CONTROLLER" "$GAMEPAD_DEVICE" &
  MAPPER_PID="$!"
  echo "$(date) | Contrôleur PDF lancé PID=$MAPPER_PID" >> "$LOG"
fi

xpdf -fullscreen "$MANUAL" >> "$PDF_LOG" 2>&1

if [ -n "$MAPPER_PID" ]; then
  kill "$MAPPER_PID" 2>/dev/null || true
  echo "$(date) | Contrôleur PDF arrêté PID=$MAPPER_PID" >> "$LOG"
fi
