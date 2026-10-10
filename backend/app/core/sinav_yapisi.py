# -*- coding: utf-8 -*-
"""
[2026-10-10] YKS sınav yapısı: oturumlar, testler (soru sayıları), YÖK Atlas Net Sihirbazı alan adları ve konu listeleri.

- Net = doğru − yanlış / 4 (ÖSYM).
- Deneme girişi YÖK Atlas'ın tuttuğu alanlarla aynı ayrıntıdadır (TYT: Türkçe, Sosyal, Matematik, Fen; AYT: ders ders),
  böylece hedef programa yerleşen son öğrencinin netleriyle birebir karşılaştırılabilir.
- Konu takibi daha ayrıntılıdır (ör. TYT Fen → Fizik / Kimya / Biyoloji).
"""
from __future__ import annotations

# kod: (oturum, ad, soru sayısı, YÖK Atlas alanı)
TESTLER: dict[str, tuple[str, str, int, str]] = {
    "tyt_trk": ("TYT", "Türkçe", 40, "tytTrkNet"),
    "tyt_sos": ("TYT", "Sosyal Bilimler", 20, "tytSosNet"),
    "tyt_mat": ("TYT", "Temel Matematik", 40, "tytMatNet"),
    "tyt_fen": ("TYT", "Fen Bilimleri", 20, "tytFenNet"),
    "ayt_mat": ("AYT", "Matematik", 40, "aytMatNet"),
    "ayt_fiz": ("AYT", "Fizik", 14, "aytFizNet"),
    "ayt_kim": ("AYT", "Kimya", 13, "aytKimNet"),
    "ayt_bio": ("AYT", "Biyoloji", 13, "aytBioNet"),
    "ayt_tde": ("AYT", "Türk Dili ve Edebiyatı", 24, "aytTdeNet"),
    "ayt_trh1": ("AYT", "Tarih-1", 10, "aytTrh1Net"),
    "ayt_cog1": ("AYT", "Coğrafya-1", 6, "aytCog1Net"),
    "ayt_trh2": ("AYT", "Tarih-2", 11, "aytTrh2Net"),
    "ayt_cog2": ("AYT", "Coğrafya-2", 11, "aytCog2Net"),
    "ayt_fel": ("AYT", "Felsefe Grubu", 12, "aytFelNet"),
    "ayt_din": ("AYT", "Din Kültürü", 6, "aytDinNet"),
    "ydt_ydil": ("YDT", "Yabancı Dil", 80, "ydtYdilNet"),
}
TYT_TESTLERI = ["tyt_trk", "tyt_sos", "tyt_mat", "tyt_fen"]
PUAN_TURU_TESTLERI = {
    "SAY": TYT_TESTLERI + ["ayt_mat", "ayt_fiz", "ayt_kim", "ayt_bio"],
    "EA": TYT_TESTLERI + ["ayt_mat", "ayt_tde", "ayt_trh1", "ayt_cog1"],
    "SÖZ": TYT_TESTLERI + ["ayt_tde", "ayt_trh1", "ayt_cog1", "ayt_trh2", "ayt_cog2", "ayt_fel", "ayt_din"],
    "DİL": TYT_TESTLERI + ["ydt_ydil"],
    "TYT": TYT_TESTLERI,
}
PUAN_TURU_AD = {"SAY": "Sayısal", "EA": "Eşit Ağırlık", "SÖZ": "Sözel", "DİL": "Dil", "TYT": "TYT"}


def puan_turu_normalize(p: str | None) -> str | None:
    t = (p or "").strip().upper().replace("SOZ", "SÖZ").replace("DIL", "DİL")
    return t if t in PUAN_TURU_TESTLERI else None


