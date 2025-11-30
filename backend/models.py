from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime

# Auth Models
class StellarWalletAuth(BaseModel):
    public_key: str = Field(..., min_length=56, max_length=56)
    signature: str
    message: str

class WalletChallengeRequest(BaseModel):
    public_key: str = Field(..., min_length=56, max_length=56)

class WalletChallengeResponse(BaseModel):
    public_key: str
    challenge: str
    expires_in: int

class WalletLoginRequest(BaseModel):
    public_key: str = Field(..., min_length=56, max_length=56)
    signature: str
    challenge: str

class WalletConnectRequest(BaseModel):
    public_key: str = Field(..., min_length=56, max_length=56)

class UserResponse(BaseModel):
    id: str
    stellar_public_key: str
    openai_api_key: Optional[str] = None

class TokenResponse(BaseModel):
    token: str
    user: UserResponse

# Project Models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)

class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

# File Models
class FileCreate(BaseModel):
    path: str = Field(..., min_length=1)
    content: str = ""
    type: str = Field(default="file", pattern="^(file|folder)$")

class FileUpdate(BaseModel):
    content: Optional[str] = None
    path: Optional[str] = None

class FileResponse(BaseModel):
    id: str
    path: str
    content: str
    type: str
    created_at: datetime

# Chat Models
class ChatMessage(BaseModel):
    message: str = Field(..., min_length=1)

class ChatResponse(BaseModel):
    message: str
    response: str
    files: List[dict] = []

class ConversationResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: datetime

# Settings Models
class OpenAISettings(BaseModel):
    openai_api_key: Optional[str] = None