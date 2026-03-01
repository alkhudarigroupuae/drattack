import random
from locust import HttpUser, task, between, constant_pacing
from locust.contrib.fasthttp import FastHttpUser

# قائمة بمتصفحات مختلفة لمحاكاة زوار حقيقيين وتجنب الحظر البسيط
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36"
]

class AdvancedGovTester(FastHttpUser):
    # استخدام FastHttpUser لأداء أعلى (توليد طلبات أكثر بنفس الموارد)
    # constant_pacing يضمن معدل ثابت للطلبات بغض النظر عن سرعة الاستجابة
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """يتم تنفيذها عند بدء كل مستخدم افتراضي"""
        self.client.headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "fa-IR,fa;q=0.9,en-US;q=0.8,en;q=0.7",
            "X-Requested-With": "XMLHttpRequest"
        }

    @task(10)
    def heavy_load_homepage(self):
        """زيارة الصفحة الرئيسية (أكثر شيوعاً)"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 503:
                response.failure("Server Overloaded (503)")
            elif response.status_code == 403:
                response.failure("Firewall Blocked (403)")
            else:
                response.failure(f"Error: {response.status_code}")

    @task(3)
    def search_query_attack(self):
        """محاكاة هجوم بحث (Database Stress)"""
        # استعلامات بحث عشوائية تستهلك موارد قاعدة البيانات
        queries = ["iran", "tehran", "law", "ministry", "president", "oil", "nuclear"]
        query = random.choice(queries)
        self.client.get(f"/search?q={query}", name="/search")

    @task(1)
    def login_bruteforce_simulation(self):
        """محاكاة محاولات تسجيل دخول (Authentication Stress)"""
        # هذا يختبر قدرة السيرفر على معالجة طلبات POST والتشفير
        payload = {
            "username": f"user_{random.randint(1000, 9999)}",
            "password": "password123"
        }
        self.client.post("/login", json=payload, name="/login")

    @task(5)
    def static_assets_flood(self):
        """محاكاة تحميل مكثف للملفات الثابتة (Bandwidth Stress)"""
        # يختبر قدرة الخادم على تقديم ملفات كبيرة بسرعة
        assets = ["/static/logo.png", "/static/style.css", "/static/main.js"]
        asset = random.choice(assets)
        self.client.get(asset, name="/static_assets")

# لتشغيل الاختبار في وضع Headless وتصدير التقرير:
# locust -f simulation/locustfile.py --headless -u 1000 -r 50 --run-time 1m --host http://TARGET_IP --html report.html
