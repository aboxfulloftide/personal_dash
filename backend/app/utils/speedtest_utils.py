"""
Speed test utility functions using speedtest-cli.
"""
import logging
import time
from typing import Dict, Any

logger = logging.getLogger(__name__)


def run_speedtest(preferred_server_id: str | None = None) -> Dict[str, Any]:
    """
    Run a speed test using speedtest-cli to measure download/upload speeds.

    Args:
        preferred_server_id: Optional server ID to use for testing

    Returns:
        Dictionary containing:
        - download_mbps: Download speed in Mbps
        - upload_mbps: Upload speed in Mbps
        - ping_ms: Ping latency in milliseconds
        - server_id: Server ID used for test
        - server_name: Server name
        - server_location: Server location (city, country)
        - server_sponsor: Server sponsor/ISP name
        - test_duration_seconds: How long the test took
        - is_successful: Whether test completed successfully
        - error_message: Error message if test failed
    """
    start_time = time.time()

    try:
        import speedtest

        logger.info("Initializing speed test...")
        st = speedtest.Speedtest()

        # Get best server or use specified server
        logger.info("Selecting server...")
        if preferred_server_id:
            servers = st.get_servers([preferred_server_id])
            if not servers or preferred_server_id not in servers:
                raise ValueError(f"Server {preferred_server_id} not found")
        else:
            st.get_best_server()

        # Run download test
        logger.info("Testing download speed...")
        download_bps = st.download()
        download_mbps = download_bps / 1_000_000  # Convert to Mbps

        # Run upload test
        logger.info("Testing upload speed...")
        upload_bps = st.upload()
        upload_mbps = upload_bps / 1_000_000  # Convert to Mbps

        # Get server info
        server = st.results.server

        test_duration = time.time() - start_time

        result = {
            "download_mbps": round(download_mbps, 2),
            "upload_mbps": round(upload_mbps, 2),
            "ping_ms": round(st.results.ping, 2) if st.results.ping else None,
            "server_id": str(server.get("id", "")),
            "server_name": server.get("name", ""),
            "server_location": f"{server.get('name', '')}, {server.get('country', '')}",
            "server_sponsor": server.get("sponsor", ""),
            "test_duration_seconds": round(test_duration, 2),
            "is_successful": True,
            "error_message": None
        }

        logger.info(
            f"Speed test completed: {result['download_mbps']} Mbps down, "
            f"{result['upload_mbps']} Mbps up, {result['ping_ms']} ms ping"
        )

        return result

    except Exception as e:
        test_duration = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Speed test failed: {error_msg}")

        return {
            "download_mbps": None,
            "upload_mbps": None,
            "ping_ms": None,
            "server_id": None,
            "server_name": None,
            "server_location": None,
            "server_sponsor": None,
            "test_duration_seconds": round(test_duration, 2),
            "is_successful": False,
            "error_message": error_msg[:500]  # Truncate to fit DB column
        }
