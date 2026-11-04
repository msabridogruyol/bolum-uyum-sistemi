"""[2026-11-04] Gece bakımı — kullanıcı kuralı: "göç ve sistemi yavaşlatacak değişikliklerde zaman kurulmalı; sistemde
değişiklik yapıldığında her zaman gece 3'te güncellesin".

Her gün `gece_bakim_saati` (varsayılan 03:00, Türkiye saati) ile 06:00 arasında bir kez çalışır (sunucu o saatte yeniden
başlasa da). Çok işçili / çok sunuculu kurulumda PostgreSQL advisory lock ve `gece_bakim_kaydi`ndaki gün satırı sayesinde
yalnızca biri çalıştırır. Sırası:
  1. Yarım kalmış (geçersiz) indeksler silinir; açılışta atlanan ağır göçler (sema_guncelleme.OTOMATIK_GECE, CONCURRENTLY)
     ve açılışta kilit alamayan göçler uygulanır.
  2. Gece kuyruğu (gece_kuyrugu): pipeline sonucunu canlıya alma, katman ağırlığı değişikliği, skorların yeniden hesabı —
     yönetici gündüz ister, bu saatte uygulanır. Skor yeniden hesabı gerekiyorsa sonda bir kez yapılır.
  3. Uyum puanı hesaplama sürümü değiştiyse eski skorlar yeniden yazılır (önceden her açılışta kontrol ediliyordu).
  4. Rehber paneli için öneri özetleri (tur_oneri_ozeti) doldurulur.
  5. Saklama süreleri: kamera fotoğrafları (180 gün), sayfa ziyaretleri, Filiz mesajları, süresi geçmiş anahtar iptalleri,
     eski doğrulama kodları / şifre değişikliği talepleri.
  6. Büyük tabloların istatistikleri güncellenir (ANALYZE).
Her adımın süresi ve sonucu `gece_bakim_kaydi.ayrinti`ye yazılır (Süper admin › Gece bakımı ekranı).
"""
from __future__ import annotations

import json
import logging
import threading
import time
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import text

log = logging.getLogger("gece_bakimi")
YEREL = ZoneInfo("Europe/Istanbul")
KILIT = 2026110403
PENCERE_SONU_SAAT = 6          # 03:00'te kaçırılırsa (sunucu kapalıydı) 06:00'ya kadar yine çalışır
KUYRUK_TURLERI = {
    "pipeline_onay": "Pipeline sonucunu canlıya alma",
    "katman_agirliklari": "Katman ağırlıklarını değiştirme",
    "skor_yeniden_hesap": "Uyum skorlarını yeniden hesaplama",
}
_BUYUK_TABLOLAR = ("ogrenci_bolum_uyum_skorlari", "ogrenci_cevaplar", "ogrenci_degisken_skorlari", "ogrenci_dal_uyum_skorlari",
                   "ogrenciler", "ogrenci_degerlendirme_turu", "sayfa_ziyaretleri", "tur_oneri_ozeti")


def bakim_saati(db) -> tuple[int, int]:
    from app.core.katman_servisi import parametre_oku
    try:
        s, d = (parametre_oku(db, "gece_bakim_saati", "03:00") or "03:00").strip().split(":")
        s, d = int(s), int(d)
        if 0 <= s <= 23 and 0 <= d <= 59:
            return s, d
    except (ValueError, AttributeError):
        pass
    return 3, 0


def sonraki_bakim(db, simdi: datetime | None = None) -> datetime:
    """Bir sonraki bakımın yerel başlama zamanı (ekranda "bu gece 03:00'te" demek için)."""
    simdi = (simdi or datetime.now(YEREL)).astimezone(YEREL)
    s, d = bakim_saati(db)
    aday = simdi.replace(hour=s, minute=d, second=0, microsecond=0)
    bugun_yapildi = db.execute(text("SELECT 1 FROM gece_bakim_kaydi WHERE gun = :g AND durum <> 'calisiyor'"),
                               {"g": simdi.date()}).first() is not None
    if aday <= simdi and (bugun_yapildi or simdi.hour >= PENCERE_SONU_SAAT):
        aday += timedelta(days=1)
    return aday


