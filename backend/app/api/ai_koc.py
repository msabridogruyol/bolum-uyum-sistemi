# -*- coding: utf-8 -*-
"""
AI Koçluk Asistanı — API uç noktaları

GET  /koclugu/asistan/durum                 — asistan aktif mi, bugün kalan mesaj hakkı
POST /koclugu/asistan/oturum/baslat        — yeni oturum başlatır (varsa aktif olanı döner, mesajlarıyla)
POST /koclugu/asistan/oturum/{id}/mesaj    — mesaj gönderir, asistan cevabını döner
POST /koclugu/asistan/oturum/{id}/bitir    — oturumu kapatır, özet çıkarır
GET  /koclugu/asistan/gecmis               — geçmiş oturum özetlerini listeler
"""
from datetime import datetime, timezone
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_db
from app.api.deps import get_kvkk_onayli_ogrenci, get_mevcut_ogrenci
from app.models import Ogrenci, OgrenciKoclukOturumu, OgrenciKoclukMesaji
from app.core.ai_koc_servisi import (
    sistem_promptu_olustur, openai_ile_konus, oturumu_ozetle,
    AsistanKullanilamiyorHatasi, MAKSIMUM_TUR,
    asistan_aktif_mi, kriz_mesaji_mi, KRIZ_YANITI, GUNLUK_MESAJ_LIMITI_VARSAYILAN,
)
from app.core.katman_servisi import parametre_oku

router = APIRouter(prefix="/asistan", tags=["ai-koc"])


class OturumMesajiOut(BaseModel):
    rol: str
    icerik: str


class OturumOut(BaseModel):
    oturum_id: int
    durum: str
    mesajlar: list[OturumMesajiOut] = []


class MesajIstek(BaseModel):
    mesaj: str
    sayfa: str | None = None  # [2026-10-04] öğrencinin o an bulunduğu sayfa (bağlam için)
    baglam_oturum_id: int | None = None  # [2026-10-10] geçmişten "devam et" ile açılan sohbet


class AsistanDurumOut(BaseModel):
    aktif: bool
    mod: str = "ai"                    # [2026-10-10] ai | otomatik (yapay zekâ bağlı değilken kural tabanlı rehber)
    ornek_sorular: list[str] = []
    soru_kategorileri: list[dict] = []   # [2026-10-10] "Sorabileceklerin" sekmesi
    gunluk_limit: int
    bugun_gonderilen: int
    kalan: int


def _ai(db: Session, ogrenci: Ogrenci) -> bool:
    """[2026-10-10] Yapay zekâlı Filiz: API anahtarı tanımlı VE okulun paketinde 'filiz_ai' modülü var.
    Aksi halde Filiz, öğrencinin verilerine dayanan otomatik rehber modunda çalışır (maliyetsiz)."""
    if not asistan_aktif_mi():
        return False
    from app.core.paketler import okul_modulleri
    return "filiz_ai" in okul_modulleri(db, ogrenci.okul_id)


# [2026-10-30] Yapay zekâ her pakette; günlük sınır pakete göre (sistem parametresi, süper admin değiştirir).
# Tam paket ve okula bağlı olmayan öğrenci eski parametreyi (filiz_gunluk_mesaj_limiti) kullanır.
PAKET_LIMIT_PARAMETRESI = {"temel": ("filiz_gunluk_mesaj_limiti_temel", 5), "gelisim": ("filiz_gunluk_mesaj_limiti_gelisim", 20)}
# [2026-10-31] Okulun aylık havuzu da pakete göre (öğrenci başına): Temel 30, Gelişim 60, Tam ve diğerleri 120.
PAKET_AYLIK_PARAMETRESI = {"temel": ("filiz_okul_aylik_ogrenci_basi_temel", 30), "gelisim": ("filiz_okul_aylik_ogrenci_basi_gelisim", 60)}
AYLIK_OGRENCI_BASI_VARSAYILAN = 120   # Tam paket: okulun aylık yapay zekâ üst sınırı = öğrenci sayısı × bu değer (0 = sınırsız)


def _okul_paketi(db: Session, okul_id: int | None) -> str | None:
    if not okul_id:
        return None
    from sqlalchemy import text
    return db.execute(text("SELECT paket FROM okullar WHERE id = :o"), {"o": okul_id}).scalar()


