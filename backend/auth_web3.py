# auth_web3.py

from fastapi import Header, HTTPException, status

async def get_current_wallet_pub(
    wallet_public_key: str = Header(None, alias="X-Wallet-Public-Key")
):
    """
    Frontend her request'e 'X-Wallet-Public-Key' header'ı göndermeli.
    Bu fonksiyon public key'i doğrular (şimdilik sadece varlığını kontrol ediyor).
    """
    if not wallet_public_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing wallet public key"
        )
    
    return wallet_public_key
