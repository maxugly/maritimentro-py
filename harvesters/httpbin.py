import requests
import time

def harvest():
    try:
        t0 = time.perf_counter()
        r = requests.get("https://httpbin.org/get", timeout=4)
        t1 = time.perf_counter()
        # Mix the RTT and the length of the headers
        rtt = int((t1 - t0) * 1000000) % 1000
        return rtt + len(r.text)
    except:
        return 0