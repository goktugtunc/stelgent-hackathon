# Stelgent Backend - Deployment Guide

Kendi sunucunuzda Stelgent backend'ini kurmak için kapsamlı rehber.

## 📋 Gereksinimler

- Ubuntu 20.04 / 22.04 veya Debian 11/12
- Root veya sudo yetkisi
- En az 2GB RAM
- En az 10GB disk alanı
- Domain adı (opsiyonel, SSL için gerekli)

---

## 🚀 Kurulum Adımları

### 1. Sistem Güncellemesi

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Python 3.11 Kurulumu

```bash
# Python 3.11 ve pip kurulumu
sudo apt install -y python3.11 python3.11-venv python3-pip

# Python versiyonunu kontrol et
python3.11 --version
```

### 3. MongoDB Kurulumu

```bash
# MongoDB GPG anahtarını ekle
curl -fsSL https://pgp.mongodb.com/server-7.0.asc | \\
   sudo gpg -o /usr/share/keyrings/mongodb-server-7.0.gpg \\
   --dearmor

# MongoDB repository ekle
echo "deb [ arch=amd64,arm64 signed-by=/usr/share/keyrings/mongodb-server-7.0.gpg ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | \\
   sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list

# MongoDB'yi yükle
sudo apt update
sudo apt install -y mongodb-org

# MongoDB'yi başlat ve enable et
sudo systemctl start mongod
sudo systemctl enable mongod

# Durumu kontrol et
sudo systemctl status mongod
```

#### MongoDB Güvenlik Ayarları (Önerilen)

```bash
# MongoDB shell'e bağlan
mongosh

# Admin kullanıcısı oluştur
use admin
db.createUser({
  user: "admin",
  pwd: "STRONG_PASSWORD_HERE",
  roles: [ { role: "userAdminAnyDatabase", db: "admin" } ]
})

# Stelgent database için kullanıcı oluştur
use stelgent_db
db.createUser({
  user: "stelgent_user",
  pwd: "ANOTHER_STRONG_PASSWORD",
  roles: [ { role: "readWrite", db: "stelgent_db" } ]
})

exit
```

```bash
# MongoDB config dosyasını düzenle
sudo nano /etc/mongod.conf

# Şu satırları ekle/düzenle:
security:
  authorization: enabled

# MongoDB'yi restart et
sudo systemctl restart mongod
```

### 4. Nginx Kurulumu

```bash
sudo apt install -y nginx

# Nginx'i başlat
sudo systemctl start nginx
sudo systemctl enable nginx
```

### 5. Proje Kurulumu

```bash
# Uygulama dizini oluştur
sudo mkdir -p /opt/stelgent
cd /opt/stelgent

# Backend dosyalarını buraya yükle
# (Git clone veya SCP/FTP ile)

# Örnek: Git ile
sudo git clone https://github.com/yourusername/stelgent-backend.git backend
cd backend

# Python virtual environment oluştur
python3.11 -m venv venv

# Virtual environment'ı aktif et
source venv/bin/activate

# Dependencies yükle
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Environment Variables Ayarlama

```bash
# .env dosyası oluştur
cp .env.example .env
nano .env
```

**`.env` içeriği:**

```env
# MongoDB Configuration
MONGO_URL=mongodb://stelgent_user:ANOTHER_STRONG_PASSWORD@localhost:27017/stelgent_db?authSource=stelgent_db
DB_NAME=stelgent_db

# JWT Configuration
JWT_SECRET=GENERATE_A_RANDOM_32_CHARACTER_STRING_HERE
JWT_ALGORITHM=HS256
JWT_EXPIRATION_DAYS=7

# Gemini AI Configuration
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=False

# CORS Configuration
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
```

**JWT Secret oluşturma:**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 7. Systemd Service Oluşturma

```bash
# Service dosyası oluştur
sudo nano /etc/systemd/system/stelgent-backend.service
```

**Service dosyası içeriği:**

```ini
[Unit]
Description=Stelgent Backend API
After=network.target mongod.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/opt/stelgent/backend
Environment="PATH=/opt/stelgent/backend/venv/bin"
ExecStart=/opt/stelgent/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Restart policy
Restart=always
RestartSec=5

# Security
NoNewPrivileges=true
PrivateTmp=true

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=stelgent-backend

[Install]
WantedBy=multi-user.target
```

```bash
# Dosya izinlerini ayarla
sudo chown -R www-data:www-data /opt/stelgent/backend

# Service'i yükle ve başlat
sudo systemctl daemon-reload
sudo systemctl start stelgent-backend
sudo systemctl enable stelgent-backend

# Durumu kontrol et
sudo systemctl status stelgent-backend

