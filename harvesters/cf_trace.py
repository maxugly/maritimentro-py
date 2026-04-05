import asyncio
import re
import time
from typing import Dict, Any
from interface.constants import TIMEOUT_SECONDS

async def harvest() -> Dict[str, Any]:
    """
    Standardized Async Harvester for Cloudflare Trace.
    Uses asyncio.create_subprocess_exec for non-blocking curl.
    """
    t0 = time.perf_counter()
    try:
        proc = await asyncio.create_subprocess_exec(
            'curl', '-s', 'https://1.1.1.1/cdn-cgi/trace',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Protect with global timeout
        stdout, _ = await asyncio.wait_for(
            proc.communicate(), 
            timeout=TIMEOUT_SECONDS
        )
        
        raw = stdout.decode()
        t1 = time.perf_counter()
        
        latency = t1 - t0
        
        # Extract the remote timestamp
        ts_match = re.search(r'ts=([\d.]+)', raw)
        remote_time = None
        entropy_value = 0
        
        if ts_match:
            remote_ts_str = ts_match.group(1)
            # Use the raw timestamp string as entropy
            entropy_value = int(float(remote_ts_str) * 1000) % 1000000
            remote_time = remote_ts_str # Return raw TS for drift mixing
            
        return {
            "value": entropy_value,
            "latency": latency,
            "remote_time": remote_time,
            "error": None
        }
    except asyncio.TimeoutError:
        return {
            "value": 0,
            "latency": time.perf_counter() - t0,
            "remote_time": None,
            "error": "Cloudflare Trace Timeout"
        }
    except Exception as e:
        return {
            "value": 0,
            "latency": time.perf_counter() - t0,
            "remote_time": None,
            "error": str(e)
        }
