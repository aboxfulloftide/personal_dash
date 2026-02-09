# Reminder Widget

## Overview
A flexible reminder system that displays scheduled reminders based on recurring intervals or specific days of the week. Reminders appear on their scheduled day and can be dismissed with a click. Supports various recurrence patterns and handles missed reminders from previous days.

## Features

### 1. Reminder Types

#### Interval-Based Reminders
**Repeat every X hours/days/weeks/months**

- **Every X Hours** - For frequent reminders (e.g., "Take medication every 4 hours")
  - Range: 1-24 hours
  - Shows all instances for the day as separate reminders
  - Example: "Take Medication 1", "Take Medication 2", "Take Medication 3"

- **Every X Days** - For regular tasks (e.g., "Water plants every 3 days")
  - Range: 1-365 days
  - Shows once per day when due

- **Every X Weeks** - For weekly/bi-weekly tasks (e.g., "Change bed sheets every 2 weeks")
  - Range: 1-52 weeks
  - Shows once on the scheduled day

- **Every X Months** - For monthly tasks (e.g., "Change air filter every 3 months")
  - Range: 1-12 months
  - Shows once on the scheduled day

#### Day-of-Week Based Reminders
**Specific days of the week**

- Select one or more days: Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday
- Examples:
  - "Trash day" - Every Monday and Thursday
  - "Gym workout" - Monday, Wednesday, Friday
  - "Weekly meeting" - Every Tuesday
  - "Weekend chores" - Saturday and Sunday

### 2. Reminder Display

#### Active Reminders (Today's List)
**Shows all reminders due today**

```
┌─────────────────────────────────────┐
│ Reminders - Today (3)               │
├─────────────────────────────────────┤
│ ☐ Take Medication 1                 │
│   8:00 AM                      [✓]  │
├─────────────────────────────────────┤
│ ☐ Take Medication 2                 │
│   12:00 PM                     [✓]  │
├─────────────────────────────────────┤
│ ☐ Trash Day                         │
│   Monday                       [✓]  │
└─────────────────────────────────────┘
```

#### Display Format:
- **Checkbox** - Visual indicator (unchecked = pending)
- **Reminder Title** - Task/event name
- **Time/Day Context** - When it's due (for hourly) or day name
- **Dismiss Button [✓]** - Click to mark as complete

#### For Hourly Reminders:
- Shows all instances for the current day
- Numbered sequentially: "Task Name 1", "Task Name 2", etc.
- Each has a specific time: 8:00 AM, 12:00 PM, 4:00 PM, 8:00 PM
- Calculate times by dividing day into intervals

### 3. Reminder States

#### Active (Pending)
- Displayed in the widget
- Checkbox unchecked
- Can be dismissed

#### Dismissed (Completed)
- Removed from display
- Logged in history (for statistics)
- Cannot be undismissed (until next occurrence)

#### Overdue (From Previous Days)
**Handling missed reminders**

Two options (user-configurable per reminder):

**Option A: Show Next Day** (Default)
- Reminder carries over to the next day
- Shows with "Overdue" badge/indicator
- Remains until dismissed
- Example: Forgot to take medication yesterday → shows today as overdue

**Option B: Auto-Dismiss**
- Automatically dismissed at midnight
- Does not carry over
- Good for time-sensitive reminders
- Example: "Morning workout" - if missed, don't show next day

#### Visual Indicators:
- **Today**: Normal styling
- **Overdue**: Red accent, "Overdue" badge, shows original date
  ```
  ☐ Take Medication
    Yesterday, 8:00 AM (Overdue)     [✓]
  ```

### 4. Midnight Reset Behavior

**What happens at midnight (12:00 AM):**

1. **Generate New Reminders**
   - Check all recurring reminders
   - Create instances for today based on schedule
   - For hourly: calculate all times for the day

2. **Handle Yesterday's Reminders**
   - If "Show Next Day": Keep as overdue, add "Overdue" badge
   - If "Auto-Dismiss": Remove from display, log as missed

3. **Clear Dismissed Status**
   - Yesterday's dismissed reminders are archived
   - Ready for next occurrence

### 5. Reminder Management

#### Create New Reminder

