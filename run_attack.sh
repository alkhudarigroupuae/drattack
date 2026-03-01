#!/bin/bash

# الألوان للتنسيق
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=================================================="
echo "   🚀 ADVANCED STRESS TESTING SYSTEM - AUTO MODE   "
echo "=================================================="
echo -e "${NC}"

# التحقق من وجود بايثون
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi

# تثبيت المكتبات المطلوبة تلقائياً
echo -e "${YELLOW}[+] Checking dependencies...${NC}"
pip3 install aiohttp &> /dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[✔] Dependencies ready.${NC}"
else
    echo -e "${RED}[✘] Failed to install dependencies. Check your internet.${NC}"
    exit 1
fi

# طلب المدخلات من المستخدم
echo ""
read -p "🎯 Enter Target URL (e.g., https://example.com): " TARGET_URL

if [ -z "$TARGET_URL" ]; then
    echo -e "${RED}Error: URL is required!${NC}"
    exit 1
fi

echo ""
read -p "⚡ Enter Attack Power (Concurrency) [Default: 100]: " CONCURRENCY
CONCURRENCY=${CONCURRENCY:-100}

echo ""
read -p "⏱️  Enter Duration (Seconds) [Default: 60]: " DURATION
DURATION=${DURATION:-60}

# تأكيد البدء
echo ""
echo -e "${YELLOW}WARNING: You are about to start a stress test on: ${TARGET_URL}${NC}"
echo -e "${YELLOW}Power: ${CONCURRENCY} connections | Duration: ${DURATION}s${NC}"
read -p "Press ENTER to confirm and start..."

# تشغيل الهجوم
echo ""
echo -e "${GREEN}🚀 Launching Attack... Please wait.${NC}"
python3 advanced_stress_test.py "$TARGET_URL" -c "$CONCURRENCY" -d "$DURATION" --report

# فتح التقرير تلقائياً
echo ""
echo -e "${GREEN}✅ Attack Completed.${NC}"
echo -e "${YELLOW}📊 Opening Report...${NC}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    open attack_report.html  # macOS
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    xdg-open attack_report.html  # Linux
elif [[ "$OSTYPE" == "msys" ]]; then
    start attack_report.html  # Windows
else
    echo "Could not open browser automatically. Please open 'attack_report.html' manually."
fi
