# 🐳 VPS Docker Deployment Guide

This is the **modern way** to deploy your platform using Docker. It ensures everything runs perfectly isolated.

## 1. Connect to your VPS
Run this command from your terminal:
```bash
ssh root@76.13.179.65
```

## 2. Install Docker (Run on VPS)
Once logged in, copy and paste these commands to install Docker:

```bash
# Update and install Docker
apt-get update
apt-get install -y docker.io docker-compose

# Start Docker
systemctl start docker
systemctl enable docker
```

## 3. Upload Your Files (Run from Local Machine)
Open a **new terminal** on your laptop (keep the SSH one open) and run:

```bash
scp -r * root@76.13.179.65:/root/cyber-platform/
```
*(Enter your password when asked)*

## 4. Start the Platform (Run on VPS)
Back in your SSH session:

```bash
cd /root/cyber-platform

# Build and Start Containers
docker-compose up -d --build
```

## 5. Access Your Tools
*   **Dashboard:** `http://76.13.179.65:8501`
*   **Live Monitor:** `http://76.13.179.65:8502`

---
**Troubleshooting:**
If you cannot access the sites, check if the firewall allows these ports:
```bash
ufw allow 8501
ufw allow 8502
```
