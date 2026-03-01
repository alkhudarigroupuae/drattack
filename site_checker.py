import requests
import time
import logging
import pandas as pd
from datetime import datetime

# إعدادات التسجيل (Logging)
logging.basicConfig(
    filename='connectivity_log.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_website(url):
    """
    يفحص حالة الموقع ويسجل وقت الاستجابة وحالة الاتصال.
    """
    try:
        start_time = time.time()
        response = requests.get(url, timeout=10)
        end_time = time.time()
        
        duration = end_time - start_time
        status_code = response.status_code
        
        result = {
            'url': url,
            'status': 'Success',
            'status_code': status_code,
            'response_time': round(duration, 4),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_size': len(response.content)  # حجم البيانات المستلمة
        }
        
        logging.info(f"Checked {url}: Status {status_code}, Time {duration:.4f}s, Size {len(response.content)} bytes")
        print(f"✅ {url} - Status: {status_code} - Time: {duration:.4f}s - Size: {len(response.content)} bytes")
        return result

    except requests.exceptions.RequestException as e:
        logging.error(f"Error checking {url}: {str(e)}")
        print(f"❌ {url} - Error: {str(e)}")
        return {
            'url': url,
            'status': 'Error',
            'status_code': None,
            'response_time': None,
            'error_message': str(e),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_size': 0
        }

def main():
    targets_file = 'targets.txt'
    results = []
    
    try:
        with open(targets_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except FileNotFoundError:
        print(f"File {targets_file} not found. Creating a default one.")
        with open(targets_file, 'w') as f:
            f.write("https://www.google.com\n")
        urls = ["https://www.google.com"]

    print(f"🔍 Starting connectivity check for {len(urls)} websites...")
    print("-" * 50)

    for url in urls:
        if not url.startswith('http'):
            url = 'https://' + url
        
        result = check_website(url)
        results.append(result)
        time.sleep(1) # تأخير بسيط لتجنب الحظر

    # حفظ النتائج في ملف CSV للتحليل
    df = pd.DataFrame(results)
    df.to_csv('scan_results.csv', index=False)
    print("-" * 50)
    print("📊 Results saved to scan_results.csv")

if __name__ == "__main__":
    main()
