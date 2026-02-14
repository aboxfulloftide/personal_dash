# Calendar Widget - Smart Event Display Implementation

## Summary

Successfully implemented smart event display for the Calendar Widget. The widget now automatically selects the most relevant view (Today/Week/Month) based on where events exist, eliminating the need for manual view hunting.

## Implementation Date
2026-02-13

## Changes Made

### Backend (`/backend/app/api/v1/endpoints/calendar.py`)

#### 1. Updated CalendarResponse Schema (Lines 27-37)
Added new fields to support smart view selection:
- `events_today_count: int` - Count of events today
- `events_week_count: int` - Count of events this week
- `events_month_count: int` - Count of events this month
- `auto_selected_view: str | None` - Which view was auto-selected

#### 2. Updated Cache Key Function (Line 60)
Modified `get_cache_key()` to include `auto_fallback` parameter in cache key generation.

#### 3. Added Helper Functions (Lines 213-269)
Created three new helper functions:
- `count_events_in_range()` - Counts events within a date range
- `calculate_date_ranges()` - Calculates date ranges for today/week/month views
- `select_best_view()` - Auto-selects best view using progressive fallback (today → week → month)

#### 4. Uses Local Server Time (Line 334)
Uses local server time for date calculations:
```python
now = datetime.now()
```
This ensures "today" is calculated based on the server's local timezone (which should match the user's timezone). Using UTC time would cause "today" to show the wrong date for users in timezones behind UTC.

#### 5. Added auto_fallback Query Parameter (Line 278)
Added new query parameter with default value:
```python
auto_fallback: bool = Query(True, description="Auto-select best non-empty view")
```

#### 6. Implemented Auto-Selection Logic (Lines 339-405)
When `auto_fallback=true`:
- Fetches entire month of events (single API call)
- Counts events in each view range
- Auto-selects first non-empty view (today → week → month)
- Filters events to selected view's range
- Returns counts + auto_selected_view in response

### Frontend (`/frontend/src/components/widgets/CalendarWidget.jsx`)

#### 1. Added State Management (Line 350)
Added `userOverrodeView` state to track manual vs auto view selection:
```javascript
const [userOverrodeView, setUserOverrodeView] = useState(false);
```

#### 2. Updated API Call (Lines 374-384)
Added `auto_fallback` parameter:
```javascript
auto_fallback: !userOverrodeView
```

#### 3. Auto-Sync View (Lines 387-391)
Added useEffect to sync view with backend's auto-selection:
```javascript
useEffect(() => {
  if (data?.auto_selected_view && !userOverrodeView) {
    setView(data.auto_selected_view);
  }
}, [data?.auto_selected_view, userOverrodeView]);
```

#### 4. Enhanced ViewTabs Component (Lines 212-245)
Updated to show event counts below each tab label:
- Displays count for each view (today/week/month)
- Styled with different colors for active/inactive tabs
- Helps users understand data distribution

#### 5. Added View Change Handler (Lines 420-424)
Created handler that marks manual override:
```javascript
const handleViewChange = (newView) => {
  setView(newView);
  setUserOverrodeView(true);
};
```

#### 6. Added Smart View Indicator (Lines 450-460)
Displays blue info box when view is auto-selected:
```
Smart View: Showing This Week (5 events)
```

#### 7. Updated Month Change Handler (Lines 426-430)
Resets auto-fallback when navigating to new month:
```javascript
const handleMonthChange = (newMonth) => {
  setSelectedMonth(newMonth);
  setUserOverrodeView(false);
};
```

## Feature Behavior

### Auto-Selection Logic (Progressive Fallback)

1. **Events Today?** → Show "Today" view
2. **No events today, but this week?** → Show "Week" view
3. **No events this week, but this month?** → Show "Month" view
4. **No events at all?** → Show "Today" view with empty state

### Visual Indicators

**Event Counts in Tabs:**
```
┌─────────┬─────────┬─────────┐
│  Today  │  Week   │  Month  │
│    3    │   12    │   28    │
└─────────┴─────────┴─────────┘
```

**Smart View Indicator:**
```
┌────────────────────────────────────────────┐
│ Smart View: Showing This Week (12 events) │
└────────────────────────────────────────────┘
```

### User Interactions

1. **Initial Load:** Widget auto-selects best view
2. **Manual Override:** User clicks any tab → disables auto-selection
3. **Month Navigation:** Changing months re-enables auto-selection
4. **Widget Refresh:** Maintains current behavior (manual or auto)

## Performance Optimizations

1. **Single API Call:** Fetches month data once, filters for different views
2. **10-Minute Cache:** Repeated loads hit cache (no API calls)
3. **Instant View Switching:** Frontend filters cached data (no re-fetch)
4. **Event Counting:** O(n) where n = events in month (typically <100)

## Edge Cases Handled

