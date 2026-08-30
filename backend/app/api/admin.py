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
    Dal, Soru, SoruSecenegi, OgrenciKatmanOturumu, Degisken, SjtSecenekDegiskenAgirlik,
)
from app.core.security import sifre_hashle
from app.schemas.admin import (
    SistemParametresiOut, ParametreGuncelleIstek, BolumDurumIstek, BolumOut,
    BolumAciklamaIstek,
    BolumTopluAciklamaIstek, BolumTopluAciklamaSonucu,
    OgrenciBolumUyumDetayOut, AuditLogOut, OgrenciListeOut,
    YoneticiEkleIstek, RolGuncelleIstek, YoneticiOut,
    KontrolPaneliOut, PipelineDurumuOut, KatmanAgirligiOut, YeniAgirlikVersiyonuIstek,
    DalOut, DalEkleIstek, DalDurumIstek, SoruOut, SoruEkleIstek, SoruAktifIstek,
    PipelineYuklemeIstek, PipelineYuklemeSonucu, PipelineBolumAralikOut, PipelineTaslakGrubuOut,
    KullanimIstatistikleriOut, GunlukZiyaretOut, SayfaZiyaretOut,
    OgrenciDetayOut, OgrenciIstatistikleriOut, OkulSayisiOut, HedefBolumSayisiOut,
    BolumKademeIstatistigiOut, OkulKirilimOut, SinifKirilimOut, DetayliIstatistiklerOut,
    SoruGecerlilikYuklemeIstek, SoruGecerlilikOzetOut, SoruGecerlilikSonucuOut,
    SjtAgirlikGirisi, SecenekGirisi, DegiskenListeOut,
    TopluSoruYuklemeIstek, TopluSoruSonuc,
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


@router.post("/bolumler/toplu-aciklama", response_model=BolumTopluAciklamaSonucu)
def bolum_aciklamalarini_toplu_guncelle(
    istek: BolumTopluAciklamaIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    """[YENİ] CSV'den toplu bölüm açıklaması güncelleme — ad eşleşmesiyle çalışır."""
    bolum_map = {b.ad: b for b in db.query(Bolum).all()}
    guncellenen = 0
    eslesmeyenler = []

    for satir in istek.satirlar:
        bolum = bolum_map.get(satir.ad)
        if bolum is None:
            eslesmeyenler.append(satir.ad)
            continue
        bolum.kisa_aciklama = satir.kisa_aciklama.strip()
        guncellenen += 1

    _audit_yaz(db, admin, "bolum_aciklama_toplu_guncelleme", "bolumler", "toplu",
               f"{guncellenen} bölüm güncellendi, {len(eslesmeyenler)} eşleşmedi")
    db.commit()
    return BolumTopluAciklamaSonucu(guncellenen=guncellenen, eslesmeyenler=eslesmeyenler[:50])


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
    sorgu = (
        db.query(Soru, Katman.kod, Degisken.kod, Degisken.ad)
        .join(Katman, Katman.id == Soru.katman_id)
        .outerjoin(Degisken, Degisken.id == Soru.degisken_id)
    )
    if katman_kod:
        sorgu = sorgu.filter(Katman.kod == katman_kod)
    sonuc = sorgu.order_by(Soru.id).all()
    return [
        SoruOut(
            id=s.id, katman_kod=katman_kodu, degisken_kod=degisken_kodu, degisken_adi=degisken_adi,
            soru_tipi=s.soru_tipi, soru_metni=s.soru_metni, aktif_mi=s.aktif_mi,
        )
        for s, katman_kodu, degisken_kodu, degisken_adi in sonuc
    ]


@router.get("/degiskenler", response_model=list[DegiskenListeOut])
def degiskenleri_listele(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    satirlar = (
        db.query(Degisken, Katman.kod)
        .join(Katman, Katman.id == Degisken.katman_id)
        .order_by(Katman.kod, Degisken.kod)
        .all()
    )
    return [
        DegiskenListeOut(id=d.id, kod=d.kod, ad=d.ad, katman_kod=katman_kodu)
        for d, katman_kodu in satirlar
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
    if istek.soru_tipi == "likert" and istek.degisken_id is None:
        raise HTTPException(status_code=400, detail="Likert sorusu bir değişkene bağlı olmalı.")

    katman = db.get(Katman, istek.katman_id)
    if katman is None:
        raise HTTPException(status_code=404, detail="Katman bulunamadı.")

    soru = Soru(
        katman_id=istek.katman_id, degisken_id=istek.degisken_id, soru_tipi=istek.soru_tipi,
        soru_metni=istek.soru_metni, ters_kodlanmis_mi=istek.ters_kodlanmis_mi, aktif_mi=True,
    )
    db.add(soru)
    db.flush()

    for i, secenek_girisi in enumerate(istek.secenekler, start=1):
        secenek = SoruSecenegi(soru_id=soru.id, secenek_sirasi=i, secenek_metni=secenek_girisi.metin)
        db.add(secenek)
        db.flush()  # secenek.id lazım (SJT ağırlığı için)

        if istek.soru_tipi == "sjt":
            for agirlik_girisi in secenek_girisi.sjt_agirliklari:
                db.add(SjtSecenekDegiskenAgirlik(
                    secenek_id=secenek.id, degisken_id=agirlik_girisi.degisken_id,
                    agirlik=agirlik_girisi.agirlik,
                ))

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


# ============================================================================
# Kullanım İstatistikleri (sonradan eklendi)
# ============================================================================
# Kişi bazlı DEĞİL — yalnızca toplu/anonim sayım (sayfa_ziyaretleri tablosu,
# main.py'deki ZiyaretKaydiMiddleware tarafından doldurulur).

@router.get("/kullanim-istatistikleri", response_model=KullanimIstatistikleriOut)
def kullanim_istatistiklerini_getir(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    bugun_toplam = db.execute(
        text("SELECT COUNT(*) FROM sayfa_ziyaretleri WHERE zaman >= CURRENT_DATE")
    ).scalar() or 0

    son_7_gun_toplam = db.execute(
        text("SELECT COUNT(*) FROM sayfa_ziyaretleri WHERE zaman >= now() - interval '7 days'")
    ).scalar() or 0

    tip_dagilimi = dict(db.execute(
        text("""
            SELECT kullanici_tipi, COUNT(*) FROM sayfa_ziyaretleri
            WHERE zaman >= now() - interval '7 days'
            GROUP BY kullanici_tipi
        """)
    ).all())

    gunluk = db.execute(
        text("""
            SELECT to_char(zaman::date, 'YYYY-MM-DD') AS tarih, COUNT(*) AS sayi
            FROM sayfa_ziyaretleri
            WHERE zaman >= now() - interval '7 days'
            GROUP BY zaman::date
            ORDER BY zaman::date
        """)
    ).mappings().all()

    en_cok = db.execute(
        text("""
            SELECT yol, COUNT(*) AS sayi FROM sayfa_ziyaretleri
            WHERE zaman >= now() - interval '7 days'
            GROUP BY yol ORDER BY COUNT(*) DESC LIMIT 5
        """)
    ).mappings().all()

    return KullanimIstatistikleriOut(
        bugun_toplam=bugun_toplam,
        son_7_gun_toplam=son_7_gun_toplam,
        ogrenci_ziyaret=tip_dagilimi.get("ogrenci", 0),
        admin_ziyaret=tip_dagilimi.get("admin", 0),
        anonim_ziyaret=tip_dagilimi.get("anonim", 0),
        gunluk_dagilim=[GunlukZiyaretOut(tarih=g["tarih"], sayi=g["sayi"]) for g in gunluk],
        en_cok_ziyaret_edilen=[SayfaZiyaretOut(yol=e["yol"], sayi=e["sayi"]) for e in en_cok],
    )


# ============================================================================
# Öğrenci Detayları (sonradan eklendi)
# ============================================================================
# KVKK notu: bu uç nokta zaten yalnızca admin erişimindeki mevcut öğrenci
# tablosunu genişletiyor (yeni bir kişisel veri toplama değil) — okul ve
# hedef bölüm bilgisi öğrenci zaten kendi profilinde/koçlukta oluşturmuştu.

@router.get("/ogrenciler-detay", response_model=OgrenciIstatistikleriOut)
def ogrencileri_detayli_listele(
    limit: int = 100,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    satirlar = db.execute(
        text("""
            SELECT o.id, o.ad_soyad, o.email, o.okul, o.olusturulma_zamani,
                   b.ad AS hedef_bolum_adi, hb.bolum_id AS hedef_bolum_id
            FROM ogrenciler o
            LEFT JOIN ogrenci_hedef_bolum hb ON hb.ogrenci_id = o.id AND hb.aktif_mi = true
            LEFT JOIN bolumler b ON b.id = hb.bolum_id
            ORDER BY o.olusturulma_zamani DESC
            LIMIT :limit
        """),
        {"limit": limit},
    ).mappings().all()

    ogrenciler = []
    uyum_degerleri = []
    hedefi_olan = 0

    for r in satirlar:
        uyum = None
        if r["hedef_bolum_id"] is not None:
            hedefi_olan += 1
            uyum_satiri = db.execute(
                text("""
                    SELECT toplam_uyum FROM ogrenci_bolum_uyum_skorlari
                    WHERE ogrenci_id = :oid AND bolum_id = :bid
                    ORDER BY tur_id DESC LIMIT 1
                """),
                {"oid": str(r["id"]), "bid": r["hedef_bolum_id"]},
            ).first()
            if uyum_satiri:
                uyum = float(uyum_satiri[0])
                uyum_degerleri.append(uyum)

        ogrenciler.append(OgrenciDetayOut(
            id=str(r["id"]), ad_soyad=r["ad_soyad"], email=r["email"], okul=r["okul"],
            hedef_bolum_adi=r["hedef_bolum_adi"],
            hedef_bolum_uyum_orani=round(uyum, 2) if uyum is not None else None,
            olusturulma_zamani=r["olusturulma_zamani"],
        ))

    toplam = db.execute(text("SELECT COUNT(*) FROM ogrenciler")).scalar() or 0
    ortalama = round(sum(uyum_degerleri) / len(uyum_degerleri), 2) if uyum_degerleri else None

    en_cok_okul_satirlari = db.execute(
        text("""
            SELECT okul, COUNT(*) AS sayi FROM ogrenciler
            WHERE okul IS NOT NULL AND okul <> ''
            GROUP BY okul ORDER BY COUNT(*) DESC LIMIT 5
        """)
    ).mappings().all()

    en_cok_hedef_satirlari = db.execute(
        text("""
            SELECT b.ad AS bolum_adi, COUNT(*) AS sayi
            FROM ogrenci_hedef_bolum hb
            JOIN bolumler b ON b.id = hb.bolum_id
            WHERE hb.aktif_mi = true
            GROUP BY b.ad ORDER BY COUNT(*) DESC LIMIT 5
        """)
    ).mappings().all()

    return OgrenciIstatistikleriOut(
        toplam_ogrenci=toplam, hedefi_olan_ogrenci=hedefi_olan,
        ortalama_hedef_uyum_orani=ortalama,
        en_cok_okul=[OkulSayisiOut(okul=r["okul"], sayi=r["sayi"]) for r in en_cok_okul_satirlari],
        en_cok_hedeflenen_bolum=[HedefBolumSayisiOut(bolum_adi=r["bolum_adi"], sayi=r["sayi"]) for r in en_cok_hedef_satirlari],
        ogrenciler=ogrenciler,
    )


# ============================================================================
# Detaylı/Kademeli İstatistikler (sonradan eklendi)
# ============================================================================

@router.get("/istatistikler/detay", response_model=DetayliIstatistiklerOut)
def detayli_istatistikleri_getir(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    # --- Bölüm bazlı kademeli istatistik (hedefleyen -> yetiyor/sınırda/yetmiyor) ---
    hedef_satirlari = db.execute(
        text("""
            SELECT hb.bolum_id, b.ad AS bolum_adi,
                   (SELECT s.toplam_uyum FROM ogrenci_bolum_uyum_skorlari s
                    WHERE s.ogrenci_id = hb.ogrenci_id AND s.bolum_id = hb.bolum_id
                    ORDER BY s.tur_id DESC LIMIT 1) AS uyum
            FROM ogrenci_hedef_bolum hb
            JOIN bolumler b ON b.id = hb.bolum_id
            WHERE hb.aktif_mi = true
        """)
    ).mappings().all()

    bolum_gruplari: dict[int, dict] = {}
    for r in hedef_satirlari:
        grup = bolum_gruplari.setdefault(r["bolum_id"], {
            "bolum_adi": r["bolum_adi"], "hedefleyen": 0, "yetiyor": 0,
            "sinirda": 0, "yetmiyor": 0, "hesaplanmadi": 0, "uyumlar": [],
        })
        grup["hedefleyen"] += 1
        uyum = float(r["uyum"]) if r["uyum"] is not None else None
        if uyum is None:
            grup["hesaplanmadi"] += 1
        elif uyum >= 70:
            grup["yetiyor"] += 1
            grup["uyumlar"].append(uyum)
        elif uyum >= 40:
            grup["sinirda"] += 1
            grup["uyumlar"].append(uyum)
        else:
            grup["yetmiyor"] += 1
            grup["uyumlar"].append(uyum)

    bolumler = [
        BolumKademeIstatistigiOut(
            bolum_id=bid, bolum_adi=g["bolum_adi"], hedefleyen_sayisi=g["hedefleyen"],
            yetiyor_sayisi=g["yetiyor"], sinirda_sayisi=g["sinirda"], yetmiyor_sayisi=g["yetmiyor"],
            henuz_hesaplanmadi_sayisi=g["hesaplanmadi"],
            ortalama_uyum=round(sum(g["uyumlar"]) / len(g["uyumlar"]), 2) if g["uyumlar"] else None,
        )
        for bid, g in bolum_gruplari.items()
    ]
    bolumler.sort(key=lambda b: -b.hedefleyen_sayisi)

    # --- Okul kırılımı ---
    okul_satirlari = db.execute(
        text("""
            SELECT o.id AS ogrenci_id, o.okul, hb.bolum_id,
                   (SELECT s.toplam_uyum FROM ogrenci_bolum_uyum_skorlari s
                    WHERE s.ogrenci_id = o.id AND s.bolum_id = hb.bolum_id
                    ORDER BY s.tur_id DESC LIMIT 1) AS uyum
            FROM ogrenciler o
            LEFT JOIN ogrenci_hedef_bolum hb ON hb.ogrenci_id = o.id AND hb.aktif_mi = true
            WHERE o.okul IS NOT NULL AND o.okul <> ''
        """)
    ).mappings().all()

    okul_gruplari: dict[str, dict] = {}
    for r in okul_satirlari:
        grup = okul_gruplari.setdefault(r["okul"], {"ogrenci": 0, "hedefi_olan": 0, "uyumlar": []})
        grup["ogrenci"] += 1
        if r["bolum_id"] is not None:
            grup["hedefi_olan"] += 1
            if r["uyum"] is not None:
                grup["uyumlar"].append(float(r["uyum"]))

    okullar = [
        OkulKirilimOut(
            okul=okul, ogrenci_sayisi=g["ogrenci"], hedefi_olan_sayisi=g["hedefi_olan"],
            ortalama_uyum=round(sum(g["uyumlar"]) / len(g["uyumlar"]), 2) if g["uyumlar"] else None,
        )
        for okul, g in okul_gruplari.items()
    ]
    okullar.sort(key=lambda o: -o.ogrenci_sayisi)

    # --- Sınıf kırılımı ---
    sinif_satirlari = db.execute(
        text("""
            SELECT o.id AS ogrenci_id, o.sinif, hb.bolum_id,
                   (SELECT s.toplam_uyum FROM ogrenci_bolum_uyum_skorlari s
                    WHERE s.ogrenci_id = o.id AND s.bolum_id = hb.bolum_id
                    ORDER BY s.tur_id DESC LIMIT 1) AS uyum
            FROM ogrenciler o
            LEFT JOIN ogrenci_hedef_bolum hb ON hb.ogrenci_id = o.id AND hb.aktif_mi = true
            WHERE o.sinif IS NOT NULL AND o.sinif <> ''
        """)
    ).mappings().all()

    sinif_gruplari: dict[str, dict] = {}
    for r in sinif_satirlari:
        grup = sinif_gruplari.setdefault(r["sinif"], {"ogrenci": 0, "hedefi_olan": 0, "uyumlar": []})
        grup["ogrenci"] += 1
        if r["bolum_id"] is not None:
            grup["hedefi_olan"] += 1
            if r["uyum"] is not None:
                grup["uyumlar"].append(float(r["uyum"]))

    siniflar = [
        SinifKirilimOut(
            sinif=sinif, ogrenci_sayisi=g["ogrenci"], hedefi_olan_sayisi=g["hedefi_olan"],
            ortalama_uyum=round(sum(g["uyumlar"]) / len(g["uyumlar"]), 2) if g["uyumlar"] else None,
        )
        for sinif, g in sinif_gruplari.items()
    ]
    siniflar.sort(key=lambda s: -s.ogrenci_sayisi)

    return DetayliIstatistiklerOut(bolumler=bolumler, okullar=okullar, siniflar=siniflar)


# ============================================================================
# A7 — Soru Geçerlilik Testi (sonradan eklendi)
# ============================================================================
# Test hesaplaması (embedding) yerel pipeline'da (kullanıcının bilgisayarında)
# çalışır — bu uç noktalar yalnızca SONUCU yükler/görüntüler.

@router.post("/soru-gecerlilik/yukle", status_code=204)
def soru_gecerlilik_sonuclarini_yukle(
    istek: SoruGecerlilikYuklemeIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    if not istek.sonuclar:
        raise HTTPException(status_code=400, detail="Yüklenecek sonuç yok.")

    gecerli_soru_idler = {
        r[0] for r in db.execute(text("SELECT id FROM sorular")).all()
    }

    eslesmeyen = 0
    for s in istek.sonuclar:
        if s.soru_id not in gecerli_soru_idler:
            eslesmeyen += 1
            continue
        db.execute(
            text("""
                INSERT INTO soru_gecerlilik_sonuclari
                    (soru_id, gercek_degisken_kod, model_a_tahmin, model_a_dogru, model_a_benzerlik,
                     model_b_tahmin, model_b_dogru, model_b_benzerlik,
                     model_c_tahmin, model_c_dogru, model_c_benzerlik)
                VALUES
                    (:soru_id, :gercek, :a_t, :a_d, :a_b, :b_t, :b_d, :b_b, :c_t, :c_d, :c_b)
            """),
            {
                "soru_id": s.soru_id, "gercek": s.gercek_degisken_kod,
                "a_t": s.model_a_tahmin, "a_d": s.model_a_dogru, "a_b": s.model_a_benzerlik,
                "b_t": s.model_b_tahmin, "b_d": s.model_b_dogru, "b_b": s.model_b_benzerlik,
                "c_t": s.model_c_tahmin, "c_d": s.model_c_dogru, "c_b": s.model_c_benzerlik,
            },
        )

    _audit_yaz(db, admin, "soru_gecerlilik_yukleme", "soru_gecerlilik_sonuclari", "toplu",
               f"{len(istek.sonuclar) - eslesmeyen} sonuç yüklendi, {eslesmeyen} eşleşmedi")
    db.commit()


@router.get("/soru-gecerlilik", response_model=SoruGecerlilikOzetOut)
def soru_gecerlilik_sonuclarini_getir(
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    satirlar = db.execute(
        text("""
            SELECT DISTINCT ON (g.soru_id)
                g.soru_id, s.soru_metni, k.kod AS katman_kod, g.gercek_degisken_kod,
                g.model_a_tahmin, g.model_a_dogru, g.model_b_tahmin, g.model_b_dogru,
                g.model_c_tahmin, g.model_c_dogru, g.model_a_benzerlik, g.model_b_benzerlik,
                g.model_c_benzerlik, g.test_zamani
            FROM soru_gecerlilik_sonuclari g
            JOIN sorular s ON s.id = g.soru_id
            JOIN katmanlar k ON k.id = s.katman_id
            ORDER BY g.soru_id, g.test_zamani DESC
        """)
    ).mappings().all()

    sonuclar = []
    tam_dogru = kismi_dogru = hic_dogru_degil = 0
    for r in satirlar:
        kac_dogru = sum([r["model_a_dogru"], r["model_b_dogru"], r["model_c_dogru"]])
        if kac_dogru == 3:
            tam_dogru += 1
        elif kac_dogru == 0:
            hic_dogru_degil += 1
        else:
            kismi_dogru += 1
        ortalama_benzerlik = round(
            (float(r["model_a_benzerlik"]) + float(r["model_b_benzerlik"]) + float(r["model_c_benzerlik"])) / 3, 4
        )
        sonuclar.append(SoruGecerlilikSonucuOut(
            soru_id=r["soru_id"], soru_metni=r["soru_metni"], katman_kod=r["katman_kod"],
            gercek_degisken_kod=r["gercek_degisken_kod"],
            model_a_tahmin=r["model_a_tahmin"], model_a_dogru=r["model_a_dogru"],
            model_b_tahmin=r["model_b_tahmin"], model_b_dogru=r["model_b_dogru"],
            model_c_tahmin=r["model_c_tahmin"], model_c_dogru=r["model_c_dogru"],
            kac_model_dogru=kac_dogru, ortalama_benzerlik=ortalama_benzerlik,
            test_zamani=r["test_zamani"],
        ))

    sonuclar.sort(key=lambda s: (s.kac_model_dogru, s.ortalama_benzerlik))  # en sorunlu en üstte

    return SoruGecerlilikOzetOut(
        toplam_soru=len(sonuclar), tam_dogru=tam_dogru, kismi_dogru=kismi_dogru,
        hic_dogru_degil=hic_dogru_degil, sonuclar=sonuclar,
    )


# ============================================================================
# Birleşik Toplu Soru Yükleme (sonradan eklendi)
# ============================================================================
# TEK dosya, TEK format — 1. sütun katman, 2. sütun soru_tipi (likert/sjt).
# Uzun/tidy format: her satır bir (soru, seçenek[, sjt ağırlığı]) satırı.
# Aynı soru_gecici_id'ye sahip satırlar tek bir soruya gruplanır.

@router.post("/sorular/toplu", response_model=TopluSoruSonuc)
def sorulari_toplu_yukle(
    istek: TopluSoruYuklemeIstek,
    db: Session = Depends(get_db),
    admin: AdminKullanici = Depends(get_mevcut_admin),
):
    if not istek.satirlar:
        raise HTTPException(status_code=400, detail="Yüklenecek satır yok.")

    katman_map = {k.kod: k.id for k in db.query(Katman).all()}
    degisken_map = {d.kod: d.id for d in db.query(Degisken).all()}

    gruplar: dict[str, dict] = {}
    for satir in istek.satirlar:
        grup = gruplar.setdefault(satir.soru_gecici_id, {
            "katman_kod": satir.katman_kod, "soru_tipi": satir.soru_tipi,
            "degisken_kod": satir.degisken_kod, "soru_metni": satir.soru_metni,
            "ters_kodlanmis_mi": satir.ters_kodlanmis_mi, "secenekler": {},
        })
        secenek = grup["secenekler"].setdefault(satir.secenek_sira, {"metin": satir.secenek_metni, "agirliklar": []})
        if satir.soru_tipi == "sjt" and satir.sjt_degisken_kod:
            secenek["agirliklar"].append((satir.sjt_degisken_kod, satir.sjt_agirlik))

    eklenen_soru = eklenen_secenek = eklenen_agirlik = 0
    hatalar: list[str] = []

    for gecici_id, grup in gruplar.items():
        if grup["soru_tipi"] not in ("likert", "sjt"):
            hatalar.append(f"{gecici_id}: geçersiz soru_tipi '{grup['soru_tipi']}'")
            continue
        katman_id = katman_map.get(grup["katman_kod"])
        if katman_id is None:
            hatalar.append(f"{gecici_id}: bilinmeyen katman kodu '{grup['katman_kod']}'")
            continue
        if len(grup["secenekler"]) < 2:
            hatalar.append(f"{gecici_id}: en az 2 seçenek gerekli")
            continue

        degisken_id = None
        if grup["soru_tipi"] == "likert":
            degisken_id = degisken_map.get(grup["degisken_kod"])
            if degisken_id is None:
                hatalar.append(f"{gecici_id}: likert sorusu için geçersiz değişken kodu '{grup['degisken_kod']}'")
                continue

        gecersiz_kod = False
        if grup["soru_tipi"] == "sjt":
            for sira, sec in grup["secenekler"].items():
                for kod, _ in sec["agirliklar"]:
                    if kod not in degisken_map:
                        hatalar.append(f"{gecici_id} / seçenek {sira}: bilinmeyen değişken kodu '{kod}'")
                        gecersiz_kod = True
        if gecersiz_kod:
            continue

        soru = Soru(
            katman_id=katman_id, degisken_id=degisken_id, soru_tipi=grup["soru_tipi"],
            soru_metni=grup["soru_metni"], ters_kodlanmis_mi=grup["ters_kodlanmis_mi"], aktif_mi=True,
        )
        db.add(soru)
        db.flush()
        eklenen_soru += 1

        for sira in sorted(grup["secenekler"].keys()):
            sec = grup["secenekler"][sira]
            secenek_kaydi = SoruSecenegi(soru_id=soru.id, secenek_sirasi=sira, secenek_metni=sec["metin"])
            db.add(secenek_kaydi)
            db.flush()
            eklenen_secenek += 1
            for kod, agirlik in sec["agirliklar"]:
                db.add(SjtSecenekDegiskenAgirlik(
                    secenek_id=secenek_kaydi.id, degisken_id=degisken_map[kod], agirlik=agirlik,
                ))
                eklenen_agirlik += 1

    if eklenen_soru == 0:
        db.rollback()
        raise HTTPException(status_code=400, detail=f"Hiçbir soru eklenemedi. Hatalar: {'; '.join(hatalar[:10])}")

    _audit_yaz(db, admin, "soru_toplu_yukleme", "sorular", "toplu",
               f"{eklenen_soru} soru eklendi, {len(hatalar)} hata")
    db.commit()

    return TopluSoruSonuc(
        eklenen_soru_sayisi=eklenen_soru, eklenen_secenek_sayisi=eklenen_secenek,
        eklenen_agirlik_sayisi=eklenen_agirlik, hatalar=hatalar[:50],
    )
