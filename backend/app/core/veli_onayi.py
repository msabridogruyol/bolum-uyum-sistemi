"""
[2026-11-05] Veli onayı (18 yaş altı öğrenciler).

Kullanıcı kararları: basılı form + panelden işaret; onay gelene kadar kişisel veri işleyen asıl işlemler kilitli
(deps.get_kvkk_onayli_ogrenci: değerlendirme, yapay zekâ sohbeti, CV / mülakat, anket, portfolyo); okul yetkilisi ve
süper admin tamamlanma durumunu görür.

Durum (öğrenci başına en son veli_onaylari satırı):
  alindi      — imzalı form okula ulaştı (zorunlu maddeler onaylı); kamera: velinin isteğe bağlı kamera rızası
  resit       — öğrenci 18 yaşını doldurmuş (okul kimlikten doğrular); veli onayı gerekmez
  geri_alindi — veli rızasını geri aldı ya da yanlış işaret düzeltildi → yeniden kilitli
Test hesapları (ogrenciler.test_hesabi) bu kuraldan muaftır.
Öğrencinin kendi girdiği doğum tarihi muafiyet için KULLANILMAZ (öğrenci değiştirebilir); reşitliği okul işaretler.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.katman_servisi import IsKuraliHatasi
from app.core.kvkk_metinleri import VELI_FORM_SURUM

ISLEM_AD = {"alindi": "Veli onayı alındı", "resit": "18 yaşını doldurmuş (veli onayı gerekmez)", "geri_alindi": "Geri alındı"}
KILIT_MESAJI = ("Veli onay formun okuluna ulaşmadan bu bölüme başlayamazsın. Formu Ana Sayfa'dan indir, velin "
                "imzalasın ve okuluna teslim et; okulun işaretleyince kilit kalkar.")


def _bugun() -> date:
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).date()


def toplu_durum(db: Session, ogrenci_idler: list) -> dict:
    """{ogrenci_id: {"tamam", "islem", "form_tarihi", "veli_ad_soyad", "kamera", "yapan_ad", "zaman", "muaf"}}"""
    if not ogrenci_idler:
        return {}
    rows = db.execute(text("""
        SELECT o.id, o.test_hesabi, v.islem, v.form_tarihi, v.veli_ad_soyad, v.kamera, v.yapan_ad, v.zaman
          FROM ogrenciler o
          LEFT JOIN LATERAL (SELECT * FROM veli_onaylari x WHERE x.ogrenci_id = o.id
                              ORDER BY x.zaman DESC, x.id DESC LIMIT 1) v ON TRUE
         WHERE o.id = ANY(:ids)"""), {"ids": list(ogrenci_idler)}).all()
    out = {}
    for r in rows:
        muaf = bool(r.test_hesabi)
        islem = r.islem if r.islem in ("alindi", "resit") else None
        out[r.id] = {"tamam": muaf or islem is not None, "islem": r.islem, "muaf": muaf,
                     "form_tarihi": r.form_tarihi.isoformat() if r.form_tarihi else None,
                     "veli_ad_soyad": r.veli_ad_soyad, "kamera": bool(r.kamera) if islem == "alindi" else None,
                     "yapan_ad": r.yapan_ad, "zaman": r.zaman.isoformat() if r.zaman else None}
    return out


def durum(db: Session, ogrenci_id) -> dict:
    return toplu_durum(db, [ogrenci_id]).get(ogrenci_id) or {"tamam": False, "islem": None, "muaf": False}


def tamam_mi(db: Session, ogrenci_id) -> bool:
    return durum(db, ogrenci_id)["tamam"]


def kamera_izinli(db: Session, ogrenci_id) -> bool:
    """Öğrencinin kendi kamera rızasına EK olarak: veli formuyla onaylanan öğrencide velinin kamera rızası da gerekir."""
    d = durum(db, ogrenci_id)
    if d["muaf"] or d["islem"] == "resit":
        return True
    return d["islem"] == "alindi" and bool(d["kamera"])


def isaretle(db: Session, yapan, ogrenci_idler: list, islem: str, form_tarihi: date | None,
             veli_ad_soyad: str | None, kamera: bool) -> int:
    if islem not in ("alindi", "resit"):
        raise IsKuraliHatasi("Geçersiz işlem.")
    if not ogrenci_idler:
        raise IsKuraliHatasi("Öğrenci seçilmedi.")
    if islem == "alindi":
        if form_tarihi is None:
            raise IsKuraliHatasi("Formun imza tarihini girin.")
        if form_tarihi > _bugun():
            raise IsKuraliHatasi("Form tarihi ileri bir tarih olamaz.")
    ad = " ".join((veli_ad_soyad or "").split())[:120] or None
    for oid in ogrenci_idler:
        db.execute(text("""INSERT INTO veli_onaylari (ogrenci_id, islem, form_tarihi, veli_ad_soyad, kamera, form_surumu,
                                                      yapan_id, yapan_ad)
                           VALUES (:o, :i, :t, :a, :k, :s, :y, :ya)"""),
                   {"o": oid, "i": islem, "t": form_tarihi if islem == "alindi" else None, "a": ad if islem == "alindi" else None,
                    "k": bool(kamera) if islem == "alindi" else False, "s": VELI_FORM_SURUM if islem == "alindi" else None,
                    "y": yapan.id, "ya": yapan.ad_soyad})
    db.flush()
    return len(ogrenci_idler)


def geri_al(db: Session, yapan, ogrenci_id, aciklama: str | None) -> None:
    d = durum(db, ogrenci_id)
    if d["islem"] not in ("alindi", "resit"):
        raise IsKuraliHatasi("Bu öğrenci için geri alınacak bir onay kaydı yok.")
    db.execute(text("""INSERT INTO veli_onaylari (ogrenci_id, islem, aciklama, yapan_id, yapan_ad)
                       VALUES (:o, 'geri_alindi', :a, :y, :ya)"""),
               {"o": ogrenci_id, "a": (" ".join((aciklama or "").split())[:300] or None), "y": yapan.id, "ya": yapan.ad_soyad})
    db.flush()


def gecmis(db: Session, ogrenci_id) -> list[dict]:
    rows = db.execute(text("""SELECT islem, form_tarihi, veli_ad_soyad, kamera, aciklama, yapan_ad, zaman FROM veli_onaylari
                              WHERE ogrenci_id = :o ORDER BY zaman DESC, id DESC"""), {"o": ogrenci_id}).all()
    return [{"islem": r.islem, "islem_ad": ISLEM_AD.get(r.islem, r.islem), "form_tarihi": r.form_tarihi.isoformat() if r.form_tarihi else None,
             "veli_ad_soyad": r.veli_ad_soyad, "kamera": r.kamera, "aciklama": r.aciklama, "yapan_ad": r.yapan_ad,
             "zaman": r.zaman.isoformat()} for r in rows]


def kvkk_guncel_idler(db: Session, ogrenci_idler: list) -> dict:
    """{ogrenci_id: zaman | None} — öğrencinin güncel sürümdeki zorunlu KVKK onaylarını tamamladığı an (yoksa None)."""
    from app.core.kvkk_metinleri import KVKK_SURUM, ZORUNLU_KODLAR
    if not ogrenci_idler:
        return {}
    rows = db.execute(text("""
        SELECT DISTINCT ON (kullanici_id, onay_kodu) kullanici_id, onay_kodu, verildi, metin_surumu, zaman
          FROM kvkk_onaylari WHERE kullanici_tipi = 'ogrenci' AND kullanici_id = ANY(:ids)
         ORDER BY kullanici_id, onay_kodu, zaman DESC, id DESC"""), {"ids": list(ogrenci_idler)}).all()
    son: dict = {}
    for r in rows:
        son.setdefault(r.kullanici_id, {})[r.onay_kodu] = r
    out = {}
    for oid in ogrenci_idler:
        m = son.get(oid if isinstance(oid, uuid.UUID) else uuid.UUID(str(oid)), {})
        ok = all(k in m and m[k].verildi and m[k].metin_surumu == KVKK_SURUM for k in ZORUNLU_KODLAR)
        out[oid] = max(m[k].zaman for k in ZORUNLU_KODLAR) if ok else None
    return out
