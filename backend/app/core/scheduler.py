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

# Global scheduler instance
scheduler = None


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
                        create_package(db, cred.user_id, package_data)
                        packages_added += 1
                    except Exception as e:
                        logger.error(f"Failed to create package: {e}")

                # Process delivery confirmations
                packages_delivered = 0
                for delivery_info in scan_result.delivery_confirmations:
                    tracking_number = delivery_info.tracking_number

                    # Try to mark existing package as delivered
                    try:
                        package = mark_package_delivered_by_tracking(
                            db,
                            cred.user_id,
                            tracking_number
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

                                # Only trigger if not already active or if message changed
                                already_active = widget.get("alert_active", False)
                                current_message = widget.get("alert_message", "")

                                if not already_active or current_message != message:
                                    trigger_widget_alert(
                                        db=db,
                                        user_id=dashboard.user_id,
                                        widget_id=widget_id,
                                        severity=widget_severity,
                                        message=message,
                                    )
                                    logger.info(f"Triggered {widget_severity} alert for widget {widget_id}: {message}")
                        else:
                            # No alerts - clear any existing widget alert
                            if widget.get("alert_active"):
                                acknowledge_widget_alert(db, dashboard.user_id, widget_id)
                                logger.info(f"Cleared alert for widget {widget_id} (no active weather alerts)")

                    except Exception as e:
                        logger.error(f"Error checking alerts for widget {widget_id}: {e}")

            except Exception as e:
                logger.error(f"Error checking alerts for user {dashboard.user_id}: {e}")

    except Exception as e:
        logger.error(f"Error in weather alerts monitoring task: {e}")
    finally:
        db.close()

    logger.info("Weather alerts monitoring completed")


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

    scheduler.start()
    logger.info("Background scheduler started - email auto-scan, package cleanup, speed test cleanup, and weather alerts monitoring enabled")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
