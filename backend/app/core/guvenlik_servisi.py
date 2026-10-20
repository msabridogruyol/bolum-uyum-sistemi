"""
Güven Skoru Hesaplama — kontrol soruları + güvenlik olayları (tam ekrandan
çıkma, sekme değiştirme, pencere odağı kaybı) birleştirilerek hesaplanır.

Formül [2026-10-20 kullanıcı kararı — önceden 0,5 × kontrol + 0,5 × olay]:
    guven_skoru = min(kontrol_soru_skoru, guvenlik_olaylari_skoru)

    kontrol_soru_skoru      = (doğru cevaplanan kontrol sorusu / toplam kontrol sorusu) × 100
                               (hiç kontrol sorusu yoksa yok sayılır: güven = olay skoru)
    guvenlik_olaylari_skoru = max(0, 100 - Σ OLAY_CEZASI)
    Ortalama, iki göstergeden biri tamken diğerini hiç işlemez kılıyordu (dikkat soruları tam doğruysa sınırsız ihlal
    yine ≥ 50; dikkat soruları tamamen yanlışsa ihlalsiz tur yine 50). Düşük olanı almak her birini tek başına eşiğe bağlar.

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


def _goster(x: float) -> int:
    from app.core.rapor.veri import yuvarla
    return yuvarla(x)


def parametre_oku_float(db: Session, anahtar: str, varsayilan: float) -> float:
    p = db.query(SistemParametresi).filter(SistemParametresi.anahtar == anahtar).first()
    if p is None:
        return varsayilan
    try:
        return float(p.deger)
    except (TypeError, ValueError):
        return varsayilan


def birlesik_guven(kontrol: float | None, olay: float) -> float:
    """[2026-10-20] Güven puanı = min(kontrol, olay); kontrol sorusu yoksa (None) yalnızca olay skoru.
    Katman başına 2 dikkat sorusu: biri yanlışsa kontrol 50 (eşikte, geçerli), ikisi de yanlışsa 0 (katman sorunlu).
    [2026-10-19] Önceden kontrol yokken 100 sayılıyordu; puan 50'nin altına inemiyordu."""
    return round(olay if kontrol is None else min(kontrol, olay), 2)


def kontrol_soru_skoru_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> float | None:
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
    # [2026-10-14] Beklenen seçeneği tanımlanmamış kontrol sorusu hiç "doğru" sayılamaz; paydaya da girmez.
    cevaplar = [c for c in cevaplar if c[1].beklenen_secenek_sira is not None]
    if not cevaplar:
        return None  # kontrol sorusu hiç yoksa/cevaplanmadıysa güven yalnızca olaylara göre hesaplanır

    dogru_sayisi = sum(1 for _, soru, secenek in cevaplar if secenek.secenek_sirasi == soru.beklenen_secenek_sira)
    return round(dogru_sayisi / len(cevaplar) * 100, 2)


