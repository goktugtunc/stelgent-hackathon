from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from bson import ObjectId
from datetime import datetime, timedelta
from openai import OpenAI
import logging
import re
import time
import random
import hashlib
from typing import Optional

import json
import docker
import tempfile
import shutil
import socket
import subprocess
import os
from stellar_sdk import Keypair, Server, TransactionBuilder, Asset, Account
from stellar_sdk.exceptions import SdkError
import base64
import secrets
import ipfshttpclient
from ipfs_export import router as ipfs_router
from stellar_nft import nft_minter

from config import settings
from database import connect_db, close_db, get_db
from auth import get_current_user
from models import (
    StellarWalletAuth, WalletConnectRequest,
    ProjectCreate, ProjectResponse,
    FileCreate, FileUpdate, FileResponse,
    ChatMessage, ChatResponse, ConversationResponse,
    OpenAISettings
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Docker client
docker_client = docker.from_env()

# Port management
used_ports = set()
MIN_PORT = 3001
MAX_PORT = 3100

# Session TTL (gün)
SESSION_TTL_DAYS = 7

# Initialize FastAPI
app = FastAPI(
    title="Stelgent API",
    description="AI-powered code generation platform backend",
    version="1.0.0"
)

# IPFS router
app.include_router(ipfs_router, prefix="/api")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tüm origin'lere izin ver
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Configure OpenAI client
openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)


def openai_chat_completion_with_retry(messages, model="gpt-4o", max_tokens=2000, temperature=0.3, max_retries=6):
    """Call OpenAI chat completions with exponential backoff and jitter on retryable errors."""
    for attempt in range(1, max_retries + 1):
        try:
            return openai_client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
        except Exception as e:
            status_code = getattr(e, 'http_status', None) or getattr(e, 'status_code', None)
            if status_code is not None and status_code not in (429, 503):
                raise
            if attempt >= max_retries:
                logger.error(f"OpenAI request failed after {attempt} attempts: {e}")
                raise
            backoff = min(30, 2 ** attempt)
            jitter = random.random()
            delay = backoff + jitter
            logger.warning(f"OpenAI request attempt {attempt} failed: {e}. Retrying in {delay:.1f}s")
            time.sleep(delay)


def get_cached_ai_response(db, cache_key: str) -> Optional[dict]:
    """Return cached response dict if exists and not stale."""
    cache = db.get_collection('ai_cache')
    doc = cache.find_one({"_id": cache_key})
    return doc


def set_cached_ai_response(db, cache_key: str, response_text: str, files: list, ttl_seconds: int = 3600):
    cache = db.get_collection('ai_cache')
    doc = {
        "_id": cache_key,
        "response": response_text,
        "files": files,
        "created_at": datetime.utcnow()
    }
    cache.update_one({"_id": cache_key}, {"$set": doc}, upsert=True)


def get_available_port():
    """Find an available port in the defined range."""
    for port in range(MIN_PORT, MAX_PORT + 1):
        if port not in used_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('0.0.0.0', port))
                sock.close()
                used_ports.add(port)
                return port
            except Exception:
                continue
    raise Exception("No available ports in range")


def fix_html_file_references(html_content, project_files):
    """Fix CSS and JS references in HTML files to use correct paths"""
    if not html_content or '<html' not in html_content.lower():
        return html_content
    
    # Get CSS and JS files from project
    css_files = [f for f in project_files if f.get('path', '').endswith('.css')]
    js_files = [f for f in project_files if f.get('path', '').endswith('.js')]
    
    # Add CSS links if not already present
    for css_file in css_files:
        css_path = css_file.get('path')
        link_tag = f'<link rel="stylesheet" href="{css_path}">'
        
        # Check if this CSS file is already linked
        if css_path not in html_content and f'href="{css_path}"' not in html_content:
            # Add CSS link before </head> or at the beginning of <head>
            if '</head>' in html_content:
                html_content = html_content.replace('</head>', f'    {link_tag}\n</head>')
            elif '<head>' in html_content:
                html_content = html_content.replace('<head>', f'<head>\n    {link_tag}')
            else:
                # If no head tag, add one
                if '<html>' in html_content:
                    html_content = html_content.replace('<html>', f'<html>\n<head>\n    {link_tag}\n</head>')
    
    # Add JS scripts if not already present  
    for js_file in js_files:
        js_path = js_file.get('path')
        script_tag = f'<script src="{js_path}"></script>'
        
        # Check if this JS file is already included
        if js_path not in html_content and f'src="{js_path}"' not in html_content:
            # Add JS script before </body> or at the end of <body>
            if '</body>' in html_content:
                html_content = html_content.replace('</body>', f'    {script_tag}\n</body>')
            elif '<body>' in html_content:
                html_content = html_content.replace('</body>', f'{script_tag}\n</body>')
            else:
                # If no body tag, add script at the end
                html_content += f'\n{script_tag}'
    
    return html_content


