# -*- coding: utf-8 -*-
"""
[2026-10-17] Bölüm uyumunun açıklaması — cevaptan bölüm sonucuna kadar izlenebilir matrisler.

  1. Cevap matrisi   (soru × özellik): api/cevap_analizi.py — her cevabın her özelliğe katkısı.
  2. Uyum matrisi    (özellik × bölüm): bu modül — öğrencinin değeri, bölümün beklentisi, fark ve fark sınıfı
                     (koclugu_servisi.fark_sinifi: uyumlu / fazla / az / belirgin), hücre uyumu ve KATKI.
  3. Yöntem matrisi  (bölüm × 10 ÇKKV yöntemi): kayıtlı yontem_skorlari + Kendall W (yalnızca süper admin).

KATKI = "bu özellik olmasaydı": özellik çıkarılıp (ağırlıklar yeniden normalize edilerek) 10 yöntem tüm bölümler için
yeniden hesaplanır; katkı = gerçek TOPLAM_UYUM − özelliksiz TOPLAM_UYUM. Pozitif katkı bölümün puanını yükselten,
negatif katkı düşüren özelliktir. Böylece döküm, gösterilen puanla aynı hesaptan gelir (doğrusal yaklaşım değildir).
Katkılar toplanınca puana eşit olmaz (yöntemler doğrusal değildir); her biri "tek başına bu özelliğin etkisi"dir.
K5 dal katkısı ayrı bir satırdır (nihai − TOPLAM_UYUM). Puanlar göreli: 301 bölüm içinde öğrenciye yakınlık.
"""
import numpy as np
from sqlalchemy.orm import Session

from app.core import skor_motoru as sm
from app.models import Ogrenci, OgrenciBolumUyumSkoru, OgrenciDegerlendirmeTuru

VARSAYILAN_ILK = 10
VARSAYILAN_SON = 3


