"""
Admin uç noktaları.
GET/PUT /admin/parametreler         — E8, sistem parametreleri
POST    /admin/bolumler/{id}/durum  — E5, taslak->test_ediliyor->yayinda geçişi (audit loglu)
PUT     /admin/bolumler/{id}/aciklama — kısa açıklamayı günceller (öğrenciye Keşfet'te gösterilir)
GET     /admin/bolumler              — E5, tüm bölümler (durum dahil)
GET     /admin/uyum-detay/{ogrenci_id}/{bolum_id}  — E7, admin-only skor detayı
GET     /admin/audit-log             — E9
GET     /admin/ogrenciler            — E9
"""
from datetime import datetime, timezone
import uuid
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_admin, get_mevcut_super_admin
from app.core.database import get_db
from app.models import (
    AdminKullanici, SistemParametresi, Bolum, OgrenciBolumUyumSkoru,
    OgrenciDegerlendirmeTuru, AuditLog, Ogrenci, Katman, KatmanAgirligi,
    Dal, Soru, SoruSecenegi, OgrenciKatmanOturumu,
)
from app.core.security import sifre_hashle
from app.schemas.admin import (
    SistemParametresiOut, ParametreGuncelleIstek, BolumDurumIstek, BolumOut,
    BolumAciklamaIstek,
    OgrenciBolumUyumDetayOut, AuditLogOut, OgrenciListeOut,
    YoneticiEkleIstek, RolGuncelleIstek, YoneticiOut,
    KontrolPaneliOut, PipelineDurumuOut, KatmanAgirligiOut, YeniAgirlikVersiyonuIstek,
    DalOut, DalEkleIstek, DalDurumIstek, SoruOut, SoruEkleIstek, SoruAktifIstek,
    PipelineYuklemeIstek, PipelineYuklemeSonucu, PipelineBolumAralikOut, PipelineTaslakGrubuOut,
)

router = APIRouter()

_GECERLI_DURUMLAR = ("taslak", "test_ediliyor", "yayinda")
_GECERLI_GECISLER = {
    "taslak": {"test_ediliyor"},
    "test_ediliyor": {"yayinda", "taslak"},  # E5 mockup: "Reddet / Taslağa Döndür"
    "yayinda": set(),  # yayından geri dönüş bu iskeletin kapsamında değil — AÇIK KARAR
}


def _audit_yaz(db: Session, admin: AdminKullanici, islem: str, hedef_tablo: str, hedef_id: str, gerekce: str | None):
    db.add(AuditLog(admin_id=admin.id, islem=islem, hedef_tablo=hedef_tablo, hedef_id=hedef_id, gerekce=gerekce))


# ===================== E8 — Sistem Parametreleri ===================== #

@router.get("/parametreler", response_model=list[SistemParametresiOut])
def parametreleri_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    return db.query(SistemParametresi).order_by(SistemParametresi.anahtar).all()


@router.put("/parametreler/{anahtar}", response_model=SistemParametresiOut)
def parametreyi_guncelle(
    anahtar: str,
    istek: ParametreGuncelleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_super_admin),  # yalnızca super_admin
):
    parametre = db.query(SistemParametresi).filter(SistemParametresi.anahtar == anahtar).first()
    if parametre is None:
        raise HTTPException(status_code=404, detail=f"Parametre bulunamadı: {anahtar}")

    eski_deger = parametre.deger
    parametre.deger = istek.deger
    parametre.guncelleme_zamani = datetime.now(timezone.utc)
    parametre.guncelleyen_admin_id = admin.id

    _audit_yaz(db, admin, "parametre_guncelleme", "sistem_parametreleri", anahtar,
               f"{eski_deger} -> {istek.deger}")
    db.commit()
    db.refresh(parametre)
    return parametre


# ===================== E5 — Bölümler ===================== #

@router.get("/bolumler", response_model=list[BolumOut])
def bolumleri_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    return db.query(Bolum).order_by(Bolum.ad).all()