```
┌─────────────────────────────────────┐
│ Add New Reminder                    │
├─────────────────────────────────────┤
│ Title: *                            │
│ [________________________]          │
│                                     │
│ Recurrence: *                       │
│ ○ Every X Hours/Days/Weeks/Months   │
│ ○ Specific Days of Week             │
│                                     │
│ [If "Every X" selected:]            │
│   Every [__] [Hours ▼]              │
│   Starting: [Date/Time Picker]      │
│                                     │
│ [If "Days of Week" selected:]       │
│   ☐ Mon ☐ Tue ☐ Wed ☐ Thu          │
│   ☐ Fri ☐ Sat ☐ Sun                │
│   Time: [Time Picker] (optional)    │
│                                     │
│ If missed:                          │
│ ○ Show next day (Default)           │
│ ○ Auto-dismiss at midnight          │
│                                     │
│ Notes (optional):                   │
│ [________________________]          │
│                                     │
│         [Cancel]  [Save]            │
└─────────────────────────────────────┘
```

#### Edit Reminder
- Click on reminder title to edit
- Can modify all fields
- Changes apply to future instances only

#### Delete Reminder
- Remove entirely from schedule
- Option to delete only today's instance vs entire recurring reminder

#### Pause/Snooze (Future Enhancement)
- Temporarily disable a reminder
- Snooze for X hours/days

## Technical Implementation

### Database Schema

```python
class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)

    # Recurrence settings
    recurrence_type = Column(String(20), nullable=False)  # "interval", "day_of_week"

    # For interval-based
    interval_value = Column(Integer, nullable=True)  # The number (e.g., 4)
    interval_unit = Column(String(20), nullable=True)  # "hours", "days", "weeks", "months"

    # For day-of-week based (comma-separated: "1,3,5" for Mon,Wed,Fri)
    days_of_week = Column(String(20), nullable=True)  # "0,1,2,3,4,5,6" (0=Sunday)

    # Time for hourly reminders or day-of-week reminders
    reminder_time = Column(Time, nullable=True)

    # Start date for the reminder
    start_date = Column(Date, nullable=False)

    # Missed reminder behavior
    carry_over = Column(Boolean, default=True)  # True = show next day, False = auto-dismiss

    # Active status
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # Relationships
    instances = relationship("ReminderInstance", back_populates="reminder", cascade="all, delete-orphan")


class ReminderInstance(Base):
    """Individual occurrences of reminders for a specific date"""
    __tablename__ = "reminder_instances"

    id = Column(Integer, primary_key=True)
    reminder_id = Column(Integer, ForeignKey("reminders.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # When this instance is for
    due_date = Column(Date, nullable=False)
    due_time = Column(Time, nullable=True)  # For hourly reminders

    # Instance number for hourly reminders (1, 2, 3, etc.)
    instance_number = Column(Integer, nullable=True)

    # Status
    status = Column(String(20), default="pending")  # "pending", "dismissed", "missed"
    dismissed_at = Column(DateTime, nullable=True)

    # Is this overdue (carried over from previous day)?
    is_overdue = Column(Boolean, default=False)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    reminder = relationship("Reminder", back_populates="instances")

    # Index for efficient queries
    __table_args__ = (
        Index('idx_user_due_date', 'user_id', 'due_date', 'status'),
    )
```

### Backend API Endpoints

```python
# Get today's reminders
GET /api/v1/reminders/today
Response: {
  "reminders": [
    {
      "instance_id": 123,
      "reminder_id": 45,
      "title": "Take Medication",
      "instance_number": 1,
      "due_date": "2026-02-08",
      "due_time": "08:00:00",
      "is_overdue": false,
      "notes": "With food"
    }
  ],
  "pending_count": 5,
  "overdue_count": 1
}

# Get all reminders (schedule)
GET /api/v1/reminders
Response: {
  "reminders": [
    {
      "id": 45,
      "title": "Take Medication",
      "recurrence_type": "interval",
      "interval_value": 4,
      "interval_unit": "hours",
      "carry_over": true,
      "is_active": true,
      "next_occurrence": "2026-02-08T08:00:00"
    }
  ]
}

# Create reminder
POST /api/v1/reminders
Body: {
  "title": "Water Plants",
  "notes": "Check soil moisture",
  "recurrence_type": "interval",
  "interval_value": 3,
  "interval_unit": "days",
  "start_date": "2026-02-08",
  "carry_over": false
}

# Update reminder
PUT /api/v1/reminders/{reminder_id}
Body: { ... same as create ... }

# Delete reminder
DELETE /api/v1/reminders/{reminder_id}

# Dismiss instance
POST /api/v1/reminders/instances/{instance_id}/dismiss
Response: { "success": true }

# Get reminder history/statistics
GET /api/v1/reminders/stats
Query: { "days": 30 }
Response: {
  "total_reminders": 120,
  "dismissed": 115,
  "missed": 5,
  "completion_rate": 95.8
}
```