def create_dockerfile_content(project_files):
    """Create Dockerfile content based on project files."""
    has_nodejs = any(f.get('path') == 'package.json' for f in project_files)
    has_python = any(f.get('path', '').endswith('.py') for f in project_files)
    
    if has_nodejs:
        return """
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "start"]
""".strip()
    elif has_python:
        return """
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "app.py"]
""".strip()
    else:
        # Static HTML/CSS/JS site with proper Nginx config
        return """
FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Create directory and copy all files
RUN mkdir -p /usr/share/nginx/html
COPY . /usr/share/nginx/html/

# Set proper permissions for all files
RUN chmod -R 755 /usr/share/nginx/html
RUN find /usr/share/nginx/html -type f -name "*.html" -exec chmod 644 {} \;
RUN find /usr/share/nginx/html -type f -name "*.css" -exec chmod 644 {} \;
RUN find /usr/share/nginx/html -type f -name "*.js" -exec chmod 644 {} \;

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
""".strip()


def create_nginx_config():
    """Create Nginx configuration for static HTML sites."""
    return """
server {
    listen 80;
    server_name localhost;
    
    root /usr/share/nginx/html;
    index index.html index.htm;
    
    # MIME types for proper file serving
    location ~* \\.css$ {
        add_header Content-Type "text/css";
        add_header Cache-Control "max-age=31536000";
        add_header Access-Control-Allow-Origin "*";
        expires 1y;
    }
    
    location ~* \\.js$ {
        add_header Content-Type "application/javascript";
        add_header Cache-Control "max-age=31536000";
        add_header Access-Control-Allow-Origin "*";
        expires 1y;
    }
    
    # Other static assets
    location ~* \\.(png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        add_header Cache-Control "max-age=31536000";
        add_header Access-Control-Allow-Origin "*";
        expires 1y;
    }
    
    # Handle HTML files
    location ~* \\.html$ {
        add_header Cache-Control "no-cache, no-store, must-revalidate";
        add_header Pragma no-cache;
        add_header Expires 0;
        add_header Content-Type "text/html; charset=utf-8";
    }
    
    # Main location handler
    location / {
        try_files $uri $uri/ /index.html;
        
        # Add CORS headers for all requests
        add_header Access-Control-Allow-Origin "*";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range";
    }
    
    # Error handling
    error_page 404 /index.html;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
}
""".strip()


