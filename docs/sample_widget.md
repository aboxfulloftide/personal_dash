Here's a minimal end-to-end example — a simple Home Server Status Board that you update via a shell script.

---
Step 1: Add the widget to your dashboard

1. Open the dashboard and click Edit mode
2. Click Add Widget → select Custom Widget
3. The widget appears — note its ID (e.g. widget-1234567890) from the browser's network tab or the widget's manage panel
4. Click the widget's settings gear to choose a Display Mode: List, Compact, Table, or Grid

---
Step 2: Get a token

TOKEN=$(curl -s -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=your@email.com&password=yourpassword" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

echo $TOKEN  # verify it worked

---
Step 3: Populate it — single items or bulk

WIDGET_ID="widget-1234567890"
API="http://localhost:8000/api/v1"
AUTH=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

# Option A: add items one at a time
curl -s -X POST "$API/custom-widgets/$WIDGET_ID/items" "${AUTH[@]}" -d \
  '{"title": "Web Server", "subtitle": "nginx running", "icon": "✅", "color": "green", "priority": 3}'

curl -s -X POST "$API/custom-widgets/$WIDGET_ID/items" "${AUTH[@]}" -d \
  '{"title": "Database", "subtitle": "MySQL running", "icon": "✅", "color": "green", "priority": 2}'

# Option B: bulk push (replace_all=true wipes existing items first — ideal for cron scripts)
curl -s -X POST "$API/custom-widgets/$WIDGET_ID/items/bulk" "${AUTH[@]}" -d '{
  "replace_all": true,
  "items": [
    {"title": "Web Server", "subtitle": "nginx running", "icon": "✅", "color": "green", "priority": 3},
    {"title": "Database",   "subtitle": "MySQL running", "icon": "✅", "color": "green", "priority": 2},
    {"title": "Backups",    "subtitle": "Last run: today 3am", "icon": "💾", "color": "blue", "priority": 1}
  ]
}'

---
Step 4: Automate it with a cron script

Save this as /usr/local/bin/update_status.sh:

#!/bin/bash
WIDGET_ID="widget-1234567890"
TOKEN="eyJ..."   # paste your token here (or re-auth each run)
API="http://localhost:8000/api/v1"
AUTH=(-H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json")

# Build item list as JSON array
ITEMS="["

# Check nginx
if systemctl is-active --quiet nginx; then
    ITEMS+='{"title":"Web Server","subtitle":"nginx running","icon":"✅","color":"green","priority":3},'
else
    ITEMS+='{"title":"Web Server","subtitle":"nginx DOWN","icon":"🔴","color":"red","priority":3,
              "alert_active":true,"alert_severity":"critical","alert_message":"nginx is not running!"},'
fi

# Disk usage
DISK=$(df -h / | awk 'NR==2{print $5}')
ITEMS+="{\"title\":\"Disk\",\"subtitle\":\"$DISK used\",\"icon\":\"💾\",\"priority\":1}"

ITEMS+="]"

# Push everything at once, replacing previous state
curl -s -X POST "$API/custom-widgets/$WIDGET_ID/items/bulk" "${AUTH[@]}" \
  -d "{\"replace_all\":true,\"items\":$ITEMS}" > /dev/null

Add to cron (crontab -e):

*/5 * * * * /usr/local/bin/update_status.sh

---
What you get

- When nginx is up: green ✅ rows, no alerts
- When nginx goes down: the widget flashes red and moves to the top of the dashboard with a critical alert
- After you acknowledge the alert in the dashboard overlay, all item-level alerts are marked acknowledged
  so the scheduler won't re-trigger it until nginx goes down again on the next cron run
- After you fix nginx and the next cron run fires: alert clears automatically (replace_all resets acknowledged too)

---
Display modes

Configure via the widget's settings gear:

- List    — icon, title, subtitle, description (default)
- Compact — icon + title only, maximum density (great for many short status lines)
- Table   — two columns: title on left, subtitle on right (great for key/value pairs)
- Grid    — 2-column card layout (great for grouped status indicators)
