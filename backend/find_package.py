#!/usr/bin/env python3
"""
Script to find packages for a specific user, including dismissed/delivered ones.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.package import Package
from app.models.user import User

def find_user_packages():
    """Find all packages for matt@matheauphillips user."""
    db = SessionLocal()
    try:
        # Find user by email
        user_result = db.execute(
            select(User).where(User.email == 'matt@matheauphillips.com')
        )
        user = user_result.scalar_one_or_none()

        if not user:
            print("❌ User not found: matt@matheauphillips.com")
            print("\nAvailable users:")
            all_users = db.execute(select(User)).scalars().all()
            for u in all_users:
                print(f"  - {u.email} (ID: {u.id})")
            return

        print(f"✓ Found user: {user.email} (ID: {user.id})")
        print("=" * 80)

        # Get ALL packages for this user (including dismissed and delivered)
        query = select(Package).where(Package.user_id == user.id).order_by(Package.created_at.desc())
        result = db.execute(query)
        packages = list(result.scalars().all())

        if not packages:
            print("No packages found for this user.")
            return

        print(f"\nTotal packages: {len(packages)}\n")

        # Categorize packages
        active = []
        delivered = []
        dismissed = []

        for pkg in packages:
            if pkg.dismissed:
                dismissed.append(pkg)
            elif pkg.delivered:
                delivered.append(pkg)
            else:
                active.append(pkg)

        # Show summary
        print(f"SUMMARY:")
        print(f"  Active:    {len(active)}")
        print(f"  Delivered: {len(delivered)}")
        print(f"  Dismissed: {len(dismissed)}")
        print("=" * 80)

        # Show all packages with "limited run" in description or email
        print("\n🔍 SEARCHING FOR 'LIMITED RUN' PACKAGES:")
        print("=" * 80)

        limited_run_packages = [
            pkg for pkg in packages
            if 'limited' in (pkg.description or '').lower()
            or 'limited' in (pkg.email_subject or '').lower()
            or 'limited' in (pkg.email_sender or '').lower()
            or 'limited run' in (pkg.email_body_snippet or '').lower()
        ]

        if limited_run_packages:
            print(f"Found {len(limited_run_packages)} package(s) matching 'limited run':\n")
            for pkg in limited_run_packages:
                print(f"ID: {pkg.id}")
                print(f"  Tracking: {pkg.tracking_number}")
                print(f"  Carrier: {pkg.carrier}")
                print(f"  Description: {pkg.description}")
                print(f"  Status: {'DISMISSED' if pkg.dismissed else 'DELIVERED' if pkg.delivered else 'ACTIVE'}")
                print(f"  Created: {pkg.created_at}")
                if pkg.delivered_at:
                    print(f"  Delivered: {pkg.delivered_at}")
                if pkg.dismissed_at:
                    print(f"  Dismissed: {pkg.dismissed_at}")
                if pkg.email_subject:
                    print(f"  Email Subject: {pkg.email_subject}")
                if pkg.email_sender:
                    print(f"  Email Sender: {pkg.email_sender}")
                print()
        else:
            print("❌ No packages found with 'limited run' in description or email")

        # Show ALL packages for this user
        print("\n📦 ALL PACKAGES FOR THIS USER:")
        print("=" * 80)

        for pkg in packages:
            status_icon = "❌" if pkg.dismissed else "✓" if pkg.delivered else "📦"
            status_text = "DISMISSED" if pkg.dismissed else "DELIVERED" if pkg.delivered else "ACTIVE"

            print(f"\n{status_icon} [{status_text}] ID: {pkg.id}")
            print(f"   Tracking: {pkg.tracking_number}")
            print(f"   Carrier: {pkg.carrier}")
            print(f"   Description: {pkg.description}")
            print(f"   Created: {pkg.created_at}")
            if pkg.email_subject:
                print(f"   Email Subject: {pkg.email_subject[:100]}")
            if pkg.delivered_at:
                print(f"   Delivered: {pkg.delivered_at}")
            if pkg.dismissed_at:
                print(f"   Dismissed: {pkg.dismissed_at}")

        print("\n" + "=" * 80)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    find_user_packages()
