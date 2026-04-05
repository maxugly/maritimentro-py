import requests
import time
from utils.ua_factory import get_ua

def harvest():
    url = "https://data.aishub.net/ws.php?format=1&output=json&compress=0"
    headers = {'User-Agent': get_ua()}

    try:
        t0 = time.perf_counter()
        r = requests.get(url, headers=headers, timeout=10)
        t1 = time.perf_counter()

        # The RTT is the most basic timing 'bean'
        rtt_ns = int((t1 - t0) * 1000000)

        # Pull the Date header - this is the server's clock
        server_date = r.headers.get('Date', '')

        print(f"    [RAW_BEANS] AIS Hub - Status: {r.status_code} | RTT: {rtt_ns}ns")

        # If we have a server date, the entropy is the RTT + Server Date hash
        if server_date:
            return rtt_ns + (hash(server_date) % 10000)

    except:
        pass
    return 0
