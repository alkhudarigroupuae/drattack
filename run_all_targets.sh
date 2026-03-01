#!/bin/bash

# الألوان للتنسيق
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
echo "=================================================="
echo "   🚀 AUTO-RUNNER: TESTING ALL TARGETS   "
echo "=================================================="
echo -e "${NC}"

# التحقق من وجود بايثون
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed!${NC}"
    exit 1
fi

TARGETS_FILE="targets.txt"

if [ ! -f "$TARGETS_FILE" ]; then
    echo -e "${RED}Error: $TARGETS_FILE not found!${NC}"
    exit 1
fi

# إعدادات الهجوم الافتراضية
CONCURRENCY=50
DURATION=30
REPORTS_DIR="reports_$(date +%Y%m%d_%H%M%S)"

mkdir -p "$REPORTS_DIR"

echo -e "${YELLOW}Reading targets from $TARGETS_FILE...${NC}"
echo -e "${YELLOW}Settings: Concurrency=$CONCURRENCY, Duration=${DURATION}s per target${NC}"
echo ""

count=0
total=$(grep -c '^http' "$TARGETS_FILE")

while IFS= read -r url || [ -n "$url" ]; do
    # تجاهل الأسطر الفارغة والتعليقات
    if [[ -z "$url" || "$url" == \#* ]]; then
        continue
    fi
    
    count=$((count + 1))
    
    # تنظيف اسم الملف من الرموز الخاصة
    safe_name=$(echo "$url" | sed 's/https\?:\/\///' | sed 's/[\/:]/_/g')
    report_file="$REPORTS_DIR/${safe_name}.html"
    
    echo -e "${GREEN}[$count/$total] Testing Target: ${url}${NC}"
    
    # تشغيل الهجوم
    python3 advanced_stress_test.py "$url" -c "$CONCURRENCY" -d "$DURATION" --report --output "$report_file"
    
    echo -e "${GREEN}✔ Done. Report saved to $report_file${NC}"
    echo "--------------------------------------------------"
    
    # استراحة قصيرة لتجنب تجميد الجهاز بالكامل
    sleep 2

done < "$TARGETS_FILE"

echo ""
echo -e "${GREEN}✅ All targets processed! Reports are in directory: $REPORTS_DIR${NC}"
