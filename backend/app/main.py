"""
Bölüm-Öğrenci Uyum Sistemi — Backend Giriş Noktası
Kaynak: sistem_genel_anlatim.md Bölüm C, veritabani_taslagi.md Bölüm 4
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import token_coz
from app.api import auth, ogrenci, koclugu, admin, admin_auth
from app.api.admin_guvenlik import router as admin_guvenlik_router
from app.api.admin_sorular_detay import router as admin_sorular_detay_router
from app.api.admin_gecerlilik_v2 import router as admin_gecerlilik_v2_router

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


# ============================================================================
# Ziyaret/kullanım takibi (sonradan eklendi)
# ============================================================================
# [YENİ] Admin panelindeki "Kullanım İstatistikleri" için — KİŞİ BAZLI DEĞİL,
# yalnızca toplu/anonim sayım (KVKK kaygısıyla bilinçli olarak kullanıcı id'si
# hiç kaydedilmiyor). Loglama başarısız olsa bile asıl isteği ASLA bozmaz —
# tüm hata durumları sessizce yutulur.

_HARIC_YOLLAR = {"/saglik", "/docs", "/openapi.json", "/redoc", "/favicon.ico"}


def _kullanici_tipini_belirle(request: Request) -> str:
    yetki_basligi = request.headers.get("authorization", "")
    if not yetki_basligi.startswith("Bearer "):
        return "anonim"
    token = yetki_basligi.removeprefix("Bearer ").strip()
    payload = token_coz(token)
    if not payload:
        return "anonim"
    rol = payload.get("rol")
    if rol in ("super_admin", "icerik_editoru"):
        return "admin"
    if rol == "ogrenci":
        return "ogrenci"
    return "anonim"


class ZiyaretKaydiMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        yanit = await call_next(request)

        yol = request.url.path
        if yol in _HARIC_YOLLAR or request.method == "OPTIONS":
            return yanit

        try:
            kullanici_tipi = _kullanici_tipini_belirle(request)
            db = SessionLocal()
            try:
                db.execute(
                    text(
                        "INSERT INTO sayfa_ziyaretleri (yol, metod, kullanici_tipi, durum_kodu) "
                        "VALUES (:yol, :metod, :tip, :durum)"
                    ),
                    {"yol": yol[:255], "metod": request.method, "tip": kullanici_tipi, "durum": yanit.status_code},
                )
                db.commit()
            finally:
                db.close()
        except Exception:
            # Loglama hiçbir zaman asıl isteği etkilememeli — sessizce geç.
            pass

        return yanit


app.add_middleware(ZiyaretKaydiMiddleware)


@app.get("/saglik")
def saglik_kontrolu():
    """Cloud Run health check uç noktası."""
    return {"durum": "calisiyor"}


app.include_router(auth.router, prefix="/auth", tags=["Kimlik Doğrulama"])
app.include_router(admin_auth.router, prefix="/admin/auth", tags=["Yönetim — Giriş"])
app.include_router(ogrenci.router, prefix="/ogrenci", tags=["Öğrenci — Katman Akışı (D2-D5)"])
app.include_router(koclugu.router, prefix="/koclugu", tags=["Koçluk — Bölüm F"])
app.include_router(admin.router, prefix="/admin", tags=["Yönetim — E1-E9"])
app.include_router(admin_guvenlik_router, prefix="/admin", tags=["admin"])
app.include_router(admin_sorular_detay_router, prefix="/admin", tags=["admin"])
app.include_router(admin_gecerlilik_v2_router, prefix="/admin", tags=["admin"])

# ÖNEMLİ (C madde 6 — API response ayrımı): /ogrenci/* uç noktaları
# yontem_skorlari, kendall_w, agirlikli_varyans, etkin_meslek_sayisi,
# model bilgisi gibi alanları ASLA response'a dahil etmemeli — bu response
# şema seviyesinde (Pydantic) garanti edildi (app/schemas/ogrenci.py) ve
# test_e2e_d4.py'de ham JSON metni üzerinden doğrulandı. Bu alanlar
# yalnızca app/schemas/admin.py içinde bulunur (E7).
#
# E2 (Pipeline Durumu) şu an STUB — gerçek iş kuyruğu (Celery/Redis)
# henüz kurulmadı, bkz. app/api/admin.py içindeki uyarı.
