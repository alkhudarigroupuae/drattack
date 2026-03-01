import streamlit as st
import pandas as pd
import time
import altair as alt
from datetime import datetime
import os

# --- VPS Configuration ---
VPS_IP = "76.13.179.65"

# --- Page Configuration ---
st.set_page_config(
    page_title="Network Stress Analysis Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- Custom CSS for Professional/Scientific Look ---
st.markdown("""
<style>
    /* Global Font Settings */
    body {
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background-color: #f0f2f6;
    }
    
    /* Header Styling */
    h1 {
        font-size: 2.5rem;
        font-weight: 600;
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    h2, h3 {
        color: #34495e;
        font-weight: 500;
    }
    
    /* Metric Card Styling */
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        border-left: 5px solid #3498db;
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    
    /* Alert Styling */
    .stAlert {
        border-radius: 5px;
    }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.title("Network Stress Analysis Monitor")
st.markdown(f"**Server Node:** {VPS_IP} | **Status:** Online")
st.markdown("### Real-Time Traffic & Performance Metrics")

# --- Data Loading Logic ---
LOG_FILE = "attack_stats.csv"

def load_data():
    if not os.path.exists(LOG_FILE):
        return pd.DataFrame(columns=['timestamp', 'requests', 'success', 'failed', 'rps', 'bytes_received'])
    
    try:
        # Read only the last 100 lines for performance
        df = pd.read_csv(LOG_FILE)
        return df
    except pd.errors.EmptyDataError:
        return pd.DataFrame(columns=['timestamp', 'requests', 'success', 'failed', 'rps', 'bytes_received'])
    except Exception as e:
        st.error(f"Error reading log file: {e}")
        return pd.DataFrame()

# --- Layout ---
placeholder = st.empty()

while True:
    with placeholder.container():
        df = load_data()
        
        if df.empty:
            st.info("Waiting for data stream... Please initiate a stress test from the Control Panel.")
            st.markdown(f"[Go to Control Panel](http://{VPS_IP}:8501)")
            time.sleep(2)
            continue
            
        # Get latest metrics
        latest = df.iloc[-1]
        previous = df.iloc[-2] if len(df) > 1 else latest
        
        # --- Key Performance Indicators (KPIs) ---
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate deltas
        rps_delta = latest['rps'] - previous['rps']
        req_delta = latest['requests'] - previous['requests']
        fail_delta = latest['failed'] - previous['failed']
        
        with col1:
            st.metric(
                label="Throughput (Req/Sec)",
                value=f"{latest['rps']:.2f}",
                delta=f"{rps_delta:.2f}/s"
            )
            
        with col2:
            st.metric(
                label="Total Requests Sent",
                value=f"{int(latest['requests']):,}",
                delta=f"+{int(req_delta)}"
            )
            
        with col3:
            # Calculate Failure Rate
            failure_rate = (latest['failed'] / latest['requests'] * 100) if latest['requests'] > 0 else 0
            st.metric(
                label="Error Rate (%)",
                value=f"{failure_rate:.2f}%",
                delta=f"{latest['failed'] - previous['failed']} new errors",
                delta_color="inverse"
            )
            
        with col4:
            mb_received = latest['bytes_received'] / (1024 * 1024)
            st.metric(
                label="Data Transferred (MB)",
                value=f"{mb_received:.2f} MB"
            )

        st.markdown("---")

        # --- Time Series Analysis ---
        chart_data = df.tail(60) # Show last 60 data points (approx 60 seconds)
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.subheader("Throughput Analysis (RPS)")
            chart_rps = alt.Chart(chart_data).mark_area(
                line={'color':'#3498db'},
                color=alt.Gradient(
                    gradient='linear',
                    stops=[alt.GradientStop(color='#3498db', offset=0),
                           alt.GradientStop(color='white', offset=1)],
                    x1=1, x2=1, y1=1, y2=0
                )
            ).encode(
                x=alt.X('timestamp', axis=alt.Axis(title='Time', labelAngle=-45)),
                y=alt.Y('rps', axis=alt.Axis(title='Requests Per Second')),
                tooltip=['timestamp', 'rps', 'requests']
            ).properties(
                height=300
            )
            st.altair_chart(chart_rps, use_container_width=True)
            
        with col_chart2:
            st.subheader("Error Distribution")
            # Melt data for multi-line chart
            chart_err = alt.Chart(chart_data).mark_line().encode(
                x=alt.X('timestamp', axis=alt.Axis(title='Time', labelAngle=-45)),
                y=alt.Y('failed', axis=alt.Axis(title='Cumulative Failures')),
                color=alt.value('#e74c3c'),
                tooltip=['timestamp', 'failed']
            ).properties(
                height=300
            )
            st.altair_chart(chart_err, use_container_width=True)

        # --- Detailed Logs ---
        with st.expander("Detailed System Logs", expanded=True):
            st.dataframe(
                df.sort_index(ascending=False).head(10),
                use_container_width=True,
                column_config={
                    "timestamp": "Time",
                    "requests": "Total Requests",
                    "success": "Success (2xx/3xx)",
                    "failed": "Failed (4xx/5xx/Timeout)",
                    "rps": "Current RPS",
                    "bytes_received": "Bytes RX"
                }
            )
            
        time.sleep(1)
