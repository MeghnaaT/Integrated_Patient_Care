# Deployment Guide — IPCMS Production Setup

This document outlines the procedures to deploy the **Integrated Patient Care Management System (IPCMS)** into a production environment.

---

## 1. Production Architecture Overview

A secure, standard production deployment utilizes a multi-tier server setup:
* **Client (Web Browser):** Requests index and assets via HTTPS.
* **Nginx (Reverse Proxy & SSL):** Terminates HTTPS, serves static files directly, and forwards dynamic requests to the WSGI container.
* **Gunicorn (WSGI Server):** Spawns and manages workers to execute the Flask application.
* **MySQL Server (Database):** Hosted on a secure database instance (e.g., AWS RDS or a dedicated DB host) accessible only via internal network connections.

---

## 2. Setting Up Production Configurations

Before launching the app, modify the `.env` settings for production:
```ini
FLASK_ENV=production
SECRET_KEY=generate-a-strong-random-secure-64-character-hex-value
DB_USER=production_db_user
DB_PASSWORD=production_db_secure_password
DB_HOST=private-ip-of-mysql-host
DB_PORT=3306
DB_NAME=hospital_db
```

### Production Security Checklist
* **Debug Mode:** Always set `FLASK_ENV=production` or `DEBUG=False`. Debug mode exposes code stack traces and arbitrary code execution pathways.
* **Secure Cookies:** In production, Flask-Session and Flask-Login cookies are flagged as secure:
  - `SESSION_COOKIE_SECURE = True`
  - `REMEMBER_COOKIE_SECURE = True`

---

## 3. WSGI Container: Gunicorn Setup

On a Linux/Ubuntu production server, Gunicorn is the recommended WSGI container.

### Step 3.1: Install Gunicorn
Inside your server virtual environment:
```bash
pip install gunicorn
```

### Step 3.2: Configure Systemd Daemon
Create a system service file `/etc/systemd/system/ipcms.service` to keep the application running automatically:
```ini
[Unit]
Description=Gunicorn instance to serve IPCMS
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/Integrated_Patient_Care
Environment="PATH=/var/www/Integrated_Patient_Care/.venv/bin"
ExecStart=/var/www/Integrated_Patient_Care/.venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 run:app

[Install]
WantedBy=multi-user.target
```
Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start ipcms
sudo systemctl enable ipcms
```

---

## 4. Reverse Proxy: Nginx Configuration

Create an Nginx server block `/etc/nginx/sites-available/ipcms`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    # Redirect all HTTP requests to HTTPS
    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;

    # SSL Certificate Paths
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Serve static assets directly for high performance
    location /static/ {
        alias /var/www/Integrated_Patient_Care/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # Proxy dynamic requests to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Enable the site and reload Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/ipcms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 5. Obtaining Free SSL with Certbot (Let's Encrypt)
Run Certbot to automatically configure secure SSL certificates:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```
Certbot will configure certificate auto-renewal via a daily systemd cron job automatically.
