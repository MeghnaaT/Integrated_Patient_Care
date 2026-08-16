import urllib.request
import urllib.parse
import http.cookiejar
import re

def test_patient_portal_live():
    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    print("=== LIVE SERVER PATIENT PORTAL WORKFLOW VERIFICATION ===")

    # 1. Login as Patient
    resp_get = opener.open('http://127.0.0.1:5000/auth/login')
    html_get = resp_get.read().decode('utf-8')
    token = re.search(r'name="csrf_token" type="hidden" value="([^"]+)"', html_get).group(1)

    data = urllib.parse.urlencode({'csrf_token': token, 'email': 'patient@ipcms.com', 'password': 'patient123'}).encode('utf-8')
    resp_login = opener.open('http://127.0.0.1:5000/auth/login', data=data)
    print(f"1. Patient Login -> Final URL: {resp_login.geturl()} | PASS: {resp_login.geturl().endswith('/patient/dashboard')}")

    # 2. Doctors Directory
    resp_doctors = opener.open('http://127.0.0.1:5000/doctor/list')
    print(f"2. Doctors Directory -> Final URL: {resp_doctors.geturl()} | PASS: {resp_doctors.geturl().endswith('/doctor/list')}")

    # 3. Book Appointment Page
    resp_book = opener.open('http://127.0.0.1:5000/appointment/book')
    print(f"3. Book Appointment -> Final URL: {resp_book.geturl()} | PASS: {resp_book.geturl().endswith('/appointment/book')}")

    # 4. My Appointments Page
    resp_my_appts = opener.open('http://127.0.0.1:5000/appointment/my-appointments')
    print(f"4. My Appointments -> Final URL: {resp_my_appts.geturl()} | PASS: {resp_my_appts.geturl().endswith('/appointment/my-appointments')}")

    # 5. My EHR
    resp_ehr = opener.open('http://127.0.0.1:5000/ehr/4')
    print(f"5. My EHR -> Final URL: {resp_ehr.geturl()} | PASS: {resp_ehr.geturl().endswith('/ehr/4')}")

    # 6. My Prescriptions
    resp_rx = opener.open('http://127.0.0.1:5000/prescriptions/list')
    print(f"6. My Prescriptions -> Final URL: {resp_rx.geturl()} | PASS: {resp_rx.geturl().endswith('/prescriptions/list')}")

    # 7. My Lab Reports
    resp_lab = opener.open('http://127.0.0.1:5000/laboratory/reports')
    print(f"7. My Lab Reports -> Final URL: {resp_lab.geturl()} | PASS: {resp_lab.geturl().endswith('/laboratory/reports')}")

    # 8. My Invoices
    resp_inv = opener.open('http://127.0.0.1:5000/billing/my-invoices')
    print(f"8. My Invoices -> Final URL: {resp_inv.geturl()} | PASS: {resp_inv.geturl().endswith('/billing/my-invoices')}")

    # 9. Submit Feedback Page
    resp_fb_sub = opener.open('http://127.0.0.1:5000/feedback/submit')
    print(f"9. Submit Feedback -> Final URL: {resp_fb_sub.geturl()} | PASS: {resp_fb_sub.geturl().endswith('/feedback/submit')}")

    # 10. My Feedback History
    resp_fb_hist = opener.open('http://127.0.0.1:5000/feedback/my-feedback')
    print(f"10. My Feedback History -> Final URL: {resp_fb_hist.geturl()} | PASS: {resp_fb_hist.geturl().endswith('/feedback/my-feedback')}")

    # 11. IDOR Protection check: Try to access Patient 5's EHR
    try:
        req_other = urllib.request.Request('http://127.0.0.1:5000/ehr/5')
        opener.open(req_other)
        print("11. IDOR Check (Other Patient EHR) -> FAILED (Allowed)")
    except urllib.error.HTTPError as e:
        print(f"11. IDOR Check (Other Patient EHR) -> Status: {e.code} | PASS: {e.code == 403}")

if __name__ == '__main__':
    test_patient_portal_live()
