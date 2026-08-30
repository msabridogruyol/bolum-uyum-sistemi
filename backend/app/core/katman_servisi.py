"""
D2 katman akışı iş mantığı — tur yönetimi (D2c), soru kilitleme (D2),
Likert puanlama formülü (D2), katman tamamlama.

Bu dosya router'dan ayrı tutuldu ki iş kuruları test edilebilir kalsın.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, Katman, Soru, SoruSecenegi, SjtSecenekDegiskenAgirlik,
    OgrenciDegerlendirmeTuru, OgrenciKatmanOturumu, OgrenciCevap,
    OgrenciDegiskenSkoru, SistemParametresi,
)
# [EKLENDİ] Güven skoru — tur tamamlanınca otomatik hesaplanır.
from app.core.guvenlik_servisi import guven_skorunu_hesapla_ve_kaydet


class IsKuraliHatasi(Exception):
    """İş kuralı ihlali — 400 seviyesinde bir HTTP hatasına çevrilir (router'da)."""


def parametre_oku(db: Session, anahtar: str, varsayilan: str) -> str:
    p = db.query(SistemParametresi).filter(SistemParametresi.anahtar == anahtar).first()
    return p.deger if p is not None else varsayilan


def son_tur_getir(db: Session, ogrenci: Ogrenci) -> OgrenciDegerlendirmeTuru:
    """
    K5/dal akışları için — aktif_veya_yeni_tur_getir'den FARKLI olarak, yeni
    tur açmaya çalışmaz ve 120 günlük kısıtı tetiklemez. K5, K1-K4 tamamlanıp
    tur.durum='tamamlandi' olduktan SONRA gerçekleşir; bu yüzden "yalnızca
    devam_ediyor turu bul" mantığı (aktif_veya_yeni_tur_getir) burada yanlış
    olurdu — öğrencinin en son turunu (tamamlanmış olsa bile) döner.
    """
    tur = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id)
        .order_by(OgrenciDegerlendirmeTuru.tur_no.desc())
        .first()
    )
    if tur is None:
        raise IsKuraliHatasi("Henüz bir değerlendirme turun yok — önce K1-K4'ü tamamlamalısın.")
    return tur


def aktif_veya_yeni_tur_getir(db: Session, ogrenci: Ogrenci) -> OgrenciDegerlendirmeTuru:
    """
    D2c — Öğrencinin 'devam_ediyor' durumundaki turu varsa onu döner.
    Yoksa, son tamamlanan turdan bu yana yeniden_degerlendirme_min_gun
    geçmiş mi kontrol edip yeni bir tur açar.
    """
    aktif = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(
            OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id,
            OgrenciDegerlendirmeTuru.durum == "devam_ediyor",
        )
        .first()
    )
    if aktif is not None:
        return aktif

    son_tamamlanan = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(
            OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id,
            OgrenciDegerlendirmeTuru.durum == "tamamlandi",
        )
        .order_by(OgrenciDegerlendirmeTuru.tur_no.desc())
        .first()
    )

    yeni_tur_no = 1
    if son_tamamlanan is not None:
        min_gun = int(parametre_oku(db, "yeniden_degerlendirme_min_gun", "120"))
        simdi = datetime.now(timezone.utc)
        tamamlanma = son_tamamlanan.tamamlanma_zamani
        # [NOT] SQLite test ortamında TIMESTAMPTZ timezone bilgisini korumaz,
        # okunan değer naive döner; üretimde PostgreSQL bunu doğru saklar.
        # Karşılaştırmayı her iki ortamda da güvenli kılmak için normalize ediyoruz.
        if tamamlanma is not None and tamamlanma.tzinfo is None:
            tamamlanma = tamamlanma.replace(tzinfo=timezone.utc)
        if tamamlanma is not None and (simdi - tamamlanma) < timedelta(days=min_gun):
            kalan = timedelta(days=min_gun) - (simdi - tamamlanma)
            raise IsKuraliHatasi(
                f"Yeniden değerlendirme için henüz erken. En erken {kalan.days} gün sonra tekrar deneyebilirsin."
            )
        yeni_tur_no = son_tamamlanan.tur_no + 1

    yeni_tur = OgrenciDegerlendirmeTuru(ogrenci_id=ogrenci.id, tur_no=yeni_tur_no, durum="devam_ediyor")
    db.add(yeni_tur)
    try:
        db.flush()
    except IntegrityError:
        # [DÜZELTME — Playwright uçtan uca testinde bulundu] Eşzamanlı iki
        # istek (React StrictMode'un geliştirme modunda useEffect'i kasıtlı
        # iki kez tetiklemesi, ya da gerçek kullanıcıda çift tıklama/çoklu
        # sekme) aynı anda buraya gelirse, ikisi de "aktif tur yok" görüp
        # aynı tur_no ile satır oluşturmaya çalışabilir — UNIQUE kısıtı
        # (ogrenci_id, tur_no) ikincisini reddeder. Bunu hata olarak
        # kullanıcıya yansıtmak yerine, diğer isteğin oluşturduğu satırı
        # bulup onu döndürüyoruz — kullanıcı hiçbir şey fark etmez.
        db.rollback()
        aktif = (
            db.query(OgrenciDegerlendirmeTuru)
            .filter(
                OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id,
                OgrenciDegerlendirmeTuru.durum == "devam_ediyor",
            )
            .first()
        )
        if aktif is not None:
            return aktif
        raise  # gerçekten başka bir sorunsa hatayı yeniden fırlat
    return yeni_tur


