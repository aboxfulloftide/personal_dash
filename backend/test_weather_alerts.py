#!/usr/bin/env python3
"""
Test script for weather alerts functionality.
Run this to verify the weather alerts implementation is working.
"""
import asyncio
import sys


async def test_fetch_alerts():
    """Test fetching weather alerts from NWS API."""
    print("Testing weather alerts implementation...")
    print("-" * 60)

    # Import the function
    try:
        from app.api.v1.endpoints.weather import fetch_nws_alerts, geocode_location
    except ImportError as e:
        print(f"❌ Error importing modules: {e}")
        sys.exit(1)

    # Test locations
    test_locations = [
        ("Boston, MA", 42.3601, -71.0589),
        ("Oklahoma City, OK", 35.4676, -97.5164),  # Tornado-prone area
        ("Miami, FL", 25.7617, -80.1918),  # Hurricane-prone area
    ]

    for city, lat, lon in test_locations:
        print(f"\n📍 Testing: {city} ({lat}, {lon})")
        print("-" * 60)

        try:
            # Fetch alerts
            alerts = await fetch_nws_alerts(lat, lon)

            print(f"✅ API call successful")
            print(f"   Alert count: {alerts.alert_count}")
            print(f"   Highest severity: {alerts.highest_severity or 'None'}")

            if alerts.alert_count > 0:
                print(f"\n   🚨 ACTIVE ALERTS:")
                for i, alert in enumerate(alerts.alerts, 1):
                    print(f"\n   Alert {i}:")
                    print(f"     Event: {alert.event}")
                    print(f"     Severity: {alert.severity}")
                    print(f"     Urgency: {alert.urgency}")
                    print(f"     Headline: {alert.headline[:80]}...")
                    print(f"     Areas: {alert.affected_areas[:60]}...")
                    print(f"     Expires: {alert.expires}")
                    print(f"     Has geometry: {'Yes' if alert.geometry else 'No'}")
            else:
                print(f"   ✓ No active weather alerts (good news!)")

        except Exception as e:
            print(f"❌ Error fetching alerts: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)


async def test_geocoding():
    """Test geocoding functionality."""
    print("\n\nTesting geocoding...")
    print("-" * 60)

    from app.api.v1.endpoints.weather import geocode_location

    test_queries = [
        "Boston, MA",
        "42.3601,-71.0589",  # Coordinates format
        "New York City",
    ]

    for query in test_queries:
        print(f"\n📍 Query: {query}")
        try:
            lat, lon, display_name = await geocode_location(query)
            print(f"✅ Result: {display_name}")
            print(f"   Coordinates: {lat}, {lon}")
        except Exception as e:
            print(f"❌ Error: {e}")


async def test_monitor_task():
    """Test the background monitoring task."""
    print("\n\nTesting background monitoring task...")
    print("-" * 60)

    try:
        from app.core.scheduler import monitor_weather_alerts_task

        print("Running weather alerts monitoring task...")
        await monitor_weather_alerts_task()
        print("✅ Task completed successfully")

    except Exception as e:
        print(f"❌ Error running task: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("\n🌩️  WEATHER ALERTS IMPLEMENTATION TEST")
    print("=" * 60)

    # Run tests
    asyncio.run(test_geocoding())
    asyncio.run(test_fetch_alerts())
    asyncio.run(test_monitor_task())

    print("\n✅ All tests complete!")
    print("\nNext steps:")
    print("1. Check your dashboard - weather widget should show alerts if any active")
    print("2. Expand radar to see alert polygons on map")
    print("3. Wait for severe weather to test widget alert system")
    print("4. Check logs: tail -f /tmp/backend.log | grep -i weather")