### Background Job: Midnight Reset

**Scheduler Task** (runs at 12:00 AM daily):

```python
async def generate_daily_reminders():
    """Generate reminder instances for today"""
    today = date.today()

    # Get all active reminders
    reminders = db.query(Reminder).filter(
        Reminder.is_active == True,
        Reminder.start_date <= today
    ).all()

    for reminder in reminders:
        if should_trigger_today(reminder, today):
            if reminder.recurrence_type == "interval" and reminder.interval_unit == "hours":
                # Generate multiple instances for hourly reminders
                instances = calculate_hourly_instances(reminder, today)
                for idx, time in enumerate(instances, 1):
                    create_reminder_instance(
                        reminder=reminder,
                        due_date=today,
                        due_time=time,
                        instance_number=idx
                    )
            else:
                # Single instance for the day
                create_reminder_instance(
                    reminder=reminder,
                    due_date=today
                )

    # Handle overdue reminders
    yesterday = today - timedelta(days=1)
    overdue_instances = db.query(ReminderInstance).filter(
        ReminderInstance.due_date == yesterday,
        ReminderInstance.status == "pending"
    ).all()

    for instance in overdue_instances:
        if instance.reminder.carry_over:
            # Move to today as overdue
            instance.due_date = today
            instance.is_overdue = True
        else:
            # Auto-dismiss
            instance.status = "missed"
            instance.dismissed_at = datetime.now()

    db.commit()


def should_trigger_today(reminder: Reminder, today: date) -> bool:
    """Check if reminder should trigger today"""
    if reminder.recurrence_type == "day_of_week":
        # Check if today's day of week is in the list
        today_dow = today.weekday()  # 0=Monday
        days = [int(d) for d in reminder.days_of_week.split(",")]
        return today_dow in days

    elif reminder.recurrence_type == "interval":
        # Calculate if enough time has passed since start_date
        days_since_start = (today - reminder.start_date).days

        if reminder.interval_unit == "hours":
            return days_since_start >= 0  # Show every day
        elif reminder.interval_unit == "days":
            return days_since_start % reminder.interval_value == 0
        elif reminder.interval_unit == "weeks":
            return days_since_start % (reminder.interval_value * 7) == 0
        elif reminder.interval_unit == "months":
            # More complex - need to handle variable month lengths
            return is_month_interval_match(reminder, today)

    return False


def calculate_hourly_instances(reminder: Reminder, date: date) -> list:
    """Calculate all hourly reminder times for a day"""
    times = []
    hours_in_day = 24
    interval = reminder.interval_value

    start_time = reminder.reminder_time or time(8, 0)  # Default 8 AM start

    num_instances = hours_in_day // interval
    for i in range(num_instances):
        hour = (start_time.hour + (i * interval)) % 24
        times.append(time(hour, start_time.minute))

    return times
```

### Frontend Components

#### Widget Layout

```
┌─────────────────────────────────────┐
│ Reminders                [+ Add]    │
├─────────────────────────────────────┤
│ Today - 3 reminders                 │
│                                     │
│ ☐ Take Medication 1      [✓]       │
│   8:00 AM                           │
│                                     │
│ ☐ Take Medication 2      [✓]       │
│   12:00 PM                          │
│                                     │
│ ☐ Trash Day              [✓]       │
│   Monday                            │
│                                     │
├─────────────────────────────────────┤
│ Overdue - 1 reminder                │
│                                     │
│ ⚠️ Water Plants          [✓]        │
│   Feb 7 (Yesterday)                 │
└─────────────────────────────────────┘
```

#### States

**Empty State:**
```
┌─────────────────────────────────────┐
│ Reminders                [+ Add]    │
├─────────────────────────────────────┐
│                                     │
│           📅                        │
│    No reminders today               │
│                                     │
│  [Set up your first reminder]       │
│                                     │
└─────────────────────────────────────┘
```

**All Dismissed:**
```
┌─────────────────────────────────────┐
│ Reminders                [+ Add]    │
├─────────────────────────────────────┤
│           ✅                        │
│    All done for today!              │
│                                     │
│  3 reminders completed              │
└─────────────────────────────────────┘
```

### Widget Settings

```javascript
{
  "show_completed_count": true,  // Show "X completed today"
  "show_overdue_section": true,  // Separate section for overdue
  "default_carry_over": true,    // Default for new reminders
  "notification_enabled": false, // Browser notifications (future)
  "notification_sound": false,   // Sound alert (future)
  "compact_view": false         // Smaller display
}
```

