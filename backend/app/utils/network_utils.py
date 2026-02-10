import subprocess
import re
import statistics
import httpx
from typing import Optional


# Default ping targets
DEFAULT_PING_TARGETS = [
    {"host": "8.8.8.8", "name": "Google DNS"},
    {"host": "1.1.1.1", "name": "Cloudflare DNS"},
    {"host": "208.67.222.222", "name": "OpenDNS"},
]


def ping_host(host: str, count: int = 4) -> dict:
    """
    Ping a host and return latency, jitter, packet loss.

    Returns:
        dict with keys: is_reachable, latency_ms, jitter_ms, packet_loss_pct
    """
    try:
        # Run ping command
        result = subprocess.run(
            ["ping", "-c", str(count), "-W", "2", host],
            capture_output=True,
            text=True,
            timeout=10,
        )

        output = result.stdout

        # Check if any packets were received
        if result.returncode != 0:
            return {
                "is_reachable": False,
                "latency_ms": None,
                "jitter_ms": None,
                "packet_loss_pct": 100.0,
            }

        # Parse packet loss
        loss_match = re.search(r'(\d+)% packet loss', output)
        packet_loss = float(loss_match.group(1)) if loss_match else 0.0

        # Parse RTT times
        rtt_match = re.search(r'rtt min/avg/max/mdev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)', output)

        if rtt_match:
            avg_latency = float(rtt_match.group(2))
            mdev = float(rtt_match.group(4))  # Standard deviation = jitter

            return {
                "is_reachable": True,
                "latency_ms": round(avg_latency, 2),
                "jitter_ms": round(mdev, 2),
                "packet_loss_pct": packet_loss,
            }
        else:
            # Fallback: try to extract individual times
            times = re.findall(r'time=([\d.]+)', output)
            if times:
                latencies = [float(t) for t in times]
                avg_latency = statistics.mean(latencies)
                jitter = statistics.stdev(latencies) if len(latencies) > 1 else 0.0

                return {
                    "is_reachable": True,
                    "latency_ms": round(avg_latency, 2),
                    "jitter_ms": round(jitter, 2),
                    "packet_loss_pct": packet_loss,
                }

        return {
            "is_reachable": True,
            "latency_ms": None,
            "jitter_ms": None,
            "packet_loss_pct": packet_loss,
        }

    except subprocess.TimeoutExpired:
        return {
            "is_reachable": False,
            "latency_ms": None,
            "jitter_ms": None,
            "packet_loss_pct": 100.0,
        }
    except Exception as e:
        print(f"Error pinging {host}: {e}")
        return {
            "is_reachable": False,
            "latency_ms": None,
            "jitter_ms": None,
            "packet_loss_pct": 100.0,
        }


async def get_public_ip_info() -> dict:
    """
    Get public IP address and ISP information using ipify + ip-api.

    Returns:
        dict with keys: ip_address, isp, location
    """
    try:
        # Get public IP from ipify
        async with httpx.AsyncClient(timeout=5.0) as client:
            ip_response = await client.get("https://api.ipify.org?format=json")
            ip_data = ip_response.json()
            ip_address = ip_data.get("ip")

            if not ip_address:
                return {"ip_address": None, "isp": None, "location": None}

            # Get ISP and location info from ip-api.com
            info_response = await client.get(f"http://ip-api.com/json/{ip_address}")
            info_data = info_response.json()

            if info_data.get("status") == "success":
                isp = info_data.get("isp", "Unknown")
                city = info_data.get("city", "")
                region = info_data.get("regionName", "")
                country = info_data.get("country", "")

                # Build location string
                location_parts = [p for p in [city, region, country] if p]
                location = ", ".join(location_parts) if location_parts else None

                return {
                    "ip_address": ip_address,
                    "isp": isp,
                    "location": location,
                }

            return {
                "ip_address": ip_address,
                "isp": None,
                "location": None,
            }

    except Exception as e:
        print(f"Error getting public IP info: {e}")
        return {"ip_address": None, "isp": None, "location": None}


def determine_connection_status(ping_results: list[dict]) -> str:
    """
    Determine overall connection status based on ping results.

    Returns:
        "online", "degraded", or "offline"
    """
    if not ping_results:
        return "offline"

    reachable_count = sum(1 for r in ping_results if r["is_reachable"])
    total_count = len(ping_results)

    if reachable_count == 0:
        return "offline"
    elif reachable_count < total_count * 0.5:
        return "degraded"
    else:
        # Check for high packet loss or latency
        high_loss = any(
            r.get("packet_loss_pct", 0) > 20
            for r in ping_results
            if r["is_reachable"]
        )
        high_latency = any(
            r.get("latency_ms", 0) > 200
            for r in ping_results
            if r["is_reachable"] and r.get("latency_ms")
        )

        if high_loss or high_latency:
            return "degraded"

        return "online"
