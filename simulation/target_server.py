from flask import Flask, request, jsonify
import time
import threading

app = Flask(__name__)

# متغيرات لمحاكاة حالة الخادم
server_health = 100  # 100% تعني سليم
active_connections = 0
lock = threading.Lock()

@app.route('/')
def home():
    global active_connections, server_health
    
    with lock:
        active_connections += 1
        
    # محاكاة الضغط: كلما زاد عدد الاتصالات، زاد وقت الاستجابة
    # إذا زادت الاتصالات عن حد معين، يبدأ الخادم في الانهيار (Timeout/Error)
    
    try:
        if active_connections > 50:
            # الخادم تحت ضغط شديد -> بطء شديد أو أخطاء 503
            time.sleep(2)  # تأخير 2 ثانية
            if active_connections > 100:
                return "Server Overloaded", 503
        else:
            time.sleep(0.1)  # استجابة طبيعية

        return jsonify({
            "message": "Welcome to Iranian Gov Simulator",
            "status": "Online",
            "active_connections": active_connections
        })
        
    finally:
        with lock:
            active_connections -= 1

if __name__ == '__main__':
    print("🚀 Target Server Started on http://localhost:5000")
    print("⚠️  Warning: This server is vulnerable to High Traffic!")
    app.run(port=5000)
