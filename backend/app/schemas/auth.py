"""Kimlik doğrulama request/response şemaları — D1."""
from pydantic import BaseModel, EmailStr, Field
from app.schemas.girdi import GirdiModeli  # [2026-11-04] istek gövdesi metin sınırı


class OgrenciKayitIstek(GirdiModeli):
    ad_soyad: str = Field(min_length=2, max_length=200)
    email: EmailStr
    sifre: str = Field(min_length=8, max_length=128)


class GirisIstek(GirdiModeli):
    email: EmailStr
    sifre: str = Field(max_length=200)   # [2026-11-04] üst sınır (bcrypt 72 bayt kullanır)


class TokenCifti(BaseModel):
    erisim_tokeni: str
    yenileme_tokeni: str
    token_tipi: str = "bearer"


class YenilemeIstek(GirdiModeli):
    yenileme_tokeni: str


class OgrenciProfil(BaseModel):
    id: str
    ad_soyad: str
    email: str

    model_config = {"from_attributes": True}


# ============================================================================
# [2026-10-04] KVKK, 2 adımlı doğrulama, şifre sıfırlama
# ============================================================================
class KvkkOnayIstek(GirdiModeli):
    onaylar: dict[str, bool]


class OgrenciKayitIstekV2(OgrenciKayitIstek):
    kvkk: dict[str, bool] | None = None   # yeni kayıt ekranı gönderir; eski istemciler için isteğe bağlı


class GirisIstekV2(GirisIstek):
    cihaz_tokeni: str | None = None
    # [2026-10-11] Tek giriş ekranı: aynı tarayıcıda yönetim hesabının "bu cihazı hatırla" anahtarı ayrı saklanır
    yonetim_cihaz_tokeni: str | None = None


class GirisCevap(BaseModel):
    """Ya tokenler döner ya da (2 adımlı doğrulama gerekiyorsa) geçici token + maskeli e-posta."""
    erisim_tokeni: str | None = None
    yenileme_tokeni: str | None = None
    token_tipi: str = "bearer"
    kullanici_tipi: str | None = None          # 'ogrenci' | 'rehber' | yönetici rolü
    iki_adim_gerekli: bool = False
    gecici_token: str | None = None
    maskeli_eposta: str | None = None
    cihaz_tokeni: str | None = None             # "bu cihazı hatırla" seçildiyse


class IkiAdimDogrulaIstek(GirdiModeli):
    gecici_token: str
    kod: str = Field(min_length=4, max_length=12)
    cihazi_hatirla: bool = False


class IkiAdimTekrarIstek(GirdiModeli):
    gecici_token: str


class SifremiUnuttumIstek(GirdiModeli):
    email: EmailStr


class SifreSifirlaIstek(GirdiModeli):
    token: str = Field(min_length=10, max_length=200)
    yeni_sifre: str = Field(min_length=8, max_length=128)


class TokenBilgisiOut(BaseModel):
    amac: str
    ad: str
    maskeli_eposta: str
