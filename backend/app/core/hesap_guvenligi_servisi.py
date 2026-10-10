"""
[2026-10-04] KVKK onayları, 2 adımlı doğrulama (e-posta kodu), güvenilir cihaz, şifre sıfırlama.

Güvenlik ilkeleri:
- Kodlar, bağlantı tokenleri ve cihaz tokenleri veritabanında yalnızca SHA-256 özeti olarak tutulur.
- "Şifremi unuttum" her zaman aynı cevabı verir (hangi e-postanın kayıtlı olduğu öğrenilemez).
- Doğrulama kodu 10 dk geçerli, en fazla 5 deneme; aynı kişiye 60 sn içinde yeni kod gönderilmez.
- 2 adımlı doğrulama, e-posta altyapısı yapılandırılmamışsa ya da IKI_ADIM_KAPALI=1 ise atlanır
  (e-posta çalışmadığında kimsenin kilitlenmemesi için). Yönetim panelinden de kapatılabilir.
"""
import hashlib
import hmac
import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.katman_servisi import IsKuraliHatasi, parametre_oku
from app.core import eposta_servisi as ep
from app.core.kvkk_metinleri import KVKK_SURUM, ONAY_MADDELERI, ZORUNLU_KODLAR, TUM_KODLAR
from app.models import (
    Ogrenci, AdminKullanici, KvkkOnayi, DogrulamaKodu, SifreSifirlamaTokeni, GuvenilirCihaz,
)

log = logging.getLogger("hesap_guvenligi")
KOD_GECERLILIK = timedelta(minutes=10)
KOD_MAKS_DENEME = 5
KOD_TEKRAR_BEKLEME = timedelta(seconds=60)
SIFIRLAMA_GECERLILIK = timedelta(hours=1)
DAVET_GECERLILIK = timedelta(days=3)
SIFIRLAMA_SAATLIK_LIMIT = 3


def _simdi() -> datetime:
    return datetime.now(timezone.utc)


def _utc(d: datetime | None) -> datetime | None:
    if d is None:
        return None
    return d if d.tzinfo else d.replace(tzinfo=timezone.utc)


def _ozet(deger: str) -> str:
    return hashlib.sha256((settings.JWT_SECRET_KEY + "|" + deger).encode("utf-8")).hexdigest()


def maskeli_eposta(email: str) -> str:
    ad, _, alan = email.partition("@")
    if not alan:
        return email
    gorunen = 1 if len(ad) <= 4 else 2
    return ad[:gorunen] + "•" * max(3, len(ad) - gorunen) + "@" + alan


# ============================================================================= KVKK
def kvkk_metinleri() -> dict:
    from app.core.kvkk_metinleri import AYDINLATMA_METNI
    return {
        "surum": KVKK_SURUM,
        "aydinlatma_metni": AYDINLATMA_METNI,
        "maddeler": [{"kod": k, "metin": b, "aciklama": a, "zorunlu": z} for k, b, a, z in ONAY_MADDELERI],
    }


def kvkk_kaydet(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID, onaylar: dict, ip: str | None,
                tam_kayit: bool = True) -> None:
    """tam_kayit=True: zorunluların hepsi işaretli olmalı (kayıt / yeni sürüm onayı).
    tam_kayit=False: yalnızca isteğe bağlı maddeler değiştiriliyor (Ayarlar sayfası)."""
    bilinmeyen = set(onaylar) - TUM_KODLAR
    if bilinmeyen:
        raise IsKuraliHatasi(f"Bilinmeyen onay maddesi: {', '.join(sorted(bilinmeyen))}")
    if tam_kayit:
        eksik = [k for k in ZORUNLU_KODLAR if onaylar.get(k) is not True]
        if eksik:
            raise IsKuraliHatasi("Devam etmek için zorunlu onay kutularını işaretlemelisin.")
    else:
        if any(k in ZORUNLU_KODLAR and v is not True for k, v in onaylar.items()):
            raise IsKuraliHatasi("Zorunlu onaylar buradan geri çekilemez. Hesabının silinmesi için bize e-posta ile başvurabilirsin.")
    mevcut = kvkk_durumu(db, kullanici_tipi, kullanici_id)["onaylar"]
    for kod, deger in onaylar.items():
        deger = bool(deger)
        if tam_kayit or mevcut.get(kod) != deger:
            db.add(KvkkOnayi(kullanici_tipi=kullanici_tipi, kullanici_id=kullanici_id, onay_kodu=kod,
                             metin_surumu=KVKK_SURUM, verildi=deger, ip_adresi=(ip or "")[:64] or None))
    db.flush()


