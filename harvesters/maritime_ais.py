import aiohttp
import time
import json
from typing import Dict, Any
from utils.ua_factory import get_ua
from interface.constants import TIMEOUT_SECONDS

async def harvest(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """
    Standardized Async Harvester for Maritime AIS (AISHub).
    Returns enhanced metadata including ship_count, sector, and api_status.
    """
    url = "https://data.aishub.net/ws.php?format=1&output=json&compress=0"
    headers = {'User-Agent': get_ua()}
    t0 = time.perf_counter()

    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
        async with session.get(url, headers=headers, timeout=timeout) as response:
            t1 = time.perf_counter()
            latency = t1 - t0
            
            # The RTT is the most basic timing 'bean'
            rtt_ns = int(latency * 1000000)
            
            # Pull the Date header - this is the server's clock
            server_date = response.headers.get('Date', '')
            
            # If we have a server date, entropy is RTT + Server Date stable hash
            date_hash = 0
            if server_date:
                date_hash = sum(ord(c) for c in server_date) % 10000
            
            # Attempt to extract ship count and sector info from JSON
            ship_count = 0
            sector = "Global"
            try:
                data = await response.json()
                # AISHub JSON format: [ [ship_data], {meta} ] or similar
                if isinstance(data, list) and len(data) > 0:
                    ship_count = len(data[0]) if isinstance(data[0], list) else 0
            except:
                pass

            return {
                "value": rtt_ns + date_hash,
                "latency": latency,
                "remote_time": server_date,
                "error": None,
                "metadata": {
                    "ship_count": ship_count,
                    "sector_name": sector,
                    "api_status": f"HTTP {response.status}",
                    "raw_rtt_ns": rtt_ns
                }
            }
    except asyncio.TimeoutError:
        return {
            "value": 0, "latency": time.perf_counter() - t0, "remote_time": None, "error": "AISHub Timeout"
        }
    except Exception as e:
        return {
            "value": 0, "latency": time.perf_counter() - t0, "remote_time": None, "error": str(e)
        }
