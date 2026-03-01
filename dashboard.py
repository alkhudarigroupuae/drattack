import streamlit as st
import pandas as pd
import sqlite3
import time
import subprocess
import os
import psutil
import altair as alt
from datetime import datetime

# --- Configuration ---
DB_NAME = "cyber_operations.db"
VPS_IP = "76.13.179.65"

# --- Page Config ---
st.set_page_config(
    page_title="Strategic Cyber Command",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Professional Styling ---
st.markdown("""
<style>
    /* Dark Theme Optimization */
    .stApp {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stSidebar {
        background-color: #161b22;
        border-right: 1px solid #30363d;
    }
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #58a6ff;
    }
    .stMetric {
        background-color: #161b22;
        border: 1px solid #30363d;
        border-radius: 6px;
        padding: 15px;
    }
    .stDataFrame {
        border: 1px solid #30363d;
    }
    /* Status Indicators */
    .status-running { color: #2ea043; font-weight: bold; }
    .status-stopped { color: #8b949e; }
    .status-aborted { color: #f85149; }
</style>
""", unsafe_allow_html=True)

# --- Database Helpers ---
def get_db_connection():
    return sqlite3.connect(DB_NAME)

def create_campaign(url, concurrency, duration):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO campaigns (target_url, concurrency, duration, start_time, status)
        VALUES (?, ?, ?, ?, 'Initializing')
    ''', (url, concurrency, duration, datetime.now()))
    campaign_id = c.lastrowid
    conn.commit()
    conn.close()
    return campaign_id

def get_active_campaign():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM campaigns WHERE status='Running' ORDER BY id DESC LIMIT 1", conn)
    conn.close()
    return df.iloc[0] if not df.empty else None

def get_telemetry(campaign_id):
    conn = get_db_connection()
    df = pd.read_sql_query(f"SELECT * FROM telemetry WHERE campaign_id={campaign_id} ORDER BY timestamp DESC LIMIT 60", conn)
    conn.close()
    return df

# --- Sidebar Navigation ---
st.sidebar.title("COMMAND CENTER")
page = st.sidebar.radio("Navigation", ["Dashboard Overview", "Campaign Execution", "Live Telemetry", "System Health"])

st.sidebar.markdown("---")
st.sidebar.caption(f"Node: {VPS_IP}")
st.sidebar.caption(f"System Time: {datetime.now().strftime('%H:%M:%S UTC')}")

# --- PAGE 1: Dashboard Overview ---
if page == "Dashboard Overview":
    st.title("Strategic Cyber Command")
    st.markdown("### Operational Summary")
    
    conn = get_db_connection()
    
    # KPIs
    total_campaigns = pd.read_sql_query("SELECT COUNT(*) FROM campaigns", conn).iloc[0,0]
    total_requests = pd.read_sql_query("SELECT SUM(total_requests) FROM campaigns", conn).iloc[0,0] or 0
    avg_success = pd.read_sql_query("SELECT AVG(success_count) FROM campaigns", conn).iloc[0,0] or 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Campaigns Executed", total_campaigns)
    col2.metric("Total Requests Sent", f"{total_requests:,.0f}")
    col3.metric("Avg Success Rate", "N/A" if total_campaigns == 0 else f"{(avg_success/total_requests)*100:.1f}%")
    
    st.markdown("### Recent Operations")
    recent = pd.read_sql_query("SELECT id, target_url, status, start_time, total_requests, avg_rps FROM campaigns ORDER BY id DESC LIMIT 10", conn)
    st.dataframe(recent, use_container_width=True)
    conn.close()

# --- PAGE 2: Campaign Execution ---
elif page == "Campaign Execution":
    st.title("Campaign Execution")
    
    # Check if engine is running
    active = get_active_campaign()
    if active is not None:
        st.warning(f"⚠️ A campaign is currently active: ID #{active['id']} targeting {active['target_url']}")
        if st.button("ABORT CURRENT CAMPAIGN", type="primary"):
            subprocess.run(["pkill", "-f", "engine.py"])
            conn = get_db_connection()
            conn.execute("UPDATE campaigns SET status='Aborted' WHERE id=?", (int(active['id']),))
            conn.commit()
            conn.close()
            st.rerun()
    else:
        st.subheader("New Operation Configuration")
        
        # Load targets
        try:
            with open('targets.txt', 'r') as f:
                targets = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except:
            targets = ["http://localhost:5000"]

        with st.form("launch_form"):
            target = st.selectbox("Select Target", targets)
            col1, col2 = st.columns(2)
            concurrency = col1.number_input("Concurrency (Virtual Users)", 10, 50000, 1000)
            duration = col2.number_input("Duration (Seconds)", 10, 86400, 60)
            
            launch = st.form_submit_button("🚀 LAUNCH OPERATION")
            
            if launch:
                # 1. Create DB Entry
                campaign_id = create_campaign(target, concurrency, duration)
                
                # 2. Spawn Engine Process
                cmd = ["python3", "engine.py", target, "-c", str(concurrency), "-d", str(duration), "--id", str(campaign_id)]
                subprocess.Popen(cmd)
                
                st.success(f"Operation #{campaign_id} Initiated Successfully.")
                time.sleep(1)
                st.switch_page("dashboard.py") # Refresh to show active state (Simulated via rerun logic)
                st.rerun()

# --- PAGE 3: Live Telemetry ---
elif page == "Live Telemetry":
    st.title("Real-Time Telemetry")
    
    active = get_active_campaign()
    
    if active is None:
        st.info("No active operations. Standby.")
        
        # Show last run if available
        conn = get_db_connection()
        last = pd.read_sql_query("SELECT * FROM campaigns ORDER BY id DESC LIMIT 1", conn)
        conn.close()
        
        if not last.empty:
            st.markdown("### Last Operation Review")
            st.write(last)
    else:
        placeholder = st.empty()
        
        while True:
            df = get_telemetry(active['id'])
            
            with placeholder.container():
                st.markdown(f"**Target:** `{active['target_url']}` | **Status:** 🟢 RUNNING")
                
                if not df.empty:
                    latest = df.iloc[0]
                    
                    # KPIs
                    k1, k2, k3, k4 = st.columns(4)
                    k1.metric("Throughput", f"{latest['rps']:.0f} RPS")
                    k2.metric("Total Requests", f"{latest['requests']:,}")
                    k3.metric("Errors", f"{latest['failed']:,}", delta_color="inverse")
                    
                    # Charts
                    c1 = alt.Chart(df).mark_area(
                        line={'color':'#2ea043'},
                        color=alt.Gradient(
                            gradient='linear',
                            stops=[alt.GradientStop(color='#2ea043', offset=0),
                                   alt.GradientStop(color='transparent', offset=1)],
                            x1=1, x2=1, y1=1, y2=0
                        )
                    ).encode(
                        x='timestamp',
                        y='rps'
                    ).properties(height=300, title="Throughput (Req/Sec)")
                    
                    st.altair_chart(c1, use_container_width=True)
                
            time.sleep(1)
            # Check if still running
            active = get_active_campaign()
            if active is None:
                st.rerun()

# --- PAGE 4: System Health ---
elif page == "System Health":
    st.title("System Health Monitor")
    
    ph = st.empty()
    while True:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()
        
        with ph.container():
            col1, col2 = st.columns(2)
            col1.metric("CPU Usage", f"{cpu}%")
            col2.metric("RAM Usage", f"{ram.percent}%", f"{ram.used / (1024**3):.1f}GB / {ram.total / (1024**3):.1f}GB")
            
            # Process List
            st.subheader("Active Processes")
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'username']):
                if 'python' in p.info['name'] or 'streamlit' in p.info['name']:
                    procs.append(p.info)
            st.dataframe(pd.DataFrame(procs), use_container_width=True)
            
        time.sleep(2)
