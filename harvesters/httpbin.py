import aiohttp
import time
from typing import Dict, Any
from interface.constants import TIMEOUT_SECONDS

async def harvest(session: aiohttp.ClientSession) -> Dict[str, Any]:
    """
    Standardized Async Harvester for httpbin.org.
    """
    t0 = time.perf_counter()
    try:
        timeout = aiohttp.ClientTimeout(total=TIMEOUT_SECONDS)
        async with session.get("https://httpbin.org/get", timeout=timeout) as response:
            text = await response.text()
            t1 = time.perf_counter()
            
            latency = t1 - t0
            # Mix the RTT and the length of the response
            rtt_jitter = int(latency * 1000000) % 1000
            entropy_value = rtt_jitter + len(text)
            
            return {
                "value": entropy_value,
                "latency": latency,
                "remote_time": response.headers.get("Date"),
                "error": None
            }
    except Exception as e:
        return {
            "value": 0,
            "latency": time.perf_counter() - t0,
            "remote_time": None,
            "error": str(e)
        }
