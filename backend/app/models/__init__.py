"""
Tüm ORM modellerini tek yerden erişilebilir kılar — Alembic'in
autogenerate özelliği için tüm modellerin Base.metadata'ya kayıtlı
olması gerekir, bu dosya onu garanti eder.
"""
from app.models.kimlik import Ogrenci, AdminKullanici, OgrenciHesapOlayi
from app.models.icerik_yapisi import (
    Katman, Degisken, Soru, SoruSecenegi, SjtSecenekDegiskenAgirlik,
    Bolum, Dal, BolumDalEslesme, BolumKumelemeSonucu, BolumK5Bag, YokatlasOnbellek,
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
    SistemParametresi, KatmanAgirligi, GecerlilikSonucu, Okul, MeslekDili,
    GecerlilikOzeti, AuditLog,
)
from app.models.koclugu import (
    OgrenciHedefBolum, GelisimYorumHavuzu,
    GelisimKarsilastirmaYorumu, OgrenciGelisimAksiyonDurumu, OgrenciGelisimAdimDurumu,
    OgrenciKoclukOturumu, OgrenciKoclukMesaji, GelisimKaynakOnerisi,
)
from app.models.haftalik import OgrenciHaftalikGorev
from app.models.hesap_guvenligi import KvkkOnayi, DogrulamaKodu, SifreSifirlamaTokeni, GuvenilirCihaz
__all__ = [
    "Ogrenci", "AdminKullanici", "OgrenciHesapOlayi",
    "Katman", "Degisken", "Soru", "SoruSecenegi", "SjtSecenekDegiskenAgirlik",
    "Bolum", "Dal", "BolumDalEslesme", "BolumKumelemeSonucu", "BolumK5Bag", "YokatlasOnbellek",
    "Meslek", "Kategori", "AltGrupKategoriEslesme",
    "MeslekBolumEslesmeAday", "MeslekDegiskenSkoru",
    "BolumAgirligi",
    "OgrenciDegerlendirmeTuru", "OgrenciKatmanOturumu",
    "OgrenciDalOturumu", "OgrenciDegiskenSkoru", "OgrenciCevap",
    "GuvenlikOlayi", "GuvenlikFotografi",
    "OgrenciBolumUyumSkoru", "OgrenciDalUyumSkoru",
    "SistemParametresi", "KatmanAgirligi", "GecerlilikSonucu", "Okul", "MeslekDili",
    "GecerlilikOzeti", "AuditLog",
    "OgrenciHedefBolum", "GelisimYorumHavuzu",
    "GelisimKarsilastirmaYorumu", "OgrenciGelisimAksiyonDurumu", "OgrenciGelisimAdimDurumu",
    "OgrenciKoclukOturumu", "OgrenciKoclukMesaji", "GelisimKaynakOnerisi",
    "OgrenciHaftalikGorev",
    "KvkkOnayi", "DogrulamaKodu", "SifreSifirlamaTokeni", "GuvenilirCihaz",
]
