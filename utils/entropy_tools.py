import time
import hashlib
from typing import Any, Optional
from email.utils import parsedate_to_datetime

MASK_64 = 0xFFFFFFFFFFFFFFFF

def _ensure_int(value: Any) -> int:
    """
    Consistently converts arbitrary input types to a 64-bit integer.
    Replaces the non-deterministic hash() with a stable SHA-256 truncation.
    """
    if isinstance(value, int):
        return value & MASK_64
    
    # Stable hash for all other types (strings, dicts, etc.)
    # We use the first 8 bytes of the SHA-256 hash for a stable 64-bit int.
    hasher = hashlib.sha256(str(value).encode(errors="replace"))
    return int.from_bytes(hasher.digest()[:8], byteorder="big")

def mix_entropy(seed: int, val: int, jitter: int = 0, drift: int = 0) -> int:
    """
    Pure function for "Exclusive Bitwise Math" entropy mixing.
    Combines seed, value, jitter, and drift using XOR and Addition.
    """
    # XOR the seed with the value, then add timing components
    # Applying the 64-bit mask at each step to ensure consistency
    mixed = (seed ^ val) & MASK_64
    mixed = (mixed + jitter) & MASK_64
    mixed = (mixed + drift) & MASK_64
    return mixed

def mix_with_time(current_acc: int, value: Any, remote_time_str: Optional[str] = None) -> int:
    """
    High-level wrapper that calculates jitter/drift and mixes entropy.
    """
    # Capture local nanosecond jitter (last 6 digits for micro-entropy)
    local_ns = time.time_ns()
    jitter = local_ns % 1000000
    
    # Calculate drift if a remote timestamp was provided
    drift = 0
    if remote_time_str:
        try:
            remote_dt = parsedate_to_datetime(remote_time_str)
            remote_ts = remote_dt.timestamp()
            # Drift is the absolute difference in milliseconds
            drift = int(abs(time.time() - remote_ts) * 1000)
        except (ValueError, TypeError, OverflowError):
            pass

    # Convert value to a stable integer
    val_int = _ensure_int(value)
    
    # Delegate to the pure mixing function
    return mix_entropy(current_acc, val_int, jitter, drift)
