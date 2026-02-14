#!/usr/bin/env python3
"""
Check for duplicate packages in the database.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, func
from app.core.database import SessionLocal
from app.models.package import Package
from app.models.user import User

def check_duplicates():
    """Find and display duplicate packages."""
    db = SessionLocal()
    try:
        # Find user
        user_result = db.execute(
            select(User).where(User.email == 'matt@matheauphillips.com')
        )
        user = user_result.scalar_one_or_none()

        if not user:
            print("❌ User not found")
            return

        print(f"✓ Found user: {user.email} (ID: {user.id})")
        print("=" * 80)

        # Get ALL packages (including dismissed)
        query = select(Package).where(Package.user_id == user.id).order_by(Package.created_at.desc())
        result = db.execute(query)
        all_packages = list(result.scalars().all())

        print(f"\nTotal packages in database: {len(all_packages)}")

        # Find duplicates by tracking number
        duplicates_query = (
            select(
                Package.tracking_number,
                func.count(Package.id).label('count')
            )
            .where(Package.user_id == user.id)
            .group_by(Package.tracking_number)
            .having(func.count(Package.id) > 1)
        )

        result = db.execute(duplicates_query)
        duplicates = list(result.all())

        if duplicates:
            print(f"\n⚠️  Found {len(duplicates)} sets of duplicates:\n")
            for tracking_number, count in duplicates:
                print(f"Tracking: {tracking_number} - {count} copies")

                # Get all packages with this tracking number
                packages_query = select(Package).where(
                    Package.user_id == user.id,
                    Package.tracking_number == tracking_number
                ).order_by(Package.created_at.asc())

                packages = list(db.execute(packages_query).scalars().all())

                for pkg in packages:
                    status = "DISMISSED" if pkg.dismissed else "DELIVERED" if pkg.delivered else "ACTIVE"
                    print(f"  - ID {pkg.id}: {status} | Created: {pkg.created_at} | Desc: {pkg.description}")
                print()
        else:
            print("\n✓ No duplicates found!")

        # Show all ACTIVE (visible) packages
        active_packages = [p for p in all_packages if not p.dismissed]
        print(f"\n📦 ACTIVE/VISIBLE PACKAGES ({len(active_packages)}):")
        print("=" * 80)

        for pkg in active_packages:
            status = "DELIVERED" if pkg.delivered else "ACTIVE"
            print(f"\n[{status}] {pkg.description or 'No description'}")
            print(f"  ID: {pkg.id}")
            print(f"  Tracking: {pkg.tracking_number}")
            print(f"  Carrier: {pkg.carrier}")
            print(f"  Created: {pkg.created_at}")
            if pkg.delivered_at:
                print(f"  Delivered: {pkg.delivered_at}")

        # Check for "Corsair" specifically
        print("\n\n🔍 CORSAIR PACKAGES:")
        print("=" * 80)
        corsair_packages = [p for p in all_packages if 'corsair' in (p.description or '').lower() or 'nightsabre' in (p.description or '').lower()]

        if corsair_packages:
            print(f"Found {len(corsair_packages)} Corsair packages:\n")
            for pkg in corsair_packages:
                status = "DISMISSED" if pkg.dismissed else "DELIVERED" if pkg.delivered else "ACTIVE"
                print(f"[{status}] ID {pkg.id}: {pkg.description}")
                print(f"  Tracking: {pkg.tracking_number}")
                print(f"  Created: {pkg.created_at}")
                print(f"  Dismissed: {pkg.dismissed}, Delivered: {pkg.delivered}")
                print()
        else:
            print("No Corsair packages found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 80)
    print("Package Duplicate Check")
    print("=" * 80)
    check_duplicates()
    print("=" * 80)