# Logları izle
sudo journalctl -u stelgent-backend -f
```

### 8. Nginx Konfigürasyonu

```bash
# Nginx config dosyası oluştur
sudo nano /etc/nginx/sites-available/stelgent-backend
```

**Nginx config içeriği:**

```nginx
# Backend API
server {
    listen 80;
    server_name api.yourdomain.com;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    location / {
        limit_req zone=api_limit burst=20 nodelay;
        
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
```

```bash
# Config'i enable et
sudo ln -s /etc/nginx/sites-available/stelgent-backend /etc/nginx/sites-enabled/

# Nginx config test et
sudo nginx -t

# Nginx'i reload et
sudo systemctl reload nginx
```

### 9. SSL/HTTPS Kurulumu (Certbot)

```bash
# Certbot yükle
sudo apt install -y certbot python3-certbot-nginx

# SSL sertifikası al
sudo certbot --nginx -d api.yourdomain.com

# Otomatik yenileme testi
sudo certbot renew --dry-run
```

### 10. Firewall Ayarları (UFW)

```bash
# UFW yükle ve aktif et
sudo apt install -y ufw

# SSH, HTTP, HTTPS'e izin ver
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'

# MongoDB'ye sadece localhost'tan erişim (zaten default)
sudo ufw deny 27017

# Firewall'u enable et
sudo ufw enable

# Durumu kontrol et
sudo ufw status
```

---

## 🔧 Yönetim Komutları

### Service Yönetimi

```bash
# Service'i başlat
sudo systemctl start stelgent-backend

# Service'i durdur
sudo systemctl stop stelgent-backend

# Service'i restart et
sudo systemctl restart stelgent-backend

# Durum kontrolü
sudo systemctl status stelgent-backend

# Logları görüntüle
sudo journalctl -u stelgent-backend -n 100 --no-pager

# Logları canlı izle
sudo journalctl -u stelgent-backend -f
```

### MongoDB Yönetimi

```bash
# MongoDB'ye bağlan
mongosh -u admin -p --authenticationDatabase admin

# Database kullan
use stelgent_db

# Collections listele
show collections

# Users tablosunu görüntüle
db.users.find().pretty()

# Proje sayısını göster
db.projects.countDocuments()

# Backup al
mongodump --uri="mongodb://stelgent_user:PASSWORD@localhost:27017/stelgent_db?authSource=stelgent_db" --out=/backup/mongodb/$(date +%Y%m%d)

# Restore et
mongorestore --uri="mongodb://stelgent_user:PASSWORD@localhost:27017/stelgent_db?authSource=stelgent_db" /backup/mongodb/20240108/stelgent_db
```

### Nginx Yönetimi

```bash
# Config test et
sudo nginx -t

# Reload et
sudo systemctl reload nginx

# Restart et
sudo systemctl restart nginx

# Access log
sudo tail -f /var/log/nginx/access.log

# Error log
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 Monitoring & Logs

### Application Logs

```bash
# Son 100 log
sudo journalctl -u stelgent-backend -n 100

# Bugünkü loglar
sudo journalctl -u stelgent-backend --since today

# Belirli tarih aralığı
sudo journalctl -u stelgent-backend --since "2024-01-01" --until "2024-01-31"

# Error logları
sudo journalctl -u stelgent-backend -p err

# Canlı takip
sudo journalctl -u stelgent-backend -f
```

### System Resources

```bash
# CPU ve Memory kullanımı
htop

# Disk kullanımı
df -h

# MongoDB stats
mongosh --eval "db.serverStatus()"

# Active connections
ss -tulpn | grep :8000
```

---

## 🔄 Güncelleme

```bash
# Backend güncelleme
cd /opt/stelgent/backend

# Yedek al (opsiyonel)
sudo cp -r /opt/stelgent/backend /opt/stelgent/backend.backup

# Güncel kodu çek
sudo git pull origin main

# Virtual environment aktif et
source venv/bin/activate

# Dependencies güncelle
pip install --upgrade -r requirements.txt

# Service'i restart et
sudo systemctl restart stelgent-backend

# Durumu kontrol et
sudo systemctl status stelgent-backend
```

---

## 🐛 Troubleshooting

### Service başlamıyor

```bash
# Logları kontrol et
sudo journalctl -u stelgent-backend -n 50

# Config dosyasını kontrol et
cat /opt/stelgent/backend/.env

# Port kullanımda mı?
sudo lsof -i :8000

# Manuel başlat (debug için)
cd /opt/stelgent/backend
source venv/bin/activate
python main.py
```

### MongoDB bağlantı hatası

```bash
# MongoDB çalışıyor mu?
sudo systemctl status mongod

# MongoDB logları
sudo tail -f /var/log/mongodb/mongod.log

# Bağlantı testi
mongosh "mongodb://stelgent_user:PASSWORD@localhost:27017/stelgent_db?authSource=stelgent_db"
```

### Nginx hatası

```bash
# Nginx config test
sudo nginx -t

# Nginx error log
sudo tail -f /var/log/nginx/error.log

# Port dinliyor mu?
sudo netstat -tulpn | grep :80
```

### Yüksek memory kullanımı

```bash
# Uvicorn worker sayısını azalt
sudo nano /etc/systemd/system/stelgent-backend.service

# --workers 4 yerine --workers 2 yap
ExecStart=/opt/stelgent/backend/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2

# Restart
sudo systemctl daemon-reload
sudo systemctl restart stelgent-backend
```

---

## 🔐 Güvenlik Önerileri

1. **Güçlü şifreler kullanın** (MongoDB, JWT secret)
2. **Firewall'u aktif tutun** (UFW)
3. **SSL/HTTPS kullanın** (Let's Encrypt)
4. **Rate limiting** ayarlayın (Nginx)
5. **Regular backups** alın (MongoDB)
6. **Güncellemeleri takip edin** (apt update)
7. **Logları düzenli kontrol edin**
8. **Fail2ban** kurun (brute force koruması)

```bash
# Fail2ban kurulumu
sudo apt install -y fail2ban

# Nginx için jail oluştur
sudo nano /etc/fail2ban/jail.local

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
logpath = /var/log/nginx/error.log
maxretry = 3
bantime = 3600

sudo systemctl restart fail2ban
```

---

## 📞 Destek

Sorun yaşarsanız:
1. Logları kontrol edin
2. GitHub Issues açın
3. Dokümantasyonu tekrar okuyun

---

## 📝 Notlar

- MongoDB veritabanı `/var/lib/mongodb` dizininde saklanır
- Nginx logları `/var/log/nginx/` dizininde
- Application logları `journalctl` ile erişilebilir
- Backup'ları düzenli alın!

---

**Başarılı deployment için tüm adımları sırasıyla takip edin!** 🚀
