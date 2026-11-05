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
            "0035_koc_aracilik", "0036_kocluk_geri_bildirim_olcum", "0037_net_takibi", "0038_mor_renk", "0039_sinav_konulari", "0040_kulup_uyelik_duyuru", "0041_paketler", "0042_rehberlik", "0043_ogrenci_raporlari", "0044_okul_denemeleri", "0045_calisma", "0046_bildirimler", "0047_portfolyo", "0048_anketler", "0049_mezun_tercih", "0050_filiz_ai", "0051_simulasyon", "0052_katman_agirliklari", "0053_sayfa_ziyaretleri", "0054_is_hayati", "0055_is_hayati_beklenti", "0056_is_hayati_pratik", "0057_is_hayati_cv_mezun", "0058_ai_etkisi"]
OTOMATIK += ["0060_hata_kayitlari"]   # [2026-10-11] hata kayıtları + hız sınırı parametreleri (ayrı satır: diğer göç eklemeleriyle çakışmasın)
OTOMATIK += ["0061_filiz_yonetim_ai"]   # [2026-10-11] Filiz yönetim asistanı: günlük yapay zekâ sayacı
OTOMATIK += ["0062_performans_indeksleri"]   # [2026-10-11] okul paneli / rehberlik sorguları için tur_id indeksleri
OTOMATIK += ["0063_okul_erisim"]   # [2026-10-11] okul bazında sistem aç / kapat
OTOMATIK += ["0064_cevrimici"]   # [2026-10-11] çevrim içi öğrenciler (son görülme + gizlilik)
OTOMATIK += ["0065_aktif_gunler"]   # [2026-10-11] günlük aktiflik kaydı (öğrencinin sistemi açtığı günler)
OTOMATIK += ["0066_pilot_hazirlik"]   # [2026-10-11] oturum geçersiz kılma, laboratuvar giriş sınırı, sözlük bildirimleri
OTOMATIK += ["0067_coklu_dil"]   # [2026-10-12] kişisel dil tercihi + içerik çeviri önbelleği
OTOMATIK += ["0068_toplu_ogrenci_islemleri"]   # [2026-10-12] sınıf atlatma (geri alınabilir) + değerlendirme sıfırlama
OTOMATIK += ["0069_sonuc_epostasi"]   # [2026-10-12] değerlendirme tamamlanınca sonuç e-postası (+ PDF)
OTOMATIK += ["0070_mulakat_simulasyonu"]   # [2026-10-13] İş Hayatı → Mülakat Simülasyonu sonuçları
OTOMATIK += ["0071_dusunme_atolyesi"]   # [2026-10-13] İş Hayatı → Düşünme Atölyesi ilerlemesi
OTOMATIK += ["0072_ogrenme_deneyi"]   # [2026-10-13] Öğrenmeyi öğren deneyi (ertesi gün 2. ölçüm)
OTOMATIK += ["0074_haftalik_yansitma_metni"]   # [2026-10-14] haftalık yansıtma görevi açıklaması (gerçeği yansıtmayan cümle)
OTOMATIK += ["0075_bolum_birlestirme"]   # [2026-10-18] ayırt edilemeyen 21 bölüm grubu birleştirildi (23 bölüm silindi)
OTOMATIK += ["0076_yeni_k5_sorular"]   # [2026-10-18] yeni K1-K4 soruları (tek seferlik değişim) + yeni K5 (iş türü kapıştırma)
OTOMATIK += ["0077_bolum_kisa_aciklama"]   # [2026-10-18] boş bölüm kısa açıklamaları (pipeline veri/bolumler.csv)
OTOMATIK += ["0078_bolum_icerik_duzeltme"]   # [2026-10-18] bölüm tanıtımlarında doğrulanmış olgu düzeltmeleri (yalnızca değişmemiş metne)
OTOMATIK += ["0079_yeniden_degerlendirme_sikligi"]   # [2026-10-19] yeniden değerlendirme sıklığı sınıfa göre (12. sınıf / mezun 70 gün, diğerleri yılda 2)
OTOMATIK += ["0080_kocluk_cekirdek"]   # [2026-10-19] koçluk her pakette zorunlu (veri tutarlılığı)
OTOMATIK += ["0081_ek_olcme_sorulari"]   # [2026-10-19] K1-K4 ek sorular + katman başına 2 dikkat sorusu (yalnızca ekleme)
OTOMATIK += ["0082_bolum_kaldirma"]   # [2026-10-29] lisans programı olmayan / 3'ten az üniversitedeki 12 bölüm kaldırıldı (278 → 266)
OTOMATIK += ["0083_filiz_her_pakette"]   # [2026-10-30] Filiz her pakette; yapay zekâ sınırı pakete göre, okul aylık üst sınırı
OTOMATIK += ["0084_filiz_olcum"]   # [2026-10-31] katmanlı Filiz: cevabın kaynağı ve süresi
OTOMATIK += ["0085_veri_kaynagi_kontrol"]   # [2026-11-01] Veri Kaynakları ekranı: süper adminin kontrol kayıtları
OTOMATIK += ["0086_onlisans_bolum_kaldirma"]   # [2026-11-01] yalnızca ön lisans olan 4 bölüm kaldırıldı (266 → 262); ön lisans sonraki geliştirme
OTOMATIK += ["0087_veri_yonetimi_demo"]   # [2026-11-01] Pipeline ekranından K5 bağı / örnek meslek yükleme (yedekli) + demo okul
OTOMATIK += ["0088_pipeline_paketi"]   # [2026-11-01] pipeline'ı sistemden kurma: bilgisayar anahtarları + veri sürümleri (Storage)
OTOMATIK += ["0089_icerik_sadelestirme"]   # [2026-11-02] öğrenciye görünen içerikte lise düzeyine uygun dil (yalnızca değişmemiş metne)
OTOMATIK += ["0090_soru_sadelestirme"]   # [2026-11-02] K1–K4 soruları sade dil + gündelik hayata dengeli dağılım (yalnızca değişmemiş metne)
OTOMATIK += ["0091_kriz_okul_bildirimi"]   # [2026-11-03] Filiz kriz → okul yetkilisi bildirimi parametresi (varsayılan kapalı)
OTOMATIK += ["0092_guncel_adlar"]   # [2026-11-03] K5 katman adı "İş türü tercihleri"; kullanılmayan 4 eski parametre kaldırıldı
OTOMATIK += ["0093_denetim_guvenlik_performans"]
OTOMATIK += ["0095_gece_bakimi_ve_hesap"]   # [2026-11-04] gece bakımı kuyruğu, şifre değişikliği onayı, anahtar iptali, öneri özeti   # [2026-11-04] soru_gecerlilik_sonuclari tablosu + yük indeksleri
# [2026-11-04] Kullanıcı kuralı: sistemi yavaşlatacak göçler (büyük tablolarda indeks kurma vb.) açılışta değil, gece
# bakımında (03:00, app/core/gece_bakimi.py) ve CONCURRENTLY ile çalışır; açılışta yalnızca hafif göçler uygulanır.
OTOMATIK += ["0096_sistem_surumleri"]   # [2026-11-04] sistemin güncellenme zamanı
OTOMATIK += ["0097_veri_kaynaklari_tohumu"]   # [2026-11-04] yaşam maliyeti referansı (Türk-İş), kamu maaşları (AA), YKS 2027
OTOMATIK += ["0098_tufe_endeksi"]   # [2026-11-04] TÜFE endeksi (eski tutarların güncel tahmini) + kazanç referans ayı
OTOMATIK += ["0099_gelisim_listesi"]   # [2026-11-05] haftalık görev yerine gelişim listesi: keşif ve öz değerlendirme kayıtları
OTOMATIK_GECE = ["0094_gece_indeksleri"]
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


