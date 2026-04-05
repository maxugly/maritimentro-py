import subprocess
import re
import time
from utils.entropy_tools import mix_with_time

def harvest():
    try:
        res = subprocess.run(['curl', '-s', 'https://1.1.1.1/cdn-cgi/trace'],
                             capture_output=True, text=True, timeout=5)
        raw = res.stdout
        print(f"    [RAW_BEANS] Cloudflare Trace Captured")

        # Extract the remote timestamp
        ts_match = re.search(r'ts=(\d+)', raw)
        if ts_match:
            remote_ts = int(ts_match.group(1))
            # We use our new 'mix' tool to compare their time to ours
            return remote_ts % 100000
    except:
        pass
    return 0
