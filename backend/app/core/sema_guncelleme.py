# -*- coding: utf-8 -*-
"""
[2026-10-10] Sunucu açılışında veritabanı şemasını otomatik güncelleme.

Neden: yeni özellikler yeni sütun/tablo istediğinde SQL'in Supabase'de elle çalıştırılması unutulursa
site 500 hatası veriyordu (ör. test hesapları). Burada son migration'ların SQL'i sunucu her açıldığında
bir kez çalıştırılır. Tüm komutlar tekrar çalıştırılabilir (IF NOT EXISTS / DROP ... IF EXISTS) — zaten
uygulanmışsa hiçbir şey değişmez. Her komut ayrı işlemde çalışır; biri başarısız olursa diğerleri etkilenmez.
Birden fazla sunucu aynı anda açılırsa PostgreSQL advisory lock ile tek biri çalıştırır.
"""
import importlib.util
import logging
from pathlib import Path

from sqlalchemy import text

_log = logging.getLogger("sema_guncelleme")
_SURUMLER = Path(__file__).resolve().parents[2] / "alembic" / "versions"
# Otomatik uygulanacak migration'lar (yalnızca tekrar çalıştırılabilir SQL içerenler)
OTOMATIK = ["0024_favori_bolum", "0025_test_hesaplari", "0026_guvenlik_olay_tipleri", "0027_gecici_sifre_ogrenci_no",
            "0028_kulupler_ilgi_testi", "0029_egitim_koclari", "0030_okul_subeleri",
            "0031_yetkili_unvan", "0032_takvim_kutuphane",
            "0033_kutuphane_sayfa", "0034_koc_okullari",
            "0035_koc_aracilik", "0036_kocluk_geri_bildirim_olcum", "0037_net_takibi", "0038_mor_renk", "0039_sinav_konulari", "0040_kulup_uyelik_duyuru", "0041_paketler", "0042_rehberlik", "0043_ogrenci_raporlari", "0044_okul_denemeleri", "0045_calisma", "0046_bildirimler", "0047_portfolyo", "0048_anketler", "0049_mezun_tercih", "0050_filiz_ai"]
KILIT = 2026101001


def _sql_oku(ad: str) -> str | None:
    yol = _SURUMLER / f"{ad}.py"
    if not yol.exists():
        return None
    spec = importlib.util.spec_from_file_location(f"_m_{ad}", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return getattr(m, "SQL", None)


def _komutlar(sql: str) -> list[str]:
    return [k.strip() for k in sql.split(";\n") if k.strip() and not k.strip().startswith("--")]


def semayi_guncelle(engine) -> dict:
    if engine.dialect.name != "postgresql":
        return {"atlandi": "postgresql değil"}
    sonuc = {"uygulanan": 0, "hata": []}
    with engine.connect() as baglanti:
        baglanti = baglanti.execution_options(isolation_level="AUTOCOMMIT")
        if not baglanti.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": KILIT}).scalar():
            return {"atlandi": "başka bir sunucu güncelliyor"}
        try:
            for ad in OTOMATIK:
                sql = _sql_oku(ad)
                if not sql:
                    continue
                for komut in _komutlar(sql):
                    try:
                        baglanti.execute(text(komut))
                        sonuc["uygulanan"] += 1
                    except Exception as e:  # yetki yoksa vb. — site açılmaya devam etsin
                        sonuc["hata"].append(f"{ad}: {str(e).splitlines()[0][:160]}")
        finally:
            baglanti.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": KILIT})
    if sonuc["hata"]:
        _log.warning("Şema güncellemesinde hata: %s", sonuc["hata"])
    return sonuc