def zamanlama_metni(db) -> str:
    simdi = datetime.now(YEREL)
    z = sonraki_bakim(db, simdi)
    if z <= simdi:
        return "şu anda (bakım sürüyor)"
    gun = (z.date() - simdi.date()).days
    if gun == 0 or (gun == 1 and simdi.hour >= PENCERE_SONU_SAAT):   # gündüz ve akşam: ertesi sabahki bakım "bu gece"
        return f"bu gece {z:%H:%M}"
    if gun == 1:
        return f"yarın {z:%H:%M}"
    return f"{z:%d.%m.%Y %H:%M}"


def kuyruga_ekle(db, tur: str, veri: dict, isteyen=None, aciklama: str | None = None) -> dict:
    """Sistemi yavaşlatan değişikliği gece bakımına bırakır. Aynı türde bekleyen kayıt varsa günceller (son istek geçerli)."""
    if tur not in KUYRUK_TURLERI:
        raise ValueError(tur)
    anahtar = veri.get("grup") if tur == "pipeline_onay" else None
    var = db.execute(text("""SELECT id FROM gece_kuyrugu WHERE tur = :t AND durum = 'bekliyor'
                             AND (:a IS NULL OR veri->>'grup' = :a) ORDER BY id DESC LIMIT 1"""), {"t": tur, "a": anahtar}).scalar()
    p = {"t": tur, "v": json.dumps(veri, ensure_ascii=False), "i": getattr(isteyen, "id", None),
         "ad": getattr(isteyen, "ad_soyad", None), "ac": (aciklama or KUYRUK_TURLERI[tur])[:400]}
    if var:
        db.execute(text("""UPDATE gece_kuyrugu SET veri = CAST(:v AS jsonb), isteyen_id = :i, isteyen_ad = :ad, aciklama = :ac,
                           istenme_zamani = now() WHERE id = :id"""), {**p, "id": var})
        kid = var
    else:
        kid = db.execute(text("""INSERT INTO gece_kuyrugu (tur, veri, isteyen_id, isteyen_ad, aciklama)
                                 VALUES (:t, CAST(:v AS jsonb), :i, :ad, :ac) RETURNING id"""), p).scalar()
    return {"id": kid, "zamanlandi": zamanlama_metni(db), "aciklama": p["ac"]}


def bekleyenler(db) -> list[dict]:
    return [dict(r) for r in db.execute(text("""SELECT id, tur, veri, isteyen_ad, aciklama, istenme_zamani, durum, sonuc, calisma_zamani
                                               FROM gece_kuyrugu ORDER BY id DESC LIMIT 50""")).mappings().all()]


# ----------------------------------------------------------------------------- çalıştırıcı
def calismali_mi(db, simdi: datetime | None = None) -> bool:
    """Bakım saatinden pencere sonuna (06:00; bakım saati 06:00'dan geçse gün sonuna) kadar, bugün henüz çalışmadıysa."""
    simdi = (simdi or datetime.now(YEREL)).astimezone(YEREL)
    s, d = bakim_saati(db)
    baslangic = simdi.replace(hour=s, minute=d, second=0, microsecond=0)
    bitis = simdi.replace(hour=PENCERE_SONU_SAAT, minute=0, second=0, microsecond=0) if s < PENCERE_SONU_SAAT else \
        simdi.replace(hour=23, minute=59, second=59, microsecond=0)
    if not (baslangic <= simdi < bitis):
        return False
    # [2026-11-04] Yarıda kalan bakım (gece yayınında sunucu yeniden başladı) da yeniden çalışır: adımlar tekrarlanabilir.
    # Başka bir süreç hâlâ çalıştırıyorsa bakimi_calistir kilidi alamaz ve çıkar.
    return db.execute(text("SELECT 1 FROM gece_bakim_kaydi WHERE gun = :g AND durum <> 'calisiyor'"), {"g": simdi.date()}).first() is None


