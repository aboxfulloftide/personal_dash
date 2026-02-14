#!/usr/bin/env python3
"""
Fix the Corsair duplicate by merging the two packages.
Keep the older one (ORDER #...) and update it with the real tracking number.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.package import Package
from app.models.user import User

def fix_corsair_duplicate():
    """Merge the two Corsair packages."""
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

        # Find both Corsair packages
        pkg_51 = db.get(Package, 51)  # ORDER #114-0201237-2525863
        pkg_52 = db.get(Package, 52)  # 114-0201237-2525863

        if not pkg_51 or not pkg_52:
            print("❌ One or both packages not found")
            return

        print("Found both Corsair packages:")
        print(f"  ID 51: {pkg_51.tracking_number} (created {pkg_51.created_at})")
        print(f"  ID 52: {pkg_52.tracking_number} (created {pkg_52.created_at})")

        # Update the older package (51) with the real tracking number
        print(f"\nMerging: Updating ID 51 with real tracking number...")

        pkg_51.tracking_number = "114-0201237-2525863"  # Real tracking number
        pkg_51.carrier = "amazon"  # Update carrier
        pkg_51.description = pkg_52.description  # Use "Shipped" description

        # Delete the newer duplicate (52)
        db.delete(pkg_52)

        db.commit()

        print(f"✅ Fixed!")
        print(f"   Kept ID 51: {pkg_51.tracking_number}")
        print(f"   Deleted ID 52 (duplicate)")
        print(f"\n   Package 51 now has the real Amazon tracking number")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Fixing Corsair Duplicate")
    print("=" * 60)
    fix_corsair_duplicate()
    print("=" * 60)
