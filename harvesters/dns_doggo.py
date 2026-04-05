import asyncio
import shutil
import re
import hashlib
import time
from typing import Dict, Any
from interface.constants import TIMEOUT_SECONDS

async def harvest() -> Dict[str, Any]:
    """
    Standardized Async Harvester for DNS Table Jitter using doggo.
    Complies with project SoC and 'Pristine' rules (no shell pipes).
    """
    t0 = time.perf_counter()
    
    # Handle Void Linux / generic binary pathing gracefully
    path = shutil.which("doggo")
    if not path:
        return {
            "value": 0, 
            "latency": 0, 
            "remote_time": None, 
            "error": "Binary 'doggo' not found in PATH"
        }

    targets = ['google.com', 'cloudflare.com', 'wikipedia.org']
    raw_accumulator = ""
    
    try:
        # Run queries in parallel for efficiency
        # We wrap communicate() in wait_for to respect global timeouts
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
                raw_accumulator += stdout.decode() + stderr.decode()
            except asyncio.TimeoutError:
                # If one process hangs, kill it and move on
                try:
                    proc.kill()
                    await proc.wait()
                except ProcessLookupError:
                    pass
                continue

        t1 = time.perf_counter()
        latency = t1 - t0

        if not raw_accumulator:
            return {
                "value": 0,
                "latency": latency,
                "remote_time": None,
                "error": "No output from doggo queries"
            }

        # 1. Pull digits for entropy
        all_numbers = re.findall(r'\d+', raw_accumulator)
        numeric_sum = sum([int(n) for n in all_numbers if len(n) < 10])

        # 2. String Jitter hash
        string_hash = int(hashlib.sha256(raw_accumulator.encode()).hexdigest(), 16) % 100000

        return {
            "value": numeric_sum + string_hash,
            "latency": latency,
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