## User Experience Features

### Interaction Design

**Dismiss Action:**
- Single click on [✓] button
- Instant removal from list
- Subtle animation (fade out)
- No undo (but logged in history)

**Quick Add:**
- Floating "+" button
- Quick templates:
  - "Daily at 9 AM"
  - "Every 3 days"
  - "Weekdays only"
  - "Custom..."

**Visual Feedback:**
- Checkbox animation when dismissed
- Count badge updates in real-time
- Overdue items have red accent

### Display Priority

**Order of reminders:**
1. Overdue items (if enabled) - at top with red accent
2. Time-based (hourly) - sorted by time
3. Day-based - no specific order
4. Empty state if all dismissed

### Notifications (Future Enhancement)

**Browser Notifications:**
- Opt-in browser notification permission
- Notify at reminder time (for hourly)
- Notify at widget load if overdue reminders exist
- Click notification to open dashboard

**Sound Alerts:**
- Optional sound when reminder becomes active
- Different sounds for normal vs overdue

## Statistics & History (Future Enhancement)

### Completion Rate
- Track dismissed vs missed reminders
- Show percentage: "95% completion rate this month"
- Graph of completion over time

### Streak Tracking
- "7 day streak on Take Medication"
- Encourage consistency

### Most Missed
- Identify reminders frequently missed
- Suggest schedule changes

## Implementation Phases

### Phase 1: Core Reminder System (4-5 hours)
1. Database schema (Reminder + ReminderInstance tables)
2. Backend CRUD endpoints
3. Basic frontend widget display
4. Add reminder modal with form validation
5. Dismiss functionality

### Phase 2: Recurrence Logic (3-4 hours)
1. Interval calculation (hours, days, weeks, months)
2. Day-of-week logic
3. Hourly instance generation
4. Background job for midnight reset
5. Testing various recurrence patterns

### Phase 3: Overdue Handling (2-3 hours)
1. Carry-over vs auto-dismiss logic
2. Overdue visual indicators
3. Separate overdue section in widget
4. Configuration per reminder

### Phase 4: Polish & UX (2-3 hours)
1. Empty states and "all done" state
2. Animations for dismiss actions
3. Edit reminder functionality
4. Delete reminder with confirmation
5. Widget settings

### Phase 5: Advanced Features (4-6 hours)
1. Statistics and history view
2. Browser notifications
3. Sound alerts
4. Pause/snooze functionality
5. Completion rate tracking

## Estimated Total Effort
- **Phase 1 (Core):** 4-5 hours
- **Phase 2 (Recurrence):** 3-4 hours
- **Phase 3 (Overdue):** 2-3 hours
- **Phase 4 (Polish):** 2-3 hours
- **Phase 5 (Advanced):** 4-6 hours
- **Total:** 15-21 hours

## Priority
**High** - Very practical for daily use, fills a common need (medication reminders, chores, recurring tasks). Relatively straightforward implementation with high user value.

## Alternative: Simplified Version
If full implementation is too complex, consider a minimal version:
- Only day-of-week based reminders (no hourly)
- No overdue handling (all auto-dismiss)
- Manual refresh only (no midnight job)
- No statistics
- Estimated effort: 6-8 hours

## Integration Ideas

### Smart Home Integration
- Trigger smart home actions when dismissed
- Example: "Turn off kitchen lights" reminder triggers light automation

### Calendar Integration
- Sync reminders to calendar
- Import calendar events as reminders

### Voice Assistant (Future)
- "Alexa, what are my reminders today?"
- "Hey Google, dismiss medication reminder"

## Example Use Cases

1. **Medication Schedule**
   - "Take blood pressure medication" every 12 hours
   - Critical to not miss - carry over if missed

2. **Household Chores**
   - "Take out trash" every Monday and Thursday
   - Not critical - auto-dismiss if missed

3. **Self-Care**
   - "Drink water" every 2 hours during workday
   - Multiple instances per day
   - Auto-dismiss at end of day

4. **Pet Care**
   - "Feed cat" every 12 hours
   - Carry over if missed (important!)

5. **Plant Watering**
   - "Water plants" every 3 days
   - Carry over if missed (plants need water!)

6. **Exercise**
   - "Workout" Monday, Wednesday, Friday
   - Auto-dismiss if missed (can't make up past workouts)

## Design Mockup Notes

- Keep it simple and uncluttered
- Use checkboxes for visual satisfaction
- Clear distinction between today and overdue
- Minimize clicks to dismiss (single click)
- Mobile-friendly (large touch targets)
- Dark mode support essential
