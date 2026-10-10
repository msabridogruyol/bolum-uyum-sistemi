"""
Bölüm F — Koçluk modülü uç noktaları.
POST /koclugu/hedef              — hedef seç/değiştir (onay akışı, F8)
GET  /koclugu/hedef               — aktif hedefi getir
GET  /koclugu/hedef/durum         — aktif hedef + kalan değiştirme hakkı (Ayarlar)
GET  /koclugu/hedef/kaynaklar     — odak/güçlü alanlara uygun kitap, film, ilham veren kişi, olay, aktivite önerileri
GET  /koclugu/hedef/gelisim       — gap analizi + gelişim kartları (F2-F3)
GET  /koclugu/hedef/yol-haritasi  — 3 aşamalı gelişim planı (F4)
POST /koclugu/hedef/aksiyon       — bir gelişim aksiyonunun durumunu güncelle (F4.2)
GET  /koclugu/karsilastirma       — tur bazlı önceki/güncel karşılaştırma (F5)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.core.katman_servisi import IsKuraliHatasi, son_tur_getir
from app.core.koclugu_servisi import (
    aktif_hedef_getir, hedef_sec, gap_analizi_hesapla, yol_haritasi_olustur,
    aksiyon_durumu_guncelle, tur_karsilastirmasi_hesapla,
    gelisim_plani_olustur, adim_durumu_guncelle, HedefHakkiBitti, hedef_hak_durumu,
)
from app.core.gelisim_icerigi import ICERIK
from app.models import Ogrenci, Bolum, Katman, OgrenciGelisimAksiyonDurumu
from app.core.dal_servisi import bekleyen_dal_var_mi
from app.schemas.koclugu import (
    HedefSecIstek, AktifHedefOut, HedefDurumOut, GapSatiriOut, YolHaritasiOut,
    AksiyonDurumIstek, KarsilastirmaSatiriOut,
    GelisimPlaniOut, AdimDurumIstek,
)

from app.core.paketler import ogrenci_modulu as _om   # [2026-10-10] paket koruması
_KOCLUK = _om("kocluk")
router = APIRouter()


def _hedef_out(db: Session, ogrenci: Ogrenci, hedef) -> AktifHedefOut:
    bolum = db.get(Bolum, hedef.bolum_id)
    return AktifHedefOut(bolum_id=hedef.bolum_id, bolum_adi=bolum.ad, secim_zamani=hedef.secim_zamani.isoformat(),
                         **hedef_hak_durumu(ogrenci))


@router.post("/hedef", response_model=AktifHedefOut)
def hedefi_sec(
    istek: HedefSecIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    try:
        hedef = hedef_sec(db, ogrenci, istek.bolum_id, onay=istek.onay)
    except HedefHakkiBitti as e:
        db.rollback()
        raise HTTPException(status_code=403, detail=str(e))
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=409, detail=str(e))  # 409 — onay gerektiren çakışma
    db.commit()
    return _hedef_out(db, ogrenci, hedef)


@router.get("/hedef", response_model=AktifHedefOut | None)
def aktif_hedefi_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        return None
    return _hedef_out(db, ogrenci, hedef)


@router.get("/hedef/durum", response_model=HedefDurumOut)
def hedef_durumu(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    hedef = aktif_hedef_getir(db, ogrenci)
    return HedefDurumOut(hedef=_hedef_out(db, ogrenci, hedef) if hedef else None, **hedef_hak_durumu(ogrenci))


def _gap_satirlarini_hazirla(db: Session, ogrenci: Ogrenci):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        raise HTTPException(status_code=400, detail="Henüz bir hedef bölümün yok.")
    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi as e:
        raise HTTPException(status_code=400, detail=str(e))
    if tur.durum != "tamamlandi":
        raise HTTPException(status_code=400, detail="K1-K4 tamamlanmadan gelişim analizi hesaplanamaz.")
    # [2026-10-03] Sonuç ekranıyla aynı kural: açılan alan (K5) soruları bitmeden koçluk analizi gösterilmez
    if bekleyen_dal_var_mi(db, ogrenci, tur):
        raise HTTPException(status_code=409, detail="Koçluk analizinin hazırlanması için önce sana açılan alan (K5) sorularını tamamlamalısın.")
    satirlar = gap_analizi_hesapla(db, ogrenci, tur, hedef.bolum_id)
    katmanlar = {k.id: k for k in db.query(Katman).all()}
    durumlar = {
        a.degisken_id: a.durum
        for a in db.query(OgrenciGelisimAksiyonDurumu).filter(
            OgrenciGelisimAksiyonDurumu.ogrenci_id == ogrenci.id,
            OgrenciGelisimAksiyonDurumu.hedef_bolum_id == hedef.bolum_id,
        ).all()
    }
    for s in satirlar:
        k = katmanlar.get(s.degisken.katman_id)
        s.katman_kod, s.katman_adi = (k.kod, k.ad) if k else (None, None)
        s.aksiyon_durumu = durumlar.get(s.degisken.id)
    return satirlar


def _gap_satiri_to_out(s) -> GapSatiriOut:
    kart = s.gelisim_karti
    return GapSatiriOut(
        degisken_id=s.degisken.id, degisken_kod=s.degisken.kod, degisken_adi=s.degisken.ad,
        katman_kod=getattr(s, "katman_kod", None), katman_adi=getattr(s, "katman_adi", None),
        ogrenci_goreli=round(getattr(s, "ogrenci_goreli", s.ogrenci_puan), 1),
        bolum_goreli=round(getattr(s, "bolum_goreli", s.bolum_beklenen), 1),
        aksiyon_durumu=getattr(s, "aksiyon_durumu", None),
        nedir=ICERIK.get(s.degisken.kod, {}).get("nedir") or s.degisken.aciklama,
        ogrenci_puan=s.ogrenci_puan, bolum_beklenen=s.bolum_beklenen,
        gap=round(s.gap, 2), kategori=s.kategori, oncelik_skoru=round(s.oncelik_skoru, 2),
        durum_tespiti=kart.durum_tespiti if kart else None,
        aksiyon_onerisi=kart.aksiyon_onerisi if kart else None,
        kaynak_tipi=kart.kaynak_tipi if kart else None,
        tahmini_efor=kart.tahmini_efor if kart else None,
    )


@router.get("/hedef/gelisim", dependencies=[Depends(_KOCLUK)], response_model=list[GapSatiriOut])
def gelisim_analizi_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    satirlar = _gap_satirlarini_hazirla(db, ogrenci)
    return [_gap_satiri_to_out(s) for s in satirlar]


@router.get("/hedef/yol-haritasi", dependencies=[Depends(_KOCLUK)], response_model=YolHaritasiOut)
def yol_haritasini_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    satirlar = _gap_satirlarini_hazirla(db, ogrenci)
    harita = yol_haritasi_olustur(satirlar)
    return YolHaritasiOut(**{k: [_gap_satiri_to_out(s) for s in v] for k, v in harita.items()})


@router.post("/hedef/aksiyon/{degisken_id}", dependencies=[Depends(_KOCLUK)], status_code=204)
def aksiyon_durumunu_guncelle(
    degisken_id: int,
    istek: AksiyonDurumIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        raise HTTPException(status_code=400, detail="Henüz bir hedef bölümün yok.")
    try:
        aksiyon_durumu_guncelle(db, ogrenci, hedef.bolum_id, degisken_id, istek.durum)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()


@router.get("/karsilastirma", dependencies=[Depends(_KOCLUK)], response_model=list[KarsilastirmaSatiriOut] | None)
def tur_karsilastirmasini_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """F5.4 — ilk tur davranışı: en az 2 tamamlanmış tur yoksa null döner (frontend F5'i gizler)."""
    satirlar = tur_karsilastirmasi_hesapla(db, ogrenci)
    if satirlar is None:
        return None
    return [
        KarsilastirmaSatiriOut(
            degisken_id=s.degisken.id, degisken_adi=s.degisken.ad,
            eski_puan=s.eski_puan, yeni_puan=s.yeni_puan, degisim=round(s.degisim, 2),
            trend=s.trend, yorum_metni=s.yorum.yorum_metni if s.yorum else None,
        )
        for s in satirlar
    ]


# ============================= [2026-10-03] Detaylı gelişim planı ============================= #

@router.get("/hedef/plan", dependencies=[Depends(_KOCLUK)], response_model=GelisimPlaniOut)
def gelisim_planini_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """3 odak alan × 3 aşama yol haritası + güçlü yön adımları + sıradaki adım."""
    satirlar = _gap_satirlarini_hazirla(db, ogrenci)
    hedef = aktif_hedef_getir(db, ogrenci)
    return GelisimPlaniOut(**gelisim_plani_olustur(db, ogrenci, hedef.bolum_id, satirlar))


@router.post("/hedef/adim/{adim_kodu}", dependencies=[Depends(_KOCLUK)], status_code=204)
def adim_durumunu_guncelle(
    adim_kodu: str,
    istek: AdimDurumIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        raise HTTPException(status_code=400, detail="Henüz bir hedef bölümün yok.")
    try:
        adim_durumu_guncelle(db, ogrenci, hedef.bolum_id, adim_kodu, istek.durum)
        if istek.durum == "tamamlandi":
            from app.core.kocluk_motoru import geri_bildirim_kaydet
            geri_bildirim_kaydet(db, ogrenci, hedef.bolum_id, adim_kodu, istek)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()


# [2026-10-10] Alan tekrar ölçümü: ilk değerlendirmedeki aynı sorulardan en fazla 5'i yeniden sorulur.
@router.get("/hedef/olcum/{degisken_id}", dependencies=[Depends(_KOCLUK)])
def alan_olcum_sorulari(degisken_id: int, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.kocluk_motoru import olcum_sorulari
    try:
        return olcum_sorulari(db, ogrenci, degisken_id)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/hedef/olcum/{degisken_id}", dependencies=[Depends(_KOCLUK)])
def alan_olcum_kaydet(degisken_id: int, istek: dict, db: Session = Depends(get_db),
                      ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.core.kocluk_motoru import olcum_kaydet
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        raise HTTPException(status_code=400, detail="Henüz bir hedef bölümün yok.")
    # Ölçüm yalnızca planındaki bir odak alanında ve 3 adım kuralıyla açıldıysa kaydedilir
    try:
        plan = gelisim_plani_olustur(db, ogrenci, hedef.bolum_id, _gap_satirlarini_hazirla(db, ogrenci))
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=400, detail="Planın hesaplanamadı.")
    odak = next((o for o in plan.get("odak_alanlari", []) if o["degisken_id"] == degisken_id), None)
    if not odak or not (odak.get("olcum") or {}).get("acik"):
        raise HTTPException(status_code=400, detail="Bu alanda ölçüm henüz açılmadı.")
    try:
        sonuc = olcum_kaydet(db, ogrenci, degisken_id, hedef.bolum_id if hedef else None, istek.get("cevaplar") or [])
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()
    return sonuc


# [2026-10-09] İlham kaynakları: yönetimdeki "Gelişim Kaynak Havuzu" (kitap / film / rol model / psikolojik yaklaşım /
# aktivite / önemli olay) öğrencinin koçluk planındaki odak (gelişim) ve güçlü yön alanlarına göre seçilir.
# Önce o özelliğin TAM aralığı (ör. belirgin_altinda), yoksa aynı yöndeki komşu aralık kullanılır.
KOMSU_ARALIK = {
    "belirgin_altinda": ["belirgin_altinda", "altinda"], "altinda": ["altinda", "belirgin_altinda"],
    "belirgin_ustun": ["belirgin_ustun", "ustun"], "ustun": ["ustun", "belirgin_ustun"], "beklenti": ["beklenti"],
}
ALAN_BASINA = 4


@router.get("/hedef/kaynaklar", dependencies=[Depends(_KOCLUK)])
def ilham_kaynaklari(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    from app.models import GelisimKaynakOnerisi
    satirlar = _gap_satirlarini_hazirla(db, ogrenci)
    hedef = aktif_hedef_getir(db, ogrenci)
    plan = gelisim_plani_olustur(db, ogrenci, hedef.bolum_id, satirlar)
    alanlar = [{**{k: o[k] for k in ("degisken_id", "degisken_kod", "degisken_adi", "kategori")}, "grup": "gelisim"}
               for o in plan["odak_alanlari"]]
    alanlar += [{**{k: g[k] for k in ("degisken_id", "degisken_kod", "degisken_adi", "kategori")}, "grup": "guclu"}
                for g in plan["guclu_yonler"]]
    if not alanlar:
        return {"alanlar": []}
    havuz = (db.query(GelisimKaynakOnerisi)
             .filter(GelisimKaynakOnerisi.degisken_id.in_([a["degisken_id"] for a in alanlar]))
             .order_by(GelisimKaynakOnerisi.sira, GelisimKaynakOnerisi.id).all())
    sonuc = []
    for a in alanlar:
        secilen = []
        for aralik in KOMSU_ARALIK.get(a["kategori"], [a["kategori"]]):
            secilen += [k for k in havuz if k.degisken_id == a["degisken_id"] and k.aralik == aralik and k not in secilen]
            if len(secilen) >= ALAN_BASINA:
                break
        if not secilen:   # [2026-10-09] aynı yönde kaynak yoksa o özelliğin diğer kaynakları (konu aynı)
            secilen = [k for k in havuz if k.degisken_id == a["degisken_id"]]
        if secilen:
            sonuc.append({**a, "kaynaklar": [{"id": k.id, "tip": k.kaynak_tipi, "baslik": k.baslik, "aciklama": k.aciklama}
                                             for k in secilen[:ALAN_BASINA]]})
    toplam = db.query(GelisimKaynakOnerisi).count()
    return {"hedef_bolum_adi": plan["hedef_bolum_adi"], "alanlar": sonuc, "havuz_toplam": toplam,
            "aranan_alanlar": [a["degisken_adi"] for a in alanlar]}


# [2026-10-10] Gelişimim: tamamlanan adımların zaman çizelgesi + son 8 haftanın görev serisi + özet sayılar.
# Hedef değişse de geçmiş adımlar silinmez; her adım hangi hedef bölüm için yapıldığıyla döner.
@router.get("/gelisimim", dependencies=[Depends(_KOCLUK)])
def gelisimim(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    from datetime import date, timedelta
    from app.models import OgrenciGelisimAdimDurumu, OgrenciHaftalikGorev, Degisken

    ad_of = {d.kod: d.ad for d in db.query(Degisken).all()}
    bolum_of = {b.id: b.ad for b in db.query(Bolum).all()}

    def adim_bilgi(kod: str) -> tuple[str, str]:
        try:
            dk, grup, sira = kod.split("-")
            ham = ICERIK[dk]["gelisim" if grup == "G" else "guclu"][int(sira) - 1]
            return ham[1], ad_of.get(dk, dk)
        except Exception:
            return kod, ""

    tamam = (db.query(OgrenciGelisimAdimDurumu)
             .filter(OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id, OgrenciGelisimAdimDurumu.durum == "tamamlandi")
             .order_by(OgrenciGelisimAdimDurumu.guncelleme_zamani.desc()).all())
    adimlar = []
    for a in tamam:
        baslik, ozellik = adim_bilgi(a.adim_kodu)
        adimlar.append({"kod": a.adim_kodu, "baslik": baslik, "ozellik": ozellik, "guclu_yon": "-U-" in a.adim_kodu,
                        "bolum": bolum_of.get(a.hedef_bolum_id), "zaman": a.guncelleme_zamani})

    # Son 8 hafta (Pazartesi başlangıçlı): tamamlanan görev + adım sayısı
    bugun = date.today()
    bu_pzt = bugun - timedelta(days=bugun.weekday())
    haftalar = [bu_pzt - timedelta(weeks=i) for i in range(7, -1, -1)]
    gorevler = (db.query(OgrenciHaftalikGorev)
                .filter(OgrenciHaftalikGorev.ogrenci_id == ogrenci.id, OgrenciHaftalikGorev.hafta_baslangic >= haftalar[0]).all())
    seri = []
    for h in haftalar:
        hg = [g for g in gorevler if g.hafta_baslangic == h]
        adim_say = sum(1 for a in tamam if a.guncelleme_zamani and h <= a.guncelleme_zamani.date() < h + timedelta(days=7))
        seri.append({"hafta": h.isoformat(), "gorev_tamam": sum(1 for g in hg if g.durum == "tamamlandi"),
                     "gorev_toplam": len(hg), "adim": adim_say})
    # Kesintisiz aktif hafta serisi (bu haftadan geriye; bu hafta henüz boşsa geçen haftadan başlar)
    aktif = [s["gorev_tamam"] + s["adim"] > 0 for s in seri]
    if aktif and not aktif[-1]:
        aktif = aktif[:-1]
    ust_uste = 0
    for x in reversed(aktif):
        if not x:
            break
        ust_uste += 1

    return {
        "adimlar": adimlar,
        "haftalar": seri,
        "ozet": {"tamamlanan_adim": len(adimlar),
                 "tamamlanan_gorev": db.query(OgrenciHaftalikGorev).filter(OgrenciHaftalikGorev.ogrenci_id == ogrenci.id,
                                                                          OgrenciHaftalikGorev.durum == "tamamlandi").count(),
                 "ust_uste_hafta": ust_uste},
    }
