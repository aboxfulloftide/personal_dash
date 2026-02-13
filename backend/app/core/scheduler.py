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

                # Get existing packages for this user
                existing_packages = get_packages(db, cred.user_id, include_delivered=False)
                existing_tracking_numbers = {pkg.tracking_number.upper() for pkg in existing_packages}

                packages_added = 0

                # Add new packages
                for tracking_info in scan_result.tracking_numbers:
                    tracking_number = tracking_info.tracking_number

                    # Skip if already tracking
                    if tracking_number.upper() in existing_tracking_numbers:
                        continue

                    # Create package
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
    """
    logger.info("Starting cleanup of old delivered packages")

    db = SessionLocal()
    try:
        # Get current time
        now = datetime.now(timezone.utc).replace(tzinfo=None)

        # Find all delivered packages that haven't been dismissed
        query = select(Package).where(
            Package.delivered == True,
            Package.delivered_at.isnot(None),
            Package.dismissed == False,
        )
        result = db.execute(query)
        delivered_packages = list(result.scalars().all())

        removed_count = 0
        for package in delivered_packages:
            try:
                # Calculate midnight of the day after delivery
                delivered_date = package.delivered_at.date()
                next_midnight = datetime.combine(
                    delivered_date + timedelta(days=1),
                    datetime.min.time()
                )

                logger.info(
                    f"Checking package: {package.tracking_number} - "
                    f"delivered_at={package.delivered_at}, "
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
                        f"Auto-removed delivered package: {package.tracking_number} "
                        f"(user_id={package.user_id}, delivered_at={package.delivered_at}, "
                        f"removed_at_midnight={next_midnight})"
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


def start_scheduler():
    """Start the background scheduler."""
    global scheduler

    if scheduler is not None:
        logger.warning("Scheduler already running")
        return

    scheduler = AsyncIOScheduler()

    # Run email scan every hour
    # The actual scanning interval per user is controlled by their scan_interval_hours setting
    scheduler.add_job(
        scan_user_email_task,
        trigger=IntervalTrigger(hours=1),
        id="email_auto_scan",
        name="Auto-scan email for package tracking numbers",
        replace_existing=True,
    )

    # Run cleanup of delivered packages every 6 hours
    scheduler.add_job(
        cleanup_delivered_packages_task,
        trigger=IntervalTrigger(hours=6),
        id="cleanup_delivered_packages",
        name="Auto-remove delivered packages at midnight next day",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Background scheduler started - email auto-scan and package cleanup enabled")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
