#!/usr/bin/env python3
"""Check if alert data is in the database"""
from app.database import SessionLocal
from app.crud.dashboard import get_dashboard
from sqlalchemy import text
import json

db = SessionLocal()
try:
    # Get first user's dashboard
    user_result = db.execute(text('SELECT id FROM users LIMIT 1')).fetchone()
    if not user_result:
        print('No users found')
        exit(1)

    user_id = user_result[0]
    print(f'Checking dashboard for user_id: {user_id}\n')

    dashboard = get_dashboard(db, user_id)
    if not dashboard:
        print('No dashboard found')
        exit(1)

    widgets = dashboard.layout.get('widgets', [])
    print(f'Found {len(widgets)} widgets\n')

    # Check for alerts
    target_widget = 'widget-1770682864669'
    for widget in widgets:
        if widget.get('id') == target_widget:
            print(f'Widget {target_widget}:')
            print(f'  alert_active: {widget.get("alert_active")}')
            print(f'  alert_severity: {widget.get("alert_severity")}')
            print(f'  alert_message: {widget.get("alert_message")}')
            print(f'\n  All keys: {list(widget.keys())}')
            break
    else:
        print(f'\nWidget {target_widget} not found')

finally:
    db.close()
