# 🎓 Cybersecurity Case Study: Network Stress Testing & Analysis

**Subject:** Evaluation of Web Server Resilience Against DoS Attacks
**Level:** University / Academic
**Date:** 2026-02-28

---

## 1. Introduction
This case study explores the methodologies used to stress-test web infrastructure and firewall configurations. The objective is to understand different attack vectors, their impact on server resources (CPU, RAM, Bandwidth), and how to validate defensive mechanisms.

We utilize two primary tools developed for this study:
1.  **Application Layer Stressor** (based on `aiohttp` / `Locust`).
2.  **Transport Layer Packet Crafter** (based on `Scapy`).

---

## 2. Attack Vectors Analysis

### A. HTTP Flood (Layer 7 Attack)
*   **Tool Used:** `advanced_stress_test.py`
*   **Protocol:** HTTP/1.1 & HTTP/2
*   **Mechanism:**
    The attacker establishes full TCP connections and sends legitimate HTTP GET/POST requests. The goal is to force the web server to load application logic, query databases, and generate dynamic content.
*   **Why it is effective:**
    *   **Resource Exhaustion:** Generating a webpage is computationally expensive for the server (CPU/RAM), while sending the request is cheap for the attacker.
    *   **Evasion:** It mimics normal user behavior (using valid User-Agents), making it harder for simple firewalls to distinguish from a "flash crowd."
*   **Power Level:** ⭐⭐⭐⭐⭐ (Very High Impact on Web Apps)
*   **Target:** Web Server (Nginx/Apache), Application Server (PHP/Python), Database.

### B. TCP SYN Flood (Layer 4 Attack)
*   **Tool Used:** `simulation/syn_flood_educational.py`
*   **Protocol:** TCP (Transmission Control Protocol)
*   **Mechanism:**
    The attacker sends a stream of `SYN` packets (connection requests) often with spoofed source IPs. The server responds with `SYN-ACK` and waits for the final `ACK`. The attacker never sends the `ACK`.
*   **Why it is effective:**
    *   **Connection Table Saturation:** The server allocates memory for each "half-open" connection. Once the table fills up, the server drops legitimate new connections.
*   **Power Level:** ⭐⭐⭐ (Effective against unhardened OS kernels)
*   **Target:** Operating System Kernel, Load Balancer, Firewall.

---

## 3. Methodology & Execution

### Phase 1: Baseline Metrics
Before attacking, we measure the baseline performance of the target:
*   **Normal Latency:** ~100ms
*   **Error Rate:** 0%

### Phase 2: Stress Testing (Execution)
We execute the `advanced_stress_test.py` with high concurrency (e.g., 1000 workers).

**Command:**
```bash
python3 advanced_stress_test.py http://TARGET_IP -c 1000 -d 60
```

**Observations:**
1.  **RPS (Requests Per Second):** Increases initially, then plateaus.
2.  **Latency:** Spikes significantly as the server queue fills.
3.  **Failure Point:** The server begins returning `503 Service Unavailable` or `Connection Timeouts`.

---

## 4. Conclusion & Remediation
The study demonstrates that even a single machine running asynchronous code (AsyncIO) can generate enough load to destabilize an unprotected web server.

**Recommended Defenses:**
1.  **Rate Limiting:** Restrict the number of requests per IP (e.g., 10 req/sec).
2.  **WAF (Web Application Firewall):** Challenge suspicious traffic (e.g., CAPTCHA).
3.  **SYN Cookies:** Enable kernel-level protection against SYN Floods.

---
*This document is for educational and research purposes only.*
