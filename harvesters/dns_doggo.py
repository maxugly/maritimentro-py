import subprocess
import shutil
import re
import hashlib

def harvest():
    path = shutil.which("doggo")
    if not path: return 0

    # We query multiple domains to get a massive table
    # Google, Cloudflare, and Wikipedia - different TTLs, different paths
    targets = ['google.com', 'cloudflare.com', 'wikipedia.org']
    raw_accumulator = ""

    for target in targets:
        res = subprocess.run([path, target, '--time'],
                             capture_output=True, text=True, timeout=5)
        raw_accumulator += res.stdout + res.stderr

    print(f"    [RAW_BEANS] Captured massive DNS table ({len(raw_accumulator)} chars)")

    # 1. Pull every single digit found in the table (TTLs, IPs, Times)
    all_numbers = re.findall(r'\d+', raw_accumulator)
    numeric_sum = sum([int(n) for n in all_numbers if len(n) < 10]) # Ignore long timestamps

    # 2. Add 'String Jitter'
    # Even the order of the addresses can be a moving target
    string_hash = int(hashlib.md5(raw_accumulator.encode()).hexdigest(), 16) % 100000

    final_val = numeric_sum + string_hash
    print(f"    [FOUND] Numeric Sum: {numeric_sum} | Hash Jitter: {string_hash}")

    return final_val