@router.post("/bolumler/{bolum_id}/durum", response_model=BolumOut)
def bolum_durumunu_degistir(
    bolum_id: int,
    istek: BolumDurumIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    E5 — taslak -> test_ediliyor -> yayinda akışı. Geçersiz bir geçiş
    (örn. taslak -> yayinda, ara adım atlanarak) reddedilir. Her geçiş
    audit_log'a yazılır — gerekçe zorunludur (E5 mockup: "onay/red gerekçesi").
    """
    if istek.yeni_durum not in _GECERLI_DURUMLAR:
        raise HTTPException(status_code=400, detail=f"Geçersiz durum: {istek.yeni_durum}")

    bolum = db.get(Bolum, bolum_id)
    if bolum is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")

    if istek.yeni_durum not in _GECERLI_GECISLER[bolum.durum]:
        raise HTTPException(
            status_code=400,
            detail=f"'{bolum.durum}' durumundan '{istek.yeni_durum}' durumuna doğrudan geçilemez.",
        )
    if not istek.gerekce or not istek.gerekce.strip():
        raise HTTPException(status_code=400, detail="Durum değişikliği için gerekçe zorunludur.")

    eski_durum = bolum.durum
    bolum.durum = istek.yeni_durum
    bolum.test_notu = istek.gerekce

    _audit_yaz(db, admin, "bolum_durum_degisikligi", "bolumler", str(bolum_id),
               f"{eski_durum} -> {istek.yeni_durum}: {istek.gerekce}")
    db.commit()
    db.refresh(bolum)
    return bolum


@router.put("/bolumler/{bolum_id}/aciklama", response_model=BolumOut)
def bolum_aciklamasini_guncelle(
    bolum_id: int,
    istek: BolumAciklamaIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    [YENİ] Bölümün kısa_aciklama alanını günceller — bu metin öğrenciye
    Katman 2 (Tüm Bölümleri Keşfet) ekranında gösterilir. Durum geçişinden
    (E5) bağımsız, ayrı bir uç nokta — içerik editörleri bunu sık sık
    değiştirebilmeli, bir durum geçişi/gerekçe gerektirmemeli.
    """
    if not istek.kisa_aciklama or not istek.kisa_aciklama.strip():
        raise HTTPException(status_code=400, detail="Açıklama boş olamaz.")

    bolum = db.get(Bolum, bolum_id)
    if bolum is None:
        raise HTTPException(status_code=404, detail="Bölüm bulunamadı.")

    eski = bolum.kisa_aciklama
    bolum.kisa_aciklama = istek.kisa_aciklama.strip()

    _audit_yaz(db, admin, "bolum_aciklama_guncelleme", "bolumler", str(bolum_id),
               f"'{eski}' -> '{istek.kisa_aciklama.strip()}'")
    db.commit()
    db.refresh(bolum)
    return bolum


# ===================== E7 — Model Yakınsaması / Geçerlilik (admin-only) ===================== #

@router.get("/uyum-detay/{ogrenci_id}/{bolum_id}", response_model=OgrenciBolumUyumDetayOut)
def uyum_detayini_getir(
    ogrenci_id: str,
    bolum_id: int,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    E7 — öğrenci API'sinde ASLA görünmeyen yontem_skorlari/kendall_w
    burada tam olarak döner. Bu, D5'teki gizlilik kuralının simetrik
    doğrulamasıdır: test_e2e_d4.py öğrenci response'unda bu alanların
    YOKLUĞUNU kanıtlıyordu; bu uç nokta admin response'unda VARLIĞINI kanıtlar.
    """
    try:
        ogrenci_uuid = UUID(ogrenci_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz öğrenci id formatı.")

    son_tur = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci_uuid, OgrenciDegerlendirmeTuru.durum == "tamamlandi")
        .order_by(OgrenciDegerlendirmeTuru.tur_no.desc())
        .first()
    )
    if son_tur is None:
        raise HTTPException(status_code=404, detail="Bu öğrenci için tamamlanmış bir tur yok.")

    skor = (
        db.query(OgrenciBolumUyumSkoru)
        .filter(
            OgrenciBolumUyumSkoru.ogrenci_id == ogrenci_uuid,
            OgrenciBolumUyumSkoru.tur_id == son_tur.id,
            OgrenciBolumUyumSkoru.bolum_id == bolum_id,
        )
        .first()
    )
    if skor is None:
        raise HTTPException(status_code=404, detail="Bu öğrenci-bölüm çifti için skor bulunamadı.")

    return OgrenciBolumUyumDetayOut(
        ogrenci_id=str(skor.ogrenci_id), bolum_id=skor.bolum_id, tur_id=skor.tur_id,
        toplam_uyum=float(skor.toplam_uyum), yontem_skorlari=skor.yontem_skorlari,
        kendall_w=float(skor.kendall_w) if skor.kendall_w is not None else None,
    )


# ===================== E9 — Öğrenciler & Audit Log ===================== #

@router.get("/audit-log", response_model=list[AuditLogOut])
def audit_log_getir(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    kayitlar = db.query(AuditLog).order_by(AuditLog.zaman.desc()).limit(limit).all()
    return [
        AuditLogOut(
            id=k.id, admin_id=str(k.admin_id), islem=k.islem, hedef_tablo=k.hedef_tablo,
            hedef_id=k.hedef_id, gerekce=k.gerekce, zaman=k.zaman,
        )
        for k in kayitlar
    ]


@router.get("/ogrenciler", response_model=list[OgrenciListeOut])
def ogrencileri_listele(
    limit: int = 50,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    ogrenciler = db.query(Ogrenci).order_by(Ogrenci.olusturulma_zamani.desc()).limit(limit).all()
    return [
        OgrenciListeOut(id=str(o.id), ad_soyad=o.ad_soyad, email=o.email, olusturulma_zamani=o.olusturulma_zamani)
        for o in ogrenciler
    ]


# ===================== Yönetici Yönetimi (yalnızca super_admin) ===================== #
# İlk admin hesabı bu API üzerinden oluşturulamaz (kimin admin olacağı
# herkese açık bir uç noktadan belirlenmemeli) — ama en az 1 super_admin
# zaten var olduğunda, YENİ yöneticiler bu uç noktalarla eklenir/düzenlenir.

_GECERLI_ROLLER = ("super_admin", "icerik_editoru")


@router.post("/yoneticiler", response_model=YoneticiOut, status_code=201)
def yonetici_ekle(
    istek: YoneticiEkleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_super_admin),
):
    if istek.rol not in _GECERLI_ROLLER:
        raise HTTPException(status_code=400, detail=f"Geçersiz rol: {istek.rol}")

    mevcut = db.query(AdminKullanici).filter(AdminKullanici.email == istek.email).first()
    if mevcut is not None:
        raise HTTPException(status_code=400, detail="Bu e-posta ile zaten bir yönetici hesabı var.")

    yeni = AdminKullanici(
        ad_soyad=istek.ad_soyad, email=istek.email,
        sifre_hash=sifre_hashle(istek.sifre), rol=istek.rol,
    )
    db.add(yeni)
    _audit_yaz(db, admin, "yonetici_ekleme", "admin_kullanicilar", istek.email, f"rol={istek.rol}")
    db.commit()
    db.refresh(yeni)
    return YoneticiOut(id=str(yeni.id), ad_soyad=yeni.ad_soyad, email=yeni.email, rol=yeni.rol, olusturulma_zamani=yeni.olusturulma_zamani)


@router.get("/yoneticiler", response_model=list[YoneticiOut])
def yoneticileri_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_super_admin),
):
    yoneticiler = db.query(AdminKullanici).order_by(AdminKullanici.olusturulma_zamani).all()
    return [
        YoneticiOut(id=str(y.id), ad_soyad=y.ad_soyad, email=y.email, rol=y.rol, olusturulma_zamani=y.olusturulma_zamani)
        for y in yoneticiler
    ]


@router.put("/yoneticiler/{yonetici_id}/rol", response_model=YoneticiOut)
def yonetici_rolunu_guncelle(
    yonetici_id: str,
    istek: RolGuncelleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_super_admin),
):
    if istek.yeni_rol not in _GECERLI_ROLLER:
        raise HTTPException(status_code=400, detail=f"Geçersiz rol: {istek.yeni_rol}")

    try:
        hedef_uuid = UUID(yonetici_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Geçersiz yönetici id formatı.")

    if hedef_uuid == admin.id:
        # [TASARIM KARARI] Bir super_admin kendi rolünü değiştiremez —
        # yanlışlıkla tek super_admin'in sistemi kilitlemesini önlemek için.
        raise HTTPException(status_code=400, detail="Kendi rolünü değiştiremezsin — başka bir super_admin'den iste.")

    hedef = db.get(AdminKullanici, hedef_uuid)
    if hedef is None:
        raise HTTPException(status_code=404, detail="Yönetici bulunamadı.")

    eski_rol = hedef.rol
    hedef.rol = istek.yeni_rol
    _audit_yaz(db, admin, "yonetici_rol_degisikligi", "admin_kullanicilar", str(hedef_uuid), f"{eski_rol} -> {istek.yeni_rol}")
    db.commit()
    db.refresh(hedef)
    return YoneticiOut(id=str(hedef.id), ad_soyad=hedef.ad_soyad, email=hedef.email, rol=hedef.rol, olusturulma_zamani=hedef.olusturulma_zamani)


# ===================== E1 — Kontrol Paneli ===================== #

@router.get("/kontrol-paneli", response_model=KontrolPaneliOut)
def kontrol_paneli_ozeti(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    toplam_bolum = db.query(Bolum).count()
    yayinda_bolum = db.query(Bolum).filter(Bolum.durum == "yayinda").count()
    tanimli_dal = db.query(Dal).count()
    toplam_ogrenci = db.query(Ogrenci).count()
    tamamlanan_tur = db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.durum == "tamamlandi").count()

    toplam_oturum = db.query(OgrenciKatmanOturumu).count()
    yarida_birakilan = db.query(OgrenciKatmanOturumu).filter(OgrenciKatmanOturumu.durum == "yarida_birakildi").count()
    yarida_birakma_orani = round(yarida_birakilan / toplam_oturum * 100, 2) if toplam_oturum > 0 else None

    return KontrolPaneliOut(
        toplam_bolum_sayisi=toplam_bolum, yayinda_bolum_sayisi=yayinda_bolum,
        tanimli_dal_sayisi=tanimli_dal, toplam_ogrenci_sayisi=toplam_ogrenci,
        tamamlanan_tur_sayisi=tamamlanan_tur, yarida_birakma_orani=yarida_birakma_orani,
    )


# ===================== E2 — Pipeline Durumu (STUB) ===================== #

@router.get("/pipeline-durumu", response_model=PipelineDurumuOut)
def pipeline_durumu_getir(
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    [STUB — gerçek iş mantığı yok] veritabani_taslagi.md'nin kendi ifadesiyle
    iş kuyruğu aracı (Celery/Redis) "henüz seçilmedi". Bu uç nokta yalnızca
    frontend'in "pipeline tetikle" butonunun bir yere bağlanabilmesi için var
    — gerçek bir pipeline çalıştırmaz, durum takip etmez. Gerçek iş kuyruğu
    kurulduğunda bu fonksiyonun tamamı değiştirilmeli.
    """
    return PipelineDurumuOut(
        durum="baglanti_yok",
        aciklama="İş kuyruğu altyapısı (Celery/Redis) henüz kurulmadı — bu uç nokta yer tutucudur.",
    )


# ===================== E3 — Katmanlar & Ağırlıklar ===================== #

@router.get("/katman-agirliklari", response_model=list[KatmanAgirligiOut])
def aktif_katman_agirliklarini_getir(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    satirlar = (
        db.query(KatmanAgirligi, Katman.kod)
        .join(Katman, Katman.id == KatmanAgirligi.katman_id)
        .filter(KatmanAgirligi.aktif_mi.is_(True))
        .all()
    )
    return [
        KatmanAgirligiOut(katman_kod=kod, agirlik=float(ka.agirlik), versiyon=ka.versiyon, aktif_mi=ka.aktif_mi)
        for ka, kod in satirlar
    ]


@router.post("/katman-agirliklari", response_model=list[KatmanAgirligiOut], status_code=201)
def yeni_agirlik_versiyonu_olustur(
    istek: YeniAgirlikVersiyonuIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_super_admin),
):
    """E3 — yeni bir ağırlık versiyonu ekler, öncekini pasife alır. Toplam %100 olmalı."""
    toplam = sum(istek.agirliklar.values())
    if abs(toplam - 100.0) > 0.01:
        raise HTTPException(status_code=400, detail=f"Ağırlıklar toplamı 100 olmalı, gelen: {toplam}")

    katmanlar = {k.kod: k for k in db.query(Katman).filter(Katman.kod.in_(istek.agirliklar.keys())).all()}
    eksik = set(istek.agirliklar.keys()) - set(katmanlar.keys())
    if eksik:
        raise HTTPException(status_code=400, detail=f"Bilinmeyen katman kodu: {eksik}")

    son_versiyon = db.query(KatmanAgirligi.versiyon).order_by(KatmanAgirligi.versiyon.desc()).first()
    yeni_versiyon_no = (son_versiyon[0] + 1) if son_versiyon else 1

    # eski versiyonu pasife al
    db.query(KatmanAgirligi).filter(KatmanAgirligi.aktif_mi.is_(True)).update({"aktif_mi": False})

    yeni_satirlar = []
    for kod, agirlik in istek.agirliklar.items():
        satir = KatmanAgirligi(katman_id=katmanlar[kod].id, versiyon=yeni_versiyon_no, agirlik=agirlik, aktif_mi=True)
        db.add(satir)
        yeni_satirlar.append((satir, kod))

    _audit_yaz(db, admin, "katman_agirlik_versiyonu", "katman_agirliklari", str(yeni_versiyon_no), str(istek.agirliklar))
    db.commit()
    return [
        KatmanAgirligiOut(katman_kod=kod, agirlik=float(satir.agirlik), versiyon=satir.versiyon, aktif_mi=satir.aktif_mi)
        for satir, kod in yeni_satirlar
    ]


# ===================== E4 — Dallar (K5) ===================== #

@router.get("/dallar", response_model=list[DalOut])
def dallari_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    return db.query(Dal).order_by(Dal.kod).all()


@router.post("/dallar", response_model=DalOut, status_code=201)
def dal_ekle(
    istek: DalEkleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    mevcut = db.query(Dal).filter(Dal.kod == istek.kod).first()
    if mevcut is not None:
        raise HTTPException(status_code=400, detail=f"'{istek.kod}' kodlu dal zaten var.")
    dal = Dal(kod=istek.kod, ad=istek.ad, bagli_degisken_id=istek.bagli_degisken_id, dogrulama_durumu="taslak")
    db.add(dal)
    _audit_yaz(db, admin, "dal_ekleme", "dallar", istek.kod, None)
    db.commit()
    db.refresh(dal)
    return dal


@router.post("/dallar/{dal_id}/durum", response_model=DalOut)
def dal_durumunu_guncelle(
    dal_id: int,
    istek: DalDurumIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    if istek.yeni_durum not in ("taslak", "guclu_kanitli", "gozden_gecirilmeli"):
        raise HTTPException(status_code=400, detail=f"Geçersiz durum: {istek.yeni_durum}")
    dal = db.get(Dal, dal_id)
    if dal is None:
        raise HTTPException(status_code=404, detail="Dal bulunamadı.")
    eski = dal.dogrulama_durumu
    dal.dogrulama_durumu = istek.yeni_durum
    _audit_yaz(db, admin, "dal_durum_degisikligi", "dallar", str(dal_id), f"{eski} -> {istek.yeni_durum}")
    db.commit()
    db.refresh(dal)
    return dal


# ===================== E6 — Soru Bankası ===================== #

@router.get("/sorular", response_model=list[SoruOut])
def sorulari_listele(
    katman_kod: str | None = None,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    sorgu = db.query(Soru, Katman.kod).join(Katman, Katman.id == Soru.katman_id)
    if katman_kod:
        sorgu = sorgu.filter(Katman.kod == katman_kod)
    sonuc = sorgu.order_by(Soru.id).all()
    return [
        SoruOut(id=s.id, katman_kod=kod, soru_tipi=s.soru_tipi, soru_metni=s.soru_metni, aktif_mi=s.aktif_mi)
        for s, kod in sonuc
    ]


@router.post("/sorular", response_model=SoruOut, status_code=201)
def soru_ekle(
    istek: SoruEkleIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    if istek.soru_tipi not in ("likert", "sjt"):
        raise HTTPException(status_code=400, detail=f"Geçersiz soru tipi: {istek.soru_tipi}")
    if len(istek.secenekler) < 2:
        raise HTTPException(status_code=400, detail="Bir soru en az 2 seçenek içermeli.")

    katman = db.get(Katman, istek.katman_id)
    if katman is None:
        raise HTTPException(status_code=404, detail="Katman bulunamadı.")

    soru = Soru(
        katman_id=istek.katman_id, degisken_id=istek.degisken_id, soru_tipi=istek.soru_tipi,
        soru_metni=istek.soru_metni, ters_kodlanmis_mi=istek.ters_kodlanmis_mi, aktif_mi=True,
    )
    db.add(soru)
    db.flush()
    for i, metin in enumerate(istek.secenekler, start=1):
        db.add(SoruSecenegi(soru_id=soru.id, secenek_sirasi=i, secenek_metni=metin))

    _audit_yaz(db, admin, "soru_ekleme", "sorular", str(soru.id), None)
    db.commit()
    db.refresh(soru)
    return SoruOut(id=soru.id, katman_kod=katman.kod, soru_tipi=soru.soru_tipi, soru_metni=soru.soru_metni, aktif_mi=soru.aktif_mi)


@router.post("/sorular/{soru_id}/aktiflik", response_model=SoruOut)
def soru_aktifligini_guncelle(
    soru_id: int,
    istek: SoruAktifIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    Soru silinmez — yalnızca aktif_mi=False yapılır (E6 kuralı: geçmiş
    öğrenci oturumları zaten kilitlenen_soru_id_listesi ile donduğu için
    bir sorunun silinmesi geçmiş verileri bozar).
    """
    soru = db.get(Soru, soru_id)
    if soru is None:
        raise HTTPException(status_code=404, detail="Soru bulunamadı.")
    eski = soru.aktif_mi
    soru.aktif_mi = istek.aktif_mi
    katman = db.get(Katman, soru.katman_id)
    _audit_yaz(db, admin, "soru_aktiflik_degisikligi", "sorular", str(soru_id), f"{eski} -> {istek.aktif_mi}")
    db.commit()
    db.refresh(soru)
    return SoruOut(id=soru.id, katman_kod=katman.kod, soru_tipi=soru.soru_tipi, soru_metni=soru.soru_metni, aktif_mi=soru.aktif_mi)


# ============================================================================
# Pipeline Sonuçları (sonradan eklendi)
# ============================================================================
# Pipeline sizin bilgisayarınızda çalışır (bulutta değil — maliyet/karmaşıklık
# nedeniyle bilinçli bir tercih). Bu uç noktalar, o çıktının admin panelinden
# GÜVENLİ şekilde (önce taslak, yalnızca onaylanınca canlıya) yüklenmesini
# sağlar. Taslak aşamasında canlı bolum_agirliklari tablosuna HİÇBİR yazma
# işlemi yapılmaz.

def _bolum_aralik_istatistigi(db: Session, yukleme_grubu: str) -> tuple[list[PipelineBolumAralikOut], float]:
    satirlar = db.execute(
        text("""
            SELECT b.ad AS bolum_adi, MIN(t.agirlik_degeri) AS min_deger, MAX(t.agirlik_degeri) AS max_deger
            FROM bolum_agirliklari_taslak t
            JOIN bolumler b ON b.id = t.bolum_id
            WHERE t.yukleme_grubu = :grup
            GROUP BY b.ad
            ORDER BY (MAX(t.agirlik_degeri) - MIN(t.agirlik_degeri)) ASC
        """),
        {"grup": yukleme_grubu},
    ).mappings().all()

    hepsi = [
        PipelineBolumAralikOut(
            bolum_adi=r["bolum_adi"], min_deger=float(r["min_deger"]), max_deger=float(r["max_deger"]),
            aralik=float(r["max_deger"]) - float(r["min_deger"]),
        )
        for r in satirlar
    ]
    ortalama = sum(b.aralik for b in hepsi) / len(hepsi) if hepsi else 0.0
    return hepsi[:10], round(ortalama, 2)


@router.post("/pipeline/yukle", response_model=PipelineYuklemeSonucu)
def pipeline_ciktisi_yukle(
    istek: PipelineYuklemeIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """
    Pipeline'ın (sizin bilgisayarınızda üretilen) CSV çıktısını taslak
    tabloya yükler. CANLI bolum_agirliklari tablosuna DOKUNMAZ — yalnızca
    /onayla çağrıldığında gerçek tabloya yazılır.
    """
    if not istek.satirlar:
        raise HTTPException(status_code=400, detail="Yüklenecek satır yok.")

    yukleme_grubu = str(uuid.uuid4())

    # bölüm adı / değişken kodu -> id eşleme tabloları (tek seferde çekilir)
    bolum_map = {ad: bid for bid, ad in db.execute(text("SELECT id, ad FROM bolumler")).all()}
    degisken_map = {kod: did for did, kod in db.execute(text("SELECT id, kod FROM degiskenler")).all()}

    eslesmeyen = []
    eslesen_sayisi = 0

    for satir in istek.satirlar:
        bolum_id = bolum_map.get(satir.bolum_adi)
        degisken_id = degisken_map.get(satir.degisken_kod)
        if bolum_id is None or degisken_id is None:
            eslesmeyen.append(f"{satir.bolum_adi} / {satir.degisken_kod}")
            continue
        eslesen_sayisi += 1
        db.execute(
            text("""
                INSERT INTO bolum_agirliklari_taslak
                    (yukleme_grubu, bolum_adi_ham, degisken_kod_ham, bolum_id, degisken_id,
                     agirlik_degeri, yakinsama_skoru, agirlikli_varyans, etkin_meslek_sayisi,
                     yukleyen_admin_id, durum)
                VALUES
                    (:grup, :bolum_ham, :degisken_ham, :bolum_id, :degisken_id,
                     :agirlik, :yakinsama, :varyans, :etkin_meslek, :admin_id, 'bekliyor')
            """),
            {
                "grup": yukleme_grubu, "bolum_ham": satir.bolum_adi, "degisken_ham": satir.degisken_kod,
                "bolum_id": bolum_id, "degisken_id": degisken_id, "agirlik": satir.agirlik_degeri,
                "yakinsama": satir.yakinsama_skoru, "varyans": satir.agirlikli_varyans,
                "etkin_meslek": satir.etkin_meslek_sayisi, "admin_id": str(admin.id),
            },
        )

    if eslesen_sayisi == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail="Hiçbir satır eşleşmedi — bölüm adları/değişken kodları kontrol edilmeli.")

    _audit_yaz(db, admin, "pipeline_ciktisi_yukleme", "bolum_agirliklari_taslak", yukleme_grubu,
               f"{eslesen_sayisi} satır yüklendi, {len(eslesmeyen)} eşleşmedi")
    db.commit()

    en_duz_10, ortalama_aralik = _bolum_aralik_istatistigi(db, yukleme_grubu)
    bolum_sayisi = db.execute(
        text("SELECT COUNT(DISTINCT bolum_id) FROM bolum_agirliklari_taslak WHERE yukleme_grubu = :grup"),
        {"grup": yukleme_grubu},
    ).scalar()

    return PipelineYuklemeSonucu(
        yukleme_grubu=yukleme_grubu, toplam_satir=len(istek.satirlar), eslesen_satir=eslesen_sayisi,
        eslesmeyen_satirlar=eslesmeyen[:50],  # çok uzunsa kırp
        bolum_sayisi=bolum_sayisi or 0, ortalama_aralik=ortalama_aralik, en_duz_10=en_duz_10,
    )


@router.get("/pipeline/taslaklar", response_model=list[PipelineTaslakGrubuOut])
def pipeline_taslaklarini_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    gruplar = db.execute(
        text("""
            SELECT yukleme_grubu, MIN(yuklenme_zamani) AS yuklenme_zamani,
                   COUNT(*) AS toplam_satir, COUNT(DISTINCT bolum_id) AS bolum_sayisi,
                   MAX(durum) AS durum
            FROM bolum_agirliklari_taslak
            GROUP BY yukleme_grubu
            ORDER BY MIN(yuklenme_zamani) DESC
        """)
    ).mappings().all()

    sonuc = []
    for g in gruplar:
        _, ortalama = _bolum_aralik_istatistigi(db, str(g["yukleme_grubu"]))
        sonuc.append(PipelineTaslakGrubuOut(
            yukleme_grubu=str(g["yukleme_grubu"]), yuklenme_zamani=g["yuklenme_zamani"],
            toplam_satir=g["toplam_satir"], bolum_sayisi=g["bolum_sayisi"],
            ortalama_aralik=ortalama, durum=g["durum"],
        ))
    return sonuc


@router.get("/pipeline/taslaklar/{grup}", response_model=PipelineYuklemeSonucu)
def pipeline_taslak_detayi(
    grup: str,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    en_duz_10, ortalama = _bolum_aralik_istatistigi(db, grup)
    if not en_duz_10:
        raise HTTPException(status_code=404, detail="Taslak grubu bulunamadı.")
    toplam = db.execute(text("SELECT COUNT(*) FROM bolum_agirliklari_taslak WHERE yukleme_grubu = :g"), {"g": grup}).scalar()
    bolum_sayisi = db.execute(text("SELECT COUNT(DISTINCT bolum_id) FROM bolum_agirliklari_taslak WHERE yukleme_grubu = :g"), {"g": grup}).scalar()
    return PipelineYuklemeSonucu(
        yukleme_grubu=grup, toplam_satir=toplam, eslesen_satir=toplam, eslesmeyen_satirlar=[],
        bolum_sayisi=bolum_sayisi, ortalama_aralik=ortalama, en_duz_10=en_duz_10,
    )


@router.post("/pipeline/taslaklar/{grup}/onayla", status_code=204)
def pipeline_taslagini_onayla(
    grup: str,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_super_admin),  # yalnızca super_admin canlıya alabilir
):
    """
    Taslağı gerçek bolum_agirliklari tablosuna YENİ bir versiyon olarak
    yazar. Eski versiyon SİLİNMEZ (skor_motoru zaten en yüksek versiyonu
    kullanıyor) — geçmişe dönük inceleme için durur.
    """
    var_mi = db.execute(text("SELECT 1 FROM bolum_agirliklari_taslak WHERE yukleme_grubu = :g AND durum = 'bekliyor' LIMIT 1"), {"g": grup}).first()
    if not var_mi:
        raise HTTPException(status_code=404, detail="Onay bekleyen taslak bulunamadı (zaten işlenmiş olabilir).")

    yeni_versiyon = (db.execute(text("SELECT COALESCE(MAX(versiyon), 0) + 1 FROM bolum_agirliklari")).scalar())

    db.execute(
        text("""
            INSERT INTO bolum_agirliklari (bolum_id, degisken_id, agirlik_degeri, yakinsama_skoru, agirlikli_varyans, etkin_meslek_sayisi, versiyon)
            SELECT bolum_id, degisken_id, agirlik_degeri, yakinsama_skoru, agirlikli_varyans, etkin_meslek_sayisi, :versiyon
            FROM bolum_agirliklari_taslak
            WHERE yukleme_grubu = :grup AND durum = 'bekliyor'
        """),
        {"versiyon": yeni_versiyon, "grup": grup},
    )
    db.execute(text("UPDATE bolum_agirliklari_taslak SET durum = 'onaylandi' WHERE yukleme_grubu = :g"), {"g": grup})

    _audit_yaz(db, admin, "pipeline_taslagi_onaylama", "bolum_agirliklari", grup, f"versiyon {yeni_versiyon} olarak canlıya alındı")
    db.commit()


@router.post("/pipeline/taslaklar/{grup}/reddet", status_code=204)
def pipeline_taslagini_reddet(
    grup: str,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    db.execute(text("UPDATE bolum_agirliklari_taslak SET durum = 'reddedildi' WHERE yukleme_grubu = :g AND durum = 'bekliyor'"), {"g": grup})
    _audit_yaz(db, admin, "pipeline_taslagi_reddetme", "bolum_agirliklari_taslak", grup, None)
    db.commit()