def bakimi_calistir(engine, gun: date | None = None) -> dict | None:
    """Bakımı bir kez çalıştırır (kilit alınamazsa ya da bugün yapıldıysa None). Testler ve elle çalıştırma da kullanır."""
    from app.core.database import SessionLocal
    gun = gun or datetime.now(YEREL).date()
    with engine.connect() as kilit_bag:
        kilit_bag = kilit_bag.execution_options(isolation_level="AUTOCOMMIT")
        if not kilit_bag.execute(text("SELECT pg_try_advisory_lock(:k)"), {"k": KILIT}).scalar():
            return None
        try:
            r = kilit_bag.execute(text("SELECT id, durum FROM gece_bakim_kaydi WHERE gun = :g"), {"g": gun}).first()
            if r is not None and r.durum != "calisiyor":
                return None
            if r is not None:   # yarıda kalmış: aynı satırla baştan (kilit bizde; çalışan başka süreç yok)
                kid = r.id
                kilit_bag.execute(text("UPDATE gece_bakim_kaydi SET baslama = now(), ayrinti = '[]'::jsonb WHERE id = :i"), {"i": kid})
            else:
                kid = kilit_bag.execute(text("""INSERT INTO gece_bakim_kaydi (gun) VALUES (:g) ON CONFLICT (gun) DO NOTHING RETURNING id"""),
                                        {"g": gun}).scalar()
                if kid is None:
                    return None
            ayrinti: list[dict] = []
            for ad, fn in _ADIMLAR:
                t0 = time.time()
                db = SessionLocal()
                try:
                    db.execute(text("SET statement_timeout = 0"))
                    sonuc = fn(db, engine)
                    db.commit()
                    ayrinti.append({"adim": ad, "durum": "tamam", "sonuc": sonuc, "sn": round(time.time() - t0, 1)})
                except Exception as e:   # bir adım hata verse de diğerleri çalışır
                    db.rollback()
                    log.exception("Gece bakımı adımı hata verdi: %s", ad)
                    ayrinti.append({"adim": ad, "durum": "hata", "sonuc": str(e).splitlines()[0][:300], "sn": round(time.time() - t0, 1)})
                finally:
                    try:
                        db.execute(text("RESET statement_timeout"))
                        db.commit()
                    except Exception:
                        pass
                    db.close()
                kilit_bag.execute(text("UPDATE gece_bakim_kaydi SET ayrinti = CAST(:a AS jsonb) WHERE id = :i"),
                                  {"a": json.dumps(ayrinti, ensure_ascii=False, default=str), "i": kid})
            durum = "hata" if any(a["durum"] == "hata" for a in ayrinti) else "tamam"
            kilit_bag.execute(text("UPDATE gece_bakim_kaydi SET bitis = now(), durum = :d WHERE id = :i"), {"d": durum, "i": kid})
            log.info("Gece bakımı bitti (%s): %s", durum, ayrinti)
            return {"gun": str(gun), "durum": durum, "ayrinti": ayrinti}
        finally:
            kilit_bag.execute(text("SELECT pg_advisory_unlock(:k)"), {"k": KILIT})


def zamanlayiciyi_baslat(engine) -> None:
    """Sunucu açılışında arka plan iş parçacığı: dakikada bir saate bakar."""
    from app.core.database import SessionLocal

    def _dongu():
        while True:
            try:
                db = SessionLocal()
                try:
                    calis = calismali_mi(db)
                finally:
                    db.close()
                if calis:
                    bakimi_calistir(engine)
            except Exception:
                log.exception("Gece bakımı zamanlayıcısı")
            time.sleep(60)

    threading.Thread(target=_dongu, name="gece-bakimi", daemon=True).start()


