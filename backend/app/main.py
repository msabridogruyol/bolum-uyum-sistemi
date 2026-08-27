"""
Bölüm-Öğrenci Uyum Sistemi — Backend Giriş Noktası
Kaynak: sistem_genel_anlatim.md Bölüm C, veritabani_taslagi.md Bölüm 4
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api import auth, ogrenci, koclugu, admin, admin_auth

app = FastAPI(
    title="Bölüm Uyum Sistemi API",
    description="Öğrenci ve yönetici arayüzlerinin veritabanıyla tek temas noktası.",
    version="0.1.0",
)

# CORS — yalnızca Firebase Hosting domaini (veritabani_taslagi.md 4.5)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/saglik")
def saglik_kontrolu():
    """Cloud Run health check uç noktası."""
    return {"durum": "calisiyor"}


app.include_router(auth.router, prefix="/auth", tags=["Kimlik Doğrulama"])
app.include_router(admin_auth.router, prefix="/admin/auth", tags=["Yönetim — Giriş"])
app.include_router(ogrenci.router, prefix="/ogrenci", tags=["Öğrenci — Katman Akışı (D2-D5)"])
app.include_router(koclugu.router, prefix="/koclugu", tags=["Koçluk — Bölüm F"])
app.include_router(admin.router, prefix="/admin", tags=["Yönetim — E1-E9"])

# ÖNEMLİ (C madde 6 — API response ayrımı): /ogrenci/* uç noktaları
# yontem_skorlari, kendall_w, agirlikli_varyans, etkin_meslek_sayisi,
# model bilgisi gibi alanları ASLA response'a dahil etmemeli — bu response
# şema seviyesinde (Pydantic) garanti edildi (app/schemas/ogrenci.py) ve
# test_e2e_d4.py'de ham JSON metni üzerinden doğrulandı. Bu alanlar
# yalnızca app/schemas/admin.py içinde bulunur (E7).
#
# E2 (Pipeline Durumu) şu an STUB — gerçek iş kuyruğu (Celery/Redis)
# henüz kurulmadı, bkz. app/api/admin.py içindeki uyarı.