def guvenlik_olaylari_skoru_hesapla(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> tuple[float, int]:
    """Bu turda kaydedilen güvenlik olayı sayısına göre 0-100 skor. (skor, olay_sayisi) döner."""
    tipler = [t for (t,) in db.query(GuvenlikOlayi.olay_tipi)
              .filter(GuvenlikOlayi.ogrenci_id == ogrenci.id, GuvenlikOlayi.tur_id == tur.id).all()]
    cezali = [t for t in tipler if OLAY_CEZASI.get(t, 0) > 0]
    skor = max(0.0, 100.0 - sum(OLAY_CEZASI[t] for t in cezali))
    return round(skor, 2), len(cezali)


def gecerli_mi(guven_skoru: float, esik: float) -> bool:
    """[2026-10-14] Geçerlilik kararı, öğrenciye ve yöneticiye GÖSTERİLEN tam sayı puanla verilir (yarım yukarı yuvarlanır):
    ekranda "50 / eşik 50" gören öğrencinin turu 49,72 yüzünden geçersiz sayılmaz."""
    from app.core.rapor.veri import yuvarla
    return yuvarla(guven_skoru) >= esik


def canli_guven_durumu(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict:
    """[2026-10-10] Sınav sırasında öğrenciye gösterilen güven puanı.
    [2026-10-20] Yalnızca ihlallerden (olay skoru) hesaplanır: dikkat soruları anlık puana katılsaydı öğrenci yanlış
    cevabını puanın düşmesinden anlayıp geri dönüp düzeltebilirdi (dikkat sorusu işlevini yitirir) ve ilk yanlışta
    puan 0 görünürdü. Dikkat soruları tur bitince kayıtlı güven puanına (min(kontrol, olay)) katılır."""
    olay_skoru, ihlal = guvenlik_olaylari_skoru_hesapla(db, ogrenci, tur)
    sayim: dict[str, int] = {}
    for (t,) in db.query(GuvenlikOlayi.olay_tipi).filter(GuvenlikOlayi.ogrenci_id == ogrenci.id,
                                                         GuvenlikOlayi.tur_id == tur.id).all():
        if OLAY_CEZASI.get(t, 0) > 0:
            sayim[t] = sayim.get(t, 0) + 1
    return {
        "guven_puani": _goster(olay_skoru),   # kayıttaki olay bileşeniyle aynı hesap, aynı yuvarlama
        "esik": parametre_oku_float(db, "guven_skoru_esigi", 50.0),
        "ihlal_sayisi": ihlal,
        "ihlaller": [{"tip": t, "ad": OLAY_ADI.get(t, t), "sayi": n, "ceza": OLAY_CEZASI[t]} for t, n in sayim.items()],
    }


def guven_skorunu_hesapla_ve_kaydet(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> float:
    """
    Tur tamamlandığında çağrılır — kontrol soru skoru ile güvenlik olayları
    skorundan düşük olanı alır, tur kaydına yazar, eşik altındaysa
    sonuc_gecerli_mi=False yapar.
    """
    kontrol_skoru = kontrol_soru_skoru_hesapla(db, ogrenci, tur)
    olay_skoru, olay_sayisi = guvenlik_olaylari_skoru_hesapla(db, ogrenci, tur)

    guven_skoru = birlesik_guven(kontrol_skoru, olay_skoru)
    esik = parametre_oku_float(db, "guven_skoru_esigi", 50.0)

    tur.guven_skoru = guven_skoru
    if not gecerli_mi(guven_skoru, esik):
        tur.sonuc_gecerli_mi = False
        tur.gecersizlik_nedeni = (
            f"Güven skoru eşiğin altında ({_goster(guven_skoru)} < {esik:g}). "
            + (f"Kontrol soru skoru: {kontrol_skoru}, " if kontrol_skoru is not None else "")
            + f"güvenlik olayı sayısı: {olay_sayisi} (olay skoru: {olay_skoru})."
        )
    else:
        tur.sonuc_gecerli_mi = True
        tur.gecersizlik_nedeni = None

    db.flush()
    return guven_skoru


# ----------------------------------------------------------------------------- [2026-10-12] Katman bazında güven
def katman_guven_durumlari(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict[str, dict]:
    """Ana katmanların (K1–K4) her biri için güven puanı: o katmanın kontrol soruları + o katmanda kaydedilen ihlaller.
    Tur güven puanıyla aynı formül (kontrol ile olaydan düşük olanı); yalnızca o katmanın verisiyle hesaplanır."""
    from app.models import Katman
    esik = parametre_oku_float(db, "guven_skoru_esigi", 50.0)
    katmanlar = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).order_by(Katman.sira).all()
    cevaplar = (
        db.query(Soru.katman_id, Soru.beklenen_secenek_sira, SoruSecenegi.secenek_sirasi)
        .join(OgrenciCevap, OgrenciCevap.soru_id == Soru.id)
        .join(SoruSecenegi, SoruSecenegi.id == OgrenciCevap.secenek_id)
        .filter(OgrenciCevap.ogrenci_id == ogrenci.id, OgrenciCevap.tur_id == tur.id, Soru.soru_tipi == "kontrol")
        .all()
    )
    olaylar = [(k, t) for k, t in db.query(GuvenlikOlayi.katman_kod, GuvenlikOlayi.olay_tipi)
               .filter(GuvenlikOlayi.ogrenci_id == ogrenci.id, GuvenlikOlayi.tur_id == tur.id).all()]
    sonuc = {}
    for k in katmanlar:
        kc = [(b, s) for kid, b, s in cevaplar if kid == k.id]
        kc = [(b, s) for b, s in kc if b is not None]   # beklenen seçeneği olmayan kontrol sorusu paydaya girmez
        kontrol = round(sum(1 for b, s in kc if s == b) / len(kc) * 100, 2) if kc else None
        cezali = [t for kk, t in olaylar if kk == k.kod and OLAY_CEZASI.get(t, 0) > 0]
        olay = max(0.0, 100.0 - sum(OLAY_CEZASI[t] for t in cezali))
        guven = birlesik_guven(kontrol, olay)
        sonuc[k.kod] = {"kod": k.kod, "ad": k.ad, "katman_id": k.id, "guven": guven, "kontrol": kontrol,
                        "ihlal": len(cezali), "sorunlu": not gecerli_mi(guven, esik)}
    return sonuc


def sorunlu_katmanlar(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> list[dict]:
    """Geçersiz sayılan (güven puanı eşiğin altında) bir turda tekrar çözülmesi gereken katmanlar.
    Katman puanı eşiğin altında olanlar; hiçbiri tek başına eşiğin altında değilse en düşük güvenli katman."""
    if tur is None or tur.durum != "tamamlandi" or tur.sonuc_gecerli_mi is not False:
        return []
    durumlar = list(katman_guven_durumlari(db, ogrenci, tur).values())
    sorunlu = [d for d in durumlar if d["sorunlu"]]
    if not sorunlu and durumlar:
        en_dusuk = min(d["guven"] for d in durumlar)
        sorunlu = [d for d in durumlar if d["guven"] == en_dusuk]
    return sorunlu
