import aiohttp
import time
from typing import Dict, Any
from utils.ua_factory import get_ua
from interface.constants import TIMEOUT_SECONDS

async def harvest(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """
    Standardized Async Harvester for Maritime AIS (AISHub).
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
                # Simple stable-ish hash for local entropy before State mixing
                date_hash = sum(ord(c) for c in server_date) % 10000
                
            return {
                "value": rtt_ns + date_hash,
                "latency": latency,
                "remote_time": server_date,
                "error": None
            }
    except asyncio.TimeoutError:
        return {
            "value": 0,
            "latency": time.perf_counter() - t0,
            "remote_time": None,
            "error": "AISHub Timeout"
        }
    except Exception as e:
        return {
            "value": 0,
            "latency": time.perf_counter() - t0,
            "remote_time": None,
            "error": str(e)
        }
