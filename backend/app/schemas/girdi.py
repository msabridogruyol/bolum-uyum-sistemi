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


class GirdiModeli(BaseModel):
    model_config = ConfigDict(str_max_length=METIN_EN_FAZLA)
