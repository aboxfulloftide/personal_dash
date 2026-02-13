#!/usr/bin/env python3
"""Fix corrupted layout y-positions in the database"""
import requests
import json
import os

# Get token
token = os.getenv('AUTH_TOKEN')
if not token:
    print("Please set AUTH_TOKEN environment variable")
    print("Get it from browser: F12 -> Application -> Local Storage -> token")
    exit(1)

base_url = "http://localhost:8000/api/v1"
headers = {"Authorization": f"Bearer {token}"}

# Get current layout
print("Fetching current layout...")
response = requests.get(f"{base_url}/dashboard/layout", headers=headers)
response.raise_for_status()
data = response.json()

print(f"\nFound {len(data['widgets'])} widgets")
print(f"Found {len(data['layout'])} layout items")

# Show current y-positions
print("\nCurrent y-positions:")
for item in sorted(data['layout'], key=lambda x: x['y']):
    print(f"  Widget {item['i']}: y={item['y']}")

# Reset y-positions to reasonable values
print("\nResetting layout to grid arrangement...")
fixed_layout = []
x = 0
y = 0
row_height = 0

for item in data['layout']:
    w = item['w']
    h = item['h']

    # Check if widget fits in current row
    if x + w > 24:
        # Move to next row
        x = 0
        y += row_height
        row_height = 0

    fixed_item = {
        **item,
        'x': x,
        'y': y
    }
    fixed_layout.append(fixed_item)

    x += w
    row_height = max(row_height, h)

# Show new positions
print("\nNew y-positions:")
for item in sorted(fixed_layout, key=lambda x: x['y']):
    print(f"  Widget {item['i']}: y={item['y']}")

# Save fixed layout
print("\nSaving fixed layout...")
response = requests.put(
    f"{base_url}/dashboard/layout",
    headers={**headers, "Content-Type": "application/json"},
    json={"widgets": data['widgets'], "layout": fixed_layout}
)
response.raise_for_status()

print("✅ Layout fixed! Refresh your dashboard.")
