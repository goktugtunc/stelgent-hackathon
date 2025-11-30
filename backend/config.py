from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    # MongoDB
    MONGO_URL: str
    DB_NAME: str = "stelgent_db"

    # OpenAI (ChatGPT) API
    OPENAI_API_KEY: str

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8005
    DEBUG: bool = False

    # CORS
    FRONTEND_URL: str = "http://hackstack.com.tr:3011"
    CORS_ORIGINS: str = "http://localhost:3011,http://localhost:3000,http://hackstack.com.tr:3011,https://hackstack.com.tr:3011,*"

    # IPFS
    IPFS_API_URL: str | None = None          # ör: "http://127.0.0.1:5001"
    IPFS_GATEWAY_URL: str | None = None      # ör: "https://ipfs.io/ipfs"

    # Stellar / Lisans Asset
    STELLAR_ISSUER_PUBLIC_KEY: str | None = None
    STELLAR_ISSUER_SECRET_KEY: str | None = None
    STELLAR_ASSET_CODE: str | None = None
    STELLAR_HORIZON_URL: str = "https://horizon-testnet.stellar.org"
    STELLAR_NETWORK_PASSPHRASE: str = "Test SDF Network ; September 2015"

    # Soroban Smart Contracts
    STELLAR_DEPLOYER_SECRET: str | None = None
    STELLAR_DEPLOYER_PUBLIC: str | None = None
    SOROBAN_RPC_URL: str | None = None
    SOROBAN_NETWORK_PASSPHRASE: str | None = None
    SOROBAN_CONTRACT_ID: str | None = None
    SOROBAN_SOURCE_IDENTITY: str | None = None
    SOROBAN_NETWORK: str | None = None

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