def kvkk_durumu(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID) -> dict:
    kayitlar = (db.query(KvkkOnayi)
                .filter(KvkkOnayi.kullanici_tipi == kullanici_tipi, KvkkOnayi.kullanici_id == kullanici_id)
                .order_by(KvkkOnayi.zaman, KvkkOnayi.id).all())
    son, son_surum = {}, {}
    for k in kayitlar:  # en son satır geçerli
        son[k.onay_kodu] = k.verildi
        son_surum[k.onay_kodu] = k.metin_surumu
    guncel = all(son.get(k) is True and son_surum.get(k) == KVKK_SURUM for k in ZORUNLU_KODLAR)
    return {"surum": KVKK_SURUM, "guncel": guncel, "onaylar": {k: son.get(k, False) for k in TUM_KODLAR}}


def onay_var_mi(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID, kod: str) -> bool:
    k = (db.query(KvkkOnayi)
         .filter(KvkkOnayi.kullanici_tipi == kullanici_tipi, KvkkOnayi.kullanici_id == kullanici_id, KvkkOnayi.onay_kodu == kod)
         .order_by(KvkkOnayi.zaman.desc(), KvkkOnayi.id.desc()).first())
    return bool(k and k.verildi)


# ============================================================================= 2 adımlı doğrulama
def iki_adim_aktif_mi(db: Session) -> bool:
    if (settings.IKI_ADIM_KAPALI or "").strip() == "1":
        return False
    if not ep.eposta_yapilandirildi_mi():
        return False
    return parametre_oku(db, "iki_adimli_dogrulama", "acik").strip().lower() != "kapali"


def cihaz_guvenilir_mi(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID, cihaz_tokeni: str | None) -> bool:
    if not cihaz_tokeni:
        return False
    c = db.query(GuvenilirCihaz).filter(GuvenilirCihaz.cihaz_ozeti == _ozet(cihaz_tokeni)).first()
    return bool(c and c.kullanici_tipi == kullanici_tipi and c.kullanici_id == kullanici_id and _utc(c.son_kullanma) > _simdi())


def cihaz_kaydet(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID) -> str:
    gun = int(parametre_oku(db, "guvenilir_cihaz_gun", "30") or 30)
    tok = secrets.token_urlsafe(32)
    db.add(GuvenilirCihaz(kullanici_tipi=kullanici_tipi, kullanici_id=kullanici_id, cihaz_ozeti=_ozet(tok),
                          son_kullanma=_simdi() + timedelta(days=gun)))
    db.flush()
    return tok


class BeklemeHatasi(IsKuraliHatasi):
    """Yeni kod istemek için kısa süre beklenmeli (HTTP 429)."""


def dogrulama_kodu_gonder(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID, email: str, ad: str,
                          tekrar: bool = False) -> None:
    son = (db.query(DogrulamaKodu)
           .filter(DogrulamaKodu.kullanici_tipi == kullanici_tipi, DogrulamaKodu.kullanici_id == kullanici_id)
           .order_by(DogrulamaKodu.olusturulma_zamani.desc(), DogrulamaKodu.id.desc()).first())
    if son and not son.kullanildi and _utc(son.olusturulma_zamani) and _simdi() - _utc(son.olusturulma_zamani) < KOD_TEKRAR_BEKLEME:
        if tekrar:
            kalan = int((KOD_TEKRAR_BEKLEME - (_simdi() - _utc(son.olusturulma_zamani))).total_seconds()) + 1
            raise BeklemeHatasi(f"Yeni kod istemek için {kalan} saniye bekle.")
        return  # tekrarlanan giriş: önceki kod hâlâ geçerli, yeni e-posta gönderilmez
    for eski in db.query(DogrulamaKodu).filter(DogrulamaKodu.kullanici_tipi == kullanici_tipi,
                                               DogrulamaKodu.kullanici_id == kullanici_id,
                                               DogrulamaKodu.kullanildi.is_(False)).all():
        eski.kullanildi = True  # yeni kod gelince eskiler geçersiz
    kod = f"{secrets.randbelow(1_000_000):06d}"
    db.add(DogrulamaKodu(kullanici_tipi=kullanici_tipi, kullanici_id=kullanici_id,
                         kod_ozeti=_ozet(f"{kullanici_id}:{kod}"), son_kullanma=_simdi() + KOD_GECERLILIK,
                         olusturulma_zamani=_simdi()))
    db.flush()
    konu, html, metin = ep.dogrulama_kodu_epostasi((ad or "").split(" ")[0], kod)
    if not ep.eposta_gonder(email, konu, html, metin):
        raise IsKuraliHatasi("Doğrulama kodu e-postası gönderilemedi. Birkaç dakika sonra tekrar dene.")


