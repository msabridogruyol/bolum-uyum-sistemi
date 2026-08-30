"""
Öğrenci katman akışı uç noktaları — D2.
GET  /ogrenci/katmanlar                     — tüm katmanlar + ilerleme durumu
POST /ogrenci/katmanlar/{kod}/basla         — katmanı başlat/devam et, soru seti döner
POST /ogrenci/katmanlar/{kod}/cevap         — bir soruyu cevapla
POST /ogrenci/katmanlar/{kod}/tamamla       — katmanı bitir, değişken puanlarını hesapla
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.api.deps import get_mevcut_ogrenci
from app.core.database import get_db
from app.core.security import sifre_hashle, sifre_dogrula
from datetime import datetime, timedelta, timezone

from app.core.katman_servisi import (
    IsKuraliHatasi, aktif_veya_yeni_tur_getir, son_tur_getir, katman_oturumu_baslat,
    cevabi_kaydet, katmani_tamamla, tum_ana_katmanlar_tamamlandi_mi, parametre_oku,
)
from app.core.dal_servisi import (
    k5_tetikle, dal_bul, dal_oturumu_baslat, dali_tamamla,
)
from app.core.skor_motoru import toplam_uyum_hesapla, siralama_getir
from app.core.kesfet_servisi import bolumleri_ara
from app.models import (
    Ogrenci, Katman, OgrenciKatmanOturumu, Degisken, SoruSecenegi, OgrenciDalOturumu, Bolum,
    OgrenciDegerlendirmeTuru, GuvenlikOlayi, GuvenlikFotografi,
)
from app.schemas.ogrenci import (
    KatmanOut, KatmanBaslatCevap, SoruOut, SecenekOut,
    CevapIstek, KatmanTamamlamaCevap, KatmanSonucSatiri,
    K5DurumOut, DalAdayOut, DalBaslatCevap, DalTamamlamaCevap,
    BolumSiralamaSatiri, KesfetSonucOut, DurumOzetiOut,
    ProfilOut, ProfilGuncelleIstek, SifreDegistirIstek, ProfilFotoIstek, MeslekAramaSonucu,
    KatmanGecmisSonucOut,
    BolumOrnekMeslekOut,
)

router = APIRouter()


def _puan_araligi(puan: float) -> str:
    """
    Bir puanı 5 aralıktan birine ('belirgin_ustun'...'belirgin_altinda') eşler.
    NOT: Sınırlar (80/60/40/20) belgede açık şekilde tanımlanmamıştı — F2.1'deki
    gap kategorilerinin (±15/±5) aralık genişliği mantığına dayanan, buraya
    özel çıkarılmış bir varsayım. Kalibre edilmesi gerekirse yalnızca bu
    fonksiyon değişir.
    """
    if puan >= 80:
        return "belirgin_ustun"
    if puan >= 60:
        return "ustun"
    if puan >= 40:
        return "beklenti"
    if puan >= 20:
        return "altinda"
    return "belirgin_altinda"


def _yorumlari_ekle(db: Session, sonuclar: list[KatmanSonucSatiri]) -> list[KatmanSonucSatiri]:
    """Her sonuç satırına, gelisim_yorum_havuzu'ndan puana uygun yorumu ekler."""
    for s in sonuclar:
        aralik = _puan_araligi(s.puan)
        satir = db.execute(
            text("""
                SELECT durum_tespiti, aksiyon_onerisi, kaynak_tipi, tahmini_efor
                FROM gelisim_yorum_havuzu
                WHERE degisken_id = :did AND aralik = :aralik
            """),
            {"did": s.degisken_id, "aralik": aralik},
        ).mappings().first()
        if satir:
            s.durum_tespiti = satir["durum_tespiti"]
            s.aksiyon_onerisi = satir["aksiyon_onerisi"]
            s.kaynak_tipi = satir["kaynak_tipi"]
            s.tahmini_efor = satir["tahmini_efor"]
    return sonuclar


def _katman_bul(db: Session, kod: str) -> Katman:
    katman = db.query(Katman).filter(Katman.kod == kod.upper()).first()
    if katman is None:
        raise HTTPException(status_code=404, detail=f"Katman bulunamadı: {kod}")
    return katman


