"""
Uygulama ayarları. Değerler ortam değişkenlerinden (.env) okunur.
Üretimde bu değerler GCP Secret Manager üzerinden enjekte edilir
(bkz. veritabani_taslagi.md 2.4) — kod içine gömülmez.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- Veritabanı ---
    DATABASE_URL: str = "postgresql+psycopg2://user:pass@localhost:5432/bolum_uyum"

    # --- JWT (D1 — access + refresh token) ---
    JWT_SECRET_KEY: str = "CHANGE_ME_IN_PRODUCTION"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # --- CORS (yalnızca Firebase Hosting domaini — veritabani_taslagi.md 4.5) ---
    CORS_ALLOWED_ORIGINS: list[str] = ["http://localhost:5173"]

    # --- İş kuyruğu (veritabani_taslagi.md Madde 1 — Celery + Redis) ---
    REDIS_URL: str = "redis://localhost:6379/0"

    # --- Sistem varsayılanları (E8'deki varsayılanlarla birebir aynı;
    #     gerçek değerler sistem_parametreleri tablosunda tutulur, bunlar
    #     yalnızca tablo boşsa kullanılacak "ilk kurulum" değerleridir) ---
    DEFAULT_K5_ESIK_PUANI: int = 80
    DEFAULT_K5_MAX_DAL_SAYISI: int = 3
    DEFAULT_YENIDEN_DEGERLENDIRME_MIN_GUN: int = 120


settings = Settings()