def dogrulama_kodunu_kontrol_et(db: Session, kullanici_tipi: str, kullanici_id: uuid.UUID, kod: str) -> None:
    k = (db.query(DogrulamaKodu)
         .filter(DogrulamaKodu.kullanici_tipi == kullanici_tipi, DogrulamaKodu.kullanici_id == kullanici_id,
                 DogrulamaKodu.kullanildi.is_(False))
         .order_by(DogrulamaKodu.olusturulma_zamani.desc(), DogrulamaKodu.id.desc()).first())
    if k is None or _utc(k.son_kullanma) < _simdi():
        raise IsKuraliHatasi("Kodun süresi doldu. Yeni kod iste.")
    if k.deneme_sayisi >= KOD_MAKS_DENEME:
        k.kullanildi = True
        db.flush()
        raise IsKuraliHatasi("Çok fazla hatalı deneme. Yeni kod iste.")
    temiz = "".join(ch for ch in str(kod) if ch.isdigit())
    if not hmac.compare_digest(k.kod_ozeti, _ozet(f"{kullanici_id}:{temiz}")):
        k.deneme_sayisi += 1
        db.flush()
        kalan = KOD_MAKS_DENEME - k.deneme_sayisi
        raise IsKuraliHatasi(f"Kod hatalı. {kalan} deneme hakkın kaldı." if kalan > 0 else "Çok fazla hatalı deneme. Yeni kod iste.")
    k.kullanildi = True
    db.flush()


# ============================================================================= şifre sıfırlama / davet
def _site_adresi(origin: str | None) -> str:
    izinli = [o.rstrip("/") for o in (settings.CORS_ALLOWED_ORIGINS or [])]
    if origin and origin.rstrip("/") in izinli and not origin.startswith("http://localhost"):
        return origin.rstrip("/")
    if settings.FRONTEND_URL:
        return settings.FRONTEND_URL.rstrip("/")
    if origin and origin.rstrip("/") in izinli:
        return origin.rstrip("/")
    return "http://localhost:5173"


def _hesap_bul(db: Session, email: str, kapsam: str):
    """kapsam='ogrenci': öğrenci. kapsam='yonetim': süper admin ve okul yetkilileri (yönetim giriş sayfası)."""
    email = (email or "").strip().lower()
    if kapsam == "ogrenci":
        o = db.query(Ogrenci).filter(func.lower(Ogrenci.email) == email).first()
        if o:
            return "ogrenci", o
        return (None, None)
    a = db.query(AdminKullanici).filter(func.lower(AdminKullanici.email) == email, AdminKullanici.aktif_mi.is_(True)).first()
    return ("yonetim", a) if a else (None, None)


def sifirlama_baglantisi_gonder(db: Session, email: str, kapsam: str, origin: str | None) -> None:
    """Her durumda sessizce döner (e-posta kayıtlı mı bilgisi sızmaz)."""
    tip, hesap = _hesap_bul(db, email, kapsam)
    if hesap is None:
        return
    son_saat = (db.query(SifreSifirlamaTokeni)
                .filter(SifreSifirlamaTokeni.kullanici_tipi == tip, SifreSifirlamaTokeni.kullanici_id == hesap.id,
                        SifreSifirlamaTokeni.olusturulma_zamani >= (_simdi() - timedelta(hours=1)).replace(tzinfo=None))
                .count())
    if son_saat >= SIFIRLAMA_SAATLIK_LIMIT:
        log.warning("Şifre sıfırlama limiti aşıldı: %s", hesap.id)
        return
    tok = secrets.token_urlsafe(32)
    db.add(SifreSifirlamaTokeni(kullanici_tipi=tip, kullanici_id=hesap.id, token_ozeti=_ozet(tok), amac="sifirlama",
                                son_kullanma=_simdi() + SIFIRLAMA_GECERLILIK, olusturulma_zamani=_simdi()))
    db.flush()
    yol = "/admin/sifre-sifirla" if kapsam == "yonetim" else "/sifre-sifirla"
    konu, html, metin = ep.sifre_sifirlama_epostasi((hesap.ad_soyad or "").split(" ")[0], f"{_site_adresi(origin)}{yol}?token={tok}")
    ep.eposta_gonder(hesap.email, konu, html, metin)