def katman_oturumu_baslat(
    db: Session, ogrenci: Ogrenci, katman: Katman, tur: OgrenciDegerlendirmeTuru
) -> tuple[OgrenciKatmanOturumu, list[Soru]]:
    """
    D2 — 'Her katmana başlarken o anki aktif soru seti donar
    (kilitlenen_soru_id_listesi)' kuralını uygular. Oturum zaten varsa
    (öğrenci geri dönmüşse) donmuş soru setini aynen döner — admin bu
    sırada soru değiştirse bile öğrenci tutarlı kalır.
    """
    oturum = (
        db.query(OgrenciKatmanOturumu)
        .filter(
            OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
            OgrenciKatmanOturumu.tur_id == tur.id,
            OgrenciKatmanOturumu.katman_id == katman.id,
        )
        .first()
    )

    if oturum is not None and oturum.kilitlenen_soru_id_listesi:
        soru_idler = oturum.kilitlenen_soru_id_listesi
        sorular = db.query(Soru).filter(Soru.id.in_(soru_idler)).all()
        # DB sırası garanti değildir — kilitlenen sırayı koru
        sirali = sorted(sorular, key=lambda s: soru_idler.index(s.id))
        return oturum, sirali

    if oturum is not None and oturum.durum == "tamamlandi":
        raise IsKuraliHatasi(f"{katman.kod} bu tur için zaten tamamlandı.")

    aktif_sorular = (
        db.query(Soru)
        .filter(Soru.katman_id == katman.id, Soru.aktif_mi.is_(True))
        .order_by(Soru.id)
        .all()
    )
    if not aktif_sorular:
        raise IsKuraliHatasi(f"{katman.kod} için aktif soru bulunamadı — admin henüz soru eklememiş olabilir.")

    soru_idler = [s.id for s in aktif_sorular]

    if oturum is None:
        oturum = OgrenciKatmanOturumu(
            ogrenci_id=ogrenci.id, tur_id=tur.id, katman_id=katman.id,
            durum="devam_ediyor", kilitlenen_soru_id_listesi=soru_idler,
            baslama_zamani=datetime.now(timezone.utc),
        )
        db.add(oturum)
    else:
        oturum.kilitlenen_soru_id_listesi = soru_idler
        oturum.durum = "devam_ediyor"
        oturum.baslama_zamani = datetime.now(timezone.utc)

    db.flush()
    return oturum, aktif_sorular


def cevabi_kaydet(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru, soru_id: int, secenek_id: int) -> None:
    secenek = db.get(SoruSecenegi, secenek_id)
    if secenek is None or secenek.soru_id != soru_id:
        raise IsKuraliHatasi("Geçersiz seçenek — bu soruya ait değil.")

    mevcut = (
        db.query(OgrenciCevap)
        .filter(
            OgrenciCevap.ogrenci_id == ogrenci.id,
            OgrenciCevap.tur_id == tur.id,
            OgrenciCevap.soru_id == soru_id,
        )
        .first()
    )
    if mevcut is not None:
        mevcut.secenek_id = secenek_id
        mevcut.cevap_zamani = datetime.now(timezone.utc)
    else:
        db.add(OgrenciCevap(ogrenci_id=ogrenci.id, tur_id=tur.id, soru_id=soru_id, secenek_id=secenek_id))
    db.flush()


def likert_puan(secenek_sirasi: int, toplam_secenek: int, ters_kodlanmis_mi: bool) -> float:
    """D2 — puan = (seçenek_sırası - 1) / (toplam_seçenek - 1) × 100; ters kodlamada 100 - puan."""
    if toplam_secenek <= 1:
        return 50.0
    puan = (secenek_sirasi - 1) / (toplam_secenek - 1) * 100
    return 100 - puan if ters_kodlanmis_mi else puan


