"""
[2026-10-12] Değerlendirme tamamlanınca öğrenciye sonuç e-postası (+ PDF sonuç raporu).

Ne zaman gider?
  * Değerlendirmenin SON bölümü bitince: K1–K4 tamamlanmış (tur 'tamamlandi') VE açılan K5 derinleşme dallarının
    hepsi bitmiş olmalı (dal_servisi.bekleyen_dal_var_mi — sonuç ekranıyla aynı kural). K5 dalı açılmadıysa K4
    bitince gider. Cevap isteğini bekletmez; arka planda (BackgroundTasks) hazırlanır.
  * Güven puanı düşük (sonuc_gecerli_mi = False) turda GİTMEZ: sonuçlar güvenilir sayılmaz. Öğrenci sorunlu katmanı
    yeniden çözüp tur tekrar tamamlanınca gider.
  * Test hesaplarına, e-postası olmayan öğrencilere ve 'sonuc_epostasi_acik' parametresi '0' ise gitmez.
  * Bir tamamlanma için bir kez gider (ogrenci_degerlendirme_turu.sonuc_epostasi_zamani). Okul yetkilisi
    öğrenci detayından elle yeniden gönderebilir.
PDF eki: okulun paketinde 'Öğrenci raporları' modülü varsa öğrenci raporu (indirilebilen raporla aynı) eklenir;
yoksa e-posta eksiz gider ve sonuçların hesaptan görülebileceğini söyler (paket dışı içerik verilmez).
"""
import logging
import uuid

from sqlalchemy import text
from sqlalchemy.orm import Session

log = logging.getLogger("sonuc_epostasi")


def _tarih(z) -> str:
    return z.strftime("%d.%m.%Y") if z else ""


def otomatik_acik_mi(db: Session) -> bool:
    from app.core.katman_servisi import parametre_oku
    return str(parametre_oku(db, "sonuc_epostasi_acik", "1")).strip() not in ("0", "false", "hayir", "")


def rapor_ekli_mi(db: Session, okul_id) -> bool:
    from app.core.paketler import okul_modulleri
    return "ogrenci_raporlari" in okul_modulleri(db, okul_id)


