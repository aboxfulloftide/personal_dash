#!/usr/bin/env python3
"""
Update Limited Run Games package with tracking URL.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.core.database import SessionLocal
from app.models.package import Package
from app.models.user import User

def update_package_url():
    """Update Limited Run Games package with tracking URL."""
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

        # Find the Limited Run Games package
        package = db.execute(
            select(Package).where(
                Package.user_id == user.id,
                Package.tracking_number == "ORDER #3411107"
            )
        ).scalar_one_or_none()

        if not package:
            print("❌ Package not found")
            return

        # Update tracking URL
        tracking_url = "https://limitedrungames.com/_t/c/v3/AAC93wCyxfwxy-3YucakKRZUmJz-TQogsaWJ7plagMsZ2vdb5y9UCwpuWo1sx9NsNVWXHNkUkg9fbrO6ulm6iRUnLkj_8AA-kmAKR131n71pn86orin5tuSwBKyiN3bYMyfunWk87p1Y7jLrFniVNKaa5UspkYdB8mV9eRZX9a-N9hf-vPH_mDGtNlvvVNvCTKOEPMObMLyyuetI2e-laNFYLqkC0MbzyLNNPE9cW5sNmAd3Z8WLwf3ntdRH29kmnPwjJTGJeBD6PTjyyjR8wKxM-NqJ8c0g13hyBIuQlU4WOf9f79kZhzyEIOsZhSS8rQLYq5eiRxEjOYu_LOVW58rb09q2ubA8KPltdGfxHMMg4Y0w_xZhXUQc_X7UaFkaCwx80CRTneZsAl2J_T2NsEFX0Nc9tB98aucfDna91m1xwlozax6gQ-vISJy7s6P3Gf-zdTySGUuY7OY0B_yEo8vS1ln6BjvvcdIIrAz1-ooVqcLhuszsUGT2E5hjzFptPPvnMv7S5qdTkFYkPtA60dbrdkVzREb8FxMZt72lTL_WsohFN20w018gDPhxVg5yBgTsbscfe8Hulau9W6W7u4aQsMCh_F8pca5qmaNnJyvBiIvoBq10mWyr6j1Sy9jWq-WgYsnSyAv8LtK49rztNHWNgQ37BEJphapJ21-Y5XkbbjQYjMJtAgRLcTQzmJtB7y1tRMdFNj7DuIe7Lcg-aKNiI6yUTfdtduPtLf4aUCBHtAyItww5n8G1pPwmNoR0So4GAeK7OSfWgFFb7PKQWsWqLFooXsrqzP0-Vukyb0meXTBqv8DFfM_Z3TStjgnpPj3NjUz7gwNNzsvWCODsXjj_L7Klx0q4RF0jPIjquwHXeHalNX-6Pb5U8Cy8-nWbyKf2XNopqd-auxzNMcnf-bnuCSSJ4S3ulSc7dk675HD_ljqr5jU9AeTBFZiGWcJ3QXsG9iCsuM4qZ7iDfMdEHs8_CHfPfCywDvICRjW1gKq41RcOHb6XB_3R6yO6Y296RtnvRVGBY0rq_JMacgO9hz8aZ3qmS1f0pvvojGNuRHPfOQEmCpJa99DapdwrJJyj4NqleSuQIzGarWrURxdWKaufQtq1T_xBfM1ZoCJ5NLR-EGCEIxDQITZ-MGIqTwq0l5wo8lqPn2bhObZCl4gGmjE4hT0Tf3bQWnQgdZ24t541Oe0YK36Z4tLYFQV4hEdOoC187vWxFcUdBguXpLUoyBqzh8elxVKjBVmN5f--umiNPExCS4BQ2Taxun6SYtoVulAzugF5K-1Rn4nLKlQGSUHf0oI4tIrzGbzrN1dI2pvNZKAYBuJRoS11gxkwbroXlrJliWbIm9ZVt-3t2duZ6kIMUk1s9y40NJD9gqf3LtbS0IBYygAPyviUhcnRHF9EfwOMGup6i4ayrtPkxgUxFGNIhgZ5koxI3kiZp-po_Kwod030r-tw7N_6gzjK8b3X-0tTRf8b9fODoQqJHE9OIZ2bEmVcKGL2VkXUmfg_TVRARBBUxvBGS1FzEbNiyt5X"

        package.tracking_url = tracking_url

        db.commit()

        print(f"✅ Updated Limited Run Games package!")
        print(f"   Package ID: {package.id}")
        print(f"   Tracking: {package.tracking_number}")
        print(f"   URL: {tracking_url[:100]}...")
        print(f"\n   Package now has clickable tracking link!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    print("=" * 60)
    print("Updating Limited Run Games Package URL")
    print("=" * 60)
    update_package_url()
    print("=" * 60)
