"""[2026-11-04] Güvenlik / yük denetimi — istek gövdesi metin sınırı.

İstek modellerinin büyük çoğunluğunda metin alanlarına üst sınır yoktu: 100.000 karakterlik ad soyad ya da 2 MB'lık
"ilgi alanları" kabul edilip veritabanına yazılıyor, rehberin Excel/PDF çıktılarına ve ekranlarına taşınıyordu (yalnızca
25 MB'lık genel gövde sınırı vardı). Tüm istek gövdesi modelleri bu tabandan türer: alan kendi `max_length`'ini
vermediyse metin (ve metin listesi öğeleri) en çok METIN_EN_FAZLA karakter olur; aşımda 422. Dosya / görsel (base64)
alanları kendi sınırlarını açıkça verir (Field(max_length=…)); ad, e-posta, şifre gibi alanlar daha dar sınır taşır.
Yanıt modelleri bu tabandan türemez (çıktı sınırlanmaz).
"""
from pydantic import BaseModel, ConfigDict

METIN_EN_FAZLA = 20_000
AD_SOYAD_EN_FAZLA = 30   # [2026-11-04] kullanıcı kuralı: kişi adı soyadı en fazla 30 karakter (öğrenci, yetkili, yönetici, koç, öğretmen)
# Düzenleme formları kayıtlı adı geri gönderir; kural öncesi kaydedilmiş uzun adlar formu kilitlemesin diye bu alanların
# şema sınırı geniştir ve 30 karakter kuralı yalnızca YENİ ya da DEĞİŞEN ada ad_soyad_denetle ile uygulanır.
AD_SOYAD_ALAN_SINIRI = 200


def ad_soyad_denetle(yeni: str | None, eski: str | None = None) -> None:
    """Yeni ya da değişen ad 30 karakteri aşıyorsa 400 (kayıtlı ad olduğu gibi geri gönderildiyse dokunulmaz)."""
    from fastapi import HTTPException
    y = " ".join((yeni or "").split())
    if y and y != " ".join((eski or "").split()) and len(y) > AD_SOYAD_EN_FAZLA:
        raise HTTPException(status_code=400, detail=f"Ad soyad en fazla {AD_SOYAD_EN_FAZLA} karakter olabilir.")


class GirdiModeli(BaseModel):
    model_config = ConfigDict(str_max_length=METIN_EN_FAZLA)
