import asyncio
import shutil
import re
import hashlib
import time
import random
import math
from typing import Dict, Any, List
from interface.constants import TIMEOUT_SECONDS

def calculate_jitter(data: List[float]) -> float:
    """Calculates standard deviation (jitter) for a list of values."""
    if len(data) < 2: return 0.0
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    return math.sqrt(variance)

async def harvest() -> Dict[str, Any]:
    """
    Standardized Async Harvester for DNS Table Jitter using doggo.
    Returns enhanced metadata including 'Table Jitter' (Standard Deviation).
    """
    t0 = time.perf_counter()
    
    path = shutil.which("doggo")
    if not path:
        return {"value": 0, "latency": 0, "remote_time": None, "error": "doggo not found"}

    # We probe multiple targets in a single 'hit' to calculate internal table jitter
    targets = ['google.com', 'cloudflare.com', 'wikipedia.org']
    raw_accumulator = ""
    probe_latencies = []
    
    try:
        # Run queries in parallel
        tasks = []
        for target in targets:
            tasks.append(asyncio.create_subprocess_exec(
                path, target, '--time',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            ))
        
        procs = await asyncio.gather(*tasks)
        
        for proc in procs:
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), 
                    timeout=TIMEOUT_SECONDS
                )
                output = stdout.decode() + stderr.decode()
                raw_accumulator += output
                
                # Extract RTT for this specific probe
                rtt_match = re.search(r'(\d+)ms', output)
                if rtt_match:
                    probe_latencies.append(float(rtt_match.group(1)))
                    
            except asyncio.TimeoutError:
                try: proc.kill(); await proc.wait()
                except: pass

        t1 = time.perf_counter()
        latency = t1 - t0

        if not raw_accumulator:
            return {"value": 0, "latency": latency, "remote_time": None, "error": "No output"}

        # Calculate Table Jitter (Std Dev of internal probes)
        table_jitter = calculate_jitter(probe_latencies)

        # 1. Pull digits for entropy
        all_numbers = re.findall(r'\d+', raw_accumulator)
        numeric_sum = sum([int(n) for n in all_numbers if len(n) < 10])

        # 2. String Jitter hash
        string_hash = int(hashlib.sha256(raw_accumulator.encode()).hexdigest(), 16) % 100000

        return {
            "value": numeric_sum + string_hash,
            "latency": latency,
            "remote_time": None,
            "error": None,
            "metadata": {
                "query_targets": len(targets),
                "table_jitter_ms": round(table_jitter, 3),
                "latency_ms": round(latency * 1000, 2),
                "entropy_type": "DNS Table Jitter"
            }
        }
    except Exception as e:
        return {
            "value": 0, "latency": time.perf_counter() - t0, "remote_time": None, "error": str(e)
        }