def gonder(db: Session, ogrenci_id, tur_id: int, zorla: bool = False, yapan: str = "sistem") -> dict:
    """Sonuç e-postasını gönderir ve tur kaydına işler. Dönen: {durum, ekli, alici}.
    durum: gonderildi | hata | yapilandirilmadi | uygun_degil | zaten_gonderildi | kapali"""
    from app.core import eposta_servisi as ep
    from app.core.config import settings
    from app.core.hesap_yonetimi import olay_yaz
    from app.models import Ogrenci

    o = db.get(Ogrenci, uuid.UUID(str(ogrenci_id)))
    tur = db.execute(text("""SELECT id, durum, sonuc_gecerli_mi, tamamlanma_zamani, sonuc_epostasi_zamani
                             FROM ogrenci_degerlendirme_turu WHERE id = :t AND ogrenci_id = :o"""),
                     {"t": tur_id, "o": o.id if o else None}).first()
    if o is None or tur is None or tur.durum != "tamamlandi" or tur.sonuc_gecerli_mi is False:
        return {"durum": "uygun_degil", "ekli": False, "alici": None}
    if getattr(o, "test_hesabi", False) or not (o.email or "").strip():
        return {"durum": "uygun_degil", "ekli": False, "alici": None}
    if not zorla and not otomatik_acik_mi(db):
        return {"durum": "kapali", "ekli": False, "alici": o.email}
    if not zorla and _k5_bekliyor(db, o, tur.id):
        return {"durum": "k5_bekliyor", "ekli": False, "alici": o.email}
    if not ep.eposta_yapilandirildi_mi():
        return {"durum": "yapilandirilmadi", "ekli": False, "alici": o.email}

    # Aynı tamamlanma için yalnızca bir kez (iki arka plan görevi aynı anda çalışsa da): kaydı önce "talep et"
    kosul = "" if zorla else "AND (sonuc_epostasi_zamani IS NULL OR sonuc_epostasi_zamani < tamamlanma_zamani)"
    alindi = db.execute(text(f"""UPDATE ogrenci_degerlendirme_turu SET sonuc_epostasi_zamani = clock_timestamp(), sonuc_epostasi_durum = 'gonderiliyor'
                                 WHERE id = :t {kosul} RETURNING id"""), {"t": tur_id}).first()
    db.commit()
    if not alindi:
        return {"durum": "zaten_gonderildi", "ekli": False, "alici": o.email}

    ekli = rapor_ekli_mi(db, o.okul_id)
    ekler = []
    if ekli:
        try:
            from app.api.raporlar import _dosya_adi
            from app.core.paketler import okul_modulleri
            from app.core.rapor.pdf import ogrenci_pdf
            from app.core.rapor.veri import ogrenci_raporu_verisi
            v = ogrenci_raporu_verisi(db, o)
            pdf = ogrenci_pdf(v, netler="net_takibi" in okul_modulleri(db, o.okul_id))
            ekler = [(f"{_dosya_adi('Filizyol_Sonuc_Raporu', o.ad_soyad)}.pdf", pdf, "application/pdf")]
        except Exception as hata:   # rapor üretilemezse e-posta eksiz gider, hata kaydedilir
            log.error("Sonuç raporu üretilemedi (%s): %s: %s", o.id, type(hata).__name__, hata)
            db.rollback()
            ekli = False
    site = (settings.FRONTEND_URL or "").rstrip("/")
    konu, html, metin = ep.sonuc_raporu_epostasi(o.ad_soyad, _tarih(tur.tamamlanma_zamani), bool(ekler),
                                                 f"{site}/profilim" if site else None)
    basarili = ep.eposta_gonder(o.email, konu, html, metin, ekler=ekler)
    durum = "gonderildi" if basarili else "hata"
    db.execute(text("UPDATE ogrenci_degerlendirme_turu SET sonuc_epostasi_durum = :d WHERE id = :t"), {"d": durum, "t": tur_id})
    olay_yaz(db, o.id, "sonuc_epostasi",
             ("Sonuç e-postası gönderildi" if basarili else "Sonuç e-postası gönderilemedi") + (" (PDF ekli)" if ekler else ""), yapan=yapan)
    db.commit()
    return {"durum": durum, "ekli": bool(ekler), "alici": o.email}


def arka_planda_gonder(ogrenci_id, tur_id: int) -> None:
    """BackgroundTasks için: kendi oturumunu açar, hiçbir hatayı dışarı sızdırmaz."""
    from app.core.database import SessionLocal
    db = SessionLocal()
    try:
        gonder(db, ogrenci_id, tur_id)
    except Exception as hata:
        log.error("Sonuç e-postası arka plan hatası (%s): %s: %s", ogrenci_id, type(hata).__name__, hata)
    finally:
        db.close()


def _k5_bekliyor(db: Session, ogrenci, tur_id: int) -> bool:
    """Açılmış ama bitmemiş (sorusu olan) K5 derinleşme dalı var mı? Varsa değerlendirme henüz bitmemiştir."""
    from app.core.dal_servisi import bekleyen_dal_var_mi
    from app.models import OgrenciDegerlendirmeTuru
    return bekleyen_dal_var_mi(db, ogrenci, db.get(OgrenciDegerlendirmeTuru, tur_id))


def otomatik_gidecek_mi(db: Session, ogrenci, tur) -> bool:
    """Son bölüm (K4 ya da son K5 dalı) bitince çağrılır: e-posta şimdi gidecek mi?
    Tamamlama ekranında 'raporun e-postana gönderilecek' yalnızca bu True ise yazılır (yanlış vaat olmasın)."""
    from app.core import eposta_servisi as ep
    return (tur is not None and tur.durum == "tamamlandi" and tur.sonuc_gecerli_mi is not False
            and not _k5_bekliyor(db, ogrenci, tur.id)
            and not getattr(ogrenci, "test_hesabi", False) and bool((ogrenci.email or "").strip())
            and otomatik_acik_mi(db) and ep.eposta_yapilandirildi_mi())
