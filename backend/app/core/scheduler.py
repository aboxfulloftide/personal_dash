"""
Background task scheduler for auto-scanning email for packages.
Uses APScheduler to run periodic tasks.
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.core.database import SessionLocal
from app.crud.email_credential import get_credentials_due_for_scan, update_scan_status
from app.crud.package import create_package, get_packages
from app.api.v1.endpoints.email_scanner import scan_imap_email
from app.schemas.package import PackageCreate
from app.core.encryption import decrypt_password

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
                        package_data = PackageCreate(
                            tracking_number=tracking_number,
                            carrier=tracking_info.carrier.lower(),
                            description=f"Auto: {tracking_info.found_in_subject[:50]}",
                            status="in_transit",
                        )
                        create_package(db, cred.user_id, package_data)
                        packages_added += 1
                    except Exception as e:
                        logger.error(f"Failed to create package: {e}")

                # Update scan status
                update_scan_status(
                    db,
                    cred,
                    status="success",
                    message=f"Found {len(scan_result.tracking_numbers)} tracking numbers",
                    packages_found=packages_added,
                )

                logger.info(f"Successfully scanned user {cred.user_id}: {packages_added} packages added")

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

    scheduler.start()
    logger.info("Background scheduler started - email auto-scan enabled")


def stop_scheduler():
    """Stop the background scheduler."""
    global scheduler

    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("Background scheduler stopped")
