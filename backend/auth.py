# auth.py
from datetime import datetime
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from bson import ObjectId
from stellar_sdk import Keypair, exceptions as stellar_exceptions

from database import get_db


def _extract_public_key(
    x_public_key: Optional[str] = Header(default=None, alias="X-Public-Key"),
    authorization: Optional[str] = Header(default=None, alias="Authorization"),
) -> str:
    """
    İstekten cüzdan public key'ini çıkarır.

    Kabul edilen formatlar:
    1) X-Public-Key: G.... (header)
    2) Authorization: Bearer G....  (header)
    """
    if x_public_key:
        return x_public_key.strip()

    if authorization:
        parts = authorization.split()
        if len(parts) == 2:
            # "Bearer G...." veya "Token G...." fark etmiyor, ikinci parçayı alıyoruz.
            return parts[1].strip()

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Missing wallet public key",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
    public_key: str = Depends(_extract_public_key),
    db=Depends(get_db),
):
    """
    Header'daki token'ı doğrudan Stellar public key olarak kabul eder,
    bu key'e ait kullanıcıyı bulur ve {"userId": "...", "stellar_public_key": "..."} döner.
    """

    # 1) Public key formatı gerçekten Stellar key mi?
    try:
        Keypair.from_public_key(public_key)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Stellar public key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2) Kullanıcıyı bul
    user = db.users.find_one({"stellar_public_key": public_key})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found for this wallet",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # main.py'de current_user["userId"] şeklinde kullanıyorsun
    return {
        "userId": str(user["_id"]),
        "stellar_public_key": public_key,
    }
