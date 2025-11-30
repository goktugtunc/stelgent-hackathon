# Stelgent Backend - Python FastAPI

AI destekli kod üretim platformu için Python FastAPI backend.

## 🚀 Özellikler

- **FastAPI** - Modern, hızlı Python web framework
- **MongoDB** - NoSQL veritabanı
- **JWT Authentication** - Güvenli kullanıcı kimlik doğrulama
- **OpenAI (ChatGPT) Integration** - ChatGPT ile kod üretimi
- **Multi-turn Conversation** - Context'i koruyan sohbet
- **File Management** - Proje bazlı dosya sistemi
- **RESTful API** - Standart HTTP endpoint'ler

---

## 📁 Dosya Yapısı

```
backend/
├── main.py              # Ana FastAPI uygulaması
├── models.py            # Pydantic data modelleri
├── auth.py              # JWT authentication
├── database.py          # MongoDB bağlantısı
├── config.py            # Ayarlar ve environment variables
├── requirements.txt     # Python dependencies
├── .env.example         # Environment variables template
├── DEPLOYMENT.md        # Detaylı deployment rehberi
└── README.md            # Bu dosya
```

---

## 🔧 Local Development

### 1. Gereksinimler

- Python 3.11+
- MongoDB 7.0+
- OpenAI API Key (ChatGPT)

### 2. Kurulum

```bash
# Virtual environment oluştur
python3 -m venv venv

# Activate et (Linux/Mac)
source venv/bin/activate

# Activate et (Windows)
venv\\Scripts\\activate

# Dependencies yükle
pip install -r requirements.txt
```

### 3. Environment Variables

```bash
# .env dosyası oluştur
cp .env.example .env

# .env dosyasını düzenle
nano .env
```

**.env içeriği:**
```env
MONGO_URL=mongodb://localhost:27017
DB_NAME=stelgent_db
JWT_SECRET=your-secret-key-here
OPENAI_API_KEY=your-openai-api-key
FRONTEND_URL=http://localhost:3000
CORS_ORIGINS=http://localhost:3000
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

### 4. MongoDB Başlat

```bash
# MongoDB servisini başlat
sudo systemctl start mongod

# Veya Docker ile
docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

### 5. Uygulamayı Çalıştır

```bash
# Development mode (hot reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8005

# Veya direkt Python ile
python main.py
```

API şimdi http://localhost:8000 adresinde çalışıyor!

---

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/auth/register` | Yeni kullanıcı kaydı |
| POST | `/api/auth/login` | Kullanıcı girişi |
| GET | `/api/auth/me` | Mevcut kullanıcı bilgisi |

### Projects

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| POST | `/api/projects` | Yeni proje oluştur |
| GET | `/api/projects` | Tüm projeleri listele |
| GET | `/api/projects/{id}` | Tek proje detayı |
| DELETE | `/api/projects/{id}` | Proje sil |

### Files

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/projects/{id}/files` | Proje dosyalarını listele |
| POST | `/api/projects/{id}/files` | Yeni dosya oluştur |
| PUT | `/api/projects/{id}/files/{file_id}` | Dosya güncelle |
| DELETE | `/api/projects/{id}/files/{file_id}` | Dosya sil |

### Conversations

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/projects/{id}/conversations` | Conversation history |
| POST | `/api/projects/{id}/chat` | AI ile sohbet et |

### Settings

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| PUT | `/api/settings/openai` | OpenAI API key güncelle |

### Health Check

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/` | Basit health check |
| GET | `/health` | Detaylı health check |

---

## 📖 API Kullanım Örnekleri

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \\
  -H "Content-Type: application/json" \\
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123"
  }'
```

Response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "507f1f77bcf86cd799439011",
    "email": "user@example.com"
  }
}
```

### Create Project (Authentication Required)

```bash
curl -X POST http://localhost:8000/api/projects \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "My Awesome Project"
  }'
```

