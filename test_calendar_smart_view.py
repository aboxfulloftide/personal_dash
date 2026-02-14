#!/usr/bin/env python3
"""
Test script for Calendar Smart View feature.
Verifies that the auto-selection logic works correctly.
"""

import sys
sys.path.insert(0, '/home/matheau/code/personal_dash_claude/backend')

from datetime import datetime, timedelta, timezone as tz
from app.api.v1.endpoints.calendar import (
    CalendarEvent,
    calculate_date_ranges,
    select_best_view,
)


def create_test_event(days_from_now: int, title: str) -> CalendarEvent:
    """Create a test event N days from now."""
    now = datetime.now(tz.utc).replace(tzinfo=None)
    event_date = now + timedelta(days=days_from_now)
    return CalendarEvent(
        title=title,
        start=event_date.isoformat(),
        end=(event_date + timedelta(hours=1)).isoformat(),
        all_day=False,
        location=None,
        description=None,
        source="Test Calendar",
        source_index=0,
    )


def test_auto_selection():
    """Test the auto-selection logic with various scenarios."""
    now = datetime.now(tz.utc).replace(tzinfo=None)
    date_ranges = calculate_date_ranges(now)

    print("=" * 60)
    print("Calendar Smart View - Auto-Selection Tests")
    print("=" * 60)
    print()

    # Test 1: Events today
    print("Test 1: Events today")
    events = [
        create_test_event(0, "Event Today 1"),
        create_test_event(0, "Event Today 2"),
        create_test_event(5, "Event Next Week"),
    ]
    view, today_count, week_count, month_count = select_best_view(events, date_ranges)
    print(f"  Today: {today_count}, Week: {week_count}, Month: {month_count}")
    print(f"  Selected: {view}")
    assert view == "today", f"Expected 'today', got '{view}'"
    assert today_count == 2, f"Expected 2 events today, got {today_count}"
    print("  ✓ PASS: Auto-selected 'today' view")
    print()

    # Test 2: No events today, but this week
    print("Test 2: No events today, but this week")
    events = [
        create_test_event(3, "Event in 3 Days"),
        create_test_event(5, "Event in 5 Days"),
    ]
    view, today_count, week_count, month_count = select_best_view(events, date_ranges)
    print(f"  Today: {today_count}, Week: {week_count}, Month: {month_count}")
    print(f"  Selected: {view}")
    assert view == "week", f"Expected 'week', got '{view}'"
    assert today_count == 0, f"Expected 0 events today, got {today_count}"
    assert week_count > 0, f"Expected events this week, got {week_count}"
    print("  ✓ PASS: Auto-selected 'week' view")
    print()

    # Test 3: No events this week, but this month
    print("Test 3: No events this week, but this month")
    events = [
        create_test_event(15, "Event in 15 Days"),
        create_test_event(20, "Event in 20 Days"),
    ]
    view, today_count, week_count, month_count = select_best_view(events, date_ranges)
    print(f"  Today: {today_count}, Week: {week_count}, Month: {month_count}")
    print(f"  Selected: {view}")
    assert view == "month", f"Expected 'month', got '{view}'"
    assert today_count == 0, f"Expected 0 events today, got {today_count}"
    assert week_count == 0, f"Expected 0 events this week, got {week_count}"
    assert month_count > 0, f"Expected events this month, got {month_count}"
    print("  ✓ PASS: Auto-selected 'month' view")
    print()

    # Test 4: No events at all
    print("Test 4: No events at all")
    events = []
    view, today_count, week_count, month_count = select_best_view(events, date_ranges)
    print(f"  Today: {today_count}, Week: {week_count}, Month: {month_count}")
    print(f"  Selected: {view}")
    assert view == "today", f"Expected 'today' (default), got '{view}'"
    assert today_count == 0, f"Expected 0 events today, got {today_count}"
    assert week_count == 0, f"Expected 0 events this week, got {week_count}"
    assert month_count == 0, f"Expected 0 events this month, got {month_count}"
    print("  ✓ PASS: Defaulted to 'today' view with empty state")
    print()

    print("=" * 60)
    print("All tests passed! ✓")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_auto_selection()
    except AssertionError as e:
        print(f"\n✗ FAIL: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
