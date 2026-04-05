import asyncio
import time
import shutil
import re
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
    Standardized Async Harvester for Parallel DNS Probes.
    Pristine rule: Direct asyncio.create_subprocess_exec usage.
    """
    targets = [
        'google.com', 'cloudflare.com', 'wikipedia.org', 
        'github.com', 'amazon.com', 'netflix.com'
    ]
    
    path = shutil.which("doggo")
    if not path:
        return {"value": 0, "latency": 0, "remote_time": None, "error": "doggo not found"}

    t0 = time.perf_counter()
    total_entropy = 0
    probe_latencies = []
    
    try:
        # Launch parallel probes
        procs = []
        for target in targets:
            proc = await asyncio.create_subprocess_exec(
                path, target, '--time',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            procs.append((target, proc))
        
        # Collect output
        for target, proc in procs:
            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), 
                    timeout=TIMEOUT_SECONDS
                )
                output = stdout.decode() + stderr.decode()
                
                ttls = [int(n) for n in re.findall(r'\s+(\d+)s\s+', output)]
                rtts = [int(n) for n in re.findall(r'(\d+)ms', output)]
                
                if rtts:
                    probe_latencies.append(float(rtts[0]))
                
                total_entropy += sum(ttls) + sum(rtts)
            except asyncio.TimeoutError:
                try: proc.kill(); await proc.wait()
                except: pass

        t1 = time.perf_counter()
        latency = t1 - t0

        # Calculate Table Jitter across parallel probes
        table_jitter = calculate_jitter(probe_latencies)
        
        return {
            "value": total_entropy,
            "latency": latency,
            "remote_time": None,
            "error": None,
            "metadata": {
                "transport": "Subprocess (doggo)",
                "targets_probed": len(targets),
                "table_jitter_ms": round(table_jitter, 3),
                "latency_ms": round(latency * 1000, 2),
                "results": f"{len(probe_latencies)} probes succeeded"
            }
        }
    except Exception as e:
        return {
            "value": 0, "latency": time.perf_counter() - t0, "remote_time": None, "error": str(e)
        }