def katmani_tamamla(
    db: Session, ogrenci: Ogrenci, katman: Katman, tur: OgrenciDegerlendirmeTuru, oturum: OgrenciKatmanOturumu
) -> list[tuple[int, float]]:
    """
    Katmandaki tüm sorular cevaplanmışsa, D2'deki formülle her değişken için
    nihai puanı hesaplar (aynı değişkene birden fazla soru bağlıysa
    ortalaması alınır — [ÇIKARIM], belgede birden fazla soru/değişken
    durumu için birleştirme kuralı açıkça yazılmamıştı), ogrenci_degisken_skorlari'na
    yazar, oturumu 'tamamlandi' yapar. Dönen liste: [(degisken_id, puan), ...]

    [NOT] soru_tipi='kontrol' soruları buradan bilinçli olarak DIŞLANIR —
    bunlar hiçbir değişken puanına katkı yapmaz, yalnızca güven skoru
    hesaplamasında (guvenlik_servisi.py) kullanılır.
    """
    soru_idler = oturum.kilitlenen_soru_id_listesi or []
    sorular = {s.id: s for s in db.query(Soru).filter(Soru.id.in_(soru_idler)).all()}

    cevaplar = (
        db.query(OgrenciCevap)
        .filter(OgrenciCevap.ogrenci_id == ogrenci.id, OgrenciCevap.tur_id == tur.id, OgrenciCevap.soru_id.in_(soru_idler))
        .all()
    )
    cevaplanan_soru_idler = {c.soru_id for c in cevaplar}
    eksik = set(soru_idler) - cevaplanan_soru_idler
    if eksik:
        raise IsKuraliHatasi(f"{len(eksik)} soru henüz cevaplanmadı — katman tamamlanamaz.")

    # değişken_id -> puan listesi
    degisken_puanlari: dict[int, list[float]] = {}

    for cevap in cevaplar:
        soru = sorular[cevap.soru_id]
        secenek = db.get(SoruSecenegi, cevap.secenek_id)
        toplam_secenek = db.query(func.count(SoruSecenegi.id)).filter(SoruSecenegi.soru_id == soru.id).scalar()

        if soru.soru_tipi == "likert":
            if soru.degisken_id is None:
                continue
            puan = likert_puan(secenek.secenek_sirasi, toplam_secenek, soru.ters_kodlanmis_mi)
            degisken_puanlari.setdefault(soru.degisken_id, []).append(puan)

        elif soru.soru_tipi == "sjt":
            # [ÇIKARIM] — SJT ağırlığı (0-1 aralığı varsayılıyor) doğrudan
            # o değişken için 0-100 skalasına ölçeklenip katkı puanı sayılır.
            agirliklar = (
                db.query(SjtSecenekDegiskenAgirlik)
                .filter(SjtSecenekDegiskenAgirlik.secenek_id == cevap.secenek_id)
                .all()
            )
            for a in agirliklar:
                degisken_puanlari.setdefault(a.degisken_id, []).append(float(a.agirlik) * 100)

        # soru_tipi == "kontrol" -> hiçbir değişkene puan katkısı yapılmaz (kasıtlı)

    sonuc: list[tuple[int, float]] = []
    for degisken_id, puanlar in degisken_puanlari.items():
        nihai_puan = round(sum(puanlar) / len(puanlar), 2)
        nihai_puan = max(0.0, min(100.0, nihai_puan))

        mevcut_skor = (
            db.query(OgrenciDegiskenSkoru)
            .filter(
                OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
                OgrenciDegiskenSkoru.tur_id == tur.id,
                OgrenciDegiskenSkoru.degisken_id == degisken_id,
            )
            .first()
        )
        if mevcut_skor is not None:
            mevcut_skor.puan = nihai_puan
        else:
            db.add(OgrenciDegiskenSkoru(ogrenci_id=ogrenci.id, tur_id=tur.id, degisken_id=degisken_id, puan=nihai_puan))
        sonuc.append((degisken_id, nihai_puan))

    oturum.durum = "tamamlandi"
    oturum.tamamlanma_zamani = datetime.now(timezone.utc)
    db.flush()
    return sonuc


def tum_ana_katmanlar_tamamlandi_mi(db: Session, ogrenci: Ogrenci, tur: OgrenciDegerlendirmeTuru) -> bool:
    """D4 — K1-K4'ün dördü de tamamlanmadan TOPLAM_UYUM hesaplanmaz kuralının ön koşulu."""
    ana_katmanlar = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).all()
    tamam_sayisi = (
        db.query(func.count(OgrenciKatmanOturumu.id))
        .filter(
            OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
            OgrenciKatmanOturumu.tur_id == tur.id,
            OgrenciKatmanOturumu.katman_id.in_([k.id for k in ana_katmanlar]),
            OgrenciKatmanOturumu.durum == "tamamlandi",
        )
        .scalar()
    )
    if tamam_sayisi == len(ana_katmanlar):
        tur.durum = "tamamlandi"
        tur.tamamlanma_zamani = datetime.now(timezone.utc)
        db.flush()
        # [EKLENDİ] Güven skoru — kontrol soruları + güvenlik olayları
        # birleştirilip hesaplanır, eşik altındaysa tur.sonuc_gecerli_mi=False olur.
        guven_skorunu_hesapla_ve_kaydet(db, ogrenci, tur)
        return True
    return False
