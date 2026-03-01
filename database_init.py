import sqlite3
import time
from datetime import datetime

DB_NAME = "cyber_operations.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # 1. Campaigns Table (Stores metadata about each test run)
    c.execute('''
        CREATE TABLE IF NOT EXISTS campaigns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_url TEXT NOT NULL,
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
    
    # 2. Telemetry Table (High-frequency data points for charting)
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
    
    # 3. System Logs (Audit trail)
    c.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP,
            level TEXT,
            component TEXT,
            message TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[Database] Initialized schema for {DB_NAME}")

if __name__ == "__main__":
    init_db()
