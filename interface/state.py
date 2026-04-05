import asyncio
import time
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from utils.entropy_tools import mix_with_time, MASK_64

@dataclass
class HarvesterStats:
    """Statistics for an individual harvester."""
    name: str
    hits: int = 0
    errors: int = 0
    last_value: Any = None
    last_latency: float = 0.0
    last_update: float = 0.0
    error_message: Optional[str] = None

class EntropyState:
    """
    Thread-safe (async-compatible) state manager for the Maritimentro entropy stream.
    Manages the global seed and harvester statistics.
    
    Designed for consumption by a non-blocking asyncio loop and a Rich-based TUI.
    """
    
    def __init__(self, initial_seed: int = 32416190071):
        # Defaulting to a 64-bit integer range
        self._seed = initial_seed & MASK_64
        self._harvesters: Dict[str, HarvesterStats] = {}
        self._lock = asyncio.Lock()
        self._start_time = time.time()
        # Non-blocking buffer for the TUI "Matrix Fade"
        self._bean_pool: List[Dict[str, Any]] = []
        self._max_beans = 100

    @property
    def seed(self) -> int:
        """Returns the current global seed."""
        return self._seed

    async def update_seed(self, value: Any, remote_time_str: Optional[str] = None):
        """
        Updates the global seed using the provided value and optional remote time.
        Uses the mixing logic from utils.entropy_tools.
        """
        async with self._lock:
            self._seed = mix_with_time(self._seed, value, remote_time_str)

    async def report_harvester(self, name: str, value: Any = None, latency: float = 0.0, error: Optional[str] = None):
        """
        Reports the result of a harvester run.
        Updates statistics and the global seed if a value is provided.
        """
        async with self._lock:
            if name not in self._harvesters:
                self._harvesters[name] = HarvesterStats(name=name)
            
            stats = self._harvesters[name]
            stats.last_update = time.time()
            stats.last_latency = latency
            
            if error:
                stats.errors += 1
                stats.error_message = error
            else:
                stats.hits += 1
                stats.last_value = value
                stats.error_message = None
                
                # If we have a value, update the seed
                if value is not None:
                    self._seed = mix_with_time(self._seed, value)
                    # Add to bean pool for TUI visual
                    self._bean_pool.append({
                        "name": name,
                        "value": value,
                        "ts": time.time()
                    })
                    if len(self._bean_pool) > self._max_beans:
                        self._bean_pool.pop(0)

    async def get_bean_pool(self) -> List[Dict[str, Any]]:
        """Returns the current pool of entropy 'beans' for visualization."""
        async with self._lock:
            return list(self._bean_pool)

    async def get_harvester_stats(self) -> List[HarvesterStats]:
        """Returns a list of all harvester statistics."""
        async with self._lock:
            # Return copies to avoid external modification of the internal state
            return [
                HarvesterStats(
                    name=s.name,
                    hits=s.hits,
                    errors=s.errors,
                    last_value=s.last_value,
                    last_latency=s.last_latency,
                    last_update=s.last_update,
                    error_message=s.error_message
                ) 
                for s in self._harvesters.values()
            ]

    async def get_global_stats(self) -> Dict[str, Any]:
        """Returns global statistics for the entropy stream."""
        async with self._lock:
            total_hits = sum(h.hits for h in self._harvesters.values())
            total_errors = sum(h.errors for h in self._harvesters.values())
            return {
                "seed": self._seed,
                "uptime": time.time() - self._start_time,
                "total_harvesters": len(self._harvesters),
                "total_hits": total_hits,
                "total_errors": total_errors,
                "seed_hex": f"0x{self._seed:016x}",
            }
