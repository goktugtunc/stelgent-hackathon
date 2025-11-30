# stellar_nft.py
"""
Stellar blockchain NFT mint işlemleri için ayrı modül
"""

from stellar_sdk import Server, Keypair, TransactionBuilder, Asset, Account
from stellar_sdk.exceptions import SdkError
import logging

logger = logging.getLogger(__name__)

class StellarNFTMinter:
    def __init__(self, network="testnet"):
        if network == "testnet":
            self.server = Server("https://horizon-testnet.stellar.org")
            self.network_passphrase = "Test SDF Network ; September 2015"
        else:
            self.server = Server("https://horizon.stellar.org")
            self.network_passphrase = "Public Global Stellar Network ; September 2015"
    
    def create_project_nft(self, project_id: str, ipfs_cid: str, owner_public_key: str, issuer_secret_key: str):
        """
        Stellar blockchain'de proje NFT'si oluşturur
        """
        try:
            # Issuer keypair
            issuer_keypair = Keypair.from_secret(issuer_secret_key)
            
            # Asset kodu oluştur (max 12 karakter)
            asset_code = f"STEL{project_id[:8]}"
            
            # NFT asset oluştur
            nft_asset = Asset(asset_code, issuer_keypair.public_key)
            
            # Issuer account'ını yükle
            issuer_account = self.server.load_account(issuer_keypair.public_key)
            
            # Transaction oluştur
            transaction = (
                TransactionBuilder(
                    source_account=issuer_account,
                    network_passphrase=self.network_passphrase,
                    base_fee=100,
                )
                # Owner'a trust line oluşturmasını söyle
                .append_change_trust_op(
                    asset=nft_asset,
                    source=owner_public_key
                )
                # NFT'yi owner'a gönder (1 adet - unique)
                .append_payment_op(
                    destination=owner_public_key,
                    asset=nft_asset,
                    amount="1.0000000",
                    source=issuer_keypair.public_key
                )
                # Asset'i lock et (daha fazla mint edilemesin)
                .append_set_options_op(
                    master_weight=0,  # Master key'i deaktive et
                    source=issuer_keypair.public_key
                )
                .set_timeout(30)
                .build()
            )
            
            # IPFS metadata'sını memo olarak ekle
            transaction.add_text_memo(f"IPFS:{ipfs_cid}")
            
            # İmzala
            transaction.sign(issuer_keypair)
            
            # Blockchain'e gönder
            response = self.server.submit_transaction(transaction)
            
            return {
                "success": True,
                "tx_hash": response["hash"],
                "asset_code": asset_code,
                "issuer": issuer_keypair.public_key,
                "owner": owner_public_key,
                "ipfs_cid": ipfs_cid,
                "ledger": response.get("ledger")
            }
            
        except SdkError as e:
            logger.error(f"Stellar SDK error: {e}")
            return {
                "success": False,
                "error": f"Stellar error: {e}"
            }
        except Exception as e:
            logger.error(f"NFT mint error: {e}")
            return {
                "success": False,
                "error": f"Mint failed: {e}"
            }
    
    def get_nft_info(self, asset_code: str, issuer_public_key: str):
        """
        NFT bilgilerini getir
        """
        try:
            asset = Asset(asset_code, issuer_public_key)
            asset_info = self.server.assets().for_code(asset_code).for_issuer(issuer_public_key).call()
            
            return {
                "success": True,
                "asset_info": asset_info
            }
        except Exception as e:
            logger.error(f"Get NFT info error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global minter instance
nft_minter = StellarNFTMinter()