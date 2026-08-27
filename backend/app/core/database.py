"""
Veritabanı bağlantısı ve session yönetimi.
Bağlantı bilgisi GCP Secret Manager'dan gelir (üretimde); yerelde .env kullanılır.
Bkz: veritabani_taslagi.md madde 2.4.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
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
