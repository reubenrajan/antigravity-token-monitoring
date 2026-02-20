#!/bin/bash

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root (e.g. sudo ./setup_systemd.sh)"
  exit 1
fi

SERVICE_NAME="antigravity-metrics-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
PROJECT_DIR=$(pwd)

# Determine the actual user who ran sudo
if [ -n "$SUDO_USER" ]; then
    RUN_USER=$SUDO_USER
else
    RUN_USER=$(whoami)
fi

echo "Setting up systemd service for Token Metrics Exporter..."
echo "Project Directory: $PROJECT_DIR"
echo "Running as User: $RUN_USER"

# Create the systemd service file
cat << EOF > "$SERVICE_FILE"
[Unit]
Description=Antigravity Token Metrics Exporter
After=network.target

[Service]
Type=simple
User=$RUN_USER
WorkingDirectory=$PROJECT_DIR
ExecStart=$PROJECT_DIR/.venv/bin/python $PROJECT_DIR/tools/exporter.py
Restart=on-failure
RestartSec=10
# Ensures python output is not buffered
Environment="PYTHONUNBUFFERED=1"
Environment="PATH=$PROJECT_DIR/.venv/bin:/usr/local/bin:/usr/bin:/bin"

[Install]
WantedBy=multi-user.target
EOF

# Apply the correct permissions
chmod 644 "$SERVICE_FILE"

# Reload systemd, enable and start the service
echo "Reloading systemd daemon..."
systemctl daemon-reload

echo "Enabling service to start natively on boot..."
systemctl enable $SERVICE_NAME

echo "Restarting the service..."
systemctl restart $SERVICE_NAME

echo ""
echo "✅ Service setup complete!"
echo "You can check the logs any time with:"
echo "sudo journalctl -u $SERVICE_NAME -f"
echo "You can check the status with:"
echo "sudo systemctl status $SERVICE_NAME"