def _gunluk_limit(db: Session, ogrenci: Ogrenci) -> int:
    anahtar, varsayilan = PAKET_LIMIT_PARAMETRESI.get(_okul_paketi(db, ogrenci.okul_id) or "",
                                                      ("filiz_gunluk_mesaj_limiti", GUNLUK_MESAJ_LIMITI_VARSAYILAN))
    try:
        return max(0, int(parametre_oku(db, anahtar, str(varsayilan))))
    except (TypeError, ValueError):
        return varsayilan


def _yz_mesaj_sorgusu(db: Session, baslangic):
    """Belirli bir andan bu yana yapay zekâdan gelen asistan cevapları (rehber modu ve sabit cevaplar sayılmaz)."""
    return (
        db.query(OgrenciKoclukMesaji)
        .join(OgrenciKoclukOturumu, OgrenciKoclukOturumu.id == OgrenciKoclukMesaji.oturum_id)
        .filter(OgrenciKoclukMesaji.rol == "asistan", OgrenciKoclukMesaji.yapay_zeka.is_(True),
                OgrenciKoclukMesaji.olusturulma_zamani >= baslangic.replace(tzinfo=None))
    )


def _bugun_gonderilen(db: Session, ogrenci: Ogrenci) -> int:
    """Türkiye saatine göre bugün öğrencinin yapay zekâyla yaptığı mesajlaşma sayısı."""
    from app.core.haftalik_servisi import TR_SAAT
    simdi = datetime.now(timezone.utc).astimezone(TR_SAAT)
    gun_basi = simdi.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    return _yz_mesaj_sorgusu(db, gun_basi).filter(OgrenciKoclukOturumu.ogrenci_id == ogrenci.id).count()


def _okul_aylik_doldu(db: Session, ogrenci: Ogrenci) -> bool:
    """[2026-10-30] Okulun bu ayki yapay zekâ kullanımı üst sınıra ulaştı mı (Türkiye saatine göre ay başından beri)."""
    if not ogrenci.okul_id:
        return False
    anahtar, varsayilan = PAKET_AYLIK_PARAMETRESI.get(_okul_paketi(db, ogrenci.okul_id) or "",
                                                      ("filiz_okul_aylik_ogrenci_basi", AYLIK_OGRENCI_BASI_VARSAYILAN))
    try:
        kisi_basi = int(parametre_oku(db, anahtar, str(varsayilan)))
    except (TypeError, ValueError):
        kisi_basi = varsayilan
    if kisi_basi <= 0:
        return False
    from sqlalchemy import text
    from app.core.haftalik_servisi import TR_SAAT
    ogrenci_sayisi = db.execute(text("SELECT count(*) FROM ogrenciler WHERE okul_id = :o AND NOT coalesce(test_hesabi, FALSE)"),
                                {"o": ogrenci.okul_id}).scalar() or 0
    simdi = datetime.now(timezone.utc).astimezone(TR_SAAT)
    ay_basi = simdi.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    kullanilan = (_yz_mesaj_sorgusu(db, ay_basi).join(Ogrenci, Ogrenci.id == OgrenciKoclukOturumu.ogrenci_id)
                  .filter(Ogrenci.okul_id == ogrenci.okul_id).count())
    return kullanilan >= max(1, ogrenci_sayisi) * kisi_basi


def _yz_durumu(db: Session, ogrenci: Ogrenci) -> tuple[bool, str | None, int, int]:
    """(yapay zekâ bu mesajda kullanılabilir mi, kullanılamıyorsa öğrenciye not, günlük sınır, bugün kullanılan).
    Yapay zekâ kapalıysa (anahtar yok / okulda filiz_ai kapalı) not yoktur; sınır dolduysa Filiz rehber moduna geçer."""
    limit, gonderilen = _gunluk_limit(db, ogrenci), _bugun_gonderilen(db, ogrenci)
    if not _ai(db, ogrenci):
        return False, None, limit, gonderilen
    if gonderilen >= limit:
        return False, "Bugünkü yapay zekâ mesaj hakkın doldu; yarına kadar sonuçlarına dayanan rehber modunda cevaplıyorum.", limit, gonderilen
    if _okul_aylik_doldu(db, ogrenci):
        return False, "Okulunun bu ayki yapay zekâ kullanımı doldu; ay sonuna kadar sonuçlarına dayanan rehber modunda cevaplıyorum.", limit, gonderilen
    return True, None, limit, gonderilen


