"""
Veritabanı bağlantısı ve session yönetimi.
Bağlantı bilgisi GCP Secret Manager'dan gelir (üretimde); yerelde .env kullanılır.
Bkz: veritabani_taslagi.md madde 2.4.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

import os as _os
# [2026-10-11] Havuz açıkça ayarlanır: varsayılan 5+10 bağlantı, aynı anda ~40 iş parçacığına (FastAPI threadpool) yetmiyordu.
# Çok işçili kurulumda toplam bağlantı = işçi sayısı × HAVUZ_KAPASITESI; veritabanının bağlantı sınırını aşmamalı.
_HAVUZ_BOYUTU = int(_os.environ.get("DB_POOL_SIZE", "10"))
_HAVUZ_TASMA = int(_os.environ.get("DB_MAX_OVERFLOW", "20"))
HAVUZ_KAPASITESI = _HAVUZ_BOYUTU + _HAVUZ_TASMA
_sqlite = settings.DATABASE_URL.startswith("sqlite")
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, **({} if _sqlite else {
    "pool_size": _HAVUZ_BOYUTU, "max_overflow": _HAVUZ_TASMA,
    "pool_timeout": int(_os.environ.get("DB_POOL_TIMEOUT", "15"))}))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Tüm ORM modellerinin miras aldığı taban sınıf."""
    pass


def get_db():
    """FastAPI dependency — her istek için ayrı bir DB session açar/kapatır."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
