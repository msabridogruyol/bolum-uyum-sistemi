# -*- coding: utf-8 -*-
"""
[2026-10-09] Öğrenci cevap analizi — YALNIZCA SÜPER ADMİN.

GET /yonetim/ogrenci/{ogrenci_id}/cevap-analizi?tur_no=

Öğrencinin bir değerlendirme turundaki her cevabı: soru, tüm şıklar (seçilen / en az uyan işaretli),
bu cevabın hangi özelliğe kaç puan kattığı (katman tamamlanırken kullanılan puanlama kuralının AYNISI:
katman_servisi.cevaplari_puanla), kontrol sorularında beklenen–verilen.
Özellik özeti: özellik puanı = o özelliğe katkı veren cevapların ortalaması.
Sonuca etkisi: ilk 5 öneri ve her biri için bölümü diğer bölümlere göre öne çıkaran / geri çeken özellikler
(kriter ağırlığı × özellik uyumu, bölüm ortalamasına göre fark — ÇKKV yöntemlerinin ortak girdisi).
Okul yetkilisi bu uç noktaya erişemez (öğrencinin ham cevapları hassas veridir).
"""
import uuid

import numpy as np
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.katman_servisi import cevaplari_puanla, puanlama_onbellegi
from app.models import (
    AdminKullanici, Dal, Degisken, Katman, Ogrenci, OgrenciCevap, OgrenciDegerlendirmeTuru,
    OgrenciDegiskenSkoru, Soru,
)

router = APIRouter(prefix="/yonetim/ogrenci", tags=["Cevap analizi (süper admin)"])

TIP_ADI = {"likert": "Likert", "sjt": "Durum sorusu", "kutup": "İki uç", "kontrol": "Dikkat kontrolü"}


