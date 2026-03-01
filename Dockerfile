# استخدام صورة بايثون الرسمية الخفيفة
FROM python:3.9-slim

# إعداد متغيرات البيئة
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# إنشاء مجلد العمل
WORKDIR /app

# تثبيت أدوات النظام الضرورية
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملف المتطلبات وتثبيتها
COPY requirements.txt .
# إضافة المكتبات الإضافية التي استخدمناها
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir aiohttp scapy altair locust

# نسخ باقي ملفات المشروع
COPY . .

# فتح المنافذ المطلوبة
EXPOSE 8501 8502

# سكربت التشغيل الافتراضي (سيتم تجاوزه بواسطة docker-compose)
CMD ["streamlit", "run", "dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