def davet_baglantisi_olustur(db: Session, hesap: AdminKullanici, origin: str | None) -> str:
    tok = secrets.token_urlsafe(32)
    db.add(SifreSifirlamaTokeni(kullanici_tipi="yonetim", kullanici_id=hesap.id, token_ozeti=_ozet(tok), amac="davet",
                                son_kullanma=_simdi() + DAVET_GECERLILIK, olusturulma_zamani=_simdi()))
    db.flush()
    return f"{_site_adresi(origin)}/sifre-sifirla?token={tok}"


def _token_kaydi(db: Session, token: str) -> SifreSifirlamaTokeni:
    k = db.query(SifreSifirlamaTokeni).filter(SifreSifirlamaTokeni.token_ozeti == _ozet(token or "")).first()
    if k is None or k.kullanilma_zamani is not None or _utc(k.son_kullanma) < _simdi():
        raise IsKuraliHatasi("Bu bağlantı geçersiz ya da süresi dolmuş. Yeni bir bağlantı iste.")
    return k


def _hesap(db: Session, tip: str, kullanici_id: uuid.UUID):
    return db.get(Ogrenci, kullanici_id) if tip == "ogrenci" else db.get(AdminKullanici, kullanici_id)


def token_bilgisi(db: Session, token: str) -> dict:
    k = _token_kaydi(db, token)
    h = _hesap(db, k.kullanici_tipi, k.kullanici_id)
    if h is None:
        raise IsKuraliHatasi("Bu bağlantı geçersiz.")
    return {"amac": k.amac, "ad": (h.ad_soyad or "").split(" ")[0], "maskeli_eposta": maskeli_eposta(h.email)}


def sifreyi_sifirla(db: Session, token: str, yeni_sifre: str) -> str:
    from app.core.security import sifre_hashle
    if len(yeni_sifre or "") < 8:
        raise IsKuraliHatasi("Şifre en az 8 karakter olmalı.")
    k = _token_kaydi(db, token)
    h = _hesap(db, k.kullanici_tipi, k.kullanici_id)
    if h is None:
        raise IsKuraliHatasi("Bu bağlantı geçersiz.")
    h.sifre_hash = sifre_hashle(yeni_sifre)
    h.sifre_degistirmeli = False   # [2026-10-09] geçici şifre artık geçersiz
    h.gecici_sifre_sifreli = None  # [2026-10-10]
    if k.kullanici_tipi == "ogrenci":
        from app.core.hesap_yonetimi import olay_yaz
        olay_yaz(db, h.id, "sifre_degisti", "E-postadaki bağlantıyla yeni şifre belirlendi", "Öğrenci")
    k.kullanilma_zamani = _simdi()
    # aynı kişinin diğer bağlantıları ve hatırlanan cihazları geçersiz olur
    for diger in db.query(SifreSifirlamaTokeni).filter(SifreSifirlamaTokeni.kullanici_tipi == k.kullanici_tipi,
                                                       SifreSifirlamaTokeni.kullanici_id == k.kullanici_id,
                                                       SifreSifirlamaTokeni.kullanilma_zamani.is_(None)).all():
        diger.kullanilma_zamani = _simdi()
    db.query(GuvenilirCihaz).filter(GuvenilirCihaz.kullanici_tipi == k.kullanici_tipi,
                                    GuvenilirCihaz.kullanici_id == k.kullanici_id).delete()
    db.flush()
    return k.kullanici_tipi


def eski_fotograflari_temizle(db: Session, gun: int = 180) -> int:
    """KVKK metninde taahhüt edilen saklama süresi: kamera fotoğrafları 6 ay sonra silinir."""
    from app.models import GuvenlikFotografi
    try:
        sinir = (_simdi() - timedelta(days=gun)).replace(tzinfo=None)
        n = db.query(GuvenlikFotografi).filter(GuvenlikFotografi.cekim_zamani < sinir).delete(synchronize_session=False)
        db.flush()
        return n
    except Exception as hata:
        log.warning("Eski fotoğraf temizliği yapılamadı: %s", hata)
        db.rollback()
        return 0
