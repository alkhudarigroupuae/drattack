# Advanced Stress Testing Tool - User Guide

This tool is designed for **High Performance Load Testing**. It uses Python's `asyncio` and `aiohttp` libraries to generate thousands of requests per second from a single machine, simulating heavy traffic to stress-test web servers and firewalls.

## ⚠️ Disclaimer
**For authorized testing only.** Ensure you have permission to test the target system. The author is not responsible for misuse.

## 1. Installation

You need Python 3 and the `aiohttp` library.

```bash
pip install aiohttp
```

## 2. Basic Usage

Run the script from your terminal. By default, it tests `http://localhost:5000`.

```bash
python3 advanced_stress_test.py
```

## 3. Targeting a Specific Website

To test a specific URL, pass it as an argument.

**Example:**
```bash
python3 advanced_stress_test.py https://example.com
```

## 4. Increasing Power (Concurrency)

Use the `-c` (concurrency) flag to set how many simultaneous connections to open.
*   **Low Load:** 50 - 100
*   **Medium Load:** 500 - 1000
*   **High Load:** 2000+ (Depends on your CPU/Network)

**Example (Heavy Load):**
```bash
python3 advanced_stress_test.py https://example.com -c 1000
```

## 5. Setting Duration

Use the `-d` flag to set how long the test should run (in seconds).

**Example (Run for 5 minutes):**
```bash
python3 advanced_stress_test.py https://example.com -c 500 -d 300
```

## 6. Interpreting Results

At the end of the test, you will see a report:

*   **Successful Requests:** Requests that got a valid response (200 OK, etc.).
*   **Failed Requests:** Requests that were blocked, timed out, or returned server errors (500/503).
*   **Speed (RPS):** Requests Per Second. Higher is better for the attacker/tester. If this number drops suddenly during a test, the server might be down or blocking you.

---
**Note:** If you see many errors or timeouts, it means the target server is struggling or the firewall has blocked your IP.
