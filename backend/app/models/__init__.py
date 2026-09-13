"""
Tüm ORM modellerini tek yerden erişilebilir kılar — Alembic'in
autogenerate özelliği için tüm modellerin Base.metadata'ya kayıtlı
olması gerekir, bu dosya onu garanti eder.
"""
from app.models.kimlik import Ogrenci, AdminKullanici
from app.models.icerik_yapisi import (
    Katman, Degisken, Soru, SoruSecenegi, SjtSecenekDegiskenAgirlik,
    Bolum, Dal, BolumDalEslesme, BolumKumelemeSonucu,
)
from app.models.meslek_verisi import (
    Meslek, Kategori, AltGrupKategoriEslesme,
    MeslekBolumEslesmeAday, MeslekDegiskenSkoru,
)
from app.models.hesaplama_ciktilari import BolumAgirligi
from app.models.ogrenci_verisi import (
    OgrenciDegerlendirmeTuru, OgrenciKatmanOturumu,
    OgrenciDalOturumu, OgrenciDegiskenSkoru, OgrenciCevap,
    GuvenlikOlayi, GuvenlikFotografi,
)
from app.models.sonuclar import OgrenciBolumUyumSkoru, OgrenciDalUyumSkoru
from app.models.sistem import (
    SistemParametresi, KatmanAgirligi, GecerlilikSonucu,
    GecerlilikOzeti, AuditLog,
)
from app.models.koclugu import (
    OgrenciHedefBolum, GelisimYorumHavuzu,
    GelisimKarsilastirmaYorumu, OgrenciGelisimAksiyonDurumu,
    OgrenciKoclukOturumu, OgrenciKoclukMesaji,
)
__all__ = [
    "Ogrenci", "AdminKullanici",
    "Katman", "Degisken", "Soru", "SoruSecenegi", "SjtSecenekDegiskenAgirlik",
    "Bolum", "Dal", "BolumDalEslesme", "BolumKumelemeSonucu",
    "Meslek", "Kategori", "AltGrupKategoriEslesme",
    "MeslekBolumEslesmeAday", "MeslekDegiskenSkoru",
    "BolumAgirligi",
    "OgrenciDegerlendirmeTuru", "OgrenciKatmanOturumu",
    "OgrenciDalOturumu", "OgrenciDegiskenSkoru", "OgrenciCevap",
    "GuvenlikOlayi", "GuvenlikFotografi",
    "OgrenciBolumUyumSkoru", "OgrenciDalUyumSkoru",
    "SistemParametresi", "KatmanAgirligi", "GecerlilikSonucu",
    "GecerlilikOzeti", "AuditLog",
    "OgrenciHedefBolum", "GelisimYorumHavuzu",
    "GelisimKarsilastirmaYorumu", "OgrenciGelisimAksiyonDurumu",
    "OgrenciKoclukOturumu", "OgrenciKoclukMesaji",
]
