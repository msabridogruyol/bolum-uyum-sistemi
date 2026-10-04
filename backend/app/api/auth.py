"""Kimlik doğrulama request/response şemaları — D1."""
from pydantic import BaseModel, EmailStr, Field


class OgrenciKayitIstek(BaseModel):
    ad_soyad: str = Field(min_length=2, max_length=200)
    email: EmailStr
    sifre: str = Field(min_length=8, max_length=128)


class GirisIstek(BaseModel):
    email: EmailStr
    sifre: str


class TokenCifti(BaseModel):
    erisim_tokeni: str
    yenileme_tokeni: str
    token_tipi: str = "bearer"


class YenilemeIstek(BaseModel):
    yenileme_tokeni: str


class OgrenciProfil(BaseModel):
    id: str
    ad_soyad: str
    email: str

    model_config = {"from_attributes": True}


# ============================================================================
# [2026-10-04] KVKK, 2 adımlı doğrulama, şifre sıfırlama
# ============================================================================
class KvkkOnayIstek(BaseModel):
    onaylar: dict[str, bool]


class OgrenciKayitIstekV2(OgrenciKayitIstek):
    kvkk: dict[str, bool] | None = None   # yeni kayıt ekranı gönderir; eski istemciler için isteğe bağlı


class GirisIstekV2(GirisIstek):
    cihaz_tokeni: str | None = None


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


class IkiAdimDogrulaIstek(BaseModel):
    gecici_token: str
    kod: str = Field(min_length=4, max_length=12)
    cihazi_hatirla: bool = False


class IkiAdimTekrarIstek(BaseModel):
    gecici_token: str


class SifremiUnuttumIstek(BaseModel):
    email: EmailStr


class SifreSifirlaIstek(BaseModel):
    token: str = Field(min_length=10, max_length=200)
    yeni_sifre: str = Field(min_length=8, max_length=128)


class TokenBilgisiOut(BaseModel):
    amac: str
    ad: str
    maskeli_eposta: str
