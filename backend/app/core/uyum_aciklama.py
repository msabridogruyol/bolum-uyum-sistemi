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
            sinif = fark_sinifi(fark, bool(getattr(degisken.get(girdi.degisken_idler[j]), 'ters_yonlu', False)))
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



# [2026-10-17] Raporlarda kıyaslanacak bölümler: hedef + seçilenler; A4 sayfaya sığan en çok sütun sayısı
RAPOR_BOLUM_SINIRI = 6
KIYAS_ESIGI = 0.3     # puan; bundan küçük katkı farkı "fark yaratan özellik" sayılmaz


def son_tamamlanan_tur(db: Session, o: Ogrenci):
    return (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id,
                                                      OgrenciDegerlendirmeTuru.durum == "tamamlandi")
            .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())


def rapor_secimi(db: Session, o: Ogrenci, tur: OgrenciDegerlendirmeTuru, bolum_idler: list[int] | None = None) -> dict:
    """Rapor bölüm seçimi: hedef her zaman ilk sırada (varsa); seçim yoksa hedef + ilk öneriler; en çok RAPOR_BOLUM_SINIRI."""
    from app.core.koclugu_servisi import aktif_hedef_getir
    sira = sm.siralama_getir(db, o, tur, ilk_n=301)
    gecerli = {s.bolum_id for s in sira}
    hedef = aktif_hedef_getir(db, o)
    hedef_id = hedef.bolum_id if hedef and hedef.bolum_id in gecerli else None
    istenen = [b for b in dict.fromkeys(bolum_idler or []) if b in gecerli]
    if not istenen:
        istenen = [s.bolum_id for s in sira[:RAPOR_BOLUM_SINIRI]]
    secim = ([hedef_id] if hedef_id else []) + [b for b in istenen if b != hedef_id]
    return {"secim": secim[:RAPOR_BOLUM_SINIRI], "hedef_id": hedef_id, "kirpildi": len(secim) > RAPOR_BOLUM_SINIRI,
            "sira": sira}


def hedef_kiyasi(m: dict | None) -> dict | None:
    """Hedef bölüm ile matristeki diğer bölümler: puan ve sıra farkı; farkı en çok yaratan özellikler.
    Özellik etkisi = hedefteki katkı − diğer bölümdeki katkı ("bu özellik olmasaydı" katkılarının farkı; gösterilen
    puanla aynı hesap). Eksi: hedefi o bölümün gerisinde bırakan, artı: hedefi önde tutan özellik."""
    if not m or not m.get("bolumler"):
        return None
    oz = m["ozellikler"]
    ref = next((b for b in m["bolumler"] if b.get("hedef")), None)

    def ozellik(j, b, etki=None):
        x = {"kod": oz[j]["kod"], "ad": oz[j]["ad"], "bolum_sinif": b["hucreler"][j]["sinif"]}
        if ref is not None:
            x["hedef_sinif"] = ref["hucreler"][j]["sinif"]
        if etki is not None:
            x["etki"] = round(etki, 2)
        return x

    satirlar = []
    for b in m["bolumler"]:
        if b is ref:
            continue
        satir = {"bolum_id": b["bolum_id"], "bolum": b["bolum"], "sira": b["sira"], "uyum": b["uyum"]}
        if ref is not None:
            D = [ref["hucreler"][j]["katki"] - b["hucreler"][j]["katki"] for j in range(len(oz))]
            sirali = sorted(range(len(oz)), key=lambda j: D[j])
            satir["fark"] = round(ref["uyum"] - b["uyum"], 1)
            satir["geride_birakan"] = [ozellik(j, b, D[j]) for j in sirali[:3] if D[j] < -KIYAS_ESIGI]
            satir["one_cikaran"] = [ozellik(j, b, D[j]) for j in sirali[::-1][:3] if D[j] > KIYAS_ESIGI]
        else:
            satir["yukselten"] = [ozellik(x["j"], b, x["katki"]) for x in b["yukselten"][:3]]
            satir["dusuren"] = [ozellik(x["j"], b, x["katki"]) for x in b["dusuren"][:3]]
        satirlar.append(satir)
    hedef = None if ref is None else {"bolum_id": ref["bolum_id"], "bolum": ref["bolum"], "sira": ref["sira"],
                                     "uyum": ref["uyum"]}
    return {"hedef": hedef, "satirlar": satirlar, "bolum_sayisi": m.get("bolum_sayisi")}


def rapor_eki(db: Session, o: Ogrenci, bolum_idler: list[int] | None = None, cevaplar: bool = False) -> dict | None:
    """[2026-10-17] Raporlar için: seçilen bölümler (hedef + en çok 5) — hedef kıyası (öğrenci, veli, yönetici raporu)
    ve yalnızca yönetici raporu için uyum matrisi + soru–cevap dökümü (cevaplar=True)."""
    tur = son_tamamlanan_tur(db, o)
    if tur is None:
        return None
    s = rapor_secimi(db, o, tur, bolum_idler)
    m = uyum_matrisi(db, o, tur, s["secim"] or None)
    if m is None:
        return None
    ek = {"tur_no": tur.tur_no, "matris": m, "kiyas": hedef_kiyasi(m), "kirpildi": s["kirpildi"],
          "sinir": RAPOR_BOLUM_SINIRI}
    if cevaplar:
        from app.api.cevap_analizi import _cevaplar_ve_ozellikler
        ek["cevaplar"], _ = _cevaplar_ve_ozellikler(db, o, tur)
    return ek


def rapor_bolum_onerisi(db: Session, o: Ogrenci) -> dict:
    """Rapor penceresi için varsayılan seçim (hedef + ilk öneriler) ve sınır."""
    tur = son_tamamlanan_tur(db, o)
    if tur is None:
        return {"hedef": None, "varsayilan": [], "sinir": RAPOR_BOLUM_SINIRI, "hazir": False}
    s = rapor_secimi(db, o, tur)
    sira_no = {x.bolum_id: i for i, x in enumerate(s["sira"], 1)}
    from app.models import Bolum
    ad = {b.id: b.ad for b in db.query(Bolum).filter(Bolum.id.in_(s["secim"] or [-1]))}
    puan = {x.bolum_id: round(float(x.toplam_uyum), 1) for x in s["sira"]}
    liste = [{"id": b, "ad": ad.get(b), "sira": sira_no.get(b), "uyum": puan.get(b), "hedef": b == s["hedef_id"]} for b in s["secim"]]
    return {"hedef": next((x for x in liste if x["hedef"]), None), "varsayilan": liste, "sinir": RAPOR_BOLUM_SINIRI, "hazir": True}
