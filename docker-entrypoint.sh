#!/usr/bin/env bash
set -e

# Start Xvfb virtual framebuffer for headless Firefox
echo "Starting Xvfb virtual display on :99..."
Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX +render -noreset &
export DISPLAY=:99

# Ensure data directories exist
mkdir -p /app/profiles /app/profile /app/logs /app/queue

# Execute the main command passed to the container
exec "$@"
