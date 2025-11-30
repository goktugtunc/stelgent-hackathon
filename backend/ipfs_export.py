# ipfs_export.py
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from datetime import datetime
import tempfile
import json
import shutil
import subprocess

import ipfshttpclient
from pydantic import BaseModel

from database import get_db
from auth import get_current_user

router = APIRouter(tags=["ipfs"])


# ================== Request Model ==================

class ExportRequest(BaseModel):
    stellar_address: str


# ================== ENV AYARLARI ==================

# IPFS
IPFS_API_URL = os.getenv("IPFS_API_URL", "/ip4/127.0.0.1/tcp/5001")
IPFS_GATEWAY_URL = os.getenv("IPFS_GATEWAY_URL", "https://ipfs.io/ipfs")

# Soroban / Stellar
SOROBAN_CONTRACT_ID = os.getenv("SOROBAN_CONTRACT_ID")
SOROBAN_NETWORK = os.getenv("SOROBAN_NETWORK", "testnet")
SOROBAN_SOURCE_IDENTITY = os.getenv("SOROBAN_SOURCE_IDENTITY", "deployer")
SOROBAN_RPC_URL = os.getenv("SOROBAN_RPC_URL")  # Şu an kullanmıyoruz ama dursun
SOROBAN_NETWORK_PASSPHRASE = os.getenv("SOROBAN_NETWORK_PASSPHRASE")

# Kontrattaki fonksiyon adı (mint)
SOROBAN_FUNCTION_MINT = "mint"

# Debug (istersen yorumlayabilirsin)
print("DEBUG SOROBAN_CONTRACT_ID:", SOROBAN_CONTRACT_ID)
print("DEBUG SOROBAN_NETWORK:", SOROBAN_NETWORK)
print("DEBUG SOROBAN_SOURCE_IDENTITY:", SOROBAN_SOURCE_IDENTITY)


# ================== SOROBAN HELPER ==================

def invoke_soroban_contract(function_name: str, args: list[str]) -> str:
    """
    soroban CLI ile contract invoke eden helper.
    args: fonksiyona gidecek CLI argümanları
          Örn: ["--to", "<G...>", "--project_id", "...", "--ipfs_cid", "..."]
    """
    if not SOROBAN_CONTRACT_ID:
        raise HTTPException(
            status_code=500,
            detail="SOROBAN_CONTRACT_ID env değişkeni tanımlı değil."
        )

    cmd = [
        "soroban",
        "contract",
        "invoke",
        "--id",
        SOROBAN_CONTRACT_ID,
        "--source-account",
        SOROBAN_SOURCE_IDENTITY,
        "--network",
        SOROBAN_NETWORK,
        "--",
        function_name,
    ] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Soroban çağrısı başarısız: {e}",
        )

    if result.returncode != 0:
        raise HTTPException(
            status_code=500,
            detail=f"Soroban hata: {result.stderr.strip() or result.stdout.strip()}",
        )

    return result.stdout.strip()


# ================== ENDPOINT: EXPORT + MINT ==================

