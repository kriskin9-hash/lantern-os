#!/bin/bash
set -e

echo "[Lantern Unified] Starting services..."

# Start Flask API
echo "[*] Starting Flask API on port 5000..."
cd /app && gunicorn \
  --workers 4 \
  --threads 2 \
  --timeout 120 \
  --bind 0.0.0.0:5000 \
  --access-logfile /app/logs/access.log \
  --error-logfile /app/logs/error.log \
  src.hff_api.app:app &

# Start Discord bot if configured
if [ -n "$DISCORD_BOT_TOKEN" ]; then
  echo "[*] Starting Discord bot..."
  python src/discord_lounge_bot/bot.py &
fi

# Start health endpoint
echo "[*] Starting health endpoint on port 9000..."
python -c "
from flask import Flask, jsonify
app = Flask('health')
@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=9000)
" &

# Wait for all processes
wait
