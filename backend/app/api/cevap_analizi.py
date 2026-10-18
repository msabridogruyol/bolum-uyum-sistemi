# -*- coding: utf-8 -*-
"""
[2026-10-09] Öğrenci cevap analizi. [2026-10-17] Süper admin VE okul yetkilisi (yalnızca kendi okulunun öğrencisi;
her görüntüleme / indirme işlem kaydına yazılır). Öğrenci bu ekranı görmez.

GET /yonetim/ogrenci/{ogrenci_id}/cevap-analizi?tur_no=&bolumler=1,2,3
GET /yonetim/ogrenci/{ogrenci_id}/cevap-analizi.xlsx?tur_no=      (tüm matrisler, Excel)

Cevap matrisi: öğrencinin bir turdaki her cevabı: soru, tüm şıklar (seçilen / en az uyan işaretli), bu cevabın hangi
özelliğe kaç puan kattığı (katman tamamlanırken kullanılan puanlama kuralının AYNISI: katman_servisi.cevaplari_puanla),
kontrol sorularında beklenen–verilen. Özellik özeti: özellik puanı = o özelliğe katkı veren cevapların ortalaması.
Uyum matrisi ve katkılar: core/uyum_aciklama ("bu özellik olmasaydı" katkısı; gösterilen puanla aynı hesap).
Yöntem matrisi (10 ÇKKV yöntemi + Kendall W) yalnızca süper admine döner.
"""
import re
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_yonetimi import _ogrenci_kapsami
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.katman_servisi import cevaplari_puanla, puanlama_onbellegi
from app.models import (
    AdminKullanici,
    Dal,
    Degisken,
    Katman,
    Ogrenci,
    OgrenciCevap,
    OgrenciDegerlendirmeTuru,
    OgrenciDegiskenSkoru,
    Soru,
)

router = APIRouter(prefix="/yonetim/ogrenci", tags=["Cevap analizi (süper admin + okul yetkilisi)"])

TIP_ADI = {"likert": "Likert", "sjt": "Durum sorusu", "kutup": "İki uç", "kontrol": "Dikkat kontrolü"}
OKUMA_NOTU = ("Uyum puanı göreli: 301 bölüm içinde öğrencinin profiline yakınlık (100 = en yakın, 0 = en uzak). "
              "Katkı = bu özellik olmasaydı puan ne kadar değişirdi (artı: yükseltiyor, eksi: düşürüyor); katkı da göreli "
              "olduğundan, farkı olan bir özellik öğrenci o özellikte bu bölüme diğer bölümlerin çoğundan daha yakınsa artı çıkabilir. "
              "Fark = öğrenci − bölüm beklentisi (katman içi ölçek); |fark| < 5 uyumlu, 5–15 fazla / az, 15+ belirgin.")


def _ogrenci_ve_tur(db: Session, yon: AdminKullanici, ogrenci_id: str, tur_no: int | None):
    o = _ogrenci_kapsami(db, yon, ogrenci_id)   # okul yetkilisi yalnızca kendi okulu (403)
    turlar = (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == o.id)
              .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).all())
    tur = next((t for t in turlar if t.tur_no == tur_no), turlar[0]) if turlar else None
    return o, turlar, tur


def _cevaplar_ve_ozellikler(db: Session, o: Ogrenci, tur: OgrenciDegerlendirmeTuru):
    """Cevap matrisi (soru × özellik katkısı) ve özellik özeti; ekran ve Excel ortak kullanır."""
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
            "uc_a": s.uc_a_metni, "uc_b": s.uc_b_metni,   # [2026-10-18] uçlar sorusunda iki ucun metni
            "secenekler": [{"id": x.id, "sira": x.secenek_sirasi, "metin": x.secenek_metni,
                            "secildi": x.id == c.secenek_id, "en_az": x.id == c.en_az_secenek_id} for x in secenekler],
            "katkilar": katki_listesi, "kontrol": kontrol, "zaman": c.cevap_zamani,
        })

    kayitli = {x.degisken_id: float(x.puan) for x in db.query(OgrenciDegiskenSkoru).filter(
        OgrenciDegiskenSkoru.ogrenci_id == o.id, OgrenciDegiskenSkoru.tur_id == tur.id).all()}
    ozellikler = []
    for did in sorted(set(kayitli) | set(katkilar_of), key=lambda d: (degiskenler[d].katman_id if d in degiskenler else 0,
                                                                      degiskenler[d].sira if d in degiskenler else 0)):
        k = katkilar_of.get(did, [])
        ozellikler.append({**ozellik(did), "puan": kayitli.get(did),
                           "hesaplanan": round(sum(x["puan"] for x in k) / len(k), 1) if k else None,
                           "cevap_sayisi": len(k), "cevaplar": [x["sira"] for x in k]})
    return satirlar, ozellikler