@router.post("/projects/{project_id}/export-ipfs")
async def export_project_to_ipfs(
    project_id: str,
    payload: ExportRequest,  # Stellar adresi body'den geliyor
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Projeyi + dosyaları + konuşmayı tek bir JSON olarak IPFS'e yükler.
    Ardından Soroban ProjectNft kontratında `mint` çağırarak
    bu proje için bir NFT mint eder.

    NFT, isteği atan kullanıcının gönderdiği Stellar adresine mint edilir.
    Aynı projeden tekrar mint edilirse, DB'deki eski kayıt overwrite edilir:
    1 proje = 1 aktif NFT kaydı.
    """
    projects = db.projects
    files_col = db.files
    conv_col = db.conversations
    nft_mints = db.nft_mints

    # 1) Projeyi bul ve sahibini kontrol et
    project = projects.find_one({
        "_id": ObjectId(project_id),
        "user_id": current_user["userId"],
    })
    if not project:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    # 2) Dosyaları ve konuşmaları çek
    files = list(files_col.find({"project_id": project_id}))
    conversations = list(conv_col.find({"project_id": project_id}))

    # Mongo ObjectId ve datetime'leri serialize edilecek hale getir
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
        "owner_wallet": current_user.get("userId", "unknown"),
    }

    # 3) Kullanıcının Stellar adresini body'den al
    user_stellar_address = payload.stellar_address.strip()

    if not user_stellar_address:
        raise HTTPException(
            status_code=400,
            detail="Geçerli bir Stellar cüzdan adresi gönderilmedi.",
        )

    # 4) Geçici dosyaya yaz
    tmp_dir = tempfile.mkdtemp(prefix="stelgent_export_")
    tmp_path = os.path.join(tmp_dir, f"project_{project_id}.json")

    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, ensure_ascii=False, indent=2)

        # 5) IPFS'e yükle
        try:
            client = ipfshttpclient.connect(IPFS_API_URL)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"IPFS bağlantı hatası: {e}",
            )

        res = client.add(tmp_path)
        cid = res["Hash"]

        # 6) Soroban ProjectNft kontratında mint çağır
        #
        # Kontrat imzası:
        # pub fn mint(env: Env, to: Address, project_id: String, ipfs_cid: String) -> Result<u128, Error>
        #
        # CLI tarafında:
        #   --to <G...> --project_id "<project_id>" --ipfs_cid "<cid>"

        soroban_args = [
            "--to",
            user_stellar_address,
            "--project_id",
            str(project_id),
            "--ipfs_cid",
            cid,
        ]

        soroban_raw = invoke_soroban_contract(SOROBAN_FUNCTION_MINT, soroban_args)

        # CLI string döndürdüğü için olası çift tırnakları da temizleyelim
        minted_token_id = soroban_raw.strip().strip('"')

        # 7) Mint bilgisini DB'ye yaz (1 proje = 1 aktif NFT kaydı)
        now = datetime.utcnow()

        nft_mints.update_one(
            {"project_id": project_id},   # aynı proje için tek kayıt olsun
            {
                "$set": {
                    "project_id": project_id,
                    "user_id": current_user["userId"],
                    "stellar_address": user_stellar_address,
                    "token_id": minted_token_id,
                    "ipfs_cid": cid,
                    "contract_id": SOROBAN_CONTRACT_ID,
                    "updated_at": now,
                },
                "$setOnInsert": {
                    "created_at": now,
                },
            },
            upsert=True,
        )

        return {
            "message": "Project exported to IPFS and NFT minted on Soroban",
            "ipfs_cid": cid,
            "ipfs_url": f"{IPFS_GATEWAY_URL.rstrip('/')}/{cid}",
            "nft": {
                "contract_id": SOROBAN_CONTRACT_ID,
                "function": SOROBAN_FUNCTION_MINT,
                "to": user_stellar_address,
                "project_id": str(project_id),
                "token_id": minted_token_id,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"IPFS export failed: {e}",
        )
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ================== ENDPOINT: KULLANICININ MINT ETTİĞİ PROJELER ==================

@router.get("/nfts/my")
async def list_my_minted_projects(
    current_user: dict = Depends(get_current_user),
    db=Depends(get_db),
):
    """
    Giriş yapmış kullanıcının mint ettiği projeleri listeler.
    Her proje için maksimum 1 kayıt (son mint) döner.
    """
    nft_mints = db.nft_mints
    projects_col = db.projects

    user_id = current_user["userId"]

    mints = list(nft_mints.find({"user_id": user_id}))

    # İlgili projeleri tek seferde çek
    project_ids = [m["project_id"] for m in mints]
    if project_ids:
        proj_objs = list(
            projects_col.find(
                {"_id": {"$in": [ObjectId(pid) for pid in project_ids]}}
            )
        )
    else:
        proj_objs = []

    proj_map = {str(p["_id"]): p for p in proj_objs}

    result = []
    for m in mints:
        pid = m["project_id"]
        proj = proj_map.get(pid, {})

        title = (
            proj.get("title")
            or proj.get("name")
            or "Unnamed project"
        )
        description = proj.get("description") or proj.get("summary") or ""

        result.append(
            {
                "project_id": pid,
                "project_title": title,
                "project_description": description,
                "token_id": m.get("token_id"),
                "stellar_address": m.get("stellar_address"),
                "ipfs_cid": m.get("ipfs_cid"),
                "ipfs_url": f"{IPFS_GATEWAY_URL.rstrip('/')}/{m.get('ipfs_cid')}",
                "contract_id": m.get("contract_id"),
                "created_at": m.get("created_at"),
                "updated_at": m.get("updated_at"),
            }
        )

    # updated_at'e göre yeni -> eski sırala
    result.sort(
        key=lambda x: x.get("updated_at") or x.get("created_at") or datetime.min,
        reverse=True,
    )

    return result