def create_docker_container(project_files, project_name):
    """Create and run a Docker container for the project."""
    try:
        host_port = get_available_port()
        temp_dir = tempfile.mkdtemp(prefix=f"stelgent_project_{project_name}_")
        
        # Write project files with proper directory structure
        for file in project_files:
            file_path = os.path.join(temp_dir, file.get('path', 'index.html'))
            file_dir = os.path.dirname(file_path)
            
            # Create directory structure if needed
            if file_dir and file_dir != temp_dir:
                os.makedirs(file_dir, exist_ok=True)
            
            # Write file content
            with open(file_path, 'w', encoding='utf-8') as f:
                content = file.get('content', '')
                f.write(content)
            
            # Set proper file permissions
            os.chmod(file_path, 0o644)
            
            logger.info(f"Created file: {file.get('path')} (size: {len(content)} chars)")
        
        # Fix HTML files to include proper CSS/JS references before deployment
        html_files = [f for f in project_files if f.get('path', '').endswith('.html')]
        for html_file in html_files:
            html_path = os.path.join(temp_dir, html_file.get('path', 'index.html'))
            if os.path.exists(html_path):
                with open(html_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
                
                fixed_content = fix_html_file_references(original_content, project_files)
                
                if fixed_content != original_content:
                    with open(html_path, 'w', encoding='utf-8') as f:
                        f.write(fixed_content)
                    logger.info(f"Fixed HTML references for deployment: {html_file.get('path')}")
        
        dockerfile_content = create_dockerfile_content(project_files)
        
        dockerfile_path = os.path.join(temp_dir, 'Dockerfile')
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        has_nodejs = any(f.get('path') == 'package.json' for f in project_files)
        has_python = any(f.get('path', '').endswith('.py') for f in project_files)
        
        if not has_nodejs and not has_python:
            nginx_config_path = os.path.join(temp_dir, 'nginx.conf')
            with open(nginx_config_path, 'w') as f:
                f.write(create_nginx_config())
        
        if not has_nodejs and not has_python:
            index_exists = any(f.get('path') == 'index.html' for f in project_files)
            if not index_exists:
                default_html = """<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Stelgent Site</title>
</head>
<body>
    <h1>Hoş Geldiniz!</h1>
    <p>Siteniz başarıyla deploy edildi.</p>
</body>
</html>"""
                with open(os.path.join(temp_dir, 'index.html'), 'w', encoding='utf-8') as f:
                    f.write(default_html)
        
        image_name = f"stelgent-project-{project_name.lower()}-{int(time.time())}"
        docker_client.images.build(
            path=temp_dir,
            tag=image_name,
            rm=True
        )
        
        container_port = 80 if 'nginx' in dockerfile_content else (3000 if 'node' in dockerfile_content else 8000)
        container = docker_client.containers.run(
            image_name,
            ports={container_port: host_port},
            detach=True,
            name=f"stelgent-{project_name.lower()}-{int(time.time())}"
        )
        
        shutil.rmtree(temp_dir)
        
        return {
            "container_id": container.id,
            "port": host_port,
            "url": f"http://localhost:{host_port}",
            "status": "running"
        }
        
    except Exception as e:
        logger.error(f"Failed to create Docker container: {e}")
        if 'temp_dir' in locals() and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        raise HTTPException(status_code=500, detail=f"Container creation failed: {str(e)}")


def stop_docker_container(container_id):
    """Stop and remove a Docker container."""
    try:
        container = docker_client.containers.get(container_id)
        container.stop()
        container.remove()
        
        if hasattr(container, 'ports') and container.ports:
            for port_info in container.ports.values():
                if port_info:
                    host_port = int(port_info[0]['HostPort'])
                    used_ports.discard(host_port)
        
        return {"status": "stopped"}
    except Exception as e:
        logger.error(f"Failed to stop container: {e}")
        raise HTTPException(status_code=500, detail=f"Container stop failed: {str(e)}")


def need_clarification(message: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Heuristic that returns whether clarification is needed, a single targeted question,
    and the field being asked (e.g. 'pages', 'theme', 'platform', 'features')."""
    if not message or not message.strip():
        return True, "Ne yapmak istediğinizi kısaca anlatır mısınız? Hangi sayfalar/özellikler olsun?", "general"

    m = message.lower()

    pages_keywords = [
        'index', 'home', 'hero', 'navbar', 'menu', 'page', 'pages', 'about', 'contact', 'profile',
        'shop', 'store', 'gallery', 'blog', 'dashboard', 'ana sayfa', 'anasayfa', 'oyun listesi', 'profil', 'mağaza', 'puan', 'puan tablosu'
    ]
    theme_keywords = ['dark', 'light', 'retro', 'neon', 'minimal', 'modern', 'classic', 'material', 'flat', 'vintage']
    auth_keywords = ['login', 'signup', 'register', 'account', 'auth', 'profile', 'giriş', 'giris', 'kayıt', 'kayit', 'üye', 'uye']
    multiplayer_keywords = ['multiplayer', 'co-op', 'online', 'server', 'lobby', 'çok oyunculu', 'cok oyunculu']
    platform_keywords = ['mobile', 'android', 'ios', 'browser', 'web', 'desktop', 'tarayıcı', 'tarayici', 'mobil', 'masaüstü', 'masaustu']
    feature_keywords = ['leaderboard', 'levels', 'score', 'store', 'shop', 'achievements', 'forum', 'chat', 'payment', 'subscription', 'puan', 'sıralama', 'siralama', 'puan tablosu', 'liderboard', 'liderbord']

    found_pages = any(k in m for k in pages_keywords)
    found_theme = any(k in m for k in theme_keywords)
    found_auth = any(k in m for k in auth_keywords)
    found_multiplayer = any(k in m for k in multiplayer_keywords)
    found_platform = any(k in m for k in platform_keywords)
    found_feature = any(k in m for k in feature_keywords)

    if len(m.strip()) < 80 and not found_pages:
        q = "Hangi sayfaları istiyorsunuz? Ör: ana sayfa, oyun listesi, profil, mağaza, puan tablosu."
        return True, q, 'pages'

    if not found_theme:
        q = "Bir tema/estetik tercihiniz var mı? (örn. modern, neon, retro, minimal)"
        return True, q, 'theme'

    if not found_platform:
        q = "Hedef platform ne olacak? (örn. tarayıcı/web, mobil (Android/iOS), veya masaüstü)"
        return True, q, 'platform'

    if not (found_auth or found_multiplayer or found_feature):
        q = "Özel özellikler ister misiniz? (örn. giriş/üye, puan tablosu, çok oyunculu, mağaza)"
        return True, q, 'features'

    return False, None, None


def classify_clarification(message: str) -> tuple[bool, Optional[str], Optional[str]]:
    """Use OpenAI to classify whether clarification is needed and return (needs, question, field)."""
    try:
        prompt = (
            "You will receive a user request to create a website.\n"
            "Return a JSON object with keys: needs_clarify (true/false), missing_field (one of pages, theme, platform, features, general or null), question (a single short question to ask the user, or null).\n"
            "Example output: {\"needs_clarify\": true, \"missing_field\": \"pages\", \"question\": \"Which pages do you want?\"}\n\n"
            "User request:\n" + message + "\n\nRespond ONLY with the JSON object."
        )

        resp = openai_chat_completion_with_retry(
            messages=[{"role": "system", "content": "You are a concise classifier."}, {"role": "user", "content": prompt}],
            model="gpt-4o",
            max_tokens=300,
            temperature=0.0,
            max_retries=3
        )

        text = resp.choices[0].message.content.strip()
        try:
            start = text.find('{')
            end = text.rfind('}')
            if start != -1 and end != -1:
                json_text = text[start:end+1]
            else:
                json_text = text
            obj = json.loads(json_text)
            needs = bool(obj.get('needs_clarify'))
            field = obj.get('missing_field')
            question = obj.get('question')
            return needs, question, field
        except Exception:
            logger.warning('Could not parse classification JSON, falling back to heuristic')
            return need_clarification(message)
    except Exception as e:
        logger.warning(f'Classification call failed: {e}. Falling back to heuristic')
        return need_clarification(message)


def get_last_assistant_clarify(conversations, project_id: str):
    """Return the latest assistant message that has meta.clarify_field, or None."""
    doc = conversations.find_one(
        {"project_id": project_id, "role": "assistant", "meta.clarify_field": {"$exists": True}},
        sort=[("created_at", -1)]
    )
    return doc


@app.on_event("startup")
async def startup_event():
    connect_db()
    logger.info("Stelgent API started successfully")


@app.on_event("shutdown")
async def shutdown_event():
    close_db()
    logger.info("Stelgent API shutdown")


@app.get("/")
async def root():
    return {"status": "ok", "message": "Stelgent API is running"}


@app.get("/health")
async def health_check():
    try:
        db = get_db()
        db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "unhealthy", "error": str(e)}
        )

# ==================== AUTH ENDPOINTS ====================

@app.get("/api/auth/me", response_model=dict)
async def get_me(current_user: dict = Depends(get_current_user)):
    """Get current user info (wallet-session üzerinden)."""
    try:
        db = get_db()
        users = db.users
        
        user = users.find_one({"_id": ObjectId(current_user["userId"])})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user": {
                "id": str(user["_id"]),
                "stellar_public_key": user.get("stellar_public_key"),
                "openai_api_key": user.get("openai_api_key")
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get user error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ==================== STELLAR WALLET AUTH ENDPOINTS ====================

@app.post("/api/auth/wallet/connect", response_model=dict)
def wallet_connect(payload: WalletConnectRequest, db = Depends(get_db)):
    """
    Freighter'dan gelen public_key ile login olur.
    Kullanıcıyı bulur; yoksa oluşturur.
    Token olarak doğrudan public key döner.
    """
    users = db.users

    # 1) Kullanıcı var mı?
    user = users.find_one({"stellar_public_key": payload.public_key})

    # 2) Yoksa oluştur
    if not user:
        now = datetime.utcnow()
        res = users.insert_one({
            "stellar_public_key": payload.public_key,
            "created_at": now,
            "openai_api_key": None,
        })
        user = users.find_one({"_id": res.inserted_id})

    # 3) Frontend'e dönecek user objesi
    user_payload = {
        "id": str(user["_id"]),
        "stellar_public_key": user["stellar_public_key"],
        "openai_api_key": user.get("openai_api_key"),
    }

    # “token” artık direkt public key.
    return {
        "token": payload.public_key,
        "user": user_payload,
    }


@app.post("/api/auth/wallet/verify", response_model=dict)
async def verify_wallet_signature(auth_data: StellarWalletAuth):
    """
    İleride imza doğrulama akışı için placeholder endpoint.
    Şu anda yalnızca public key formatını doğrular.
    """
    try:
        try:
            Keypair.from_public_key(auth_data.public_key)
        except (SdkError, Exception):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Stellar public key"
            )
        
        return {
            "message": "Public key format is valid (signature verification not implemented).",
            "public_key": auth_data.public_key
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Wallet verify error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ==================== PROJECT ENDPOINTS ====================

@app.post("/api/projects", response_model=dict)
async def create_project(
    project_data: ProjectCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new project"""
    try:
        db = get_db()
        projects = db.projects
        
        now = datetime.utcnow()
        result = projects.insert_one({
            "user_id": current_user["userId"],
            "name": project_data.name,
            "created_at": now
        })
        
        return {
            "message": "Project created successfully",
            "project": {
                "id": str(result.inserted_id),
                "name": project_data.name,
                "created_at": now
            }
        }
    except Exception as e:
        logger.error(f"Create project error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/api/projects")
async def get_projects(current_user: dict = Depends(get_current_user)):
    """Get all user projects"""
    try:
        db = get_db()
        projects = db.projects
        
        user_projects = list(projects.find(
            {"user_id": current_user["userId"]}
        ).sort("created_at", -1))
        
        return {
            "projects": [
                {
                    "id": str(p["_id"]),
                    "name": p["name"],
                    "created_at": p["created_at"]
                }
                for p in user_projects
            ]
        }
    except Exception as e:
        logger.error(f"Get projects error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.get("/api/projects/{project_id}")
async def get_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single project"""
    try:
        db = get_db()
        projects = db.projects
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        return {
            "project": {
                "id": str(project["_id"]),
                "name": project["name"],
                "created_at": project["created_at"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get project error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.delete("/api/projects/{project_id}")
async def delete_project(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete project and all associated files and conversations"""
    try:
        db = get_db()
        projects = db.projects
        files = db.files
        conversations = db.conversations
        
        result = projects.delete_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        files.delete_many({"project_id": project_id})
        conversations.delete_many({"project_id": project_id})
        
        return {"message": "Project deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete project error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ==================== FILE ENDPOINTS ====================

@app.get("/api/projects/{project_id}/files")
async def get_files(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all files in a project"""
    try:
        db = get_db()
        projects = db.projects
        files = db.files
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project_files = list(files.find({"project_id": project_id}))
        
        return {
            "files": [
                {
                    "id": str(f["_id"]),
                    "path": f["path"],
                    "content": f["content"],
                    "type": f["type"],
                    "created_at": f["created_at"]
                }
                for f in project_files
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get files error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/api/projects/{project_id}/files")
async def create_file(
    project_id: str,
    file_data: FileCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new file"""
    try:
        db = get_db()
        projects = db.projects
        files = db.files
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        existing_file = files.find_one({
            "project_id": project_id,
            "path": file_data.path
        })
        
        if existing_file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File already exists"
            )
        
        now = datetime.utcnow()
        result = files.insert_one({
            "project_id": project_id,
            "path": file_data.path,
            "content": file_data.content,
            "type": file_data.type,
            "created_at": now
        })
        
        return {
            "message": "File created successfully",
            "file": {
                "id": str(result.inserted_id),
                "path": file_data.path,
                "content": file_data.content,
                "type": file_data.type,
                "created_at": now
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create file error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.put("/api/projects/{project_id}/files/{file_id}")
async def update_file(
    project_id: str,
    file_id: str,
    file_data: FileUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update file content or path"""
    try:
        db = get_db()
        projects = db.projects
        files = db.files
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        update_data = {}
        if file_data.content is not None:
            update_data["content"] = file_data.content
        if file_data.path is not None:
            update_data["path"] = file_data.path
        
        result = files.update_one(
            {"_id": ObjectId(file_id), "project_id": project_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return {"message": "File updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update file error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.delete("/api/projects/{project_id}/files/{file_id}")
async def delete_file(
    project_id: str,
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a file"""
    try:
        db = get_db()
        projects = db.projects
        files = db.files
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        result = files.delete_one({
            "_id": ObjectId(file_id),
            "project_id": project_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found"
            )
        
        return {"message": "File deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete file error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

# ==================== CONVERSATION ENDPOINTS ====================

@app.get("/api/projects/{project_id}/conversations")
async def get_conversations(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get conversation history for a project"""
    try:
        db = get_db()
        projects = db.projects
        conversations = db.conversations
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        messages = list(conversations.find(
            {"project_id": project_id}
        ).sort("created_at", 1))
        
        return {
            "conversations": [
                {
                    "id": str(m["_id"]),
                    "role": m["role"],
                    "content": m["content"],
                    "created_at": m["created_at"]
                }
                for m in messages
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@app.post("/api/projects/{project_id}/chat")
async def chat(
    project_id: str,
    message_data: ChatMessage,
    current_user: dict = Depends(get_current_user)
):
    """Send chat message and generate code with OpenAI"""
    try:
        db = get_db()
        projects = db.projects
        conversations = db.conversations
        files = db.files
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        MAX_HISTORY_MESSAGES = 12
        conversation_history = list(conversations.find(
            {"project_id": project_id}
        ).sort("created_at", 1))
        if len(conversation_history) > MAX_HISTORY_MESSAGES:
            conversation_history = conversation_history[-MAX_HISTORY_MESSAGES:]
        
        conversations.insert_one({
            "project_id": project_id,
            "role": "user",
            "content": message_data.message,
            "created_at": datetime.utcnow()
        })

        last_clarify = get_last_assistant_clarify(conversations, project_id)

        user_msgs = list(conversations.find({"project_id": project_id, "role": "user"}).sort("created_at", 1))
        combined_user_text = "\n".join([m["content"] for m in user_msgs]) if user_msgs else message_data.message

        needs_clarify, clarify_q, clarify_field = need_clarification(combined_user_text)
        if needs_clarify:
            try:
                cls_needs, cls_q, cls_field = classify_clarification(combined_user_text)
                if cls_needs is not None:
                    needs_clarify, clarify_q, clarify_field = cls_needs, cls_q, cls_field
            except Exception:
                pass

        if needs_clarify:
            if last_clarify and last_clarify.get('meta', {}).get('clarify_field') == clarify_field:
                last_user_after = conversations.find_one({
                    "project_id": project_id,
                    "role": "user",
                    "created_at": {"$gt": last_clarify["created_at"]}
                }, sort=[("created_at", -1)])
                if last_user_after:
                    user_msgs = list(conversations.find({"project_id": project_id, "role": "user"}).sort("created_at", 1))
                    combined_user_text = "\n".join([m["content"] for m in user_msgs])
                    needs_clarify, clarify_q, clarify_field = need_clarification(combined_user_text)
                    if needs_clarify:
                        cls_needs, cls_q, cls_field = classify_clarification(combined_user_text)
                        if cls_needs is not None:
                            needs_clarify, clarify_q, clarify_field = cls_needs, cls_q, cls_field
            if needs_clarify:
                conversations.insert_one({
                    "project_id": project_id,
                    "role": "assistant",
                    "content": clarify_q,
                    "meta": {"clarify_field": clarify_field},
                    "created_at": datetime.utcnow()
                })

                return {
                    "message": "clarification_requested",
                    "question": clarify_q,
                    "field": clarify_field
                }
        
        MAX_FILE_SNIPPET = 800
        existing_files = list(files.find({"project_id": project_id}))
        file_context_parts = []
        for f in existing_files:
            content = f.get('content', '') or ''
            snippet = content if len(content) <= MAX_FILE_SNIPPET else content[:MAX_FILE_SNIPPET] + "\n...TRUNCATED..."
            file_context_parts.append(f"{f['path']}:\n{snippet}")
        file_context = "\n\n".join(file_context_parts)
        
        conversation_text = "\n\n".join([
            f"{'User' if msg['role'] == 'user' else 'Assistant'}: {msg['content']}"
            for msg in conversation_history
        ])
        
        system_prompt = f"""You are an expert full-stack developer helping to build a project.

IMPORTANT: Always respond with files in this EXACT format:

=== FILES ===
[FILE: index.html]
<!DOCTYPE html>
<html>
<head>
    <title>My Site</title>
</head>
<body>
    <h1>Hello World</h1>
</body>
</html>
[/FILE]

[FILE: styles.css]
body {{
    margin: 0;
    font-family: Arial;
}}
h1 {{
    color: blue;
}}
[/FILE]

=== EXPLANATION ===
Created basic HTML structure with CSS styling.

Rules:
1. Use [FILE: path] and [/FILE] tags for each file
2. For folders, use trailing slash: [FILE: src/]
3. If updating existing files, use the EXACT SAME path
4. Always include actual file content between tags
5. Build upon what was already created

Current files in project:
{file_context or 'No files yet'}

Previous conversation:
{conversation_text or 'This is the first message'}"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current User Request: {message_data.message}"}
        ]

        cache_key_src = system_prompt + "|" + message_data.message + "|" + project_id
        cache_key = hashlib.sha256(cache_key_src.encode('utf-8')).hexdigest()

        cached = get_cached_ai_response(db, cache_key)
        if cached:
            logger.info(f"Using cached AI response for project {project_id}")
            generated_text = cached['response']
        else:
            resp = openai_chat_completion_with_retry(
                messages=messages,
                model="gpt-4o",
                max_tokens=2000,
                temperature=0.3,
                max_retries=6
            )
            generated_text = resp.choices[0].message.content
            logger.info(f"OpenAI response length: {len(generated_text)}")
            logger.debug(f"OpenAI response: {generated_text[:500]}...")
        
        file_regex = r'\[FILE:\s*([^\]]+)\]([\s\S]*?)\[/FILE\]'
        matches = re.findall(file_regex, generated_text)
        
        new_files = []
        
        for path, content in matches:
            path = path.strip()
            content = content.strip()
            
            if not content and not path.endswith("/"):
                logger.warning(f"Skipping file {path} - no content")
                continue
                
            existing_file = files.find_one({
                "project_id": project_id,
                "path": path
            })
            
            if existing_file:
                files.update_one(
                    {"_id": existing_file["_id"]},
                    {"$set": {"content": content}}
                )
                logger.info(f"Updated file: {path}")
            else:
                file_type = "folder" if path.endswith("/") else "file"
                result = files.insert_one({
                    "project_id": project_id,
                    "path": path,
                    "content": content if file_type == "file" else "",
                    "type": file_type,
                    "created_at": datetime.utcnow()
                })
                logger.info(f"Created file: {path} with content length: {len(content)}")
                
                new_files.append({
                    "id": str(result.inserted_id),
                    "path": path,
                    "content": content if file_type == "file" else "",
                    "type": file_type
                })
        
        # Post-process HTML files to add missing CSS/JS references
        all_project_files = list(files.find({"project_id": project_id, "type": "file"}))
        html_files = [f for f in all_project_files if f.get('path', '').endswith('.html')]
        
        for html_file in html_files:
            original_content = html_file.get('content', '')
            fixed_content = fix_html_file_references(original_content, all_project_files)
            
            if fixed_content != original_content:
                files.update_one(
                    {"_id": html_file["_id"]},
                    {"$set": {"content": fixed_content}}
                )
                logger.info(f"Fixed HTML references in: {html_file.get('path')}")
        
        try:
            if not cached:
                set_cached_ai_response(db, cache_key, generated_text, new_files)
        except Exception:
            logger.warning("Could not set AI cache (non-fatal)")
        
        explanation_match = re.search(r'===\s*EXPLANATION\s*===([\s\S]*?)$', generated_text, re.IGNORECASE)
        explanation = explanation_match.group(1).strip() if explanation_match else generated_text
        
        conversations.insert_one({
            "project_id": project_id,
            "role": "assistant",
            "content": explanation,
            "created_at": datetime.utcnow()
        })
        
        return {
            "message": "Chat response generated",
            "response": explanation,
            "files": new_files
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

# ==================== DOCKER CONTAINER ENDPOINTS ====================

@app.post("/api/projects/{project_id}/deploy")
async def deploy_project_container(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deploy project files as a Docker container"""
    try:
        db = get_db()
        projects = db.projects
        files = db.files
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        project_files = list(files.find({"project_id": project_id, "type": "file"}))
        
        if not project_files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No files found in project"
            )
        
        container_info = create_docker_container(project_files, project["name"])
        
        projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$set": {
                    "container_id": container_info["container_id"],
                    "container_port": container_info["port"],
                    "container_url": container_info["url"],
                    "deployed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "message": "Project deployed successfully",
            "container_url": container_info["url"],
            "port": container_info["port"],
            "container_id": container_info["container_id"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Deploy project error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deployment failed: {str(e)}"
        )

@app.delete("/api/projects/{project_id}/deploy")
async def stop_project_container(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Stop and remove project's Docker container"""
    try:
        db = get_db()
        projects = db.projects
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        container_id = project.get("container_id")
        if not container_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Project is not deployed"
            )
        
        stop_docker_container(container_id)
        
        projects.update_one(
            {"_id": ObjectId(project_id)},
            {
                "$unset": {
                    "container_id": "",
                    "container_port": "",
                    "container_url": "",
                    "deployed_at": ""
                }
            }
        )
        
        return {"message": "Container stopped successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Stop container error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Container stop failed: {str(e)}"
        )

@app.get("/api/projects/{project_id}/container-status")
async def get_container_status(
    project_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current container status for project"""
    try:
        db = get_db()
        projects = db.projects
        
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": current_user["userId"]
        })
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        container_id = project.get("container_id")
        if not container_id:
            return {
                "deployed": False,
                "status": "not_deployed"
            }
        
        try:
            container = docker_client.containers.get(container_id)
            return {
                "deployed": True,
                "status": container.status,
                "url": project.get("container_url"),
                "port": project.get("container_port")
            }
        except docker.errors.NotFound:
            projects.update_one(
                {"_id": ObjectId(project_id)},
                {
                    "$unset": {
                        "container_id": "",
                        "container_port": "",
                        "container_url": "",
                        "deployed_at": ""
                    }
                }
            )
            return {
                "deployed": False,
                "status": "container_not_found"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get container status error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


# ==================== IPFS AND MINT FUNCTIONS ====================

def export_project_to_ipfs(project_id: str, owner_pk: str):
    """
    Projeyi IPFS'e export eder ve CID döner
    """
    try:
        db = get_db()
        projects = db.projects
        files_col = db.files
        conv_col = db.conversations

        # 1) Projeyi bul
        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": owner_pk,
        })
        if not project:
            raise Exception("Project not found")

        # 2) Dosyaları ve konuşmaları çek
        files = list(files_col.find({"project_id": project_id}))
        conversations = list(conv_col.find({"project_id": project_id}))

        # Mongo ObjectId ve datetime'leri serialize et
        def normalize(doc):
            out = {}
            for k, v in doc.items():
                if k == "_id":
                    out["id"] = str(v)
                elif isinstance(v, ObjectId):
                    out[k] = str(v)
                elif isinstance(v, datetime):
                    out[k] = v.isoformat()
                else:
                    out[k] = v
            return out

        bundle = {
            "project": normalize(project),
            "files": [normalize(f) for f in files],
            "conversations": [normalize(c) for c in conversations],
            "exported_at": datetime.utcnow().isoformat(),
            "owner_wallet": owner_pk,
        }

        # 3) Geçici dosyaya yaz
        tmp_dir = tempfile.mkdtemp(prefix="stelgent_export_")
        tmp_path = os.path.join(tmp_dir, f"project_{project_id}.json")
        
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(bundle, f, ensure_ascii=False, indent=2)

            # 4) IPFS'e yükle
            client = ipfshttpclient.connect("/ip4/127.0.0.1/tcp/5001")
            res = client.add(tmp_path)
            cid = res["Hash"]

            return {
                "cid": cid,
                "ipfs_url": f"https://ipfs.io/ipfs/{cid}",
            }
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)
            
    except Exception as e:
        logger.error(f"IPFS export error: {e}")
        raise Exception(f"IPFS export failed: {e}")


def export_and_mint_project(project_id: str, owner_pk: str):
    """
    1) Projeyi IPFS'e export eder
    2) Stellar blockchain'de NFT mint eder
    """
    try:
        # 1) IPFS'e export
        export_result = export_project_to_ipfs(project_id, owner_pk)
        cid = export_result["cid"]
        
        # 2) Stellar NFT mint etme
        # TODO: Production'da issuer secret key güvenli şekilde saklanmalı
        # Şimdilik test amaçlı random keypair kullanıyoruz
        issuer_keypair = Keypair.random()
        issuer_secret = issuer_keypair.secret
        
        # NFT mint et
        mint_result = nft_minter.create_project_nft(
            project_id=project_id,
            ipfs_cid=cid,
            owner_public_key=owner_pk,
            issuer_secret_key=issuer_secret
        )
        
        if mint_result["success"]:
            logger.info(f"NFT minted successfully for project {project_id}")
            return {
                "cid": cid,
                "tx_hash": mint_result["tx_hash"],
                "asset_code": mint_result["asset_code"],
                "issuer": mint_result["issuer"],
                "ipfs_url": export_result["ipfs_url"],
                "status": "minted_successfully"
            }
        else:
            # NFT mint başarısız ama IPFS export başarılı
            logger.warning(f"NFT mint failed for project {project_id}: {mint_result['error']}")
            return {
                "cid": cid,
                "ipfs_url": export_result["ipfs_url"],
                "status": "ipfs_exported_mint_failed",
                "mint_error": mint_result["error"]
            }
        
    except Exception as e:
        logger.error(f"Export and mint error: {e}")
        raise Exception(f"Export and mint failed: {e}")


@app.post("/api/projects/{project_id}/export", response_model=dict)
async def api_export_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    Projeyi IPFS'e export eder ve CID döner.
    current_user içinden owner_public_key'i alıyoruz.
    """
    try:
        db = get_db()
        projects = db.projects

        # current_user formatın neyse ona göre oku:
        owner_pk = (
            current_user.get("wallet_public_key")
            or current_user.get("userId")
        )
        if not owner_pk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing wallet public key",
            )

        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": owner_pk,
        })
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        result = export_project_to_ipfs(project_id, owner_pk)
        return {
            "message": "Project exported to IPFS",
            "cid": result["cid"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export project error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export failed",
        )


@app.post("/api/projects/{project_id}/export-and-mint", response_model=dict)
async def api_export_and_mint_project(
    project_id: str,
    current_user: dict = Depends(get_current_user),
):
    """
    1) Projeyi IPFS'e export eder (chat + dosyalar tek JSON).
    2) Kullanıcıya lisans asset'i mint eder.
    """
    try:
        db = get_db()
        projects = db.projects

        owner_pk = (
            current_user.get("wallet_public_key")
            or current_user.get("userId")
        )
        if not owner_pk:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing wallet public key",
            )

        project = projects.find_one({
            "_id": ObjectId(project_id),
            "user_id": owner_pk,
        })
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        result = export_and_mint_project(project_id, owner_pk)

        return {
            "message": "Project exported and license minted",
            "cid": result["cid"],
            "tx_hash": result["tx_hash"],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Export and mint error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Export and mint failed",
        )


# ==================== SETTINGS ENDPOINTS ====================

@app.put("/api/settings/openai")
async def update_openai_settings(
    settings_data: OpenAISettings,
    current_user: dict = Depends(get_current_user)
):
    """Update OpenAI API key"""
    try:
        db = get_db()
        users = db.users
        
        users.update_one(
            {"_id": ObjectId(current_user["userId"])},
            {"$set": {"openai_api_key": settings_data.openai_api_key}}
        )
        
        return {"message": "OpenAI API key updated successfully"}
    except Exception as e:
        logger.error(f"Update OpenAI settings error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
