"""
D5, Katman 2 — Tüm Bölümleri Keşfet.
Kaynak: sistem_genel_anlatim.md D5

301 bölümün tamamı aranabilir; her sonuç için % uyum (varsa, D4'ten —
hesaplanmamışsa null) + katman bazlı ortalama (31 değişkenin tek tek
dökümü DEĞİL, K1-K4 için 4 sayı) + kısa bilgi notu döner.

[ÇIKARIM]: "Katman bazlı ortalama" ifadesinin, öğrencinin kendi katman
puanları mı yoksa BÖLÜMÜN o katmandaki ortalama beklentisi mi olduğu
belgede net değildi. Bölüm-özgü, arama sonucunda anlamlı bir fark
yaratacağı için "bölümün kendi katman ortalaması" (bolum_agirliklari'nin
katman bazında ortalaması) olarak yorumlandı — aksi halde öğrencinin
kendi K1-K4 puanları her aramada aynı kalır, bu görüntüleme katmanının
amacına aykırı olurdu.
"""
from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, Bolum, Degisken, Katman, BolumAgirligi,
    OgrenciDegerlendirmeTuru, OgrenciBolumUyumSkoru,
)


def bolum_katman_ortalamalari(db: Session, bolum_id: int) -> dict[str, float]:
    """Bölümün 31 değişkenlik agirlik_degeri'lerini katman bazında ortalar."""
    satirlar = (
        db.query(BolumAgirligi, Degisken.katman_id)
        .join(Degisken, Degisken.id == BolumAgirligi.degisken_id)
        .filter(BolumAgirligi.bolum_id == bolum_id)
        .all()
    )
    en_guncel: dict[tuple[int, int], tuple[BolumAgirligi, int]] = {}
    for agirlik, katman_id in satirlar:
        anahtar = (agirlik.degisken_id, katman_id)
        if anahtar not in en_guncel or agirlik.versiyon > en_guncel[anahtar][0].versiyon:
            en_guncel[anahtar] = (agirlik, katman_id)

    katmanlar = {k.id: k.kod for k in db.query(Katman).all()}
    toplam: dict[str, list[float]] = {}
    for agirlik, katman_id in en_guncel.values():
        kod = katmanlar.get(katman_id)
        if kod is None:
            continue
        toplam.setdefault(kod, []).append(float(agirlik.agirlik_degeri))

    return {kod: round(sum(v) / len(v), 2) for kod, v in toplam.items()}


def bolumleri_ara(db: Session, ogrenci: Ogrenci, arama_terimi: str, limit: int = 20) -> list[dict]:
    """
    D5 Katman 2 — isim bazlı arama (case-insensitive, kısmi eşleşme).
    Yalnızca durum='yayinda' bölümler döner (E5 kuralı).
    """
    bolumler = (
        db.query(Bolum)
        .filter(Bolum.durum == "yayinda", Bolum.ad.ilike(f"%{arama_terimi}%"))
        .order_by(Bolum.ad)
        .limit(limit)
        .all()
    )

    # öğrencinin en son tamamlanmış turu varsa TOPLAM_UYUM'u oradan oku
    son_tamamlanan_tur = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id, OgrenciDegerlendirmeTuru.durum == "tamamlandi")
        .order_by(OgrenciDegerlendirmeTuru.tur_no.desc())
        .first()
    )
    uyum_skorlari: dict[int, float] = {}
    if son_tamamlanan_tur is not None:
        uyum_skorlari = {
            s.bolum_id: float(s.toplam_uyum)
            for s in db.query(OgrenciBolumUyumSkoru).filter(
                OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id,
                OgrenciBolumUyumSkoru.tur_id == son_tamamlanan_tur.id,
            ).all()
        }

    sonuc = []
    for bolum in bolumler:
        sonuc.append({
            "bolum_id": bolum.id,
            "bolum_adi": bolum.ad,
            "kisa_aciklama": bolum.kisa_aciklama,
            "toplam_uyum": uyum_skorlari.get(bolum.id),  # None -> henüz hesaplanmadı
            "katman_ortalamalari": bolum_katman_ortalamalari(db, bolum.id),
        })
    return sonuc
