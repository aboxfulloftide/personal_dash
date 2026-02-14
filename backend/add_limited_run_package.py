#!/usr/bin/env python3
"""
Script to manually add the Limited Run Games package for matt@matheauphillips.com
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime
from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.package import Package
from app.models.user import User

def add_limited_run_package():
    """Add Limited Run Games package for user."""
    db = SessionLocal()
    try:
        # Find user
        user_result = db.execute(
            select(User).where(User.email == 'matt@matheauphillips.com')
        )
        user = user_result.scalar_one_or_none()

        if not user:
            print("❌ User not found: matt@matheauphillips.com")
            return

        print(f"✓ Found user: {user.email} (ID: {user.id})")

        # Check if package already exists
        existing = db.execute(
            select(Package).where(
                Package.user_id == user.id,
                Package.tracking_number == "ORDER #3411107"
            )
        ).scalar_one_or_none()

        if existing:
            print(f"⚠️  Package already exists (ID: {existing.id})")
            print(f"   Status: {'DISMISSED' if existing.dismissed else 'DELIVERED' if existing.delivered else 'ACTIVE'}")
            return

        # Create package
        package = Package(
            user_id=user.id,
            tracking_number="ORDER #3411107",
            carrier="other",
            description="Limited Run Games Order",
            status="Shipped",
            source="manual",  # Manually added
            email_source="matt@matheauphillips.com",
            email_subject="Limited Run Games - Order Shipped",
            email_sender="Limited Run Games <orders@limitedrungames.com>",
            email_date="Wed, Feb 12, 2026 1:47 PM",
            email_body_snippet="Your order #3411107 is on the way!",
            tracking_url=None,  # No tracking URL provided
            delivered=False,
            dismissed=False,
        )

        db.add(package)
        db.commit()
        db.refresh(package)

        print(f"\n✅ Successfully added Limited Run Games package!")
        print(f"   Package ID: {package.id}")
        print(f"   Tracking: {package.tracking_number}")
        print(f"   Carrier: {package.carrier}")
        print(f"   Description: {package.description}")
        print(f"   Created: {package.created_at}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Adding Limited Run Games Package")
    print("=" * 60)
    add_limited_run_package()
    print("=" * 60)