# ----------------------------------------------------------------------------- adımlar
def _gocler(db, engine) -> dict:
    gecersiz = [r[0] for r in db.execute(text("""SELECT c.relname FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
                                                 JOIN pg_namespace n ON n.oid = c.relnamespace
                                                 WHERE NOT i.indisvalid AND n.nspname = current_schema()""")).all()]
    db.commit()
    with engine.connect() as b:
        b = b.execution_options(isolation_level="AUTOCOMMIT")
        for ad in gecersiz:   # yarım kalmış CONCURRENTLY kurulumu: sil, aşağıda yeniden kurulur
            b.execute(text(f'DROP INDEX CONCURRENTLY IF EXISTS "{ad}"'))
    from app.core.sema_guncelleme import semayi_guncelle
    s = semayi_guncelle(engine, gece=True)
    return {"silinen_gecersiz_indeks": gecersiz, "uygulanan_komut": s.get("uygulanan"), "hata": s.get("hata") or s.get("atlandi")}


def _kuyruk(db, engine) -> dict:
    """Kuyruktaki değişiklikler uygulanır; gerekiyorsa skorlar yeniden hesaplanır. İşler skor hesabı bitene kadar 'calisiyor'
    kalır ve göçlerin 'bekleyen_skor_hesabi' işareti ancak hesaptan sonra silinir: yarıda kesilirse (sunucu yeniden başladı)
    bir sonraki deneme aynı işleri yeniden uygular (uygulamalar tekrarlanabilir) ve skorları yeniden hesaplar."""
    # bakım kilidi bizde: 'calisiyor' kalmış işler yarıda kesilmiş bir denemeden kalmıştır
    db.execute(text("UPDATE gece_kuyrugu SET durum = 'bekliyor' WHERE durum = 'calisiyor'"))
    db.commit()
    satirlar = db.execute(text("SELECT id, tur, veri FROM gece_kuyrugu WHERE durum = 'bekliyor' ORDER BY id")).mappings().all()
    skor_gerekli = False
    bekleyen = []   # (id, mesaj) — skor hesabından sonra 'tamamlandi'
    sonuc = []
    for r in satirlar:
        db.execute(text("UPDATE gece_kuyrugu SET durum = 'calisiyor', calisma_zamani = now() WHERE id = :i"), {"i": r["id"]})
        db.commit()
        try:
            if r["tur"] == "pipeline_onay":
                from app.api.admin import pipeline_taslagini_uygula
                mesaj, degisti = pipeline_taslagini_uygula(db, r["veri"]["grup"], r["veri"].get("isteyen_id"))
            elif r["tur"] == "katman_agirliklari":
                from app.api.admin import katman_agirliklarini_uygula
                mesaj, degisti = katman_agirliklarini_uygula(db, r["veri"]["agirliklar"], r["veri"].get("isteyen_id"))
            else:
                mesaj, degisti = "skorlar yeniden hesaplanacak", True
            skor_gerekli = skor_gerekli or degisti
            if degisti:   # yarıda kesilirse yeniden denemede skorlar mutlaka hesaplansın (işaret hesaptan sonra silinir)
                db.execute(text("""INSERT INTO tek_seferlik_gocler (ad) SELECT 'bekleyen_skor_hesabi'
                                   WHERE NOT EXISTS (SELECT 1 FROM tek_seferlik_gocler WHERE ad = 'bekleyen_skor_hesabi')"""))
                db.commit()
            bekleyen.append((r["id"], mesaj))
        except Exception as e:
            db.rollback()
            db.execute(text("UPDATE gece_kuyrugu SET durum = 'hata', sonuc = :s WHERE id = :i"), {"s": str(e).splitlines()[0][:500], "i": r["id"]})
            db.commit()
            sonuc.append({"id": r["id"], "tur": r["tur"], "durum": "hata"})
    try:
        isaret = db.execute(text("SELECT count(*) FROM tek_seferlik_gocler WHERE ad = 'bekleyen_skor_hesabi'")).scalar() or 0
    except Exception:
        db.rollback()
        isaret = 0
    if skor_gerekli or isaret:
        from app.api.admin import uyum_skorlarini_yeniden_hesapla
        sonuc.append({"yeniden_hesaplanan_tur": uyum_skorlarini_yeniden_hesapla(db)})
        if isaret:
            db.execute(text("DELETE FROM tek_seferlik_gocler WHERE ad = 'bekleyen_skor_hesabi'"))
    for kid, mesaj in bekleyen:
        db.execute(text("UPDATE gece_kuyrugu SET durum = 'tamamlandi', sonuc = :s WHERE id = :i"), {"s": mesaj, "i": kid})
        sonuc.append({"id": kid, "durum": "tamamlandi"})
    db.commit()
    return {"isler": sonuc}


