import time
import urllib.request
import urllib.parse
import http.cookiejar
import re
import sys

def percentile(data, pct):
    """Calculate percentile without numpy."""
    if not data:
        return 0.0
    sorted_data = sorted(data)
    index = (pct / 100.0) * (len(sorted_data) - 1)
    lower = int(index)
    upper = min(lower + 1, len(sorted_data) - 1)
    fraction = index - lower
    return sorted_data[lower] + fraction * (sorted_data[upper] - sorted_data[lower])

def measure_api_performance():
    print("=== MEASURING REST API 95TH PERCENTILE RESPONSE TIME ===")
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    # Authenticate as Admin
    resp_get = opener.open('http://127.0.0.1:5000/auth/login')
    html_get = resp_get.read().decode('utf-8')
    match = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html_get)
    csrf_token = match.group(1) if match else ''

    data = urllib.parse.urlencode({'csrf_token': csrf_token, 'email': 'admin@ipcms.com', 'password': 'admin123'}).encode('utf-8')
    opener.open('http://127.0.0.1:5000/auth/login', data=data)

    # These are the actual REST API paths registered under /api/v1
    endpoints = [
        ('/api/v1/patients',       'GET Patients'),
        ('/api/v1/doctors',        'GET Doctors'),
        ('/api/v1/consultations',  'GET Consultations'),
        ('/api/v1/prescriptions',  'GET Prescriptions'),
        ('/api/v1/laboratory',     'GET Lab Reports'),
        ('/api/v1/pharmacy',       'GET Pharmacy'),
        ('/api/v1/billing',        'GET Billing'),
        ('/api/v1/notifications',  'GET Notifications'),
    ]

    all_times = []
    endpoint_results = []
    for ep, label in endpoints:
        ep_times = []
        error_count = 0
        for _ in range(10):
            t0 = time.time()
            try:
                resp = opener.open(f'http://127.0.0.1:5000{ep}')
                resp.read()  # consume body
                t1 = time.time()
                ms = (t1 - t0) * 1000
                ep_times.append(ms)
                all_times.append(ms)
            except Exception as e:
                error_count += 1
        avg_ep = sum(ep_times) / len(ep_times) if ep_times else 0
        p95_ep = percentile(ep_times, 95) if ep_times else 0
        status = 'PASS' if p95_ep <= 300 else 'FAIL'
        endpoint_results.append((ep, avg_ep, p95_ep, error_count, status))
        print(f"  {label:<25} | Avg: {avg_ep:6.1f}ms | P95: {p95_ep:6.1f}ms | Errors: {error_count} | {status}")

    overall_p95 = percentile(all_times, 95) if all_times else 0
    req_pass = overall_p95 <= 300
    print(f"\nOverall P95: {overall_p95:.1f} ms | Requirement: <= 300 ms | {'PASS' if req_pass else 'FAIL'}")
    return overall_p95, req_pass

def measure_notification_delivery():
    print("\n=== MEASURING NOTIFICATION DELIVERY SUCCESS RATE ===")
    sys.path.insert(0, '.')
    from app import create_app
    from models.notification import Notification

    app = create_app('default')
    with app.app_context():
        total = Notification.query.count()
        delivered = Notification.query.filter(Notification.status.in_(['Delivered', 'Read'])).count()
        failed = Notification.query.filter_by(status='Failed').count()
        rate = (delivered / total * 100) if total > 0 else 100.0
        req_pass = rate >= 95.0
        print(f"Total: {total} | Delivered: {delivered} | Failed: {failed} | Rate: {rate:.1f}% | Req >=95% | {'PASS' if req_pass else 'FAIL'}")
        return rate, req_pass

if __name__ == '__main__':
    p95, api_pass = measure_api_performance()
    rate, notif_pass = measure_notification_delivery()
    print(f"\n=== SUMMARY ===")
    print(f"M3 REST API P95 Requirement (<= 300ms): {'PASS' if api_pass else 'FAIL'} ({p95:.1f} ms)")
    print(f"M3 Notification Delivery (>= 95%): {'PASS' if notif_pass else 'FAIL'} ({rate:.1f}%)")