@router.get("/{ogrenci_id}/cevap-analizi")
def cevap_analizi(ogrenci_id: str, tur_no: int | None = Query(None), db: Session = Depends(get_db),
                  admin: AdminKullanici = Depends(get_mevcut_admin)):
    try:
        o = db.get(Ogrenci, uuid.UUID(ogrenci_id))
    except ValueError:
        o = None
    if o is None:
        raise HTTPException(status_code=404, detail="Öğrenci bulunamadı.")

    turlar = (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id)
              .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).all())
    if not turlar:
        return {"turlar": [], "tur": None, "cevaplar": [], "ozellikler": [], "etki": [], "not": "Öğrenci teste henüz başlamadı."}
    tur = next((t for t in turlar if t.tur_no == tur_no), turlar[0])

    cevaplar = (db.query(OgrenciCevap).filter(OgrenciCevap.ogrenci_id == o.id, OgrenciCevap.tur_id == tur.id)
                .order_by(OgrenciCevap.cevap_zamani, OgrenciCevap.id).all())
    sorular = {s.id: s for s in db.query(Soru).filter(Soru.id.in_([c.soru_id for c in cevaplar] or [-1])).all()}
    onb = puanlama_onbellegi(db, list(sorular))
    katmanlar = {k.id: k for k in db.query(Katman).all()}
    degiskenler = {d.id: d for d in db.query(Degisken).all()}
    dallar = {d.id: d.ad for d in db.query(Dal).all()}

    def ozellik(did):
        d = degiskenler.get(did)
        if d is None:
            return {"id": did, "kod": "?", "ad": "?"}
        k = katmanlar.get(d.katman_id)
        return {"id": did, "kod": d.kod, "ad": d.ad, "katman": k.kod if k else None,
                "dal": dallar.get(d.dal_id) if d.dal_id else None}

    satirlar, katkilar_of = [], {}
    for sira, c in enumerate(cevaplar, start=1):
        s = sorular.get(c.soru_id)
        if s is None:
            continue
        secenekler = sorted(onb["soru_secenekleri"].get(s.id, []), key=lambda x: x.secenek_sirasi)
        katki = cevaplari_puanla(db, {s.id: s}, [c], onb) if s.soru_tipi != "kontrol" else {}
        katki_listesi = []
        for did, puanlar in katki.items():
            p = round(sum(puanlar) / len(puanlar), 1)
            katki_listesi.append({**ozellik(did), "puan": p})
            katkilar_of.setdefault(did, []).append({"sira": sira, "puan": p})
        katki_listesi.sort(key=lambda x: -abs(x["puan"] - 50))
        secilen = onb["secenek"].get(c.secenek_id)
        kontrol = None
        if s.soru_tipi == "kontrol":
            kontrol = {"beklenen": s.beklenen_secenek_sira, "verilen": secilen.secenek_sirasi if secilen else None,
                       "dogru": bool(secilen and s.beklenen_secenek_sira == secilen.secenek_sirasi)}
        k = katmanlar.get(s.katman_id)
        satirlar.append({
            "sira": sira, "soru_id": s.id, "katman": k.kod if k else "?", "katman_ad": k.ad if k else "?",
            "tip": s.soru_tipi, "tip_ad": TIP_ADI.get(s.soru_tipi, s.soru_tipi),
            "cevap_bicimi": s.cevap_bicimi, "ters": bool(s.ters_kodlanmis_mi), "soru": s.soru_metni,
            "secenekler": [{"id": x.id, "sira": x.secenek_sirasi, "metin": x.secenek_metni,
                            "secildi": x.id == c.secenek_id, "en_az": x.id == c.en_az_secenek_id} for x in secenekler],
            "katkilar": katki_listesi, "kontrol": kontrol, "zaman": c.cevap_zamani,
        })

    # Özellik özeti: kayıtlı puan + katkı veren cevaplar
    kayitli = {x.degisken_id: float(x.puan) for x in db.query(OgrenciDegiskenSkoru).filter(
        OgrenciDegiskenSkoru.ogrenci_id == o.id, OgrenciDegiskenSkoru.tur_id == tur.id).all()}
    ozellikler = []
    for did in sorted(set(kayitli) | set(katkilar_of), key=lambda d: (degiskenler[d].katman_id if d in degiskenler else 0,
                                                                      degiskenler[d].sira if d in degiskenler else 0)):
        k = katkilar_of.get(did, [])
        ozellikler.append({**ozellik(did), "puan": kayitli.get(did),
                           "hesaplanan": round(sum(x["puan"] for x in k) / len(k), 1) if k else None,
                           "cevap_sayisi": len(k), "cevaplar": [x["sira"] for x in k]})

    # Sonuca etkisi
    etki, not_metni = [], None
    if tur.durum == "tamamlandi":
        try:
            from app.core.skor_motoru import girdi_hazirla, siralama_getir
            girdi = girdi_hazirla(db, o, tur)
            sira_listesi = siralama_getir(db, o, tur, 5)
            if girdi is not None:
                satir_of = {b: i for i, b in enumerate(girdi.bolum_idler)}
                ort = girdi.performans.mean(axis=0)
                for st in sira_listesi:
                    i = satir_of.get(st.bolum_id)
                    if i is None:
                        continue
                    fark = girdi.agirliklar * (girdi.performans[i] - ort)   # uyum puanına katkının bölüm ortalamasına göre farkı (puan)
                    sirali = np.argsort(fark)
                    def kalem(j):
                        did = girdi.degisken_idler[j]
                        return {**ozellik(did), "etki": round(float(fark[j]), 2), "ogrenci_puan": kayitli.get(did),
                                "bolum_beklenti": round(float(girdi.bolum_olcekli[i][j]), 1),
                                "ogrenci_olcekli": round(float(girdi.ogrenci_olcekli[j]), 1),
                                "uyum": round(float(girdi.performans[i][j]), 1)}
                    etki.append({
                        "bolum_id": st.bolum_id, "bolum": girdi.bolum_adlari.get(st.bolum_id), "uyum": round(st.toplam_uyum, 1),
                        "yukari": [kalem(j) for j in sirali[::-1][:5] if fark[j] > 0],
                        "asagi": [kalem(j) for j in sirali[:3] if fark[j] < 0],
                    })
        except Exception as e:  # analiz sonucu göstermeyi engellemesin
            db.rollback()
            not_metni = f"Sonuç etkisi hesaplanamadı: {type(e).__name__}"
    else:
        not_metni = "Tur tamamlanmadığı için bölüm sonuçları henüz hesaplanmadı."

    denetim_yaz(db, admin, "cevap_analizi_goruntule", "ogrenciler", o.id, f"{o.ad_soyad}: {tur.tur_no}. tur cevapları görüntülendi", o.okul_id)
    db.commit()
    return {
        "turlar": [{"tur_no": t.tur_no, "durum": t.durum} for t in turlar],
        "tur": {"tur_no": tur.tur_no, "durum": tur.durum, "baslama": tur.baslama_zamani, "tamamlanma": tur.tamamlanma_zamani},
        "cevaplar": satirlar, "ozellikler": ozellikler, "etki": etki, "not": not_metni,
    }
