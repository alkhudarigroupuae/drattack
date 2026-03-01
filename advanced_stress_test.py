import asyncio
import aiohttp
import random
import time
import sys
import argparse
from datetime import datetime

# --- Configuration ---
DEFAULT_TARGET = "http://localhost:5000"
DEFAULT_CONCURRENCY = 100
DEFAULT_DURATION = 60

# Professional User-Agent Rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
]

# Statistics
stats = {
    "requests": 0,
    "success": 0,
    "failed": 0,
    "bytes_received": 0,
    "start_time": 0
}

# CSV Logging
LOG_FILE = "attack_stats.csv"

def init_log_file():
    with open(LOG_FILE, "w") as f:
        f.write("timestamp,requests,success,failed,rps,bytes_received\n")

async def log_stats_periodically(stop_event):
    """Writes stats to CSV every second for real-time monitoring."""
    while not stop_event.is_set():
        elapsed = time.time() - stats["start_time"]
        if elapsed > 0:
            rps = stats["requests"] / elapsed
            with open(LOG_FILE, "a") as f:
                timestamp = datetime.now().strftime('%H:%M:%S')
                f.write(f"{timestamp},{stats['requests']},{stats['success']},{stats['failed']},{rps:.2f},{stats['bytes_received']}\n")
        await asyncio.sleep(1)

async def fetch(session, url):
    """Sends a single request with randomized headers."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    
    try:
        async with session.get(url, headers=headers, timeout=5) as response:
            data = await response.read()
            stats["requests"] += 1
            stats["bytes_received"] += len(data)
            
            if response.status < 400:
                stats["success"] += 1
                return response.status
            else:
                stats["failed"] += 1
                return response.status
                
    except Exception:
        stats["requests"] += 1
        stats["failed"] += 1
        return 0

async def worker(url, duration):
    """A worker that continuously sends requests for the given duration."""
    async with aiohttp.ClientSession() as session:
        end_time = time.time() + duration
        while time.time() < end_time:
            await fetch(session, url)

async def main():
    parser = argparse.ArgumentParser(description="Professional Network Stress Testing Engine")
    parser.add_argument("url", nargs="?", default=DEFAULT_TARGET, help="Target URL")
    parser.add_argument("-c", "--concurrency", type=int, default=DEFAULT_CONCURRENCY, help="Concurrent Connections")
    parser.add_argument("-d", "--duration", type=int, default=DEFAULT_DURATION, help="Test Duration (s)")
    
    args = parser.parse_args()
    
    target_url = args.url
    concurrency = args.concurrency
    duration = args.duration
    
    print(f"[*] Initializing Stress Test Engine")
    print(f"[*] Target:      {target_url}")
    print(f"[*] Concurrency: {concurrency} workers")
    print(f"[*] Duration:    {duration} seconds")
    
    stats["start_time"] = time.time()
    init_log_file()
    
    # Create stop event for logger
    stop_event = asyncio.Event()
    
    # Start logger task
    logger_task = asyncio.create_task(log_stats_periodically(stop_event))
    
    # Create worker tasks
    tasks = []
    for _ in range(concurrency):
        tasks.append(asyncio.create_task(worker(target_url, duration)))
    
    # Wait for all tasks to complete
    await asyncio.gather(*tasks)
    
    # Stop logger
    stop_event.set()
    await logger_task
    
    print("[+] Test Complete.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Test aborted by user.")
