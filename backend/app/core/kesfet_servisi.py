"""
D5, Katman 2 — Tüm Bölümleri Keşfet.
Kaynak: sistem_genel_anlatim.md D5

301 bölümün tamamı aranabilir; her sonuç için % uyum (varsa, D4'ten —
hesaplanmamışsa null) + öne çıkan değişkenler + kısa bilgi notu döner.

[ÇIKARIM — SONRADAN DEĞİŞTİRİLDİ]: İlk sürümde bu alan "katman bazlı
ortalama" (31 değişkenin K1-K4 için 4 sayıya indirgenmiş hali) olarak
yorumlanmıştı. Proje sahibi, bu ortalamanın bölümün kendine özgü
profilini gizlediğini (farklı profildeki iki bölümün aynı ortalamaya
sahip olup ayırt edilemez hale gelebildiğini) fark edip, bunun yerine
bölümün en yüksek ağırlıklı 5 değişkenini doğrudan göstermeye karar
verdi — bkz. bolum_on_cikan_degiskenler().

[DÜZELTME — kullanıcı bildirimi üzerine bulundu] Önceki sürüm arama için
SQL'in ILIKE komutunu kullanıyordu (Bolum.ad.ilike(...)). PostgreSQL'in
ILIKE'ı, veritabanı collation ayarına bağlı olarak Türkçe'nin dört harfli
İ/I/ı/i ayrımını doğru çeviremiyor — örneğin "TIP" (düz ASCII I) tam
yazılınca eşleşiyordu ama "tıp" (Türkçe'ye özel noktasız ı) hiç
eşleşmiyordu, çünkü veritabanı "ı"yı "I"ya doğru büyütemiyordu. Çözüm:
arama artık SQL'e bırakılmıyor; 301 bölüm zaten küçük bir küme olduğu
için tamamı çekilip Python'da, Türkçe'ye özel doğru bir küçültme
fonksiyonuyla karşılaştırılıyor.
"""
from sqlalchemy.orm import Session

from app.models import (
    Ogrenci, Bolum, Degisken, BolumAgirligi,
    OgrenciDegerlendirmeTuru, OgrenciBolumUyumSkoru,
)


def turkce_kucult(metin: str) -> str:
    """
    Python'un (ve çoğu veritabanının) varsayılan küçültme/büyütme mantığı
    İngilizce kurallarını kullanır: 'I'.lower() -> 'i' verir. Ama Türkçe'de
    'I' harfinin küçüğü 'ı'dır (noktasız), 'i'nin büyüğü ise 'İ'dir
    (noktalı) — bunlar dört AYRI harf. Bu fonksiyon önce bu iki harfi
    Türkçe kurallarına göre doğru çevirir, sonra geri kalanını (ş, ğ, ü,
    ö, ç dahil — bunlarda İngilizce/Türkçe kuralı zaten aynı olduğu için
    sorun yok) standart .lower() ile küçültür.
    """
    return metin.replace("İ", "i").replace("I", "ı").lower()


def bolum_on_cikan_degiskenler(db: Session, bolum_id: int, adet: int = 5) -> list[dict]:
    """
    [DEĞİŞTİRİLDİ — proje sahibinin kararıyla] Önceki sürüm, 31 değişkeni
    katman bazında ortalayıp yalnızca 4 sayı (K1-K4) döndürüyordu. Ancak
    bu ortalama, bölümün KENDİNE ÖZGÜ profilini gizliyor — biri D1'de çok
    yüksek diğer değişkenlerde düşük, öbürü tam tersi olan iki bölüm bile
    aynı katman ortalamasına sahip olabiliyor, bu da arama sonuçlarını
    ayırt edici olmaktan çıkarıyordu.

    Yeni yaklaşım: bölümün 31 değişken ağırlığından EN YÜKSEK olan N
    tanesini (varsayılan 5), hangi katmandan olduklarına bakmaksızın,
    doğrudan isimleriyle döndürür — bu, o bölümü gerçekten diğerlerinden
    ayıran özellikleri (örn. "Bu bölüm özellikle Analitik Düşünme ve
    Sayısal Yetkinlik istiyor") ortaya çıkarır.
    """
    satirlar = (
        db.query(BolumAgirligi, Degisken.kod, Degisken.ad)
        .join(Degisken, Degisken.id == BolumAgirligi.degisken_id)
        .filter(BolumAgirligi.bolum_id == bolum_id)
        .all()
    )
    en_guncel: dict[int, tuple] = {}  # degisken_id -> (agirlik, kod, ad)
    for agirlik, kod, ad in satirlar:
        anahtar = agirlik.degisken_id
        if anahtar not in en_guncel or agirlik.versiyon > en_guncel[anahtar][0].versiyon:
            en_guncel[anahtar] = (agirlik, kod, ad)

    siralanmis = sorted(en_guncel.values(), key=lambda x: float(x[0].agirlik_degeri), reverse=True)
    return [
        {"degisken_kod": kod, "degisken_adi": ad, "agirlik_degeri": round(float(agirlik.agirlik_degeri), 2)}
        for agirlik, kod, ad in siralanmis[:adet]
    ]


def bolumleri_ara(db: Session, ogrenci: Ogrenci, arama_terimi: str, limit: int = 20) -> list[dict]:
    """
    D5 Katman 2 — isim bazlı arama (case-insensitive, kısmi eşleşme,
    Türkçe İ/I/ı/i ayrımına duyarlı). Yalnızca durum='yayinda' bölümler
    döner (E5 kuralı).
    """
    arama_normalize = turkce_kucult(arama_terimi.strip())

    # [DÜZELTME] SQL ILIKE yerine: tüm yayındaki bölümler çekilip Python'da
    # Türkçe-güvenli karşılaştırma yapılıyor (301 satır — performans sorunu
    # yaratmayacak kadar küçük bir küme).
    tum_bolumler = (
        db.query(Bolum)
        .filter(Bolum.durum == "yayinda")
        .order_by(Bolum.ad)
        .all()
    )
    bolumler = [
        b for b in tum_bolumler
        if arama_normalize in turkce_kucult(b.ad)
    ][:limit]

    # öğrencinin en son tamamlanmış turu varsa TOPLAM_UYUM'u oradan oku
    son_tamamlanan_tur = (
        db.query(OgrenciDegerlendirmeTuru)
        .filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id, OgrenciDegerlendirmeTuru.durum == "tamamlandi")
        .order_by(OgrenciDegerlendirmeTuru.tur_no.desc())
        .first()
    )
    uyum_skorlari: dict[int, float] = {}
    if son_tamamlanan_tur is not None:
        uyum_skorlari = {
            s.bolum_id: float(s.toplam_uyum)
            for s in db.query(OgrenciBolumUyumSkoru).filter(
                OgrenciBolumUyumSkoru.ogrenci_id == ogrenci.id,
                OgrenciBolumUyumSkoru.tur_id == son_tamamlanan_tur.id,
            ).all()
        }

    sonuc = []
    for bolum in bolumler:
        sonuc.append({
            "bolum_id": bolum.id,
            "bolum_adi": bolum.ad,
            "kisa_aciklama": bolum.kisa_aciklama,
            "toplam_uyum": uyum_skorlari.get(bolum.id),  # None -> henüz hesaplanmadı
            "on_cikan_degiskenler": bolum_on_cikan_degiskenler(db, bolum.id),
        })
    return sonuc