@router.get("/{ogrenci_id}/cevap-analizi")
def cevap_analizi(ogrenci_id: str, tur_no: int | None = Query(None), bolumler: str | None = Query(None),
                  db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    o, turlar, tur = _ogrenci_ve_tur(db, yon, ogrenci_id, tur_no)
    if tur is None:
        return {"turlar": [], "tur": None, "cevaplar": [], "ozellikler": [], "matris": None, "not": "Öğrenci teste henüz başlamadı."}
    satirlar, ozellikler = _cevaplar_ve_ozellikler(db, o, tur)

    matris, not_metni = None, None
    if tur.durum == "tamamlandi":
        try:
            from app.core.uyum_aciklama import hedef_kiyasi, uyum_matrisi
            secim = [int(x) for x in re.findall(r"\d+", bolumler or "")][:30] or None
            matris = uyum_matrisi(db, o, tur, secim, yontem=yon.rol == "super_admin")
            if matris is not None:
                matris["kiyas"] = hedef_kiyasi(matris)   # [2026-10-17] hedef bölüm kıyası (raporla aynı hesap)
            if matris is None:
                not_metni = "Öğrencinin profili eksik olduğu için bölüm uyumu hesaplanamadı."
        except Exception as e:  # analiz cevapları göstermeyi engellemesin
            db.rollback()
            not_metni = f"Bölüm uyumu açıklaması hesaplanamadı: {type(e).__name__}"
    else:
        not_metni = "Tur tamamlanmadığı için bölüm sonuçları henüz hesaplanmadı."

    denetim_yaz(db, yon, "cevap_analizi_goruntule", "ogrenciler", o.id, f"{o.ad_soyad}: {tur.tur_no}. tur cevapları görüntülendi", o.okul_id)
    db.commit()
    return {
        "turlar": [{"tur_no": t.tur_no, "durum": t.durum} for t in turlar],
        "tur": {"tur_no": tur.tur_no, "durum": tur.durum, "baslama": tur.baslama_zamani, "tamamlanma": tur.tamamlanma_zamani},
        "cevaplar": satirlar, "ozellikler": ozellikler, "matris": matris, "okuma_notu": OKUMA_NOTU, "not": not_metni,
    }


def _dosya_adi(*parcalar) -> str:
    metin = "_".join(str(p) for p in parcalar if p)
    metin = metin.translate(str.maketrans("çğıöşüÇĞİÖŞÜ", "cgiosuCGIOSU"))
    metin = unicodedata.normalize("NFKD", metin).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", metin).strip("_")[:120]


@router.get("/{ogrenci_id}/cevap-analizi.xlsx")
def cevap_analizi_excel(ogrenci_id: str, tur_no: int | None = Query(None),
                        db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """Tüm matrisler: cevaplar (soru × özellik), özellikler, uyum (bölüm × özellik farkı), katkılar, bölüm beklentileri;
    süper admin için ayrıca 10 yöntem + Kendall W."""
    from app.core.rapor.uyum_excel import cevap_analizi_xlsx
    from app.core.uyum_aciklama import tam_matris
    o, _turlar, tur = _ogrenci_ve_tur(db, yon, ogrenci_id, tur_no)
    if tur is None:
        raise HTTPException(status_code=404, detail="Öğrencinin değerlendirme kaydı yok.")
    satirlar, ozellikler = _cevaplar_ve_ozellikler(db, o, tur)
    tam = tam_matris(db, o, tur) if tur.durum == "tamamlandi" else None
    icerik = cevap_analizi_xlsx(db, o, tur, satirlar, ozellikler, tam, yontem=yon.rol == "super_admin", not_metni=OKUMA_NOTU)
    denetim_yaz(db, yon, "cevap_analizi_indir", "ogrenciler", o.id, f"{o.ad_soyad}: {tur.tur_no}. tur cevap ve uyum matrisleri indirildi (Excel)", o.okul_id)
    db.commit()
    ad = _dosya_adi("Cevap_ve_Uyum_Matrisi", o.ad_soyad, f"tur{tur.tur_no}")
    return Response(content=icerik, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f'attachment; filename="{ad}.xlsx"', "Cache-Control": "no-store"})