@router.get("/durum", response_model=AsistanDurumOut)
def asistan_durumu(db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    ai, _not, limit, gonderilen = _yz_durumu(db, ogrenci)   # [2026-10-30] sınır dolduysa rehber modu gösterilir
    from app.core.filiz_rehber import ORNEK_SORULAR, SORU_KATEGORILERI
    return AsistanDurumOut(aktif=True, mod="ai" if ai else "otomatik", ornek_sorular=ORNEK_SORULAR[:6],
                           soru_kategorileri=SORU_KATEGORILERI,
                           gunluk_limit=limit, bugun_gonderilen=gonderilen, kalan=max(0, limit - gonderilen) if ai else limit)


class MesajCevap(BaseModel):
    asistan_yaniti: str
    oturum_kapandi_mi: bool = False
    otomatik: bool = False             # [2026-10-10] cevap kural tabanlı rehberden geldiyse


class GecmisOturumOut(BaseModel):
    oturum_id: int
    baslama_zamani: datetime
    ozet: str | None
    bitis_zamani: datetime | None = None
    baslik: str | None = None        # [2026-10-10] öğrencinin ilk mesajı (liste başlığı)
    mesaj_sayisi: int = 0


@router.post("/oturum/baslat", response_model=OturumOut)
def oturum_baslat(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_kvkk_onayli_ogrenci),
):
    aktif = (
        db.query(OgrenciKoclukOturumu)
        .filter(OgrenciKoclukOturumu.ogrenci_id == ogrenci.id, OgrenciKoclukOturumu.durum == "aktif")
        .first()
    )
    if aktif:
        mesajlar = (
            db.query(OgrenciKoclukMesaji)
            .filter(OgrenciKoclukMesaji.oturum_id == aktif.id)
            .order_by(OgrenciKoclukMesaji.olusturulma_zamani, OgrenciKoclukMesaji.id)
            .all()
        )
        return OturumOut(oturum_id=aktif.id, durum=aktif.durum,
                         mesajlar=[OturumMesajiOut(rol=m.rol, icerik=m.icerik) for m in mesajlar])

    yeni = OgrenciKoclukOturumu(ogrenci_id=ogrenci.id, durum="aktif")
    db.add(yeni)
    db.commit()
    db.refresh(yeni)
    return OturumOut(oturum_id=yeni.id, durum=yeni.durum)


