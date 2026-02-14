#!/usr/bin/env python3
"""
One-time script to fix package tracking issues:
1. Remove duplicate packages (keep oldest)
2. Trigger cleanup of old delivered packages
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models.package import Package

def remove_duplicates():
    """Remove duplicate packages, keeping the oldest one."""
    db = SessionLocal()
    try:
        print("Checking for duplicate packages...")

        # Find duplicates: same user_id + tracking_number
        duplicates_query = (
            select(
                Package.user_id,
                Package.tracking_number,
                func.count(Package.id).label('count')
            )
            .group_by(Package.user_id, Package.tracking_number)
            .having(func.count(Package.id) > 1)
        )

        result = db.execute(duplicates_query)
        duplicates = list(result.all())

        if not duplicates:
            print("✓ No duplicates found")
            return

        print(f"Found {len(duplicates)} sets of duplicate packages")

        removed_count = 0
        for user_id, tracking_number, count in duplicates:
            print(f"\n  User {user_id}, Tracking {tracking_number}: {count} duplicates")

            # Get all packages with this user_id and tracking_number
            packages_query = select(Package).where(
                Package.user_id == user_id,
                Package.tracking_number == tracking_number
            ).order_by(Package.created_at.asc())  # Oldest first

            packages = list(db.execute(packages_query).scalars().all())

            # Keep the first (oldest), remove the rest
            keep = packages[0]
            remove = packages[1:]

            print(f"    Keeping: {keep.id} (created {keep.created_at})")
            for pkg in remove:
                print(f"    Removing: {pkg.id} (created {pkg.created_at})")
                db.delete(pkg)
                removed_count += 1

        if removed_count > 0:
            db.commit()
            print(f"\n✓ Removed {removed_count} duplicate packages")

    except Exception as e:
        print(f"Error removing duplicates: {e}")
        db.rollback()
    finally:
        db.close()


def cleanup_old_delivered():
    """Clean up delivered packages that should have been removed."""
    db = SessionLocal()
    try:
        print("\nChecking for old delivered packages...")

        now = datetime.now()  # Local time

        # Find delivered packages that should be cleaned up
        query = select(Package).where(
            Package.delivered == True,
            Package.delivered_at.isnot(None),
            Package.dismissed == False,
        )

        result = db.execute(query)
        delivered_packages = list(result.scalars().all())

        print(f"Found {len(delivered_packages)} delivered packages")
        print(f"Current time (local): {now}")

        removed_count = 0
        for package in delivered_packages:
            from datetime import timedelta

            delivered_date = package.delivered_at.date()
            next_midnight = datetime.combine(
                delivered_date + timedelta(days=1),
                datetime.min.time()
            )

            should_remove = now >= next_midnight

            print(f"\n  Package: {package.tracking_number}")
            print(f"    Delivered at: {package.delivered_at}")
            print(f"    Delivered date: {delivered_date}")
            print(f"    Next midnight: {next_midnight}")
            print(f"    Should remove: {should_remove}")

            if should_remove:
                package.dismissed = True
                package.dismissed_at = now
                removed_count += 1
                print(f"    ✓ Marked as dismissed")

        if removed_count > 0:
            db.commit()
            print(f"\n✓ Cleaned up {removed_count} old delivered packages")
        else:
            print("\n✓ No old delivered packages to clean up")

    except Exception as e:
        print(f"Error cleaning up delivered packages: {e}")
        db.rollback()
    finally:
        db.close()


def show_package_stats():
    """Show current package statistics."""
    db = SessionLocal()
    try:
        print("\nCurrent package statistics:")

        total = db.execute(select(func.count(Package.id))).scalar()
        delivered = db.execute(select(func.count(Package.id)).where(Package.delivered == True)).scalar()
        dismissed = db.execute(select(func.count(Package.id)).where(Package.dismissed == True)).scalar()
        active = db.execute(select(func.count(Package.id)).where(
            Package.dismissed == False,
            Package.delivered == False
        )).scalar()

        print(f"  Total packages: {total}")
        print(f"  Active (not delivered, not dismissed): {active}")
        print(f"  Delivered (not dismissed): {delivered - dismissed}")
        print(f"  Dismissed (removed): {dismissed}")

    except Exception as e:
        print(f"Error getting stats: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    print("=" * 60)
    print("Package Tracker Cleanup Script")
    print("=" * 60)

    show_package_stats()
    print()

    # Remove duplicates
    remove_duplicates()

    # Clean up old delivered packages
    cleanup_old_delivered()

    # Show final stats
    show_package_stats()

    print("\n" + "=" * 60)
    print("Cleanup complete!")
    print("=" * 60)
