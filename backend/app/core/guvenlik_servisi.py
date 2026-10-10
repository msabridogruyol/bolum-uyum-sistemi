"""
Güven Skoru Hesaplama — kontrol soruları + güvenlik olayları (tam ekrandan
çıkma, sekme değiştirme, pencere odağı kaybı) birleştirilerek hesaplanır.

Formül [ÇIKARIM — kullanıcıyla netleştirildi]:
    guven_skoru = 0.5 × kontrol_soru_skoru + 0.5 × guvenlik_olaylari_skoru

    kontrol_soru_skoru      = (doğru cevaplanan kontrol sorusu / toplam kontrol sorusu) × 100
                               (hiç kontrol sorusu yoksa 100 varsayılır — ceza yok)
    guvenlik_olaylari_skoru = max(0, 100 - OLAY_BASINA_CEZA × olay_sayısı)

Eşik altında kalan turlar `sonuc_gecerli_mi = False` olarak işaretlenir —
ama VERİ SİLİNMEZ, yalnızca "geçersiz" etiketlenir (admin isterse inceler).
"""
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, OgrenciDegerlendirmeTuru, OgrenciCevap, Soru, SoruSecenegi,
    GuvenlikOlayi, SistemParametresi,
)

OLAY_BASINA_CEZA = 10.0  # (eski sabit — geriye uyumluluk için duruyor)
# [2026-10-10] Olay türüne göre ceza. "Geri dönüldü" olayları ve kamera onayı vermemek ceza almaz
# (KVKK: rızanın özgür olması için reddetmek cezalandırılmaz; raporda "kamerasız" diye görünür).
OLAY_CEZASI = {
    "tam_ekrandan_cikti": 10.0, "sekme_degisti": 10.0, "pencere_odagi_kaybedildi": 5.0,
    "coklu_ekran": 15.0, "ekran_goruntusu_tusu": 10.0, "kopyalama": 5.0, "kamera_kapandi": 5.0,
}
OLAY_ADI = {
    "tam_ekrandan_cikti": "Tam ekrandan çıkma", "sekme_degisti": "Sekme değiştirme",
    "pencere_odagi_kaybedildi": "Başka pencereye geçme", "coklu_ekran": "İkinci ekran",
    "ekran_goruntusu_tusu": "Ekran görüntüsü tuşu", "kopyalama": "Kopyalama denemesi", "kamera_kapandi": "Kamera kapandı",
}


def parametre_oku_float(db: Session, anahtar: str, varsayilan: float) -> float:
    p = db.query(SistemParametresi).filter(SistemParametresi.anahtar == anahtar).first()
    if p is None:
        return varsayilan
    try:
        return float(p.deger)
    except (TypeError, ValueError):
        return varsayilan


def kontrol_soru_skoru_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> float:
    """Bu tur içinde cevaplanmış kontrol sorularının doğruluk oranı, 0-100."""
    cevaplar = (
        db.query(OgrenciCevap, Soru, SoruSecenegi)
        .join(Soru, Soru.id == OgrenciCevap.soru_id)
        .join(SoruSecenegi, SoruSecenegi.id == OgrenciCevap.secenek_id)
        .filter(
            OgrenciCevap.ogrenci_id == ogrenci.id,
            OgrenciCevap.tur_id == tur.id,
            Soru.soru_tipi == "kontrol",
        )
        .all()
    )
    if not cevaplar:
        return 100.0  # kontrol sorusu hiç yoksa/cevaplanmadıysa ceza uygulanmaz

    dogru_sayisi = sum(
        1 for _, soru, secenek in cevaplar
        if soru.beklenen_secenek_sira is not None and secenek.secenek_sirasi == soru.beklenen_secenek_sira
    )
    return round(dogru_sayisi / len(cevaplar) * 100, 2)


def guvenlik_olaylari_skoru_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> tuple[float, int]:
    """Bu turda kaydedilen güvenlik olayı sayısına göre 0-100 skor. (skor, olay_sayisi) döner."""
    tipler = [t for (t,) in db.query(GuvenlikOlayi.olay_tipi)
              .filter(GuvenlikOlayi.ogrenci_id == ogrenci.id, GuvenlikOlayi.tur_id == tur.id).all()]
    cezali = [t for t in tipler if OLAY_CEZASI.get(t, 0) > 0]
    skor = max(0.0, 100.0 - sum(OLAY_CEZASI[t] for t in cezali))
    return round(skor, 2), len(cezali)


def canli_guven_durumu(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict:
    """[2026-10-10] Sınav sırasında öğrenciye gösterilen güven puanı (kontrol soruları + ihlaller)."""
    kontrol = kontrol_soru_skoru_hesapla(db, ogrenci, tur)
    olay_skoru, ihlal = guvenlik_olaylari_skoru_hesapla(db, ogrenci, tur)
    sayim: dict[str, int] = {}
    for (t,) in db.query(GuvenlikOlayi.olay_tipi).filter(GuvenlikOlayi.ogrenci_id == ogrenci.id,
                                                         GuvenlikOlayi.tur_id == tur.id).all():
        if OLAY_CEZASI.get(t, 0) > 0:
            sayim[t] = sayim.get(t, 0) + 1
    return {
        "guven_puani": round(0.5 * kontrol + 0.5 * olay_skoru),
        "esik": parametre_oku_float(db, "guven_skoru_esigi", 50.0),
        "ihlal_sayisi": ihlal,
        "ihlaller": [{"tip": t, "ad": OLAY_ADI.get(t, t), "sayi": n, "ceza": OLAY_CEZASI[t]} for t, n in sayim.items()],
    }


def guven_skorunu_hesapla_ve_kaydet(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> float:
    """
    Tur tamamlandığında çağrılır — kontrol soru skoru + güvenlik olayları
    skorunu eşit ağırlıkla birleştirir, tur kaydına yazar, eşik altındaysa
    sonuc_gecerli_mi=False yapar.
    """
    kontrol_skoru = kontrol_soru_skoru_hesapla(db, ogrenci, tur)
    olay_skoru, olay_sayisi = guvenlik_olaylari_skoru_hesapla(db, ogrenci, tur)

    guven_skoru = round(0.5 * kontrol_skoru + 0.5 * olay_skoru, 2)
    esik = parametre_oku_float(db, "guven_skoru_esigi", 50.0)

    tur.guven_skoru = guven_skoru
    if guven_skoru < esik:
        tur.sonuc_gecerli_mi = False
        tur.gecersizlik_nedeni = (
            f"Güven skoru eşiğin altında ({guven_skoru} < {esik}). "
            f"Kontrol soru skoru: {kontrol_skoru}, güvenlik olayı sayısı: {olay_sayisi} (olay skoru: {olay_skoru})."
        )
    else:
        tur.sonuc_gecerli_mi = True
        tur.gecersizlik_nedeni = None

    db.flush()
    return guven_skoru