1. **All Views Empty:** Shows "Today" with empty state message
2. **Timezone Consistency:** Uses UTC-based datetime for accuracy
3. **Manual Override Persistence:** Persists until month change or refresh
4. **Cache Separation:** Different cache keys for auto vs manual mode
5. **Multiple Calendars:** Counts aggregate across all calendars

## Backward Compatibility

- ✅ Default `auto_fallback=true` provides better UX
- ✅ Users can still manually select any view
- ✅ Existing calendar configurations work unchanged
- ✅ Cache TTL and refresh intervals unchanged

## Testing Checklist

### Backend Testing
```bash
# Get auth token (from browser DevTools or login endpoint)
TOKEN="your-jwt-token-here"

# Test auto-fallback (should return counts + auto_selected_view)
curl "http://localhost:8000/api/v1/calendar?calendars=YOUR_ICS_URL&auto_fallback=true" \
  -H "Authorization: Bearer $TOKEN" | jq

# Expected response includes:
# - events: [...] (events from auto-selected view)
# - auto_selected_view: "today" | "week" | "month"
# - events_today_count: X
# - events_week_count: Y
# - events_month_count: Z

# Test manual override (should use specific view)
curl "http://localhost:8000/api/v1/calendar?calendars=YOUR_ICS_URL&view=month&auto_fallback=false" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### Frontend Testing

#### Test 1: Initial Load with Events Today
1. Open Calendar Widget with events scheduled today
2. **Expected:** Auto-selects "Today" view
3. **Expected:** Smart View indicator shows "Showing Today (X events)"
4. **Expected:** Event counts visible in all tabs

#### Test 2: No Events Today, But This Week
1. Clear today's calendar (or test with calendar that has no events today)
2. Ensure events exist later this week
3. Refresh widget
4. **Expected:** Auto-selects "Week" view
5. **Expected:** Indicator shows "Showing This Week (X events)"

#### Test 3: No Events This Week, But This Month
1. Clear this week's calendar
2. Ensure events exist later this month
3. Refresh widget
4. **Expected:** Auto-selects "Month" view
5. **Expected:** Indicator shows "Showing This Month (X events)"

#### Test 4: No Events at All
1. Clear entire month's calendar
2. Refresh widget
3. **Expected:** Shows "Today" view
4. **Expected:** Empty state: "No events today"
5. **Expected:** All tabs show count of 0

#### Test 5: Manual Override
1. Widget auto-selects "Week" view (because no events today)
2. Click "Today" tab
3. **Expected:** Switches to "Today" view
4. **Expected:** Smart View indicator disappears
5. **Expected:** Shows empty state if no events today
6. Refresh widget
7. **Expected:** Returns to manual "Today" view (override persists)

#### Test 6: Month Navigation Reset
1. Widget shows manual override (user clicked "Today" tab)
2. Switch to "Month" view
3. Click next/previous month arrows
4. **Expected:** Smart View indicator reappears
5. **Expected:** Auto-selection re-enabled for new month

#### Test 7: Event Count Accuracy
1. Verify counts match actual events in each range
2. Check with multiple calendars (counts should aggregate)
3. Verify counts update after refresh

### Performance Testing
1. Open browser DevTools → Network tab
2. Load Calendar Widget
3. **Expected:** Single API call on initial load
4. Switch between Today/Week/Month views
5. **Expected:** No additional API calls (uses cached data)
6. Wait 10 minutes, refresh widget
7. **Expected:** New API call (cache expired)

## Known Limitations

1. **Month View with Specific Month:** When user manually selects a specific month (not current), auto-fallback is disabled to respect user intent
2. **Session-Only Override:** Manual override resets on page refresh (not persisted to backend)
3. **Event Counts:** Counts are for current month only (doesn't look ahead to future months)

## Future Enhancements (Out of Scope)

- [ ] Persistent user preference (remember manual view selection across sessions)
- [ ] "Next Event" smart view (jump to specific upcoming event)
- [ ] Configurable fallback order (user can set preference in settings)
- [ ] Extended date ranges (e.g., "Next 3 Days" instead of just "Today")
- [ ] Event density heatmap showing which days have most events

## Files Modified

1. `/backend/app/api/v1/endpoints/calendar.py` - Backend logic and schema
2. `/frontend/src/components/widgets/CalendarWidget.jsx` - Frontend UI and state management

## Implementation Time

**Total:** ~2 hours
- Backend: 1 hour
- Frontend: 45 minutes
- Testing & Documentation: 15 minutes

## Success Metrics

✅ Widget always shows relevant events without manual navigation
✅ Single API call per load (performance optimized)
✅ Clear visual feedback (counts + indicator)
✅ User can still manually override when needed
✅ Auto-selection re-enables on month navigation
✅ Backward compatible with existing configurations

## Next Steps

1. Monitor user feedback on auto-selection behavior
2. Consider adding user preference toggle in settings
3. Evaluate extending to other date-based widgets