def _skor_surumu(db, engine) -> dict:
    from app.core.skor_motoru import eski_uyum_skorlarini_guncelle
    return {"yeniden_yazilan_tur": eski_uyum_skorlarini_guncelle(db)}


def _oneri_ozetleri(db, engine) -> dict:
    from app.core.skor_motoru import oneri_ozetlerini_doldur
    return {"doldurulan_tur": oneri_ozetlerini_doldur(db)}


def _saklama(db, engine) -> dict:
    from app.core.hesap_guvenligi_servisi import eski_fotograflari_temizle
    from app.core.katman_servisi import parametre_oku

    def gun(anahtar, varsayilan):
        try:
            return max(0, int(parametre_oku(db, anahtar, str(varsayilan))))
        except ValueError:
            return varsayilan
    s = {"kamera_fotografi": eski_fotograflari_temizle(db)}
    g = gun("sayfa_ziyareti_saklama_gun", 180)
    if g:
        s["sayfa_ziyareti"] = db.execute(text("DELETE FROM sayfa_ziyaretleri WHERE zaman < now() - make_interval(days => :g)"), {"g": g}).rowcount
    g = gun("filiz_mesaj_saklama_gun", 730)
    if g:
        s["filiz_mesaji"] = db.execute(text("DELETE FROM ogrenci_koclugu_mesajlari WHERE olusturulma_zamani < now() - make_interval(days => :g)"),
                                       {"g": g}).rowcount
    s["iptal_anahtari"] = db.execute(text("DELETE FROM iptal_edilen_tokenlar WHERE son_kullanma < now()")).rowcount
    s["dogrulama_kodu"] = db.execute(text("DELETE FROM dogrulama_kodlari WHERE olusturulma_zamani < now() - interval '30 days'")).rowcount
    s["sifre_talebi"] = db.execute(text("DELETE FROM sifre_degisiklik_talepleri WHERE olusturulma_zamani < now() - interval '30 days'")).rowcount
    s["gece_kuyrugu"] = db.execute(text("DELETE FROM gece_kuyrugu WHERE durum <> 'bekliyor' AND istenme_zamani < now() - interval '180 days'")).rowcount
    return s


def _istatistik(db, engine) -> dict:
    db.commit()
    with engine.connect() as b:
        b = b.execution_options(isolation_level="AUTOCOMMIT")
        for t in _BUYUK_TABLOLAR:
            try:
                b.execute(text(f"ANALYZE {t}"))
            except Exception:
                pass
    return {"tablo": len(_BUYUK_TABLOLAR)}


def _tufe(db, engine) -> dict:
    """[2026-11-04] Ayın 4'ünden sonra bir önceki ayın TÜFE'si yoksa TÜİK'ten otomatik çekilir (hata bakımı durdurmaz)."""
    from app.core.otomatik_cekme import gece_tufe
    return gece_tufe(db, datetime.now(YEREL).date())


_ADIMLAR = [("gocler", _gocler), ("kuyruk", _kuyruk), ("skor_surumu", _skor_surumu), ("oneri_ozetleri", _oneri_ozetleri),
            ("saklama", _saklama), ("istatistik", _istatistik), ("tufe", _tufe)]
