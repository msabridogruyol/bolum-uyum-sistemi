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