@router.post("/oturum/{oturum_id}/mesaj", response_model=MesajCevap)
def mesaj_gonder(
    oturum_id: int,
    istek: MesajIstek,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_kvkk_onayli_ogrenci),
):
    oturum = db.get(OgrenciKoclukOturumu, oturum_id)
    if oturum is None or oturum.ogrenci_id != ogrenci.id:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı.")
    if oturum.durum != "aktif":
        raise HTTPException(status_code=400, detail="Bu oturum kapatılmış, yeni bir oturum başlatın.")
    metin = istek.mesaj.strip()[:2000]
    if not metin:
        raise HTTPException(status_code=400, detail="Mesaj boş olamaz.")

    # [2026-10-04] Kriz ifadesi: model çağrılmaz, güvenli yönlendirme cevabı verilir (limit ve anahtardan bağımsız)
    if kriz_mesaji_mi(metin):
        db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="ogrenci", icerik=metin))
        db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="asistan", icerik=KRIZ_YANITI))
        db.commit()
        return MesajCevap(asistan_yaniti=KRIZ_YANITI, oturum_kapandi_mi=False)

    # [2026-10-11] Hiyerarşi koruması (yapay zekâ ve otomatik rehber): başka bir öğrenciyi hedefleyen soru (okuldaki başka
    # bir öğrencinin adı, "arkadaşımın puanı", "en yüksek net kimde", okul/sınıf ortalaması) modele GİTMEZ; sabit cevap.
    from app.core.filiz_gizlilik import ogrenci_dizini, ogrenci_hiyerarsi_yaniti, ogrenci_metni_maskele
    dizin = ogrenci_dizini(db, ogrenci)
    ai = _ai(db, ogrenci)
    ret = ogrenci_hiyerarsi_yaniti(metin, dizin, ogrenci.ad_soyad)
    if ret:
        db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="ogrenci", icerik=metin))
        db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="asistan", icerik=ret))
        db.commit()
        return MesajCevap(asistan_yaniti=ret, oturum_kapandi_mi=False, otomatik=not ai)

    # [2026-10-30] Sınırlar yapay zekâ maliyeti içindir. Günlük (pakete göre) ya da okulun aylık sınırı dolunca hizmet
    # kesilmez: Filiz, öğrencinin verilerine dayanan rehber modunda cevap verir (önceden 429 dönüyordu).
    ai, sinir_notu, _limit, _gonderilen = _yz_durumu(db, ogrenci)

    onceki_mesajlar = (
        db.query(OgrenciKoclukMesaji)
        .filter(OgrenciKoclukMesaji.oturum_id == oturum.id)
        .order_by(OgrenciKoclukMesaji.olusturulma_zamani, OgrenciKoclukMesaji.id)
        .all()
    )
    # [2026-10-11] Modele giden metinlerde e-posta / telefon / TC ve okul arkadaşlarının adları maskelenir (kendi adı korunur)
    mesaj_gecmisi = [
        {"role": "user" if m.rol == "ogrenci" else "assistant", "content": ogrenci_metni_maskele(dizin, m.icerik, ogrenci.ad_soyad)}
        for m in onceki_mesajlar
    ]
    mesaj_gecmisi.append({"role": "user", "content": ogrenci_metni_maskele(dizin, metin, ogrenci.ad_soyad)})

    # [2026-10-10] Filiz geçmişi hatırlasın: son 3 sohbetin özeti (tarihleriyle); öğrenci geçmişten bir sohbeti
    # "devam et" ile açtıysa o sohbet en başta verilir.
    onceki = (
        db.query(OgrenciKoclukOturumu)
        .filter(
            OgrenciKoclukOturumu.ogrenci_id == ogrenci.id,
            OgrenciKoclukOturumu.durum == "tamamlandi",
            OgrenciKoclukOturumu.id != oturum.id,
            OgrenciKoclukOturumu.ozet.isnot(None),
        )
        .order_by(OgrenciKoclukOturumu.bitis_zamani.desc())
        .limit(3)
        .all()
    )
    baglam = None
    if getattr(istek, "baglam_oturum_id", None):
        b = db.get(OgrenciKoclukOturumu, istek.baglam_oturum_id)
        if b is not None and b.ogrenci_id == ogrenci.id and b.id != oturum.id:
            baglam = b
            onceki = [b] + [x for x in onceki if x.id != b.id][:2]
    parcalar = [f"({(x.bitis_zamani or x.baslama_zamani).strftime('%d.%m.%Y')}"
                + (", öğrencinin devam etmek istediği sohbet" if baglam is not None and x.id == baglam.id else "")
                + f") {x.ozet}" for x in onceki if x.ozet]
    onceki_ozet = ogrenci_metni_maskele(dizin, "\n".join(parcalar), ogrenci.ad_soyad) or None

    sistem_promptu = sistem_promptu_olustur(db, ogrenci, onceki_ozet, istek.sayfa)

    yanit = None
    if ai:
        try:
            yanit = openai_ile_konus(sistem_promptu, mesaj_gecmisi)
            from app.core.filiz_gizlilik import ad_normalize
            yanit = dizin.maskele(yanit, haric=ad_normalize(ogrenci.ad_soyad))   # son kontrol: yanıtta başka öğrenci adı olmasın
        except AsistanKullanilamiyorHatasi:
            # [2026-10-31] Yapay zekâ yoğun / hata / zaman aşımı: sohbet kesilmez (önceden 503), rehber modu cevap verir.
            ai = False
            sinir_notu = "Yapay zekâ şu an yoğun; bu cevabı sonuçlarına dayanan rehber modunda hazırladım."
    otomatik = not ai
    if otomatik:   # [2026-10-10] yapay zekâ bağlı değil: öğrencinin verilerine dayanan otomatik rehber cevabı
        from app.core.filiz_rehber import otomatik_yanit
        yanit = otomatik_yanit(db, ogrenci, metin)
        if sinir_notu:
            yanit = f"{sinir_notu}\n\n{yanit}"

    db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="ogrenci", icerik=metin))
    db.add(OgrenciKoclukMesaji(oturum_id=oturum.id, rol="asistan", icerik=yanit, yapay_zeka=ai))
    db.commit()

    toplam_mesaj = len(onceki_mesajlar) + 2
    kapandi = False
    if toplam_mesaj >= MAKSIMUM_TUR:
        _oturumu_kapat_ve_ozetle(db, oturum, sistem_promptu, mesaj_gecmisi + [{"role": "assistant", "content": yanit}], ai)
        kapandi = True

    return MesajCevap(asistan_yaniti=yanit, oturum_kapandi_mi=kapandi, otomatik=otomatik)


