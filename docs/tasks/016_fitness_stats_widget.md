# Task 016: Fitness Stats Widget

## Status: Completed

## Objective
Build a fitness stats widget supporting manual weight logging and Garmin Connect sync for steps, sleep, resting heart rate, and workouts.

## What Was Built

### Design Decisions (vs. original plan)
- **Garmin Connect added** via the `garth` unofficial client library — steps, sleep, HR, and activities sync automatically every 6 hours
- **Simpler schema** — skipped FitnessProfile/FitnessEntry abstraction in favor of direct `weight_entries` + Garmin-specific tables
- **No BMI, body fat %, or CSV export** in this iteration — kept scope focused
- Each metric can come from either source independently (e.g. manual weight + Garmin steps)

---

## Database Schema

### `weight_entries` (extended)
Added `source` column (`'manual'` | `'garmin'`).

### `garmin_credentials` (new)
| Column | Type | Notes |
|--------|------|-------|
| user_id | Integer (UNIQUE FK) | One per user |
| email | String | Garmin login email |
| garmin_username | String | Display name for API calls |
| encrypted_tokens | Text | JSON of garth OAuth1+OAuth2 tokens, Fernet-encrypted |
| sync_enabled | Boolean | Default True |
| last_synced_at | DateTime | Updated after each sync |
| sync_status | String | `'ok'` \| `'error'` \| `'never'` |
| sync_error | String | Last error message |

### `garmin_daily_stats` (new)
| Column | Type | Notes |
|--------|------|-------|
| user_id | FK | |
| date | Date | UNIQUE with user_id |
| steps | Integer | |
| active_calories | Integer | |
| sleep_minutes | Integer | |
| resting_hr | Integer | |

### `garmin_activities` (new)
| Column | Type | Notes |
|--------|------|-------|
| user_id | FK | |
| garmin_activity_id | String | UNIQUE with user_id (dedup key) |
| activity_type | String | e.g. `running`, `cycling` |
| name | String | Activity name from Garmin |
| start_time | DateTime | |
| duration_minutes | Integer | |
| distance_km | Numeric | |
| calories | Integer | |
| avg_hr | Integer | |

Migration: `f3a9c2d8e1b4_add_fitness_tables.py`

---

## Garmin Integration

**Library:** `garth>=0.4.0` — unofficial Garmin Connect client, no API key or partnership required.

**Auth flow:**
1. User enters email + password in `GarminSetupModal`
2. `POST /fitness/garmin/connect` calls `garth.Client().login(email, password)`
3. OAuth1 + OAuth2 tokens serialized to JSON, Fernet-encrypted, stored in `garmin_credentials`
4. Password is **never stored**
5. garth handles token refresh automatically; updated tokens saved back on each sync

**Garmin API calls (via `client.connectapi()`):**
- Daily summary: `/usersummary-service/usersummary/daily/{username}?calendarDate={date}`
- Sleep: `/wellness-service/wellness/dailySleepData/{username}?date={date}`
- Activities: `/activitylist-service/activities/search/activities?startDate=...&endDate=...`
- Weight: `/weight-service/weight/dateRange?startDate=...&endDate=...`

**Limitation:** 2FA/MFA must be disabled on the Garmin account.

---

## Backend Files

| File | Action |
|------|--------|
| `backend/app/models/fitness.py` | Extended — `WeightEntry` + `GarminCredential`, `GarminDailyStat`, `GarminActivity` |
| `backend/app/models/user.py` | Added `garmin_credential`, `garmin_daily_stats`, `garmin_activities` relationships |
| `backend/app/schemas/fitness.py` | New — all Pydantic schemas |
| `backend/app/crud/fitness.py` | New — weight CRUD, garmin credential management, garth token serialization, upserts, aggregated stats |
| `backend/app/api/v1/endpoints/fitness.py` | New — all REST endpoints + `sync_garmin_for_user()` shared sync logic |
| `backend/app/api/v1/router.py` | Added `fitness.router` |
| `backend/app/core/scheduler.py` | Added `sync_garmin_task()` — runs every 6 hours |
| `backend/requirements.txt` | Added `garth>=0.4.0` |
| `backend/alembic/versions/f3a9c2d8e1b4_add_fitness_tables.py` | Migration |

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/fitness/stats` | Aggregated widget data |
| GET | `/fitness/weight` | Weight history for chart |
| POST | `/fitness/weight` | Log manual weight entry |
| DELETE | `/fitness/weight/{id}` | Delete entry |
| GET | `/fitness/activities` | Recent activities |
| GET | `/fitness/garmin/status` | Sync status |
| POST | `/fitness/garmin/connect` | Connect Garmin account |
| POST | `/fitness/garmin/sync` | Manual sync trigger |
| DELETE | `/fitness/garmin/disconnect` | Remove credentials |

---

## Frontend Files

| File | Action |
|------|--------|
| `frontend/src/components/widgets/FitnessWidget.jsx` | New — main widget |
| `frontend/src/components/widgets/FitnessLogModal.jsx` | New — manual weight entry form |
| `frontend/src/components/widgets/GarminSetupModal.jsx` | New — connect/manage Garmin |
| `frontend/src/components/widgets/widgetRegistry.js` | Updated `fitness` entry |

### Widget Layout
1. **Empty state** — two CTAs: "+ Log Weight" and "Connect Garmin (steps, sleep, HR, workouts)"
2. **Today summary row** — 4 chips: Steps / Sleep / Resting HR / Weight
3. **Weight section** — Recharts line chart + "+ Log" button
4. **Recent activities** — list of last 5 workouts with type icon, duration, calories (only shown when Garmin connected)
5. **Footer** — Garmin sync status badge or "+ Connect Garmin for steps, sleep & workouts" link

### Widget Config Schema
```
title          — text, default "Fitness Stats"
unit           — select: lbs / kg
days_back      — number 7–90, default 30
refresh_interval — number 60–3600, default 300
```

---

## Acceptance Criteria

- [x] Manual weight entry (date, weight, unit, notes)
- [x] Weight history chart (Recharts line chart)
- [x] lbs / kg unit support with on-the-fly conversion
- [x] Garmin Connect authentication (email/password → OAuth tokens only)
- [x] Garmin daily stats sync (steps, active calories, sleep, resting HR)
- [x] Garmin activities sync (workouts with type, duration, distance, calories, HR)
- [x] Garmin weight sync (Index scale, if connected)
- [x] Background sync every 6 hours via scheduler
- [x] Manual "Sync Now" button in settings modal
- [x] Clear empty state with setup instructions
- [x] Garmin sync status shown in widget footer

## Notes
- garth v0.6.3 was already installed in the dev environment
- Token refresh is handled automatically by garth on each API call
- Daily stats fall back to yesterday if today's data hasn't synced yet
- Weight entries from Garmin are only created if no manual entry exists for that date (manual takes priority)

## Next Task
Task 017: Dashboard Layout & Polish