# ----------------------------------------------------------------------------- konu takibi
# kod: (oturum, ad, [konular]) — konu listeleri ÖSYM/MEB müfredatındaki yaygın başlıklardır.
KONU_DERSLERI: dict[str, tuple[str, str, list[str]]] = {
    "tyt_turkce": ("TYT", "Türkçe", [
        "Sözcükte Anlam", "Cümlede Anlam", "Paragraf", "Ses Bilgisi", "Yazım Kuralları", "Noktalama İşaretleri",
        "Sözcükte Yapı", "İsimler", "Sıfatlar", "Zamirler", "Zarflar", "Edat – Bağlaç – Ünlem", "Fiiller",
        "Fiilimsiler", "Cümlenin Ögeleri", "Cümle Türleri", "Anlatım Bozuklukları"]),
    "tyt_matematik": ("TYT", "Temel Matematik", [
        "Temel Kavramlar", "Sayı Basamakları", "Bölme ve Bölünebilme", "EBOB – EKOK", "Rasyonel Sayılar",
        "Basit Eşitsizlikler", "Mutlak Değer", "Üslü Sayılar", "Köklü Sayılar", "Çarpanlara Ayırma", "Oran – Orantı",
        "Denklem Çözme", "Sayı Problemleri", "Kesir Problemleri", "Yaş Problemleri", "Yüzde – Kâr – Zarar",
        "Karışım Problemleri", "Hareket Problemleri", "İşçi – Havuz Problemleri", "Grafik Problemleri", "Kümeler",
        "Mantık", "Fonksiyonlar", "Polinomlar", "Permütasyon – Kombinasyon", "Olasılık", "Veri – İstatistik"]),
    "tyt_geometri": ("TYT", "Geometri", [
        "Doğruda ve Üçgende Açılar", "Dik Üçgen ve Trigonometri", "İkizkenar ve Eşkenar Üçgen", "Üçgende Alan",
        "Üçgende Benzerlik", "Açıortay – Kenarortay", "Çokgenler", "Dörtgenler", "Çember ve Daire",
        "Analitik Geometri (Nokta – Doğru)", "Katı Cisimler"]),
    "tyt_fizik": ("TYT", "Fizik", [
        "Fizik Bilimine Giriş", "Madde ve Özellikleri", "Hareket ve Kuvvet", "İş – Güç – Enerji", "Isı ve Sıcaklık",
        "Elektrostatik", "Elektrik Akımı ve Devreler", "Manyetizma", "Basınç ve Kaldırma Kuvveti", "Dalgalar", "Optik"]),
    "tyt_kimya": ("TYT", "Kimya", [
        "Kimya Bilimi", "Atom ve Periyodik Sistem", "Kimyasal Türler Arası Etkileşimler", "Maddenin Halleri",
        "Doğa ve Kimya", "Kimyanın Temel Kanunları", "Mol Kavramı", "Kimyasal Tepkimeler", "Karışımlar",
        "Asitler, Bazlar ve Tuzlar", "Kimya Her Yerde"]),
    "tyt_biyoloji": ("TYT", "Biyoloji", [
        "Canlıların Ortak Özellikleri", "Canlıların Temel Bileşenleri", "Hücre ve Organelleri", "Hücre Zarından Madde Geçişi",
        "Canlıların Sınıflandırılması", "Hücre Bölünmeleri", "Kalıtım", "Ekosistem Ekolojisi", "Güncel Çevre Sorunları"]),
    "tyt_tarih": ("TYT", "Tarih", [
        "Tarih Bilimine Giriş", "İlk Çağ Uygarlıkları", "İlk Türk Devletleri", "İslam Tarihi ve Türk-İslam Devletleri",
        "Osmanlı Kuruluş ve Yükselme", "Osmanlı Duraklama – Gerileme – Dağılma", "Kurtuluş Savaşı",
        "Atatürk İlke ve İnkılapları", "Çağdaş Türk ve Dünya Tarihi"]),
    "tyt_cografya": ("TYT", "Coğrafya", [
        "Doğa ve İnsan", "Dünya'nın Şekli ve Hareketleri", "Harita Bilgisi", "İklim Bilgisi", "Yer Şekilleri",
        "Nüfus ve Yerleşme", "Türkiye'nin Coğrafi Özellikleri", "Ekonomik Faaliyetler", "Doğal Afetler"]),
    "tyt_felsefe": ("TYT", "Felsefe", [
        "Felsefeye Giriş", "Bilgi Felsefesi", "Varlık Felsefesi", "Ahlak Felsefesi", "Sanat Felsefesi",
        "Din Felsefesi", "Siyaset Felsefesi", "Bilim Felsefesi"]),
    "tyt_din": ("TYT", "Din Kültürü", [
        "Bilgi ve İnanç", "İslam ve İbadet", "Ahlak ve Değerler", "Hz. Muhammed'in Hayatı", "İslam Düşüncesinde Yorumlar"]),
    "ayt_matematik": ("AYT", "Matematik", [
        "Fonksiyonlar", "Polinomlar", "İkinci Dereceden Denklemler", "Karmaşık Sayılar", "Parabol", "Eşitsizlikler",
        "Trigonometri", "Logaritma", "Diziler", "Limit ve Süreklilik", "Türev", "İntegral", "Permütasyon – Kombinasyon – Olasılık"]),
    "ayt_geometri": ("AYT", "Geometri", [
        "Üçgenler", "Çokgenler ve Dörtgenler", "Çember ve Daire", "Analitik Geometri", "Dönüşüm Geometrisi",
        "Çemberin Analitik İncelenmesi", "Katı Cisimler"]),
    "ayt_fizik": ("AYT", "Fizik", [
        "Vektörler", "Bağıl Hareket", "Newton'un Hareket Yasaları", "Atışlar", "İş – Enerji ve Momentum", "Tork ve Denge",
        "Elektriksel Kuvvet ve Alan", "Manyetizma ve İndüksiyon", "Alternatif Akım", "Çembersel Hareket",
        "Basit Harmonik Hareket", "Dalga Mekaniği", "Atom Fiziği ve Radyoaktivite", "Modern Fizik"]),
    "ayt_kimya": ("AYT", "Kimya", [
        "Modern Atom Teorisi", "Gazlar", "Sıvı Çözeltiler", "Kimyasal Tepkimelerde Enerji", "Tepkime Hızları",
        "Kimyasal Denge", "Asit – Baz Dengesi", "Çözünürlük Dengesi", "Kimya ve Elektrik", "Karbon Kimyasına Giriş",
        "Organik Bileşikler", "Enerji Kaynakları"]),
    "ayt_biyoloji": ("AYT", "Biyoloji", [
        "Sinir Sistemi", "Endokrin Sistem", "Duyu Organları", "Destek ve Hareket Sistemi", "Sindirim Sistemi",
        "Dolaşım ve Bağışıklık", "Solunum Sistemi", "Boşaltım Sistemi", "Üreme Sistemi", "Komünite ve Popülasyon",
        "Genden Proteine", "Canlılarda Enerji Dönüşümleri", "Bitki Biyolojisi"]),
    "ayt_edebiyat": ("AYT", "Türk Dili ve Edebiyatı", [
        "Anlam Bilgisi", "Şiir Bilgisi", "Edebi Sanatlar", "İslamiyet Öncesi Türk Edebiyatı", "Halk Edebiyatı",
        "Divan Edebiyatı", "Tanzimat Edebiyatı", "Servet-i Fünun ve Fecr-i Âti", "Milli Edebiyat",
        "Cumhuriyet Dönemi Edebiyatı", "Edebi Akımlar", "Dünya Edebiyatı"]),
    "ayt_tarih": ("AYT", "Tarih", [
        "Tarih ve Zaman", "İlk ve Orta Çağlarda Türk Dünyası", "Türk-İslam Devletleri", "Beylikten Devlete Osmanlı",
        "Dünya Gücü Osmanlı", "Değişen Dünya Dengeleri", "Uluslararası İlişkilerde Denge Stratejisi", "XX. Yüzyıl Başlarında Osmanlı",
        "Milli Mücadele", "Atatürkçülük ve Türk İnkılabı", "İki Savaş Arası Dönem", "II. Dünya Savaşı ve Soğuk Savaş",
        "Küreselleşen Dünya"]),
    "ayt_cografya": ("AYT", "Coğrafya", [
        "Ekosistem", "Nüfus Politikaları", "Türkiye'de Nüfus ve Yerleşme", "Ekonomik Faaliyetler ve Doğal Kaynaklar",
        "Türkiye Ekonomisi", "Türkiye'de Tarım, Sanayi ve Ulaşım", "Kültür Bölgeleri", "Küresel ve Bölgesel Örgütler",
        "Çevre ve Toplum"]),
    "ayt_felsefe": ("AYT", "Felsefe Grubu", [
        "Felsefe Tarihi", "Mantığa Giriş", "Klasik Mantık", "Sembolik Mantık", "Psikolojiye Giriş", "Öğrenme ve Bellek",
        "Ruh Sağlığı", "Sosyolojiye Giriş", "Toplumsal Yapı ve Kurumlar", "Kültür ve Toplumsal Değişme"]),
}
PUAN_TURU_KONU_DERSLERI = {
    "SAY": ["ayt_matematik", "ayt_geometri", "ayt_fizik", "ayt_kimya", "ayt_biyoloji"],
    "EA": ["ayt_matematik", "ayt_geometri", "ayt_edebiyat", "ayt_tarih", "ayt_cografya"],
    "SÖZ": ["ayt_edebiyat", "ayt_tarih", "ayt_cografya", "ayt_felsefe"],
    "DİL": [],
    "TYT": [],
}
KONU_DURUMLARI = ("baslamadi", "calisiyor", "bitti", "tekrar")


def net_hesapla(dogru: int, yanlis: int) -> float:
    return round(dogru - yanlis / 4, 2)
