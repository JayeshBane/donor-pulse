# backend\config.py
from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # MongoDB
    mongodb_uri: str
    database_name: str = "donorpulse"
    
    # JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 8
    
    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"
    port: int = 8000
    
    # Environment
    environment: str = "development"  # development, staging, production
    
    # Frontend URL for magic links
    frontend_url: str = "http://localhost:3000"
    
    # Twilio (Optional)
    twilio_account_sid: Optional[str] = ""
    twilio_auth_token: Optional[str] = ""
    twilio_phone_number: Optional[str] = ""

    # Vonage (Optional)
    vonage_whatsapp_api_url: Optional[str] = ""
    vonage_api_key: Optional[str] = ""
    vonage_api_secret: Optional[str] = ""
    vonage_whatsapp_number: Optional[str] = ""

    # Cloudflare (Optional)
    cloudflare_account_id: Optional[str] = ""
    cloudflare_auth_token: Optional[str] = ""
    
    # Rate limiting
    rate_limit_requests: int = 100  # per minute
    rate_limit_window: int = 60  # seconds
    
    # Donor cooldown period in days
    donor_cooldown_days: int = 56
    
    @property
    def cors_origins_list(self) -> List[str]:
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()