_KAYIT_TABLOSU = """CREATE TABLE IF NOT EXISTS sema_uygulanan (
    ad TEXT PRIMARY KEY, ozet TEXT NOT NULL, zaman TIMESTAMPTZ NOT NULL DEFAULT now())"""


def semayi_guncelle(engine, gece: bool = False) -> dict:
    """Açılışta (gece=False): OTOMATIK listesindeki hafif göçler; kilit beklemesi 5 sn (canlı trafiği kuyruğa sokmasın).
    Gece bakımında (gece=True): ayrıca OTOMATIK_GECE (ağır, CONCURRENTLY) göçleri; kilit beklemesi 60 sn.
    [2026-11-04] Uygulanan göç (içeriğinin özetiyle) sema_uygulanan'a yazılır ve bir sonraki açılışta yeniden çalıştırılmaz;
    önceden ~65 göç her açılışta yeniden çalışıyor, ALTER TABLE'lar tabloları kısa süre kilitliyordu. İçerik değişirse yeniden
    çalışır. Hata veren göç kaydedilmez; bir sonraki açılışta ya da gece bakımında yeniden denenir."""
    import hashlib
    if engine.dialect.name != "postgresql":
        return {"atlandi": "postgresql değil"}
    sonuc = {"uygulanan": 0, "atlanan": 0, "hata": []}
    with engine.connect() as baglanti:
        baglanti = baglanti.execution_options(isolation_level="AUTOCOMMIT")
        if not baglanti.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": KILIT}).scalar():
            return {"atlandi": "başka bir sunucu güncelliyor"}
        try:
            baglanti.execute(text("SET lock_timeout = '%s'" % ("60s" if gece else "5s")))
            baglanti.execute(text("SET statement_timeout = 0"))
            baglanti.execute(text(_KAYIT_TABLOSU))
            uygulanmis = dict(baglanti.execute(text("SELECT ad, ozet FROM sema_uygulanan")).all())
            for ad in OTOMATIK + (OTOMATIK_GECE if gece else []):
                sql = _sql_oku(ad)
                if not sql:
                    continue
                ozet = hashlib.sha256(sql.encode("utf-8")).hexdigest()[:16]
                if uygulanmis.get(ad) == ozet:
                    sonuc["atlanan"] += 1
                    continue
                basarili = True
                for komut in _komutlar(sql):
                    try:
                        baglanti.execute(text(komut))
                        sonuc["uygulanan"] += 1
                    except Exception as e:  # yetki yoksa / kilit alınamadıysa vb. — site açılmaya devam etsin
                        basarili = False
                        sonuc["hata"].append(f"{ad}: {str(e).splitlines()[0][:160]}")
                if basarili:
                    baglanti.execute(text("""INSERT INTO sema_uygulanan (ad, ozet, zaman) VALUES (:a, :o, now())
                                             ON CONFLICT (ad) DO UPDATE SET ozet = EXCLUDED.ozet, zaman = now()"""), {"a": ad, "o": ozet})
        finally:
            baglanti.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": KILIT})
            baglanti.execute(text("RESET lock_timeout"))      # bağlantı havuza döner; ayar uygulamanın isteklerine taşınmasın
            baglanti.execute(text("RESET statement_timeout"))
    if sonuc["hata"]:
        _log.warning("Şema güncellemesinde hata: %s", sonuc["hata"])
    return sonuc
