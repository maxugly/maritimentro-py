import time
import hashlib

def mix_with_time(current_acc, value, remote_time_str=None):
    """
    Combines the current seed with a value and high-resolution timing.
    """
    # Capture local nanosecond jitter immediately
    local_ns = time.time_ns()
    
    # Calculate drift if a remote timestamp was provided
    drift = 0
    if remote_time_str:
        try:
            # Simple conversion of 'Date' header to epoch
            from email.utils import parsedate_to_datetime
            remote_dt = parsedate_to_datetime(remote_time_str)
            remote_ts = remote_dt.timestamp()
            # The 'Drift' is the jitter between your clock and theirs
            drift = int(abs(time.time() - remote_ts) * 1000)
        except:
            pass

    # The Mixing Formula: Seed XOR Value + Nano Jitter + Drift
    new_seed = (current_acc ^ int(hash(str(value)))) + (local_ns % 1000000) + drift
    return new_seed