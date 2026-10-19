"""FastAPI dependency'leri — JWT doğrulama, DB session, mevcut kullanıcı."""
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import token_coz, token_hesaba_uygun_mu
from app.models import Ogrenci, AdminKullanici
from app.core.okul_erisim import okul_acik_olmali, hesap_okulu_acik_olmali

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/giris")
oauth2_opsiyonel = OAuth2PasswordBearer(tokenUrl="/auth/giris", auto_error=False)

_YETKISIZ = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Geçersiz veya süresi dolmuş oturum.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_mevcut_ogrenci(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Ogrenci:
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") != "ogrenci":
        raise _YETKISIZ

    try:
        ogrenci_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ

    ogrenci = db.get(Ogrenci, ogrenci_id)
    if ogrenci is None or not token_hesaba_uygun_mu(payload, ogrenci):   # [2026-10-11] şifre sıfırlandıysa eski oturum düşer
        raise _YETKISIZ
    okul_acik_olmali(db, ogrenci.okul_id)   # [2026-10-11] okulun sistemi kapalıysa 423
    return ogrenci


def get_mevcut_admin(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminKullanici:
    """
    [2026-10-09] Sistem yönetimi uç noktaları (içerik, pipeline, parametreler...) — YALNIZCA süper admin.
    Okul yetkilisi bu uç noktalara erişemez; onun uç noktaları get_mevcut_yonetim + okul kapsamı kullanır.
    """
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") != "super_admin":
        raise _YETKISIZ

    try:
        admin_id = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ

    admin = db.get(AdminKullanici, admin_id)
    if admin is None or admin.rol != "super_admin" or admin.aktif_mi is False or not token_hesaba_uygun_mu(payload, admin):
        raise _YETKISIZ
    return admin


YONETIM_ROLLERI = ("super_admin", "okul_yetkilisi")


def get_mevcut_yonetim(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AdminKullanici:
    """[2026-10-09] Süper admin veya okul yetkilisi. Okul kapsamı uç noktanın içinde ayrıca denetlenir."""
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") not in YONETIM_ROLLERI:
        raise _YETKISIZ
    try:
        kid = uuid.UUID(payload["sub"])
    except (KeyError, ValueError):
        raise _YETKISIZ
    hesap = db.get(AdminKullanici, kid)
    if (hesap is None or hesap.rol not in YONETIM_ROLLERI or hesap.aktif_mi is False or hesap.rol != payload.get("rol")
            or not token_hesaba_uygun_mu(payload, hesap)):
        raise _YETKISIZ
    hesap_okulu_acik_olmali(db, hesap, hesap.rol)   # [2026-10-11] okul yetkilisinin okulu kapalıysa 423
    return hesap


def get_mevcut_super_admin(
    admin: AdminKullanici = Depends(get_mevcut_admin),
) -> AdminKullanici:
    if admin.rol != "super_admin":
        raise HTTPException(status_code=403, detail="Bu işlem yalnızca sistem yöneticisine açık.")
    return admin


def get_opsiyonel_ogrenci(
    token: str | None = Depends(oauth2_opsiyonel),
    db: Session = Depends(get_db),
) -> Ogrenci | None:
    """[2026-10-09] Herkese açık uç noktalarda: geçerli öğrenci oturumu varsa öğrenciyi, yoksa None döner (hata vermez)."""
    if not token:
        return None
    payload = token_coz(token)
    if payload is None or payload.get("tip") != "access" or payload.get("rol") != "ogrenci":
        return None
    try:
        o = db.get(Ogrenci, uuid.UUID(payload["sub"]))
    except (KeyError, ValueError):
        return None
    return o if o is not None and token_hesaba_uygun_mu(payload, o) else None


def get_kvkk_onayli_ogrenci(db: Session = Depends(get_db), ogrenci=Depends(get_mevcut_ogrenci)):
    """[2026-10-19] Kişisel veri işleyen asıl işlemler (değerlendirme başlatma, yapay zekâ sohbeti) güncel KVKK onayı ister.
    Ön yüzdeki onay penceresi bunu zaten zorunlu tutar; bu kontrol API'nin doğrudan kullanılmasına karşıdır."""
    from app.core.hesap_guvenligi_servisi import kvkk_durumu
    if not kvkk_durumu(db, "ogrenci", ogrenci.id)["guncel"]:
        raise HTTPException(status_code=403, detail="Devam etmek için önce Kişisel Verilerin Korunması onaylarını tamamla.")
    return ogrenci