@router.post("/oturum/{oturum_id}/bitir", status_code=204)
def oturumu_bitir(
    oturum_id: int,
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    oturum = db.get(OgrenciKoclukOturumu, oturum_id)
    if oturum is None or oturum.ogrenci_id != ogrenci.id:
        raise HTTPException(status_code=404, detail="Oturum bulunamadı.")
    if oturum.durum != "aktif":
        return

    mesajlar = (
        db.query(OgrenciKoclukMesaji)
        .filter(OgrenciKoclukMesaji.oturum_id == oturum.id)
        .order_by(OgrenciKoclukMesaji.olusturulma_zamani)
        .all()
    )
    from app.core.filiz_gizlilik import ogrenci_dizini, ogrenci_metni_maskele
    dizin = ogrenci_dizini(db, ogrenci)
    mesaj_gecmisi = [
        {"role": "user" if m.rol == "ogrenci" else "assistant", "content": ogrenci_metni_maskele(dizin, m.icerik, ogrenci.ad_soyad)}
        for m in mesajlar
    ]
    sistem_promptu = sistem_promptu_olustur(db, ogrenci, None)
    _oturumu_kapat_ve_ozetle(db, oturum, sistem_promptu, mesaj_gecmisi, _ai(db, ogrenci))


def _oturumu_kapat_ve_ozetle(db: Session, oturum: OgrenciKoclukOturumu, sistem_promptu: str, mesaj_gecmisi: list[dict], ai: bool = True):
    if not ai or not asistan_aktif_mi():   # [2026-10-10] otomatik rehber: konu başlığı özet olarak saklanır
        ilk = next((m["content"] for m in mesaj_gecmisi if m["role"] == "user"), "")
        ozet = f"Otomatik rehberle sohbet: \"{ilk[:80]}\"" if ilk else None
    else:
        ozet = oturumu_ozetle(sistem_promptu, mesaj_gecmisi) if mesaj_gecmisi else None
    oturum.durum = "tamamlandi"
    oturum.bitis_zamani = datetime.now(timezone.utc)
    oturum.ozet = ozet
    db.commit()


@router.get("/gecmis", response_model=list[GecmisOturumOut])
def gecmis_oturumlari_getir(
    db: Session = Depends(get_db),
    ogrenci: Ogrenci = Depends(get_mevcut_ogrenci),
):
    oturumlar = (
        db.query(OgrenciKoclukOturumu)
        .filter(OgrenciKoclukOturumu.ogrenci_id == ogrenci.id, OgrenciKoclukOturumu.durum == "tamamlandi")
        .order_by(OgrenciKoclukOturumu.bitis_zamani.desc())
        .limit(30)
        .all()
    )
    sonuc = []
    for o in oturumlar:
        mesajlar = (db.query(OgrenciKoclukMesaji).filter(OgrenciKoclukMesaji.oturum_id == o.id)
                    .order_by(OgrenciKoclukMesaji.olusturulma_zamani, OgrenciKoclukMesaji.id).all())
        if not mesajlar:
            continue
        ilk = next((m.icerik for m in mesajlar if m.rol == "ogrenci"), "")
        sonuc.append(GecmisOturumOut(oturum_id=o.id, baslama_zamani=o.baslama_zamani, bitis_zamani=o.bitis_zamani, ozet=o.ozet,
                                     baslik=(ilk[:70] + "…") if len(ilk) > 70 else ilk, mesaj_sayisi=len(mesajlar)))
    return sonuc


@router.get("/gecmis/{oturum_id}")
def gecmis_oturum_detayi(oturum_id: int, db: Session = Depends(get_db), ogrenci: Ogrenci = Depends(get_mevcut_ogrenci)):
    """[2026-10-10] Geçmiş bir sohbetin tüm mesajları (yalnızca kendi sohbetleri)."""
    o = db.get(OgrenciKoclukOturumu, oturum_id)
    if o is None or o.ogrenci_id != ogrenci.id:
        raise HTTPException(status_code=404, detail="Sohbet bulunamadı.")
    mesajlar = (db.query(OgrenciKoclukMesaji).filter(OgrenciKoclukMesaji.oturum_id == o.id)
                .order_by(OgrenciKoclukMesaji.olusturulma_zamani, OgrenciKoclukMesaji.id).all())
    return {"oturum_id": o.id, "baslama_zamani": o.baslama_zamani, "bitis_zamani": o.bitis_zamani, "ozet": o.ozet,
            "durum": o.durum, "mesajlar": [{"rol": m.rol, "icerik": m.icerik, "zaman": m.olusturulma_zamani} for m in mesajlar]}
