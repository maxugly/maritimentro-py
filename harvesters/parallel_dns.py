import asyncio
import time
import shutil
import re
from typing import Dict, Any
from interface.constants import TIMEOUT_SECONDS

async def harvest() -> Dict[str, Any]:
    """
    Standardized Async Harvester for Parallel DNS Probes.
    Pristine rule: Direct asyncio.create_subprocess_exec usage.
    """
    # A mix of global infrastructure and high-traffic sites
    targets = [
        'google.com', 'cloudflare.com', 'wikipedia.org', 
        'github.com', 'amazon.com', 'netflix.com'
    ]
    
    path = shutil.which("doggo")
    if not path:
        return {"value": 0, "latency": 0, "remote_time": None, "error": "doggo not found"}

    t0 = time.perf_counter()
    total_entropy = 0
    
    try:
        # Launch parallel probes
        procs = []
        for target in targets:
            proc = await asyncio.create_subprocess_exec(
                path, target, '--time',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            procs.append(proc)
        
        # Collect all output with timeout protection
        for proc in procs:
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), 
                    timeout=TIMEOUT_SECONDS
                )
                raw = stdout.decode() + stderr.decode()
                
                # Extract TTLs and RTTs for entropy beans
                # Pattern matching derived from utils.network_helper logic
                ttls = [int(n) for n in re.findall(r'\s+(\d+)s\s+', raw)]
                rtts = [int(n) for n in re.findall(r'(\d+)ms', raw)]
                
                total_entropy += sum(ttls) + sum(rtts)
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                    await proc.wait()
                except:
                    pass
                continue

        t1 = time.perf_counter()
        
        return {
            "value": total_entropy,
            "latency": t1 - t0,
            "remote_time": None,
            "error": None
        }
    except Exception as e:
        return {
            "value": 0,
            "latency": time.perf_counter() - t0,
            "remote_time": None,
            "error": str(e)
        }
