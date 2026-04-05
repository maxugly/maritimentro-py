import subprocess
import re
import shutil

def get_doggo_stats(target):
    path = shutil.which("doggo")
    if not path: return None
    
    try:
        # We don't use --short so we get the full table
        res = subprocess.run([path, target, "--time"], 
                             capture_output=True, text=True, timeout=5)
        raw = res.stdout + res.stderr
        
        # Extract all TTLs (e.g. "300s") and the Time Taken (e.g. "24ms")
        ttls = [int(n) for n in re.findall(r'\s+(\d+)s\s+', raw)]
        rtts = [int(n) for n in re.findall(r'(\d+)ms', raw)]
        
        return {"target": target, "ttls": ttls, "rtts": rtts}
    except:
        return None