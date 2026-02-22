"""
Background task scheduler for auto-scanning email for packages.
Uses APScheduler to run periodic tasks.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta, timezone
from sqlalchemy import select

from app.core.database import SessionLocal
from app.crud.email_credential import get_credentials_due_for_scan, update_scan_status
from app.crud.package import create_package, get_packages, mark_package_delivered_by_tracking
from app.api.v1.endpoints.email_scanner import scan_imap_email, clean_email_subject
from app.schemas.package import PackageCreate
from app.core.encryption import decrypt_password
from app.models.package import Package
from app.models.widget import DashboardLayout
from app.crud.dashboard import trigger_widget_alert, acknowledge_widget_alert

logger = logging.getLogger(__name__)


def calculate_subject_similarity(subject1: str, subject2: str) -> float:
    """
    Calculate similarity between two email subjects using word overlap.
    Returns a score between 0.0 (no similarity) and 1.0 (identical).
    """
    # Clean and normalize subjects
    s1 = clean_email_subject(subject1).lower()
    s2 = clean_email_subject(subject2).lower()

    # Split into words and create sets
    words1 = set(s1.split())
    words2 = set(s2.split())

    # Remove very common words that don't help with matching
    common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'from'}
    words1 = words1 - common_words
    words2 = words2 - common_words

    # Handle empty sets
    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity (intersection over union)
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    return intersection / union if union > 0 else 0.0

# Global scheduler instance
scheduler = None

# In-memory cooldown tracker for weather alerts.
# Prevents re-alerting for the same weather event within WEATHER_ALERT_COOLDOWN_HOURS.
# Format: {widget_id: {"message": str, "triggered_at": datetime}}
_weather_alert_cooldowns: dict[str, dict] = {}
WEATHER_ALERT_COOLDOWN_HOURS = 4

# In-memory cooldown tracker for custom widget alerts (same 4-hour pattern).
_custom_widget_alert_cooldowns: dict[str, dict] = {}


async def scan_user_email_task():
    """
    Background task that scans email for all users who have auto-scan enabled
    and are due for scanning.
    """
    logger.info("Starting email auto-scan task")

    db = SessionLocal()
    try:
        # Get all credentials that are due for scanning
        credentials = get_credentials_due_for_scan(db)

        logger.info(f"Found {len(credentials)} users due for email scanning")

        for cred in credentials:
            try:
                logger.info(f"Scanning email for user {cred.user_id}")

                # Decrypt password
                password = decrypt_password(cred.encrypted_password)

                # Scan email
                scan_result = await scan_imap_email(
                    imap_server=cred.imap_server,
                    imap_port=cred.imap_port,
                    email_address=cred.email_address,
                    password=password,
                    days_back=cred.days_to_scan,
                )

                # Get ALL packages for this user (including delivered and dismissed)
                # This prevents re-creating packages that were manually removed
                query = select(Package).where(Package.user_id == cred.user_id)
                result = db.execute(query)
                all_packages = list(result.scalars().all())

                # Normalize tracking numbers for comparison (strip ORDER # prefix)
                existing_tracking_numbers = set()
                for pkg in all_packages:
                    tracking = pkg.tracking_number.upper()
                    existing_tracking_numbers.add(tracking)
                    # Also add normalized version without "ORDER #" prefix
                    if tracking.startswith("ORDER #"):
                        normalized = tracking.replace("ORDER #", "").strip()
                        existing_tracking_numbers.add(normalized)

                logger.info(f"User {cred.user_id} has {len(all_packages)} total packages in database (checking against all to prevent duplicates/reappearing)")

                packages_added = 0

                # Track which email subjects we've already created packages for
                # in THIS scan run, to prevent multiple false-positive tracking
                # numbers from the same email creating duplicate packages.
                emails_already_packaged = set()

                # Add new packages
                for tracking_info in scan_result.tracking_numbers:
                    tracking_number = tracking_info.tracking_number

                    # Normalize tracking number for comparison
                    tracking_upper = tracking_number.upper()

                    # Also check normalized version (without ORDER # prefix)
                    tracking_normalized = tracking_upper.replace("ORDER #", "").strip()

                    # Check if this is an exact duplicate
                    if tracking_upper in existing_tracking_numbers:
                        logger.info(f"Skipping exact duplicate: {tracking_number}")
                        continue

                    # Check if this tracking number matches an existing ORDER # package
                    # If so, UPDATE the existing package instead of creating a duplicate
                    if tracking_normalized in existing_tracking_numbers and not tracking_number.startswith("ORDER #"):
                        # Find the existing order-based package
                        existing_order = None
                        for pkg in all_packages:
                            if pkg.tracking_number.upper() == f"ORDER #{tracking_normalized}":
                                existing_order = pkg
                                break

                        if existing_order and not existing_order.dismissed:
                            # Update the existing order with real tracking number
                            logger.info(f"Updating existing order {existing_order.tracking_number} with tracking number {tracking_number}")
                            existing_order.tracking_number = tracking_number
                            existing_order.carrier = tracking_info.carrier.lower()
                            # Update description if the new one is better (has "Shipped")
                            if "shipped" in tracking_info.found_in_subject.lower():
                                cleaned_subject = clean_email_subject(tracking_info.found_in_subject)
                                existing_order.description = f"Auto: {cleaned_subject[:50]}"
                            db.commit()
                            # Update tracking sets so subsequent iterations see the change
                            existing_tracking_numbers.add(tracking_upper)
                            existing_tracking_numbers.add(tracking_normalized)
                            continue

                    # Check if this is an ORDER # and the real tracking number already exists
                    # If so, skip creating the ORDER # duplicate (reverse of above case)
                    if tracking_number.startswith("ORDER #") and tracking_normalized in existing_tracking_numbers:
                        logger.info(f"Skipping ORDER # duplicate - real tracking number already exists: {tracking_normalized}")
                        continue

                    # LAYER 3a: Per-email deduplication
                    # If we already created a package from this exact email (same subject+sender),
                    # skip any additional tracking numbers from it — they are likely false positives
                    # (e.g., 12-digit order numbers matching the FedEx regex).
                    email_key = (tracking_info.found_in_subject, tracking_info.email_sender)
                    if email_key in emails_already_packaged:
                        logger.info(
                            f"Skipping additional tracking number from same email "
                            f"(already created package from this email): {tracking_number} "
                            f"Subject: '{tracking_info.found_in_subject[:60]}'"
                        )
                        continue

                    # LAYER 3b: Check for similar subjects in recent packages (last 7 days)
                    # This catches cases where duplicate emails come in with slightly different subjects
                    # but no tracking/order numbers yet (e.g., "Order Placed" then "Shipped" emails)
                    seven_days_ago = datetime.now() - timedelta(days=7)
                    similar_found = False

                    for existing_pkg in all_packages:
                        # Only check recent packages from same user
                        if existing_pkg.created_at < seven_days_ago:
                            continue

                        # Skip if already dismissed
                        if existing_pkg.dismissed:
                            continue

                        # Calculate subject similarity
                        if existing_pkg.email_subject and tracking_info.found_in_subject:
                            similarity = calculate_subject_similarity(
                                existing_pkg.email_subject,
                                tracking_info.found_in_subject
                            )

                            # If subjects are very similar (>70% word overlap), consider it a duplicate
                            if similarity > 0.7:
                                logger.info(
                                    f"Skipping likely duplicate based on subject similarity ({similarity:.0%}): "
                                    f"New: '{tracking_info.found_in_subject[:60]}...' vs "
                                    f"Existing #{existing_pkg.id}: '{existing_pkg.email_subject[:60]}...'"
                                )

                                # If the new email has better info (has tracking, old doesn't), update it
                                if tracking_number and not tracking_number.startswith("ORDER #") and existing_pkg.tracking_number.startswith("ORDER #"):
                                    logger.info(f"Updating package #{existing_pkg.id} with better tracking info: {tracking_number}")
                                    existing_pkg.tracking_number = tracking_number
                                    existing_pkg.carrier = tracking_info.carrier.lower()
                                    if "shipped" in tracking_info.found_in_subject.lower():
                                        cleaned_subject = clean_email_subject(tracking_info.found_in_subject)
                                        existing_pkg.description = f"Auto: {cleaned_subject[:50]}"
                                    db.commit()

                                similar_found = True
                                break

                    if similar_found:
                        continue

                    # Create new package
                    try:
                        # Clean the subject line
                        cleaned_subject = clean_email_subject(tracking_info.found_in_subject)

                        package_data = PackageCreate(
                            tracking_number=tracking_number,
                            carrier=tracking_info.carrier.lower(),
                            description=f"Auto: {cleaned_subject[:50]}",
                            status="in_transit",
                            email_source=cred.email_address,
                            email_subject=tracking_info.found_in_subject,  # Keep original for preview
                            email_sender=tracking_info.email_sender,
                            email_date=tracking_info.found_date,
                            email_body_snippet=tracking_info.email_body_snippet,
                            tracking_url=tracking_info.tracking_url,
                        )
                        new_pkg = create_package(db, cred.user_id, package_data)
                        packages_added += 1

                        # CRITICAL: Update dedup state so subsequent loop iterations
                        # can see this newly created package. Without this, multiple
                        # tracking numbers from the same email all pass dedup checks.
                        existing_tracking_numbers.add(tracking_upper)
                        existing_tracking_numbers.add(tracking_normalized)
                        if new_pkg:
                            all_packages.append(new_pkg)
                        emails_already_packaged.add(email_key)
                    except Exception as e:
                        logger.error(f"Failed to create package: {e}")

                # Process delivery confirmations
                packages_delivered = 0
                for delivery_info in scan_result.delivery_confirmations:
                    tracking_number = delivery_info.tracking_number
                    delivery_subject = delivery_info.found_in_subject

                    # Try to mark existing package as delivered
                    # Pass the subject to enable subject similarity matching as fallback
                    try:
                        package = mark_package_delivered_by_tracking(
                            db,
                            cred.user_id,
                            tracking_number,
                            delivery_subject=delivery_subject
                        )
                        if package:
                            packages_delivered += 1
                            logger.info(f"Marked package {tracking_number} as delivered for user {cred.user_id}")
                    except Exception as e:
                        logger.error(f"Failed to mark package as delivered: {e}")

                # Update scan status
                status_message = f"Found {len(scan_result.tracking_numbers)} new, {len(scan_result.delivery_confirmations)} delivered"
                update_scan_status(
                    db,
                    cred,
                    status="success",
                    message=status_message,
                    packages_found=packages_added,
                )

                logger.info(f"Successfully scanned user {cred.user_id}: {packages_added} added, {packages_delivered} delivered")

            except Exception as e:
                logger.error(f"Error scanning email for user {cred.user_id}: {e}")
                update_scan_status(
                    db,
                    cred,
                    status="error",
                    message=str(e)[:500],
                    packages_found=0,
                )

    except Exception as e:
        logger.error(f"Error in email auto-scan task: {e}")
    finally:
        db.close()

    logger.info("Email auto-scan task completed")


async def cleanup_delivered_packages_task():
    """
    Background task that removes delivered packages at midnight the day after delivery.
    Marks them as dismissed (soft delete).

    Example: Package delivered 3 PM Monday → removed at 12 AM Tuesday (midnight)

    IMPORTANT: Uses LOCAL time (server timezone), not UTC, because "midnight" is a
    user-facing concept that should match the user's local day/night cycle.
    """
    logger.info("Starting cleanup of old delivered packages")

    db = SessionLocal()
    try:
        # Get current time in LOCAL timezone (not UTC!)
        # This is critical - "midnight" should match user's local timezone
        now = datetime.now()  # Local time

        # Find all delivered packages that haven't been dismissed
        query = select(Package).where(
            Package.delivered == True,
            Package.delivered_at.isnot(None),
            Package.dismissed == False,
        )
        result = db.execute(query)
        delivered_packages = list(result.scalars().all())

        logger.info(f"Found {len(delivered_packages)} delivered packages to check for cleanup")
        logger.info(f"Current time (local): {now}")

        removed_count = 0
        for package in delivered_packages:
            try:
                # delivered_at is stored in UTC, but we need to interpret it in local time
                # for "midnight of the next day" calculation
                delivered_date = package.delivered_at.date()
                next_midnight = datetime.combine(
                    delivered_date + timedelta(days=1),
                    datetime.min.time()
                )

                logger.info(
                    f"Checking package: {package.tracking_number} - "
                    f"delivered_at={package.delivered_at}, "
                    f"delivered_date={delivered_date}, "
                    f"next_midnight={next_midnight}, "
                    f"now={now}, "
                    f"should_remove={now >= next_midnight}"
                )

                # Remove if we're past that midnight
                if now >= next_midnight:
                    package.dismissed = True
                    package.dismissed_at = now
                    removed_count += 1
                    logger.info(
                        f"✓ Auto-removed delivered package: {package.tracking_number} "
                        f"(user_id={package.user_id}, delivered_at={package.delivered_at}, "
                        f"removed_at_midnight={next_midnight})"
                    )
                else:
                    logger.info(
                        f"  Package {package.tracking_number} not ready for removal yet "
                        f"(needs {(next_midnight - now).total_seconds() / 3600:.1f} more hours)"
                    )
            except Exception as e:
                logger.error(f"Failed to remove package {package.id}: {e}")

        if removed_count > 0:
            db.commit()
            logger.info(f"Auto-removed {removed_count} delivered packages")
        else:
            logger.info("No delivered packages to remove")

    except Exception as e:
        logger.error(f"Error in cleanup delivered packages task: {e}")
        db.rollback()
    finally:
        db.close()

    logger.info("Cleanup delivered packages task completed")


def cleanup_old_speed_tests_task():
    """
    Background task that removes speed test results older than 90 days.
    Runs daily to keep the database clean.
    """
    logger.info("Starting cleanup of old speed test results")

    db = SessionLocal()
    try:
        from app.crud.speedtest import cleanup_old_speed_tests

        deleted_count = cleanup_old_speed_tests(db, days=90)
        logger.info(f"Cleaned up {deleted_count} old speed test results")

    except Exception as e:
        logger.error(f"Error in cleanup old speed tests task: {e}")
    finally:
        db.close()

    logger.info("Cleanup old speed tests task completed")


async def reminders_midnight_reset_task():
    """
    Background task that runs at midnight to:
    1. Mark pending reminders from previous days as 'missed' (if carry_over=False)
    2. Mark pending reminders from previous days as 'overdue' (if carry_over=True)
    3. Generate new reminder instances for today based on active reminders

    Runs every 30 minutes to catch midnight quickly (actual logic checks date).
    """
    logger.info("Starting reminders midnight reset task")

    db = SessionLocal()
    try:
        from app.crud.reminder import mark_missed_reminders, mark_overdue_reminders, create_reminder_instance, check_instance_exists
        from app.models.reminder import Reminder
        from datetime import date, time, timedelta

        # Mark missed and overdue reminders from previous days
        missed_count = mark_missed_reminders(db)
        overdue_count = mark_overdue_reminders(db)

        if missed_count > 0 or overdue_count > 0:
            logger.info(f"Marked {missed_count} missed and {overdue_count} overdue reminders")

        # Generate new instances for today
        today = date.today()
        today_weekday = today.weekday()  # 0 = Monday, 6 = Sunday

        # Get all active reminders
        query = select(Reminder).where(
            Reminder.is_active == True,
            Reminder.start_date <= today
        )
        result = db.execute(query)
        active_reminders = list(result.scalars().all())

        logger.info(f"Checking {len(active_reminders)} active reminders for instance generation")

        instances_created = 0
        for reminder in active_reminders:
            try:
                from app.schemas.reminder import ReminderInstanceCreate

                # Check recurrence type
                if reminder.recurrence_type == "day_of_week":
                    # Day-of-week based reminder
                    if reminder.days_of_week:
                        days = [int(d.strip()) for d in reminder.days_of_week.split(",")]
                        if today_weekday in days:
                            # Check if instance already exists
                            if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                                instance_data = ReminderInstanceCreate(
                                    reminder_id=reminder.id,
                                    due_date=today,
                                    due_time=reminder.reminder_time,
                                    status="pending",
                                    is_overdue=False,
                                )
                                create_reminder_instance(db, reminder.user_id, instance_data)
                                instances_created += 1
                                logger.info(f"Created instance for day-of-week reminder {reminder.id}: {reminder.title}")

                elif reminder.recurrence_type == "interval":
                    # Interval-based reminder
                    if reminder.interval_unit == "hours":
                        # Hourly reminders - create multiple instances for today
                        hours_per_day = 24
                        interval = reminder.interval_value
                        instances_per_day = hours_per_day // interval

                        for i in range(instances_per_day):
                            hour = i * interval
                            due_time = time(hour=hour, minute=0, second=0)

                            if not check_instance_exists(db, reminder.id, today, due_time, i + 1):
                                instance_data = ReminderInstanceCreate(
                                    reminder_id=reminder.id,
                                    due_date=today,
                                    due_time=due_time,
                                    instance_number=i + 1,
                                    status="pending",
                                    is_overdue=False,
                                )
                                create_reminder_instance(db, reminder.user_id, instance_data)
                                instances_created += 1

                    elif reminder.interval_unit == "days":
                        # Daily interval (every N days)
                        days_since_start = (today - reminder.start_date).days
                        if days_since_start % reminder.interval_value == 0:
                            if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                                instance_data = ReminderInstanceCreate(
                                    reminder_id=reminder.id,
                                    due_date=today,
                                    due_time=reminder.reminder_time,
                                    status="pending",
                                    is_overdue=False,
                                )
                                create_reminder_instance(db, reminder.user_id, instance_data)
                                instances_created += 1
                                logger.info(f"Created instance for daily interval reminder {reminder.id}: {reminder.title}")

                    elif reminder.interval_unit == "weeks":
                        # Weekly interval (every N weeks)
                        days_since_start = (today - reminder.start_date).days
                        weeks_since_start = days_since_start // 7
                        if weeks_since_start % reminder.interval_value == 0 and today.weekday() == reminder.start_date.weekday():
                            if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                                instance_data = ReminderInstanceCreate(
                                    reminder_id=reminder.id,
                                    due_date=today,
                                    due_time=reminder.reminder_time,
                                    status="pending",
                                    is_overdue=False,
                                )
                                create_reminder_instance(db, reminder.user_id, instance_data)
                                instances_created += 1
                                logger.info(f"Created instance for weekly interval reminder {reminder.id}: {reminder.title}")

                    elif reminder.interval_unit == "months":
                        # Monthly interval (every N months)
                        months_since_start = (today.year - reminder.start_date.year) * 12 + (today.month - reminder.start_date.month)
                        if months_since_start % reminder.interval_value == 0 and today.day == reminder.start_date.day:
                            if not check_instance_exists(db, reminder.id, today, reminder.reminder_time):
                                instance_data = ReminderInstanceCreate(
                                    reminder_id=reminder.id,
                                    due_date=today,
                                    due_time=reminder.reminder_time,
                                    status="pending",
                                    is_overdue=False,
                                )
                                create_reminder_instance(db, reminder.user_id, instance_data)
                                instances_created += 1
                                logger.info(f"Created instance for monthly interval reminder {reminder.id}: {reminder.title}")

            except Exception as e:
                logger.error(f"Error processing reminder {reminder.id}: {e}")

        if instances_created > 0:
            logger.info(f"Created {instances_created} new reminder instances for today")
        else:
            logger.info("No new reminder instances created")

    except Exception as e:
        logger.error(f"Error in reminders midnight reset task: {e}")
    finally:
        db.close()

    logger.info("Reminders midnight reset task completed")


async def monitor_weather_alerts_task():
    """
    Background task to check for severe weather alerts and trigger widget alerts.
    Runs every 5 minutes.
    """
    logger.info("Starting weather alerts monitoring")

    db = SessionLocal()
    try:
        # Import here to avoid circular imports
        from app.api.v1.endpoints.weather import geocode_location, fetch_nws_alerts

        # Get all users with dashboards
        query = select(DashboardLayout)
        result = db.execute(query)
        dashboards = list(result.scalars().all())

        logger.info(f"Checking weather alerts for {len(dashboards)} users")

        for dashboard in dashboards:
            try:
                if not dashboard.layout:
                    continue

                widgets = dashboard.layout.get("widgets", [])

                # Find weather widgets
                for widget in widgets:
                    if widget.get("type") != "weather":
                        continue

                    config = widget.get("config", {})
                    location = config.get("location")

                    if not location:
                        continue

                    widget_id = widget.get("id")
                    if not widget_id:
                        continue

                    try:
                        # Geocode and fetch alerts
                        lat, lon, _ = await geocode_location(location)
                        alerts = await fetch_nws_alerts(lat, lon)

                        # Determine if widget alert should be triggered
                        if alerts.alert_count > 0:
                            # Map NWS severity to widget severity
                            severity_map = {
                                "Extreme": "critical",
                                "Severe": "warning",
                                "Moderate": "info",
                                "Minor": "info",
                            }

                            widget_severity = severity_map.get(alerts.highest_severity, "info")

                            # Check urgency - only trigger for immediate/expected
                            has_urgent = any(
                                a.urgency in ["Immediate", "Expected"]
                                for a in alerts.alerts
                            )

                            if has_urgent:
                                # Build alert message
                                event_types = ", ".join(set(a.event for a in alerts.alerts[:3]))  # Limit to 3 events
                                if alerts.alert_count > 3:
                                    event_types += f", +{alerts.alert_count - 3} more"

                                message = f"Severe Weather: {event_types}"

                                # Cooldown check: same alert won't fire more than once per
                                # WEATHER_ALERT_COOLDOWN_HOURS hours.  A new/different alert
                                # always fires immediately.
                                now = datetime.now()
                                cooldown_info = _weather_alert_cooldowns.get(widget_id)

                                if cooldown_info is None:
                                    should_trigger = True  # First time seeing any alert
                                elif cooldown_info["message"] != message:
                                    should_trigger = True  # Different alert — show immediately
                                elif (now - cooldown_info["triggered_at"]).total_seconds() > WEATHER_ALERT_COOLDOWN_HOURS * 3600:
                                    should_trigger = True  # Same alert but cooldown expired
                                else:
                                    should_trigger = False  # Same alert within cooldown — skip
                                    logger.debug(
                                        f"Skipping repeat alert for widget {widget_id} "
                                        f"(cooldown {WEATHER_ALERT_COOLDOWN_HOURS}h, "
                                        f"last triggered {cooldown_info['triggered_at']}): {message}"
                                    )

                                if should_trigger:
                                    trigger_widget_alert(
                                        db=db,
                                        user_id=dashboard.user_id,
                                        widget_id=widget_id,
                                        severity=widget_severity,
                                        message=message,
                                    )
                                    _weather_alert_cooldowns[widget_id] = {
                                        "message": message,
                                        "triggered_at": now,
                                    }
                                    logger.info(f"Triggered {widget_severity} alert for widget {widget_id}: {message}")
                        else:
                            # No alerts - clear any existing widget alert and reset cooldown
                            # so the next occurrence of the same event will alert again.
                            if widget.get("alert_active"):
                                acknowledge_widget_alert(db, dashboard.user_id, widget_id)
                                logger.info(f"Cleared alert for widget {widget_id} (no active weather alerts)")
                            _weather_alert_cooldowns.pop(widget_id, None)

                    except Exception as e:
                        logger.error(f"Error checking alerts for widget {widget_id}: {e}")

            except Exception as e:
                logger.error(f"Error checking alerts for user {dashboard.user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in weather alerts monitoring task: {e}")
    finally:
        db.close()

    logger.info("Weather alerts monitoring completed")


async def sync_garmin_task():
    """
    Background task that syncs Garmin data for all users with sync enabled.
    Runs every 6 hours, fetches last 7 days to backfill gaps.
    """
    logger.info("Starting Garmin sync task")

    db = SessionLocal()
    try:
        from sqlalchemy import select
        from app.models.fitness import GarminCredential
        from app.api.v1.endpoints.fitness import sync_garmin_for_user

        stmt = select(GarminCredential).where(GarminCredential.sync_enabled == True)
        result = db.execute(stmt)
        credentials = list(result.scalars().all())

        logger.info(f"Found {len(credentials)} users with Garmin sync enabled")

        for cred in credentials:
            try:
                await sync_garmin_for_user(db, cred.user_id, days_back=7)
            except Exception as e:
                logger.error(f"Garmin sync failed for user {cred.user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in Garmin sync task: {e}")
    finally:
        db.close()

    logger.info("Garmin sync task completed")


async def monitor_custom_widget_alerts_task():
    """
    Background task that scans all custom widgets for alert_active items
    and triggers/clears widget-level alerts with a 4-hour cooldown.
    """
    logger.info("Starting custom widget alerts monitoring task")

    db = SessionLocal()
    try:
        from app.crud.custom_widget import get_alert_status

        # Get all users with dashboards
        query = select(DashboardLayout)
        result = db.execute(query)
        dashboards = list(result.scalars().all())

        for dashboard in dashboards:
            try:
                if not dashboard.layout:
                    continue

                widgets = dashboard.layout.get("widgets", [])

                for widget in widgets:
                    if widget.get("type") != "custom_widget":
                        continue

                    widget_id = widget.get("id")
                    if not widget_id:
                        continue

                    try:
                        alert_active, alert_severity, alert_message = get_alert_status(
                            db, dashboard.user_id, widget_id
                        )

                        if alert_active and alert_message:
                            now = datetime.now()
                            cooldown_info = _custom_widget_alert_cooldowns.get(widget_id)

                            if cooldown_info is None:
                                should_trigger = True
                            elif cooldown_info["message"] != alert_message:
                                should_trigger = True
                            elif (now - cooldown_info["triggered_at"]).total_seconds() > WEATHER_ALERT_COOLDOWN_HOURS * 3600:
                                should_trigger = True
                            else:
                                should_trigger = False
                                logger.debug(
                                    f"Skipping repeat custom widget alert for {widget_id} "
                                    f"(cooldown {WEATHER_ALERT_COOLDOWN_HOURS}h): {alert_message}"
                                )

                            if should_trigger:
                                trigger_widget_alert(
                                    db=db,
                                    user_id=dashboard.user_id,
                                    widget_id=widget_id,
                                    severity=alert_severity,
                                    message=alert_message,
                                )
                                _custom_widget_alert_cooldowns[widget_id] = {
                                    "message": alert_message,
                                    "triggered_at": now,
                                }
                                logger.info(f"Triggered {alert_severity} alert for custom widget {widget_id}: {alert_message}")
                        else:
                            # No alerts — clear any existing widget alert and reset cooldown
                            if widget.get("alert_active"):
                                acknowledge_widget_alert(db, dashboard.user_id, widget_id)
                                logger.info(f"Cleared alert for custom widget {widget_id}")
                            _custom_widget_alert_cooldowns.pop(widget_id, None)

                    except Exception as e:
                        logger.error(f"Error checking alerts for custom widget {widget_id}: {e}")

            except Exception as e:
                logger.error(f"Error checking custom widget alerts for user {dashboard.user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in custom widget alerts monitoring task: {e}")
    finally:
        db.close()

    logger.info("Custom widget alerts monitoring completed")


def start_scheduler():
    """Start the background scheduler."""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = AsyncIOScheduler()

    # Run email scan every 30 minutes
    # The actual scanning interval per user is controlled by their scan_interval_hours setting
    scheduler.add_job(
        scan_user_email_task,
        trigger=IntervalTrigger(minutes=30),
        id="email_auto_scan",
        name="Auto-scan email for package tracking numbers",
        replace_existing=True,
    )

    # Run cleanup of delivered packages every 30 minutes (catches packages quickly after midnight)
    scheduler.add_job(
        cleanup_delivered_packages_task,
        trigger=IntervalTrigger(minutes=30),
        id="cleanup_delivered_packages",
        name="Auto-remove delivered packages at midnight next day",
        replace_existing=True,
    )

    # Run cleanup of old speed test results daily
    scheduler.add_job(
        cleanup_old_speed_tests_task,
        trigger=IntervalTrigger(days=1),
        id="cleanup_speed_tests",
        name="Cleanup old speed test results (90+ days)",
        replace_existing=True,
    )

    # Monitor weather alerts every 5 minutes
    scheduler.add_job(
        monitor_weather_alerts_task,
        trigger=IntervalTrigger(minutes=5),
        id="monitor_weather_alerts",
        name="Monitor severe weather alerts and trigger widget notifications",
        replace_existing=True,
    )

    # Run reminders midnight reset every 30 minutes (catches midnight quickly)
    scheduler.add_job(
        reminders_midnight_reset_task,
        trigger=IntervalTrigger(minutes=30),
        id="reminders_midnight_reset",
        name="Reset reminders at midnight and generate daily instances",
        replace_existing=True,
    )

    # Monitor custom widget alerts every 5 minutes
    scheduler.add_job(
        monitor_custom_widget_alerts_task,
        trigger=IntervalTrigger(minutes=5),
        id="monitor_custom_widget_alerts",
        name="Monitor custom widget alerts and trigger widget notifications",
        replace_existing=True,
    )

    # Sync Garmin data every 6 hours
    scheduler.add_job(
        sync_garmin_task,
        trigger=IntervalTrigger(hours=6),
        id="sync_garmin",
        name="Sync Garmin Connect data (steps, sleep, HR, activities)",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Background scheduler started - email auto-scan, package cleanup, speed test cleanup, weather alerts monitoring, reminders, custom widget alerts, and Garmin sync enabled")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
