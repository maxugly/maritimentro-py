import concurrent.futures
from utils.network_helper import get_doggo_stats

def harvest():
    # A mix of global infrastructure and high-traffic sites
    targets = [
        'google.com', 'cloudflare.com', 'wikipedia.org', 
        'github.com', 'amazon.com', 'netflix.com',
        '8.8.8.8', '1.1.1.1', '9.9.9.9'
    ]
    
    total_entropy = 0
    print(f"    [THREADING] Launching {len(targets)} parallel probes...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Fire and forget - the kernel handles the chaos
        results = list(executor.map(get_doggo_stats, targets))

    for res in results:
        if res:
            # Sum of all moving targets from this specific probe
            round_sum = sum(res['ttls']) + sum(res['rtts'])
            if round_sum > 0:
                print(f"    [RAW_BEANS] {res['target']}: TTLs {res['ttls']} | RTTs {res['rtts']}")
                total_entropy += round_sum

    return total_entropy