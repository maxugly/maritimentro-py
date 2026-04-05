import asyncio
import time
import math
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from utils.entropy_tools import mix_with_time, MASK_64

class RunningStats:
    """
    Implements Welford's algorithm for memory-efficient running statistics.
    Tracks mean, variance, skewness, and kurtosis in a single pass.
    """
    def __init__(self):
        self.count = 0
        self.mean = 0.0
        self.m2 = 0.0
        self.m3 = 0.0
        self.m4 = 0.0
        self.min = float('inf')
        self.max = float('-inf')
        # Simple Quantile Summary (Median/IQR) using a small sorted window or P2-lite
        # For our 4GB constraint, we'll use a small reservoir to estimate quantiles
        self._reservoir: List[float] = []
        self._max_res = 100

    def update(self, x: float):
        self.count += 1
        self.min = min(self.min, x)
        self.max = max(self.max, x)
        
        # Incremental higher-order moments (Pebay, 2008)
        n = self.count
        delta = x - self.mean
        delta_n = delta / n
        delta_n2 = delta_n * delta_n
        term1 = delta * delta_n * (n - 1)

        self.m4 += term1 * delta_n2 * (n*n - 3*n + 3) + 6 * delta_n2 * self.m2 - 4 * delta_n * self.m3
        self.m3 += term1 * delta_n * (n - 2) - 3 * delta_n * self.m2
        self.m2 += term1
        self.mean += delta_n

        # Update reservoir for quantile estimation
        if len(self._reservoir) < self._max_res:
            self._reservoir.append(x)
        else:
            # Replace random element for unbiased sampling
            import random
            idx = random.randint(0, self.count - 1)
            if idx < self._max_res:
                self._reservoir[idx] = x

    @property
    def variance(self) -> float:
        return self.m2 / self.count if self.count > 1 else 0.0

    @property
    def std_dev(self) -> float:
        return math.sqrt(self.variance)

    @property
    def skewness(self) -> float:
        if self.m2 <= 0: return 0.0
        return (math.sqrt(self.count) * self.m3) / (self.m2 ** 1.5)

    @property
    def kurtosis(self) -> float:
        if self.m2 <= 0: return 0.0
        return (self.count * self.m4) / (self.m2 ** 2) - 3.0

    @property
    def quantiles(self) -> Dict[str, float]:
        """Returns Q1, Q2 (Median), and Q3 estimates."""
        if not self._reservoir: return {"q1": 0, "q2": 0, "q3": 0, "iqr": 0}
        s = sorted(self._reservoir)
        n = len(s)
        q1 = s[int(n * 0.25)]
        q2 = s[int(n * 0.50)]
        q3 = s[int(n * 0.75)]
        return {"q1": q1, "q2": q2, "q3": q3, "iqr": q3 - q1}

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
    # Running statistical profiles
    val_stats: RunningStats = field(default_factory=RunningStats)
    lat_stats: RunningStats = field(default_factory=RunningStats)

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
        # Detailed metadata for the interactive Detail Pane
        self._latest_metadata: Dict[str, Dict[str, Any]] = {}

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

    async def report_harvester(self, name: str, value: Any = None, latency: float = 0.0, error: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
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
            
            if metadata:
                self._latest_metadata[name] = metadata
            
            if error:
                stats.errors += 1
                stats.error_message = error
            else:
                stats.hits += 1
                stats.last_value = value
                stats.error_message = None
                
                # Update running statistics (Welford's)
                if value is not None and isinstance(value, (int, float)):
                    stats.val_stats.update(float(value))
                stats.lat_stats.update(latency)

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

    async def get_harvester_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        """Returns the latest metadata for a specific harvester."""
        async with self._lock:
            return self._latest_metadata.get(name)

    async def get_bean_pool(self) -> List[Dict[str, Any]]:
        """Returns the current pool of entropy 'beans' for visualization."""
        async with self._lock:
            return list(self._bean_pool)

    async def get_harvester_stats(self) -> List[HarvesterStats]:
        """Returns a list of all harvester statistics."""
        async with self._lock:
            # Return copies to avoid external modification of the internal state
            copied_stats = []
            for s in self._harvesters.values():
                h = HarvesterStats(
                    name=s.name,
                    hits=s.hits,
                    errors=s.errors,
                    last_value=s.last_value,
                    last_latency=s.last_latency,
                    last_update=s.last_update,
                    error_message=s.error_message
                )
                # Manually copy RunningStats data
                h.val_stats.count = s.val_stats.count
                h.val_stats.mean = s.val_stats.mean
                h.val_stats.m2 = s.val_stats.m2
                h.val_stats.m3 = s.val_stats.m3
                h.val_stats.m4 = s.val_stats.m4
                h.val_stats.min = s.val_stats.min
                h.val_stats.max = s.val_stats.max
                h.val_stats._reservoir = list(s.val_stats._reservoir)
                
                h.lat_stats.count = s.lat_stats.count
                h.lat_stats.mean = s.lat_stats.mean
                h.lat_stats.m2 = s.lat_stats.m2
                h.lat_stats.m3 = s.lat_stats.m3
                h.lat_stats.m4 = s.lat_stats.m4
                h.lat_stats.min = s.lat_stats.min
                h.lat_stats.max = s.lat_stats.max
                h.lat_stats._reservoir = list(s.lat_stats._reservoir)
                copied_stats.append(h)
            return copied_stats

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
