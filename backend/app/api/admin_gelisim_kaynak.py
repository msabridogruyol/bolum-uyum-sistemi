# -*- coding: utf-8 -*-
"""
Admin — Gelişim Kaynak Havuzu Yönetimi

Bağımsız router. gelisim_kaynak_onerileri tablosundaki kitap/film/rol
model/psikolojik yaklaşım/aktivite önerilerini arayıp, düzenleyip, yeni
ekleyip, silmeyi sağlar (Soru Bankası'yla aynı desen: arama + tıkla-düzenle).

GET    /admin/gelisim-kaynak              — filtrelenmiş liste
GET    /admin/gelisim-kaynak/degiskenler  — filtre menüsü için katmana göre değişken listesi
POST   /admin/gelisim-kaynak              — yeni kaynak ekle
PUT    /admin/gelisim-kaynak/{id}         — mevcut kaynağı güncelle
DELETE /admin/gelisim-kaynak/{id}         — kaynağı sil
"""
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.api.deps import get_mevcut_admin
from app.models import AdminKullanici, Degisken, Katman, GelisimKaynakOnerisi

router = APIRouter(prefix="/gelisim-kaynak", tags=["admin-gelisim-kaynak"])

ARALIKLAR = ["belirgin_ustun", "ustun", "beklenti", "altinda", "belirgin_altinda"]
KAYNAK_TIPLERI = ["kitap", "film", "rol_model", "psikolojik_yaklasim", "aktivite"]


class KaynakOut(BaseModel):
    id: int
    degisken_kod: str
    degisken_adi: str
    katman_kod: str
    aralik: str
    kaynak_tipi: str
    baslik: str
    aciklama: str
    sira: int


class KaynakYaziIstek(BaseModel):
    degisken_kod: str
    aralik: str
    kaynak_tipi: str
    baslik: str
    aciklama: str
    sira: int = 1


class KaynakGuncelleIstek(BaseModel):
    aralik: str | None = None
    kaynak_tipi: str | None = None
    baslik: str | None = None
    aciklama: str | None = None
    sira: int | None = None


class DegiskenFiltreOut(BaseModel):
    kod: str
    ad: str


def _dogrula(alan: str, deger: str, gecerliler: list[str]):
    if deger not in gecerliler:
        raise HTTPException(status_code=400, detail=f"Geçersiz {alan}: {deger}. Geçerli değerler: {', '.join(gecerliler)}")


@router.get("/degiskenler", response_model=list[DegiskenFiltreOut])
def degiskenleri_listele(
    katman_kod: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sorgu = db.query(Degisken.kod, Degisken.ad)
    if katman_kod:
        sorgu = sorgu.join(Katman, Katman.id == Degisken.katman_id).filter(Katman.kod == katman_kod)
    satirlar = sorgu.order_by(Degisken.kod).all()
    return [DegiskenFiltreOut(kod=k, ad=a) for k, a in satirlar]


@router.get("", response_model=list[KaynakOut])
def kaynaklari_listele(
    katman_kod: str | None = None,
    degisken_kod: str | None = None,
    aralik: str | None = None,
    kaynak_tipi: str | None = None,
    arama: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sorgu = (
        db.query(GelisimKaynakOnerisi, Degisken.kod, Degisken.ad, Katman.kod)
        .join(Degisken, Degisken.id == GelisimKaynakOnerisi.degisken_id)
        .join(Katman, Katman.id == Degisken.katman_id)
    )
    if katman_kod:
        sorgu = sorgu.filter(Katman.kod == katman_kod)
    if degisken_kod:
        sorgu = sorgu.filter(Degisken.kod == degisken_kod)
    if aralik:
        sorgu = sorgu.filter(GelisimKaynakOnerisi.aralik == aralik)
    if kaynak_tipi:
        sorgu = sorgu.filter(GelisimKaynakOnerisi.kaynak_tipi == kaynak_tipi)
    if arama and arama.strip():
        sorgu = sorgu.filter(GelisimKaynakOnerisi.baslik.ilike(f"%{arama.strip()}%"))

    satirlar = sorgu.order_by(Katman.kod, Degisken.kod, GelisimKaynakOnerisi.aralik, GelisimKaynakOnerisi.sira).all()
    return [
        KaynakOut(
            id=k.id, degisken_kod=dk, degisken_adi=da, katman_kod=kk,
            aralik=k.aralik, kaynak_tipi=k.kaynak_tipi, baslik=k.baslik, aciklama=k.aciklama, sira=k.sira,
        )
        for k, dk, da, kk in satirlar
    ]


@router.post("", response_model=KaynakOut)
def kaynak_ekle(
    istek: KaynakYaziIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    _dogrula("aralik", istek.aralik, ARALIKLAR)
    _dogrula("kaynak_tipi", istek.kaynak_tipi, KAYNAK_TIPLERI)

    degisken = db.query(Degisken).filter(Degisken.kod == istek.degisken_kod).first()
    if degisken is None:
        raise HTTPException(status_code=404, detail=f"Değişken bulunamadı: {istek.degisken_kod}")
    if not istek.baslik.strip() or not istek.aciklama.strip():
        raise HTTPException(status_code=400, detail="Başlık ve açıklama boş olamaz.")

    yeni = GelisimKaynakOnerisi(
        degisken_id=degisken.id, aralik=istek.aralik, kaynak_tipi=istek.kaynak_tipi,
        baslik=istek.baslik.strip(), aciklama=istek.aciklama.strip(), sira=istek.sira,
    )
    db.add(yeni)
    db.commit()
    db.refresh(yeni)

    katman = db.get(Katman, degisken.katman_id)
    return KaynakOut(
        id=yeni.id, degisken_kod=degisken.kod, degisken_adi=degisken.ad, katman_kod=katman.kod,
        aralik=yeni.aralik, kaynak_tipi=yeni.kaynak_tipi, baslik=yeni.baslik, aciklama=yeni.aciklama, sira=yeni.sira,
    )


@router.put("/{kaynak_id}", status_code=204)
def kaynak_guncelle(
    kaynak_id: int,
    istek: KaynakGuncelleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    kaynak = db.get(GelisimKaynakOnerisi, kaynak_id)
    if kaynak is None:
        raise HTTPException(status_code=404, detail="Kaynak bulunamadı.")

    if istek.aralik is not None:
        _dogrula("aralik", istek.aralik, ARALIKLAR)
        kaynak.aralik = istek.aralik
    if istek.kaynak_tipi is not None:
        _dogrula("kaynak_tipi", istek.kaynak_tipi, KAYNAK_TIPLERI)
        kaynak.kaynak_tipi = istek.kaynak_tipi
    if istek.baslik is not None:
        if not istek.baslik.strip():
            raise HTTPException(status_code=400, detail="Başlık boş olamaz.")
        kaynak.baslik = istek.baslik.strip()
    if istek.aciklama is not None:
        if not istek.aciklama.strip():
            raise HTTPException(status_code=400, detail="Açıklama boş olamaz.")
        kaynak.aciklama = istek.aciklama.strip()
    if istek.sira is not None:
        kaynak.sira = istek.sira

    db.commit()


@router.delete("/{kaynak_id}", status_code=204)
def kaynak_sil(
    kaynak_id: int,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    kaynak = db.get(GelisimKaynakOnerisi, kaynak_id)
    if kaynak is None:
        raise HTTPException(status_code=404, detail="Kaynak bulunamadı.")
    db.delete(kaynak)
    db.commit()
