#!/bin/bash

# ==========================================
# 🚀 CYBER-STRESS PLATFORM - VPS DEPLOYMENT
# ==========================================
# Run this script on your VPS (Ubuntu/Debian) to setup the environment.
# Usage: sudo ./deploy_to_vps.sh
# ==========================================

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "################################################"
echo "   STARTING DEPLOYMENT ON VPS SERVER   "
echo "################################################"
echo -e "${NC}"

# 1. Update System
echo -e "${YELLOW}[1/5] Updating System Packages...${NC}"
apt-get update && apt-get upgrade -y
if [ $? -ne 0 ]; then
    echo -e "${RED}Error updating system. Are you root?${NC}"
    exit 1
fi

# 2. Install Python & Tools
echo -e "${YELLOW}[2/5] Installing Python3, Pip, and Git...${NC}"
apt-get install -y python3 python3-pip python3-venv git htop screen
if [ $? -ne 0 ]; then
    echo -e "${RED}Error installing dependencies.${NC}"
    exit 1
fi

# 3. Setup Project Directory
echo -e "${YELLOW}[3/5] Setting up Project Directory...${NC}"
PROJECT_DIR="/opt/cyber-stress-platform"
mkdir -p "$PROJECT_DIR"
cp -r * "$PROJECT_DIR" 2>/dev/null || echo "Copying files (if running locally)..."
cd "$PROJECT_DIR"

# 4. Install Python Libraries
echo -e "${YELLOW}[4/5] Installing Python Libraries...${NC}"
pip3 install --break-system-packages aiohttp streamlit pandas scapy locust requests altair

# 5. Create Startup Script
echo -e "${YELLOW}[5/5] Creating Startup Service...${NC}"
cat <<EOF > start_platform.sh
#!/bin/bash
echo "Starting Dashboard on port 8501..."
screen -dmS dashboard streamlit run dashboard.py --server.port 8501 --server.address 0.0.0.0
echo "Starting Live Monitor on port 8502..."
screen -dmS monitor streamlit run live_monitor.py --server.port 8502 --server.address 0.0.0.0
echo "Platform is RUNNING!"
EOF

chmod +x start_platform.sh

echo -e "${GREEN}"
echo "################################################"
echo "   ✅ DEPLOYMENT COMPLETE!   "
echo "################################################"
echo -e "${NC}"
echo "To start the platform, run:"
echo "  cd $PROJECT_DIR"
echo "  ./start_platform.sh"
echo ""
echo "Then access your dashboard at:"
echo "  http://YOUR_VPS_IP:8501"
echo -e "${NC}"
