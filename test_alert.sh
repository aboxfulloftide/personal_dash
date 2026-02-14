#!/bin/bash

# Test script for widget alert system
# Usage: ./test_alert.sh <widget_id> <severity> <message>
#
# Example: ./test_alert.sh widget-1234567890 critical "Server is down!"
#
# Severity options: critical, warning, info

if [ $# -lt 3 ]; then
    echo "Usage: $0 <widget_id> <severity> <message>"
    echo "Example: $0 widget-1234567890 critical 'Server is down!'"
    exit 1
fi

WIDGET_ID=$1
SEVERITY=$2
MESSAGE=$3

# Get token (assumes you have a .env or token stored)
# You may need to login first and get your token
TOKEN=${AUTH_TOKEN:-"your_token_here"}

echo "Triggering $SEVERITY alert on widget $WIDGET_ID..."

# Trigger alert
curl -X POST "http://localhost:8000/api/v1/widgets/${WIDGET_ID}/alert" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{
    \"severity\": \"${SEVERITY}\",
    \"message\": \"${MESSAGE}\"
  }"

echo -e "\n\nAlert triggered! Check your dashboard to see the widget moved to the top."
echo "To acknowledge the alert, run:"
echo "curl -X POST \"http://localhost:8000/api/v1/widgets/${WIDGET_ID}/acknowledge\" -H \"Authorization: Bearer ${TOKEN}\""
