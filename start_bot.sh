#!/bin/bash
# Launch the AI Service Bot (backend + Flutter web frontend).
# Usage: ./start_bot.sh [--port BACKEND_PORT] [--web-port FLUTTER_PORT]

set -e

BACKEND_PORT="${BACKEND_PORT:-8000}"
FLUTTER_PORT="${FLUTTER_PORT:-8080}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Parse arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    --port) BACKEND_PORT="$2"; shift 2 ;;
    --web-port) FLUTTER_PORT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Error: python3 not found"; exit 1; }
command -v flutter >/dev/null 2>&1 || { echo "Error: flutter not found"; exit 1; }

# Install backend dependencies
echo "Installing backend dependencies..."
cd service_bot_backend
pip install -r requirements.txt --quiet 2>/dev/null || pip install -r requirements.txt
cd ..

# Start backend
echo "Starting backend on port $BACKEND_PORT..."
cd service_bot_backend
python3 -m uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!
cd ..

# Wait for backend to be ready
echo "Waiting for backend..."
for i in $(seq 1 10); do
  if curl -s "http://localhost:$BACKEND_PORT/health" >/dev/null 2>&1; then
    echo "Backend ready."
    break
  fi
  if [ "$i" -eq 10 ]; then
    echo "Error: Backend failed to start"
    kill $BACKEND_PID 2>/dev/null
    exit 1
  fi
  sleep 1
done

# Start Flutter
echo "Starting Flutter web on port $FLUTTER_PORT..."
cd service_bot_flutter
flutter pub get
flutter run -d chrome --web-hostname=localhost --web-port="$FLUTTER_PORT" \
  --dart-define="API_BASE_URL=http://localhost:$BACKEND_PORT"

# Cleanup
kill $BACKEND_PID 2>/dev/null
echo "Stopped."