def _ortalama(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    w = w / w.sum()
    return np.mean([sm._min_max_0_100(f(X, w)) for f in sm.YONTEMLER.values()], axis=0)


def ozellik_katkilari(X: np.ndarray, w: np.ndarray) -> np.ndarray:
    """(n_bolum, m_ozellik) katkı matrisi: tam puan − o özellik çıkarılınca hesaplanan puan."""
    tam = _ortalama(X, w)
    m = X.shape[1]
    K = np.zeros_like(X, dtype=float)
    for j in range(m):
        maske = np.ones(m, dtype=bool)
        maske[j] = False
        K[:, j] = tam - _ortalama(X[:, maske], w[maske])
    return K


def uyum_matrisi(db: Session, o: Ogrenci, tur: OgrenciDegerlendirmeTuru, bolum_idler: list[int] | None = None,
                 yontem: bool = False) -> dict | None:
    """Seçilen bölümler için özellik × bölüm uyum matrisi + katkılar. bolum_idler yoksa: ilk 10 + hedef + son 3."""
    from app.core.koclugu_servisi import aktif_hedef_getir, fark_rengi, fark_sinifi
    from app.models import Degisken, Katman

    girdi = sm.girdi_hazirla(db, o, tur)
    if girdi is None:
        return None
    sira = sm.siralama_getir(db, o, tur, ilk_n=len(girdi.bolum_idler))
    sira_no = {s.bolum_id: i for i, s in enumerate(sira, 1)}
    nihai = {s.bolum_id: float(s.toplam_uyum) for s in sira}
    kayit = {s.bolum_id: s for s in db.query(OgrenciBolumUyumSkoru).filter(
        OgrenciBolumUyumSkoru.ogrenci_id == o.id, OgrenciBolumUyumSkoru.tur_id == tur.id)}
    hedef = aktif_hedef_getir(db, o)
    hedef_id = hedef.bolum_id if hedef else None

    if not bolum_idler:
        secim = [s.bolum_id for s in sira[:VARSAYILAN_ILK]]
        if hedef_id and hedef_id not in secim:
            secim.append(hedef_id)
        secim += [s.bolum_id for s in sira[-VARSAYILAN_SON:] if s.bolum_id not in secim]
    else:
        secim = [b for b in dict.fromkeys(bolum_idler) if b in sira_no]
    satir_of = {b: i for i, b in enumerate(girdi.bolum_idler)}

    K = ozellik_katkilari(girdi.performans, girdi.agirliklar)
    degisken = {d.id: d for d in db.query(Degisken).filter(Degisken.id.in_(girdi.degisken_idler)).all()}
    katman = {k.id: k for k in db.query(Katman).all()}
    ozellikler = []
    for j, did in enumerate(girdi.degisken_idler):
        d = degisken.get(did)
        k = katman.get(d.katman_id) if d else None
        ozellikler.append({"id": did, "kod": girdi.degisken_kodlari[j], "ad": d.ad if d else "?",
                           "katman": k.kod if k else None, "agirlik": round(float(girdi.agirliklar[j]) * 100, 2),
                           "ogrenci": round(float(girdi.ogrenci_olcekli[j]), 1)})

    bolumler = []
    for b in secim:
        i = satir_of[b]
        r = kayit.get(b)
        toplam = float(r.toplam_uyum) if r else None
        hucreler = []
        for j in range(len(girdi.degisken_idler)):
            fark = float(girdi.ogrenci_olcekli[j] - girdi.bolum_olcekli[i, j])
            sinif = fark_sinifi(fark)
            hucreler.append({"bolum": round(float(girdi.bolum_olcekli[i, j]), 1), "fark": round(fark, 1),
                             "sinif": sinif, "renk": fark_rengi(sinif), "uyum": round(float(girdi.performans[i, j]), 1),
                             "katki": round(float(K[i, j]), 2)})
        sirali = np.argsort(K[i])
        satir = {
            "bolum_id": b, "bolum": girdi.bolum_adlari.get(b), "sira": sira_no.get(b), "hedef": b == hedef_id,
            "uyum": round(nihai.get(b, toplam or 0.0), 1),
            "toplam_uyum": round(toplam, 1) if toplam is not None else None,
            "k5_katkisi": round(nihai[b] - toplam, 1) if (toplam is not None and b in nihai and abs(nihai[b] - toplam) >= 0.05) else None,
            "hucreler": hucreler,
            "yukselten": [{"j": int(j), "katki": round(float(K[i, j]), 2)} for j in sirali[::-1][:5] if K[i, j] > 0.05],
            "dusuren": [{"j": int(j), "katki": round(float(K[i, j]), 2)} for j in sirali[:5] if K[i, j] < -0.05],
        }
        if yontem and r is not None:
            satir["yontemler"] = {k: round(float(v), 1) for k, v in (r.yontem_skorlari or {}).items()}
            satir["kendall_w"] = float(r.kendall_w) if r.kendall_w is not None else None
        bolumler.append(satir)
    return {"ozellikler": ozellikler, "bolumler": bolumler, "bolum_sayisi": len(girdi.bolum_idler),
            "yontem_adlari": list(sm.YONTEMLER) if yontem else None}


def tam_matris(db: Session, o: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> dict | None:
    """Excel için: tüm bölümler × özellikler (bölüm beklentisi, fark, katkı) + sıra ve uyum."""
    girdi = sm.girdi_hazirla(db, o, tur)
    if girdi is None:
        return None
    sira = sm.siralama_getir(db, o, tur, ilk_n=len(girdi.bolum_idler))
    K = ozellik_katkilari(girdi.performans, girdi.agirliklar)
    satir_of = {b: i for i, b in enumerate(girdi.bolum_idler)}
    return {"girdi": girdi, "sira": sira, "satir_of": satir_of, "katki": K}


def rapor_eki(db: Session, o: Ogrenci, ilk_n: int = 5) -> dict | None:
    """[2026-10-17] Yönetici (rehber) PDF raporunun "Uyum açıklama eki": son tamamlanmış tur; ilk 5 + hedef bölüm
    uyum matrisi ve katkılar, soru–cevap dökümü. Öğrenci / veli raporuna eklenmez."""
    tur = (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id,
                                                     OgrenciDegerlendirmeTuru.durum == "tamamlandi")
           .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())
    if tur is None:
        return None
    from app.api.cevap_analizi import _cevaplar_ve_ozellikler
    from app.core.koclugu_servisi import aktif_hedef_getir
    sira = sm.siralama_getir(db, o, tur, ilk_n=ilk_n)
    secim = [s.bolum_id for s in sira[:ilk_n]]
    hedef = aktif_hedef_getir(db, o)
    if hedef and hedef.bolum_id not in secim:
        secim.append(hedef.bolum_id)
    m = uyum_matrisi(db, o, tur, secim or None)
    satirlar, _ = _cevaplar_ve_ozellikler(db, o, tur)
    return {"tur_no": tur.tur_no, "matris": m, "cevaplar": satirlar}