### Chat with AI

```bash
curl -X POST http://localhost:8000/api/projects/{project_id}/chat \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "message": "Create an index.html file with a hero section"
  }'
```

---

## 🧪 Testing

```bash
# Pytest ile test (gelecek özellik)
pytest tests/

# Manuel API test
# Postman veya Insomnia kullanabilirsiniz
# Swagger UI: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 🐳 Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# App code
COPY . .

# Expose port
EXPOSE 8000

# Run
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MONGO_URL=mongodb://mongodb:27017
      - DB_NAME=stelgent_db
      - JWT_SECRET=${JWT_SECRET}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    depends_on:
      - mongodb

  mongodb:
    image: mongo:7.0
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db

volumes:
  mongodb_data:
```

```bash
# Docker ile çalıştır
docker-compose up -d

# Logları izle
docker-compose logs -f backend
```

---

## 🔐 Güvenlik

- **JWT Tokens** - Güvenli authentication
- **Password Hashing** - Bcrypt ile şifreleme
- **CORS** - Origin kontrolü
- **Rate Limiting** - Nginx ile (production)
- **Environment Variables** - Hassas bilgiler .env'de
- **MongoDB Authentication** - Kullanıcı bazlı erişim

---

## 🚀 Production Deployment

Detaylı production deployment rehberi için: **[DEPLOYMENT.md](./DEPLOYMENT.md)**

Özet adımlar:
1. Ubuntu/Debian sunucu
2. Python 3.11+ kurulumu
3. MongoDB kurulumu ve güvenlik ayarları
4. Nginx reverse proxy
5. SSL/HTTPS (Let's Encrypt)
6. Systemd service
7. Firewall (UFW)
8. Monitoring ve logging

---

## 📊 Monitoring

### Application Logs

```bash
# Development
# Konsolda görünür

# Production (systemd)
sudo journalctl -u stelgent-backend -f
```

### Health Check

```bash
# Basit check
curl http://localhost:8000/

# Detaylı check
curl http://localhost:8000/health
```

---

## 🛠️ Development Tools

### Swagger UI

FastAPI otomatik API dokümantasyonu sağlar:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Burada tüm endpoint'leri görebilir ve test edebilirsiniz!

### Code Formatting

```bash
# Black - Python code formatter
pip install black
black .

# Isort - Import sorting
pip install isort
isort .

# Flake8 - Linting
pip install flake8
flake8 .
```

---

## 🔄 Database Schema

### Collections

**users**
```javascript
{
  _id: ObjectId,
  email: String,
  password: String (hashed),
  openai_api_key: String (optional),
  created_at: DateTime
}
```

**projects**
```javascript
{
  _id: ObjectId,
  user_id: String,
  name: String,
  created_at: DateTime
}
```

**files**
```javascript
{
  _id: ObjectId,
  project_id: String,
  path: String,
  content: String,
  type: String (file|folder),
  created_at: DateTime
}
```

**conversations**
```javascript
{
  _id: ObjectId,
  project_id: String,
  role: String (user|assistant),
  content: String,
  created_at: DateTime
}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

MIT License - İstediğiniz gibi kullanabilirsiniz!

---

## 🆘 Troubleshooting

### MongoDB bağlantı hatası
```bash
# MongoDB çalışıyor mu?
sudo systemctl status mongod

# Bağlantı string doğru mu?
echo $MONGO_URL
```

### Import hatası
```bash
# Dependencies yüklü mü?
pip install -r requirements.txt

# Virtual environment aktif mi?
which python
```

### Port zaten kullanımda
```bash
# 8000 portunu kullanan process'i bul
sudo lsof -i :8000

# Kill et
sudo kill -9 <PID>
```

---

## 📞 Destek

- GitHub Issues
- Email: support@stelgent.dev
- Dokümantasyon: [DEPLOYMENT.md](./DEPLOYMENT.md)

---

**Happy Coding! 🚀**
