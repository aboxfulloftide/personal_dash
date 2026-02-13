#!/usr/bin/env python3
"""
Test script for widget alert system

Usage:
  python test_alert.py trigger <widget_id> <severity> <message>
  python test_alert.py acknowledge <widget_id>
  python test_alert.py list-widgets

Examples:
  python test_alert.py list-widgets
  python test_alert.py trigger widget-1234567890 critical "Server is down!"
  python test_alert.py acknowledge widget-1234567890
"""

import sys
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def get_token():
    """Get authentication token - you may need to modify this"""
    # Option 1: Read from environment
    import os
    token = os.getenv('AUTH_TOKEN')
    if token:
        return token

    # Option 2: Login with credentials
    email = os.getenv('DASHBOARD_EMAIL', 'admin@example.com')
    password = os.getenv('DASHBOARD_PASSWORD', 'admin')

    try:
        response = requests.post(
            f"{BASE_URL.replace('/api/v1', '')}/api/v1/auth/login",
            json={'email': email, 'password': password}
        )
        response.raise_for_status()
        return response.json()['access_token']
    except Exception as e:
        print(f"Error getting token: {e}")
        print("\nPlease either:")
        print("  1. Set AUTH_TOKEN environment variable with your access token")
        print("  2. Set DASHBOARD_EMAIL and DASHBOARD_PASSWORD environment variables")
        print("\nOr get your token from the browser:")
        print("  - Login to the dashboard in your browser")
        print("  - Open browser DevTools (F12)")
        print("  - Go to Application/Storage > Local Storage")
        print("  - Copy the 'token' value")
        print("  - Run: export AUTH_TOKEN='your_token_here'")
        sys.exit(1)

def list_widgets(token):
    """List all widgets in the dashboard"""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f"{BASE_URL}/dashboard/layout", headers=headers)
    response.raise_for_status()

    data = response.json()
    widgets = data.get('widgets', [])

    if not widgets:
        print("No widgets found in dashboard")
        return

    print(f"\nFound {len(widgets)} widgets:\n")
    for widget in widgets:
        alert_status = ""
        if widget.get('alert_active'):
            severity = widget.get('alert_severity', 'unknown')
            alert_status = f" [ALERT: {severity.upper()}]"

        print(f"  ID: {widget['id']}")
        print(f"  Type: {widget['type']}")
        print(f"  Title: {widget.get('config', {}).get('title', 'Untitled')}{alert_status}")
        print()

def trigger_alert(token, widget_id, severity, message):
    """Trigger an alert on a widget"""
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    payload = {
        'severity': severity,
        'message': message
    }

    response = requests.post(
        f"{BASE_URL}/widgets/{widget_id}/alert",
        headers=headers,
        json=payload
    )

    if response.status_code == 200:
        print(f"✅ Alert triggered successfully!")
        print(f"   Widget: {widget_id}")
        print(f"   Severity: {severity}")
        print(f"   Message: {message}")
        print("\nThe widget should now appear at the top of your dashboard with a pulsing border.")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def acknowledge_alert(token, widget_id):
    """Acknowledge and clear an alert"""
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.post(
        f"{BASE_URL}/widgets/{widget_id}/acknowledge",
        headers=headers
    )

    if response.status_code == 200:
        print(f"✅ Alert acknowledged successfully!")
        print(f"   Widget: {widget_id}")
        print("\nThe widget should return to its original position.")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1]
    token = get_token()

    if command == 'list-widgets':
        list_widgets(token)

    elif command == 'trigger':
        if len(sys.argv) < 5:
            print("Usage: python test_alert.py trigger <widget_id> <severity> <message>")
            print("Severity: critical, warning, or info")
            sys.exit(1)

        widget_id = sys.argv[2]
        severity = sys.argv[3]
        message = ' '.join(sys.argv[4:])

        if severity not in ['critical', 'warning', 'info']:
            print("Error: Severity must be 'critical', 'warning', or 'info'")
            sys.exit(1)

        trigger_alert(token, widget_id, severity, message)

    elif command == 'acknowledge':
        if len(sys.argv) < 3:
            print("Usage: python test_alert.py acknowledge <widget_id>")
            sys.exit(1)

        widget_id = sys.argv[2]
        acknowledge_alert(token, widget_id)

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

if __name__ == '__main__':
    main()
