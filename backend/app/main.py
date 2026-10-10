"""
Filizyol (Bölüm-Öğrenci Uyum Sistemi) — Backend Giriş Noktası
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
from app.api.admin_kutup_yukleme import router as admin_kutup_router
from app.api.admin_meslek_yukleme import router as admin_meslek_router
from app.api.ai_koc import router as ai_koc_router
from app.api.motivasyon import router as motivasyon_router
from app.api.net_takibi import router as net_takibi_router
from app.api.konu_yonetimi import router as konu_yonetimi_router
from app.api.admin_gelisim_kaynak import router as admin_gelisim_kaynak_router
from app.api.haftalik import router as haftalik_router
from app.api.bolum_bilgi import router as bolum_bilgi_router

from app.api.okul import genel_router as okul_genel_router, admin_router as okul_admin_router
from app.api.okul_yonetimi import router as okul_yonetimi_router
from app.api.meslek_dili import router as meslek_dili_router
from app.api.cevap_analizi import router as cevap_analizi_router
from app.api.listem import router as listem_router
from app.api.raporlar import router as raporlar_router
from app.api.akran import router as akran_router
from app.api.takvim import ogrenci_router as takvim_ogrenci_router, router as takvim_router
from app.api.kutuphane import ogrenci_router as kutuphane_ogrenci_router, router as kutuphane_router
from app.api.admin_yokatlas import router as admin_yokatlas_router
from app.api.koclar import ogrenci_router as koc_ogrenci_router, router as koc_router
from app.api.kulupler import ogrenci_router as kulup_ogrenci_router, router as kulup_router
from app.api.test_hesaplari import router as test_hesaplari_router, giris_router as test_giris_router
app = FastAPI(
    title="Filizyol API",
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
    if rol in ("super_admin", "okul_yetkilisi"):
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


@app.on_event("startup")
def _sema_guncelle():
    """[2026-10-10] Son migration'ların SQL'ini otomatik uygula (unutulan SQL sitenin çökmesine yol açmasın)."""
    try:
        from app.core.database import engine
        from app.core.sema_guncelleme import semayi_guncelle
        semayi_guncelle(engine)
    except Exception:
        pass


@app.on_event("startup")
def _baslangic_temizligi():
    """[2026-10-04] KVKK: 6 aydan eski kamera fotoğraflarını sil (Render her uyanışta çalıştırır)."""
    try:
        from app.core.hesap_guvenligi_servisi import eski_fotograflari_temizle
        db = SessionLocal()
        try:
            eski_fotograflari_temizle(db)
            db.commit()
        finally:
            db.close()
    except Exception:
        pass


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
app.include_router(admin_kutup_router, prefix="/admin", tags=["admin"])
app.include_router(admin_meslek_router, prefix="/admin", tags=["admin"])   # [2026-10-10] Pipeline sayfasındaki meslek yükleme (önceden kayıtlı değildi → 404)
app.include_router(ai_koc_router, prefix="/koclugu", tags=["koclugu"])
app.include_router(admin_gelisim_kaynak_router, prefix="/admin", tags=["admin"])
app.include_router(haftalik_router, prefix="/haftalik", tags=["Haftalık Görevler"])
app.include_router(bolum_bilgi_router, prefix="/bolumler", tags=["Bölüm Bilgi Kartı"])
app.include_router(okul_genel_router)                       # [2026-10-09] GET /okul/aktif
app.include_router(okul_admin_router, prefix="/admin")      # [2026-10-09] /admin/okullar
app.include_router(okul_yonetimi_router)
app.include_router(meslek_dili_router)
app.include_router(cevap_analizi_router)
app.include_router(listem_router)                           # [2026-10-10] /ogrenci/listem, /ogrenci/karsilastir
app.include_router(raporlar_router)                         # [2026-10-10] PDF / Excel raporlar
app.include_router(kulup_router)                            # [2026-10-10] okul kulüpleri
app.include_router(kulup_ogrenci_router)                    # [2026-10-10] /ogrenci/ilgi-testi
app.include_router(koc_router)                              # [2026-10-10] anlaşmalı eğitim koçları
app.include_router(koc_ogrenci_router)                      # [2026-10-10] /ogrenci/koclar
app.include_router(admin_yokatlas_router)                   # [2026-10-10] YÖK Atlas eşleştirme yönetimi
app.include_router(takvim_router)                            # [2026-10-10] takvim
app.include_router(takvim_ogrenci_router)
app.include_router(kutuphane_router)                         # [2026-10-10] öğrenci kütüphanesi
app.include_router(kutuphane_ogrenci_router)
app.include_router(konu_yonetimi_router)                     # [2026-10-10] konu listesi yönetimi (süper admin + okul)
app.include_router(net_takibi_router)                       # [2026-10-10] deneme, konu takibi, hedef net kıyası
app.include_router(motivasyon_router)                       # [2026-10-10] YKS geri sayımı, mesaj, rozetler
app.include_router(akran_router)                            # [2026-10-10] akran benzerliği, şube dağılımı, aday öğrenci
app.include_router(test_hesaplari_router)                    # [2026-10-10] /yonetim/test-hesaplari (süper admin)
app.include_router(test_giris_router)                        # [2026-10-10] POST /auth/test-giris

# ÖNEMLİ (C madde 6 — API response ayrımı): /ogrenci/* uç noktaları
# yontem_skorlari, kendall_w, agirlikli_varyans, etkin_meslek_sayisi,
# model bilgisi gibi alanları ASLA response'a dahil etmemeli — bu response
# şema seviyesinde (Pydantic) garanti edildi (app/schemas/ogrenci.py) ve
# test_e2e_d4.py'de ham JSON metni üzerinden doğrulandı. Bu alanlar
# yalnızca app/schemas/admin.py içinde bulunur (E7).
#
# E2 (Pipeline Durumu) şu an STUB — gerçek iş kuyruğu (Celery/Redis)
# henüz kurulmadı, bkz. app/api/admin.py içindeki uyarı.
