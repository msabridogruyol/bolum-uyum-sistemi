"""
[2026-10-09] 17 üst alan arasındaki komşuluk — bir öğrencinin öneri listesinde birlikte görünmesi doğal olan alanlar.

Amaç: Çalışma tarzı benzeyen ama konu olarak tamamen alakasız bölümlerin (ör. Gastronomi + Müzik Çalgı,
Hukuk + Veterinerlik) aynı listede yan yana çıkmasını önlemek. Liste, öğrencinin EN GÜÇLÜ alanı (o alandaki en iyi
3 bölümün ortalaması) ve ona komşu alanlarla sınırlanır; ikinci en güçlü alan ana alana IKINCI_ALAN_FARK puandan
yakınsa (K5'te de açılan alan) ana blokten SONRA gelir. Diğer bölümler silinmez, listenin sonuna iner.
Komşuluk simetriktir (A, B'nin komşusuysa B de A'nın komşusudur); değiştirirken iki tarafı birlikte güncelleyin.
"""
import numpy as np

IKINCI_ALAN_FARK = 10.0

KOMSU: dict[str, list[str]] = {
    'Mühendislik': ['Bilişim & Yazılım', 'Mimarlık & Planlama', 'Sanat & Tasarım', 'Sağlık & Rehabilitasyon', 'Tarım, Hayvancılık, Gıda & Çevre', 'Temel Bilimler', 'Ulaştırma: Havacılık & Denizcilik', 'İşletme, Ekonomi & Finans'],
    'Bilişim & Yazılım': ['Mühendislik', 'Temel Bilimler', 'İşletme, Ekonomi & Finans'],
    'Temel Bilimler': ['Bilişim & Yazılım', 'Eğitim', 'Mühendislik', 'Sağlık & Rehabilitasyon', 'Tarım, Hayvancılık, Gıda & Çevre', 'İşletme, Ekonomi & Finans'],
    'Sağlık & Rehabilitasyon': ['Eğitim', 'Mühendislik', 'Psikoloji & Sosyal Hizmet', 'Spor Bilimleri', 'Tarım, Hayvancılık, Gıda & Çevre', 'Temel Bilimler'],
    'Spor Bilimleri': ['Eğitim', 'Müzik & Sahne Sanatları', 'Sağlık & Rehabilitasyon', 'Turizm & Hizmet'],
    'Psikoloji & Sosyal Hizmet': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Eğitim', 'Hukuk, Siyaset & Kamu', 'Sağlık & Rehabilitasyon'],
    'Eğitim': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Müzik & Sahne Sanatları', 'Psikoloji & Sosyal Hizmet', 'Sanat & Tasarım', 'Sağlık & Rehabilitasyon', 'Spor Bilimleri', 'Tarım, Hayvancılık, Gıda & Çevre', 'Temel Bilimler'],
    'Dil, Edebiyat, Tarih & Beşeri Bilimler': ['Eğitim', 'Hukuk, Siyaset & Kamu', 'Medya & İletişim', 'Müzik & Sahne Sanatları', 'Psikoloji & Sosyal Hizmet', 'Sanat & Tasarım', 'Tarım, Hayvancılık, Gıda & Çevre'],
    'Hukuk, Siyaset & Kamu': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Medya & İletişim', 'Psikoloji & Sosyal Hizmet', 'İşletme, Ekonomi & Finans'],
    'İşletme, Ekonomi & Finans': ['Bilişim & Yazılım', 'Hukuk, Siyaset & Kamu', 'Medya & İletişim', 'Mühendislik', 'Tarım, Hayvancılık, Gıda & Çevre', 'Temel Bilimler', 'Turizm & Hizmet', 'Ulaştırma: Havacılık & Denizcilik'],
    'Medya & İletişim': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Hukuk, Siyaset & Kamu', 'Müzik & Sahne Sanatları', 'Sanat & Tasarım', 'Turizm & Hizmet', 'İşletme, Ekonomi & Finans'],
    'Sanat & Tasarım': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Eğitim', 'Medya & İletişim', 'Mimarlık & Planlama', 'Mühendislik', 'Müzik & Sahne Sanatları'],
    'Müzik & Sahne Sanatları': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Eğitim', 'Medya & İletişim', 'Sanat & Tasarım', 'Spor Bilimleri'],
    'Mimarlık & Planlama': ['Mühendislik', 'Sanat & Tasarım'],
    'Tarım, Hayvancılık, Gıda & Çevre': ['Dil, Edebiyat, Tarih & Beşeri Bilimler', 'Eğitim', 'Mühendislik', 'Sağlık & Rehabilitasyon', 'Temel Bilimler', 'İşletme, Ekonomi & Finans'],
    'Ulaştırma: Havacılık & Denizcilik': ['Mühendislik', 'Turizm & Hizmet', 'İşletme, Ekonomi & Finans'],
    'Turizm & Hizmet': ['Medya & İletişim', 'Spor Bilimleri', 'Ulaştırma: Havacılık & Denizcilik', 'İşletme, Ekonomi & Finans'],
}


def alan_sirasi(alan_of: dict, skor: dict) -> dict | None:
    """alan_of: bolum_id -> alan adı; skor: bolum_id -> nihai uyum.
    Dönen: alan adı -> grup (0 = ana alan + komşuları, 1 = yakın ama ana alanla ilgisiz ikinci alan, 2 = diğer).
    Liste önce grup 0, sonra grup 1, en son grup 2 olacak şekilde sıralanır (None = kısıt yok)."""
    gruplar: dict[str, list[float]] = {}
    for b, s in skor.items():
        a = alan_of.get(b)
        if a:
            gruplar.setdefault(a, []).append(s)
    if len(gruplar) < 2:
        return None
    guc = {a: float(np.mean(sorted(l, reverse=True)[:3])) for a, l in gruplar.items()}
    sirali = sorted(guc, key=lambda a: -guc[a])
    ana = sirali[0]
    birincil = {ana, *KOMSU.get(ana, [])}
    sonuc = {a: (0 if a in birincil else 2) for a in gruplar}
    ikinci = sirali[1]
    if sonuc[ikinci] == 2 and guc[ikinci] >= guc[ana] - IKINCI_ALAN_FARK:
        sonuc[ikinci] = 1
    return sonuc
