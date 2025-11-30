# Stelgent - Quick Start Guide

Get Stelgent running in **5 minutes**!

## 📋 Requirements

Make sure your system has the following installed:

```bash
# Python version (3.11+)
python3 --version

# Node.js version (18+)
node --version

# MongoDB version (7.0+)
mongod --version
```

## ⚡ 5-Minute Setup

## 1️⃣ Start MongoDB

```bash
sudo systemctl start mongod

docker run -d -p 27017:27017 --name mongodb mongo:7.0
```

## 2️⃣ Backend Setup (2 minutes)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and add:

```env
GEMINI_API_KEY=your-api-key-here
```

Start backend:

```bash
uvicorn main:app --reload
```

## 3️⃣ Frontend Setup (2 minutes)

```bash
cd frontend
yarn install
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env
yarn dev
```

Frontend: http://localhost:3000

## 🎯 First Use

1. Open frontend  
2. Sign up  
3. Create project  
4. AI prompt example:

```
Create a simple landing page with header, hero section and footer
```

## 🧪 Testing

### Backend
```bash
curl http://localhost:8000/
```
Docs: http://localhost:8000/docs

### Frontend
Visit http://localhost:3000

## 🐛 Troubleshooting

### MongoDB
```bash
sudo systemctl status mongod
sudo journalctl -u mongod -n 50
```

### Backend
```bash
python3 --version
pip install -r requirements.txt
```

### Frontend
```bash
rm -rf node_modules .next
yarn install
```

## 🔧 Useful Commands

### Backend
```bash
uvicorn main:app --reload
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend
```bash
yarn dev
yarn build
yarn start
```

### MongoDB
```bash
mongosh
use stelgent_db
db.users.find().pretty()
```

## 🎉 You're Ready!

Support:  
GitHub Issues, README.md, support@stelgent.dev