@router.get("/katmanlar", response_model=list[KatmanOut])
def katmanlari_listele(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    [DÜZELTME — kullanıcı sorusu üzerine fark edildi] Önceden yalnızca statik
    katman bilgisini (isim, sıra, ağırlık) döndürüyordu — öğrencinin o katmanı
    tamamlayıp tamamlamadığını hiç içermiyordu, bu yüzden frontend'de
    "tamamlandı" rozeti gösterilemiyordu. Artık son_tur_getir ile öğrencinin
    gerçek oturum durumunu da katıyor.
    """
    katmanlar = db.query(Katman).order_by(Katman.sira).all()

    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        # Hiç tur başlamamış — tüm katmanlar 'baslamadi'
        return [
            KatmanOut(id=k.id, kod=k.kod, ad=k.ad, sira=k.sira,
                      normalizasyon_agirligi=float(k.normalizasyon_agirligi) if k.normalizasyon_agirligi else None,
                      kosullu_mu=k.kosullu_mu, durum="baslamadi")
            for k in katmanlar
        ]

    oturumlar = {
        o.katman_id: o.durum
        for o in db.query(OgrenciKatmanOturumu).filter(
            OgrenciKatmanOturumu.ogrenci_id == ogrenci.id, OgrenciKatmanOturumu.tur_id == tur.id
        ).all()
    }

    return [
        KatmanOut(
            id=k.id, kod=k.kod, ad=k.ad, sira=k.sira,
            normalizasyon_agirligi=float(k.normalizasyon_agirligi) if k.normalizasyon_agirligi else None,
            kosullu_mu=k.kosullu_mu,
            durum=oturumlar.get(k.id, "baslamadi"),
        )
        for k in katmanlar
    ]


@router.post("/katmanlar/{kod}/basla", response_model=KatmanBaslatCevap)
def katmani_baslat(
    kod: str,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    katman = _katman_bul(db, kod)
    try:
        tur = aktif_veya_yeni_tur_getir(db, ogrenci)
        oturum, sorular = katman_oturumu_baslat(db, ogrenci, katman, tur)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    db.commit()

    # Seçenekleri tek sorguda topla (ORM ilişkisi tanımlanmadığı için doğrudan sorgu)
    soru_idler = [s.id for s in sorular]
    tum_secenekler = (
        db.query(SoruSecenegi)
        .filter(SoruSecenegi.soru_id.in_(soru_idler))
        .order_by(SoruSecenegi.soru_id, SoruSecenegi.secenek_sirasi)
        .all()
    )
    secenekler_by_soru: dict[int, list[SoruSecenegi]] = {}
    for sec in tum_secenekler:
        secenekler_by_soru.setdefault(sec.soru_id, []).append(sec)

    soru_out = [
        SoruOut(
            id=s.id, soru_tipi=s.soru_tipi, soru_metni=s.soru_metni,
            secenekler=[
                SecenekOut(id=sec.id, secenek_sirasi=sec.secenek_sirasi, secenek_metni=sec.secenek_metni)
                for sec in secenekler_by_soru.get(s.id, [])
            ],
        )
        for s in sorular
    ]
    return KatmanBaslatCevap(tur_id=tur.id, katman_oturum_id=oturum.id, sorular=soru_out)


@router.post("/katmanlar/{kod}/cevap", status_code=204)
def soruyu_cevapla(
    kod: str,
    istek: CevapIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    katman = _katman_bul(db, kod)
    tur = aktif_veya_yeni_tur_getir(db, ogrenci)
    try:
        cevabi_kaydet(db, ogrenci, tur, istek.soru_id, istek.secenek_id)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()


@router.post("/katmanlar/{kod}/tamamla", response_model=KatmanTamamlamaCevap)
def katmani_tamamla_uc_nokta(
    kod: str,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    katman = _katman_bul(db, kod)
    tur = aktif_veya_yeni_tur_getir(db, ogrenci)

    oturum = (
        db.query(OgrenciKatmanOturumu)
        .filter(
            OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
            OgrenciKatmanOturumu.tur_id == tur.id,
            OgrenciKatmanOturumu.katman_id == katman.id,
        )
        .first()
    )
    if oturum is None:
        raise HTTPException(status_code=400, detail="Bu katman için henüz başlanmış bir oturum yok.")

    try:
        sonuclar = katmani_tamamla(db, ogrenci, katman, tur, oturum)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    # D3 — K4 (Alan Eğilimi) tamamlanınca K5 tetikleme otomatik çalışır
    if katman.kod == "K4":
        k5_tetikle(db, ogrenci, tur)

    tum_tamam = tum_ana_katmanlar_tamamlandi_mi(db, ogrenci, tur)

    # D4 — K1-K4'ün dördü de tamamlandığında TOPLAM_UYUM hesaplanır
    # (D4 kuralı: "yarım profille yanıltıcı bir sıralama üretilmez")
    if tum_tamam:
        toplam_uyum_hesapla(db, ogrenci, tur)

    db.commit()

    degisken_adlari = {d.id: d.ad for d in db.query(Degisken).filter(Degisken.id.in_([s[0] for s in sonuclar])).all()}

    sonuc_satirlari = _yorumlari_ekle(db, [
        KatmanSonucSatiri(degisken_id=did, degisken_adi=degisken_adlari.get(did, "?"), puan=puan)
        for did, puan in sonuclar
    ])

    return KatmanTamamlamaCevap(
        katman_kodu=katman.kod,
        sonuclar=sonuc_satirlari,
        tum_katmanlar_tamamlandi_mi=tum_tamam,
    )


# ===================== D3 — K5 Dal Derinleşme ===================== #

@router.get("/k5/durum", response_model=K5DurumOut)
def k5_durumu_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    Hiç tur başlamadıysa (öğrenci K1-K4'e hiç başlamadıysa) veya K4
    tamamlanmadıysa boş/eşik bilgisiyle döner (henüz tetiklenmemiş) —
    bu bir hata durumu değil, "henüz bir şey yok" durumudur.
    K4 tamamlandıysa, o an açık olan dallar + "ayrıca ilgi gösterilen ama
    derinleştirilmeyen" dallar listesi döner (D5'teki sonuç ekranı notu için).
    """
    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        return K5DurumOut(esik=float(parametre_oku(db, "k5_esik_puani", "80")), acilan=[], ilgi_gosterilen=[])
    sonuc = k5_tetikle(db, ogrenci, tur)  # idempotent — zaten açık olanları tekrar açmaz
    db.commit()
    return K5DurumOut(
        esik=sonuc["esik"],
        acilan=[DalAdayOut(**d) for d in sonuc["acilan"]],
        ilgi_gosterilen=[DalAdayOut(**d) for d in sonuc["ilgi_gosterilen"]],
    )


@router.post("/dallar/{kod}/basla", response_model=DalBaslatCevap)
def dali_baslat(
    kod: str,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    try:
        tur = son_tur_getir(db, ogrenci)
        dal = dal_bul(db, kod)
        oturum, sorular = dal_oturumu_baslat(db, ogrenci, dal, tur)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()

    soru_idler = [s.id for s in sorular]
    tum_secenekler = (
        db.query(SoruSecenegi)
        .filter(SoruSecenegi.soru_id.in_(soru_idler))
        .order_by(SoruSecenegi.soru_id, SoruSecenegi.secenek_sirasi)
        .all()
    )
    secenekler_by_soru: dict[int, list[SoruSecenegi]] = {}
    for sec in tum_secenekler:
        secenekler_by_soru.setdefault(sec.soru_id, []).append(sec)

    soru_out = [
        SoruOut(
            id=s.id, soru_tipi=s.soru_tipi, soru_metni=s.soru_metni,
            secenekler=[
                SecenekOut(id=sec.id, secenek_sirasi=sec.secenek_sirasi, secenek_metni=sec.secenek_metni)
                for sec in secenekler_by_soru.get(s.id, [])
            ],
        )
        for s in sorular
    ]
    return DalBaslatCevap(dal_oturum_id=oturum.id, sorular=soru_out)


@router.post("/dallar/{kod}/cevap", status_code=204)
def dal_soruyu_cevapla(
    kod: str,
    istek: CevapIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    try:
        tur = son_tur_getir(db, ogrenci)
        cevabi_kaydet(db, ogrenci, tur, istek.soru_id, istek.secenek_id)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()


@router.post("/dallar/{kod}/tamamla", response_model=DalTamamlamaCevap)
def dali_tamamla_uc_nokta(
    kod: str,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    try:
        tur = son_tur_getir(db, ogrenci)
        dal = dal_bul(db, kod)
    except IsKuraliHatasi as e:
        raise HTTPException(status_code=400, detail=str(e))

    oturum = (
        db.query(OgrenciDalOturumu)
        .filter(
            OgrenciDalOturumu.ogrenci_id == ogrenci.id,
            OgrenciDalOturumu.tur_id == tur.id,
            OgrenciDalOturumu.dal_id == dal.id,
        )
        .first()
    )
    if oturum is None:
        raise HTTPException(status_code=400, detail="Bu dal için henüz başlanmış bir oturum yok.")

    try:
        sonuclar = dali_tamamla(db, ogrenci, dal, tur, oturum)
    except IsKuraliHatasi as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    db.commit()

    degisken_adlari = {d.id: d.ad for d in db.query(Degisken).filter(Degisken.id.in_([s[0] for s in sonuclar])).all()}
    return DalTamamlamaCevap(
        dal_kodu=dal.kod,
        sonuclar=[
            KatmanSonucSatiri(degisken_id=did, degisken_adi=degisken_adlari.get(did, "?"), puan=puan)
            for did, puan in sonuclar
        ],
    )


# ===================== D5 — Sonuç Ekranı (Katman 1: Öneri Listesi) ===================== #

@router.get("/sonuc/siralama", response_model=list[BolumSiralamaSatiri])
def bolum_siralamasi_getir(
    ilk_n: int = 20,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    D5, Katman 1 — Öneri Listesi (ilk 15-20 bölüm). K1-K4'ün dördü de
    tamamlanmadıysa boş liste döner — D4 kuralı: yarım profille yanıltıcı
    bir sıralama üretilmez.
    """
    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        return []

    if tur.durum != "tamamlandi":
        return []  # K1-K4 henüz bitmedi — D4 kuralı gereği hiçbir skor gösterilmez

    siralama = siralama_getir(db, ogrenci, tur, ilk_n=ilk_n)
    bolum_adlari = {b.id: b.ad for b in db.query(Bolum).all()}
    return [
        BolumSiralamaSatiri(bolum_id=s.bolum_id, bolum_adi=bolum_adlari.get(s.bolum_id, "?"), toplam_uyum=float(s.toplam_uyum))
        for s in siralama
    ]


# ===================== D5 — Sonuç Ekranı (Katman 2: Tüm Bölümleri Keşfet) ===================== #

@router.get("/sonuc/kesfet", response_model=list[KesfetSonucOut])
def bolumleri_kesfet(
    q: str,
    limit: int = 20,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    D5, Katman 2 — Tüm Bölümleri Keşfet. Öneri listesinden (Katman 1)
    farklı olarak K1-K4 tamamlanmamış olsa bile çalışır (bölüm bilgisi +
    katman ortalamaları öğrenci profilinden bağımsızdır); yalnızca
    toplam_uyum alanı, profil tamamlanana kadar null döner.
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Arama terimi en az 2 karakter olmalı.")
    sonuclar = bolumleri_ara(db, ogrenci, q.strip(), limit=limit)
    return [KesfetSonucOut(**s) for s in sonuclar]


# ===================== Genel Durum Özeti (sidebar/ilerleme göstergesi) ===================== #

@router.get("/durum-ozeti", response_model=DurumOzetiOut)
def durum_ozetini_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    [YENİ — kullanıcı sorusu üzerine eklendi] Sidebar'da "3/4 katman
    tamamlandı", "K5: 2 dal açık, 1 tamamlandı", "sonraki tur: 12.02.2027"
    gibi bir özet göstermek için tek bir uç nokta. Öğrenci hiç tur
    başlatmadıysa "her şey sıfır" bir özet döner, hata fırlatmaz.
    """
    ana_katman_sayisi = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).count()

    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        return DurumOzetiOut(
            tur_no=None, tur_tamamlandi_mi=False, tamamlanan_katman_sayisi=0,
            toplam_ana_katman_sayisi=ana_katman_sayisi, k5_acilan_dal_sayisi=0,
            k5_tamamlanan_dal_sayisi=0, sonraki_tur_tarihi=None,
        )

    tamamlanan_katman = (
        db.query(OgrenciKatmanOturumu)
        .join(Katman, Katman.id == OgrenciKatmanOturumu.katman_id)
        .filter(
            OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
            OgrenciKatmanOturumu.tur_id == tur.id,
            OgrenciKatmanOturumu.durum == "tamamlandi",
            Katman.kosullu_mu.is_(False),
        )
        .count()
    )

    dal_oturumlari = db.query(OgrenciDalOturumu).filter(
        OgrenciDalOturumu.ogrenci_id == ogrenci.id, OgrenciDalOturumu.tur_id == tur.id
    ).all()
    k5_acilan = len(dal_oturumlari)
    k5_tamamlanan = sum(1 for d in dal_oturumlari if d.durum == "tamamlandi")

    sonraki_tur_tarihi = None
    if tur.durum == "tamamlandi" and tur.tamamlanma_zamani:
        min_gun = int(parametre_oku(db, "yeniden_degerlendirme_min_gun", "120"))
        tamamlanma = tur.tamamlanma_zamani
        if tamamlanma.tzinfo is None:
            tamamlanma = tamamlanma.replace(tzinfo=timezone.utc)
        sonraki_tur_tarihi = (tamamlanma + timedelta(days=min_gun)).date().isoformat()

    return DurumOzetiOut(
        tur_no=tur.tur_no, tur_tamamlandi_mi=(tur.durum == "tamamlandi"),
        tamamlanan_katman_sayisi=tamamlanan_katman, toplam_ana_katman_sayisi=ana_katman_sayisi,
        k5_acilan_dal_sayisi=k5_acilan, k5_tamamlanan_dal_sayisi=k5_tamamlanan,
        sonraki_tur_tarihi=sonraki_tur_tarihi,
    )


# ============================================================================
# Profil (sonradan eklendi)
# ============================================================================
# NOT (hukuki): dogum_tarihi/cinsiyet KVKK açısından hassas veri sayılabilir,
# veli onayı akışı ayrıca kurulmalıdır — bu uç noktalar yalnızca teknik alt yapıdır.

@router.get("/profil", response_model=ProfilOut)
def profil_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    hedef_meslek_adi = None
    if ogrenci.hedef_meslek_id:
        satir = db.execute(
            text("SELECT ad FROM meslekler WHERE id = :id"), {"id": ogrenci.hedef_meslek_id}
        ).first()
        hedef_meslek_adi = satir[0] if satir else None

    return ProfilOut(
        ad_soyad=ogrenci.ad_soyad,
        email=ogrenci.email,
        okul=ogrenci.okul,
        sinif=ogrenci.sinif,
        dogum_tarihi=ogrenci.dogum_tarihi,
        cinsiyet=ogrenci.cinsiyet,
        ilgi_alanlari=ogrenci.ilgi_alanlari,
        hedef_universite=ogrenci.hedef_universite,
        hedef_meslek_id=ogrenci.hedef_meslek_id,
        hedef_meslek_adi=hedef_meslek_adi,
        profil_foto_base64=ogrenci.profil_foto_base64,
    )


@router.put("/profil", response_model=ProfilOut)
def profil_guncelle(
    istek: ProfilGuncelleIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    veri = istek.model_dump(exclude_unset=True)

    if "cinsiyet" in veri and veri["cinsiyet"] is not None:
        if veri["cinsiyet"] not in ("kadin", "erkek", "belirtmek_istemiyorum", "diger"):
            raise HTTPException(status_code=400, detail="Geçersiz cinsiyet değeri.")

    if "hedef_meslek_id" in veri and veri["hedef_meslek_id"] is not None:
        var_mi = db.execute(
            text("SELECT 1 FROM meslekler WHERE id = :id"), {"id": veri["hedef_meslek_id"]}
        ).first()
        if not var_mi:
            raise HTTPException(status_code=400, detail="Geçersiz meslek seçimi.")

    for alan, deger in veri.items():
        setattr(ogrenci, alan, deger)

    db.commit()
    db.refresh(ogrenci)
    return profil_getir(db=db, ogrenci=ogrenci)


@router.post("/profil/sifre-degistir", status_code=204)
def sifre_degistir(
    istek: SifreDegistirIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    if not sifre_dogrula(istek.eski_sifre, ogrenci.sifre_hash):
        raise HTTPException(status_code=400, detail="Mevcut şifre yanlış.")
    if len(istek.yeni_sifre) < 8:
        raise HTTPException(status_code=400, detail="Yeni şifre en az 8 karakter olmalı.")

    ogrenci.sifre_hash = sifre_hashle(istek.yeni_sifre)
    db.commit()
    return None


@router.post("/profil/fotograf", response_model=ProfilOut)
def profil_fotografi_guncelle(
    istek: ProfilFotoIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    # Basit boyut koruması — çok büyük base64 string'leri reddet (~2MB sınırı)
    if len(istek.foto_base64) > 2_800_000:
        raise HTTPException(status_code=400, detail="Fotoğraf çok büyük (maks. ~2MB).")
    if not istek.foto_base64.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Geçersiz görsel formatı.")

    ogrenci.profil_foto_base64 = istek.foto_base64
    db.commit()
    db.refresh(ogrenci)
    return profil_getir(db=db, ogrenci=ogrenci)


@router.get("/meslek-ara", response_model=list[MeslekAramaSonucu])
def meslek_ara(
    q: str,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    if len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Arama terimi en az 2 karakter olmalı.")
    satirlar = db.execute(
        text("SELECT id, ad FROM meslekler WHERE ad ILIKE :q ORDER BY ad LIMIT 15"),
        {"q": f"%{q.strip()}%"},
    ).mappings().all()
    return [MeslekAramaSonucu(id=r["id"], ad=r["ad"]) for r in satirlar]

# ===================== Geçmiş katman sonucu (sonradan eklendi) ===================== #

@router.get("/katmanlar/{kod}/sonuc", response_model=KatmanGecmisSonucOut)
def katman_gecmis_sonucu(
    kod: str,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    [YENİ] Bir katman daha önce tamamlanmışsa, sonucunu (Ana Sayfa/detay
    ekranları için) tekrar sorgulamayı sağlar — önceden yalnızca tamamlama
    anında bir kereliğine dönüyordu. Katman tamamlanmadıysa boş liste döner,
    hata fırlatmaz.
    """
    katman = _katman_bul(db, kod)
    try:
        tur = son_tur_getir(db, ogrenci)
    except IsKuraliHatasi:
        return KatmanGecmisSonucOut(katman_kodu=katman.kod, tamamlandi_mi=False, sonuclar=[])

    oturum = (
        db.query(OgrenciKatmanOturumu)
        .filter(
            OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
            OgrenciKatmanOturumu.tur_id == tur.id,
            OgrenciKatmanOturumu.katman_id == katman.id,
        )
        .first()
    )
    if oturum is None or oturum.durum != "tamamlandi":
        return KatmanGecmisSonucOut(katman_kodu=katman.kod, tamamlandi_mi=False, sonuclar=[])

    satirlar = db.execute(
        text("""
            SELECT s.degisken_id, d.ad AS degisken_adi, s.puan
            FROM ogrenci_degisken_skorlari s
            JOIN degiskenler d ON d.id = s.degisken_id
            WHERE s.ogrenci_id = :oid AND s.tur_id = :tid AND d.katman_id = :kid
            ORDER BY d.sira
        """),
        {"oid": str(ogrenci.id), "tid": tur.id, "kid": katman.id},
    ).mappings().all()

    return KatmanGecmisSonucOut(
        katman_kodu=katman.kod,
        tamamlandi_mi=True,
        sonuclar=_yorumlari_ekle(db, [
            KatmanSonucSatiri(degisken_id=r["degisken_id"], degisken_adi=r["degisken_adi"], puan=float(r["puan"]))
            for r in satirlar
        ]),
    )


# ===================== Bölüm örnek meslekleri (Keşfet ekranı için) ===================== #

@router.get("/sonuc/kesfet/{bolum_id}/meslekler", response_model=list[BolumOrnekMeslekOut])
def bolum_ornek_meslekleri_getir(
    bolum_id: int,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """
    [YENİ] Bir bölümün altında gösterilecek örnek meslekleri getirir —
    a2_meslek_bolum_eslesme_aday.csv'den türetilmiş gerçek benzerlik
    skorlarına dayanır (bolum_ornek_meslekler tablosu).
    """
    satirlar = db.execute(
        text("""
            SELECT meslek_adi, benzerlik_skoru
            FROM bolum_ornek_meslekler
            WHERE bolum_id = :bid
            ORDER BY sira
        """),
        {"bid": bolum_id},
    ).mappings().all()
    return [
        BolumOrnekMeslekOut(meslek_adi=r["meslek_adi"], benzerlik_skoru=float(r["benzerlik_skoru"]))
        for r in satirlar
    ]


# ============================================================================
# Güvenlik/Tutarlılık Altyapısı (sonradan eklendi)
# ============================================================================
# NOT: Fotoğraf için, yukarıdaki profil_foto_base64 ile AYNI kanıtlanmış
# deseni kullanıyoruz (Supabase Storage entegrasyonu yerine base64, doğrudan
# DB'de) — tutarlılık ve basitlik için. İleride gerçek dosya depolamaya
# taşınabilir.

GUVENLIK_OLAY_TIPLERI = {
    "tam_ekrandan_cikti", "tam_ekrana_geri_donuldu",
    "sekme_degisti", "sekmeye_geri_donuldu",
    "pencere_odagi_kaybedildi", "pencere_odagi_geri_kazanildi",
    "kamera_izni_reddedildi", "kamera_desteklenmiyor",
}


class GuvenlikOlayiIstek(BaseModel):
    tur_id: int
    olay_tipi: str
    katman_kod: str | None = None


class GuvenlikFotografIstek(BaseModel):
    tur_id: int
    foto_base64: str
    katman_kod: str | None = None


def _tur_sahipligini_dogrula(db: Session, ogrenci: Ogrenci, tur_id: int) -> OgrenciDegerlendirmeTuru:
    tur = db.get(OgrenciDegerlendirmeTuru, tur_id)
    if tur is None or tur.ogrenci_id != ogrenci.id:
        raise HTTPException(status_code=404, detail="Tur bulunamadı.")
    return tur


@router.post("/guvenlik/olay", status_code=204)
def guvenlik_olayi_kaydet(
    istek: GuvenlikOlayiIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """Tam ekrandan çıkma / sekme değiştirme / pencere odağı kaybı olaylarını loglar."""
    if istek.olay_tipi not in GUVENLIK_OLAY_TIPLERI:
        raise HTTPException(status_code=400, detail="Geçersiz olay_tipi.")
    _tur_sahipligini_dogrula(db, ogrenci, istek.tur_id)

    db.add(GuvenlikOlayi(
        ogrenci_id=ogrenci.id, tur_id=istek.tur_id,
        olay_tipi=istek.olay_tipi, katman_kod=istek.katman_kod,
    ))
    db.commit()


@router.post("/guvenlik/fotograf", status_code=204)
def guvenlik_fotografi_kaydet(
    istek: GuvenlikFotografIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    """Periyodik kimlik doğrulama fotoğrafı — profil_foto_base64 ile aynı boyut/format kontrolü."""
    if len(istek.foto_base64) > 1_500_000:  # tek kare için fazlasıyla yeterli
        raise HTTPException(status_code=400, detail="Fotoğraf çok büyük (maks ~1MB).")
    if not istek.foto_base64.startswith("data:image/"):
        raise HTTPException(status_code=400, detail="Geçersiz görsel formatı.")
    _tur_sahipligini_dogrula(db, ogrenci, istek.tur_id)

    db.add(GuvenlikFotografi(
        ogrenci_id=ogrenci.id, tur_id=istek.tur_id,
        depolama_yolu=istek.foto_base64,  # [NOT] isim "depolama_yolu" ama şu an base64 içerik tutuyor
        katman_kod=istek.katman_kod,
    ))
    db.commit()
