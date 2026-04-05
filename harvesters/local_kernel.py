import time

def harvest():
    # Micro-drift between monotonic and wall clock
    return int((time.perf_counter() - time.time()) * 1000000) % 100000