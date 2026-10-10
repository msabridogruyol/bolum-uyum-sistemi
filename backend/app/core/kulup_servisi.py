# -*- coding: utf-8 -*-
"""
[2026-10-10] Öğrenci toplulukları (kulüpler) ve kısa ilgi testi.

İlgi testi: 10 ilgi boyutu × 2 madde = 20 soru, 1-5 ölçek ("Hiç hoşlanmam" … "Çok hoşlanırım").
Boyut puanı = madde ortalamasının 0-100'e çevrilmesi. Bu test meslek/bölüm önerisini ETKİLEMEZ;
yalnızca kulüp / sosyal etkinlik önerisi ve öğrencinin kendini tanıması içindir.

Kulüp uyumu = kulübün ilgi etiketlerinin ağırlıklı ortalaması (ilk etiket 1.0, diğerleri 0.7).
"""
from __future__ import annotations

import json

from sqlalchemy import text
from sqlalchemy.orm import Session

BOYUTLAR = {
    "bilim": {"ad": "Bilim ve deney", "ikon": "🔬"},
    "teknoloji": {"ad": "Teknoloji ve kodlama", "ikon": "💻"},
    "sanat": {"ad": "Görsel sanat ve tasarım", "ikon": "🎨"},
    "muzik": {"ad": "Müzik", "ikon": "🎵"},
    "sahne": {"ad": "Sahne ve sunum", "ikon": "🎭"},
    "spor": {"ad": "Spor ve hareket", "ikon": "⚽"},
    "edebiyat": {"ad": "Okuma ve yazma", "ikon": "📚"},
    "toplum": {"ad": "Gönüllülük ve toplum", "ikon": "🤝"},
    "doga": {"ad": "Doğa ve çevre", "ikon": "🌿"},
    "strateji": {"ad": "Tartışma ve strateji", "ikon": "♟️"},
}

# Sıra karışık verilir (aynı boyutun maddeleri art arda gelmesin)
SORULAR = [
    ("b1", "bilim", "Deney yapıp bir şeyin neden öyle olduğunu araştırmak"),
    ("t1", "teknoloji", "Kod yazmak, bir uygulama ya da oyun geliştirmek"),
    ("a1", "sanat", "Resim, çizim, fotoğraf ya da el işiyle bir şey üretmek"),
    ("m1", "muzik", "Bir enstrüman çalmak ya da şarkı söylemek"),
    ("h1", "sahne", "Sahnede rol almak ya da bir gösteri hazırlamak"),
    ("s1", "spor", "Bir takımda spor yapıp maçlara katılmak"),
    ("e1", "edebiyat", "Kitap okuyup üzerine sohbet etmek"),
    ("g1", "toplum", "Gönüllü bir projede ihtiyacı olanlara yardım etmek"),
    ("d1", "doga", "Doğa yürüyüşü, kamp ya da gözlem gezisi yapmak"),
    ("r1", "strateji", "Münazarada bir görüşü savunmak, karşı görüşle tartışmak"),
    ("t2", "teknoloji", "Robot, elektronik devre ya da 3B tasarım ile uğraşmak"),
    ("e2", "edebiyat", "Hikâye, şiir, haber ya da blog yazısı yazmak"),
    ("b2", "bilim", "Bilim yarışmasına ya da proje fuarına hazırlanmak"),
    ("h2", "sahne", "Kalabalık önünde sunum yapmak, bir etkinliği sunmak"),
    ("a2", "sanat", "Bir afişi, dergi sayfasını ya da bir mekânı tasarlamak"),
    ("g2", "toplum", "Okulda bir kampanya ya da sosyal sorumluluk projesi yürütmek"),
    ("s2", "spor", "Düzenli antrenmanla bir sporda kendimi geliştirmek"),
    ("r2", "strateji", "Satranç, zekâ oyunları ya da girişimcilik yarışmasında strateji kurmak"),
    ("m2", "muzik", "Bir koroda ya da müzik grubunda yer almak"),
    ("d2", "doga", "Çevre, hayvanlar ya da geri dönüşüm üzerine çalışmak"),
]
SORU_BOYUT = {k: b for k, b, _ in SORULAR}

# Lise kulüplerinde yaygın liste (okul ekler / siler / düzenler). ilgiler: ilk etiket ana ilgi.
HAZIR_KULUPLER = [
    ("Bilim ve Teknoloji Kulübü", "Deneyler, bilim şenliği ve TÜBİTAK projeleri", "bilim,teknoloji"),
    ("Robotik ve Kodlama Kulübü", "Robot yapımı, kodlama, yarışmalara hazırlık", "teknoloji,bilim"),
    ("Astronomi Kulübü", "Gök gözlemi, uzay bilimleri, gözlem geceleri", "bilim,doga"),
    ("Matematik ve Zekâ Oyunları Kulübü", "Mantık bulmacaları, akıl oyunları, olimpiyat hazırlığı", "strateji,bilim"),
    ("Satranç Kulübü", "Satranç eğitimi ve turnuvalar", "strateji"),
    ("Münazara Kulübü", "Tartışma teknikleri, münazara turnuvaları", "strateji,sahne"),
    ("Model Birleşmiş Milletler (MUN) Kulübü", "Diplomasi simülasyonu, İngilizce müzakere", "strateji,toplum,sahne"),
    ("Girişimcilik Kulübü", "İş fikri geliştirme, girişimcilik yarışmaları", "strateji,toplum"),
    ("E-Spor ve Oyun Tasarımı Kulübü", "Oyun tasarımı, takım oyunları, turnuvalar", "teknoloji,strateji"),
    ("Resim ve Görsel Sanatlar Kulübü", "Resim, çizim, sergiler", "sanat"),
    ("Fotoğrafçılık Kulübü", "Fotoğraf teknikleri, foto gezileri, sergi", "sanat,doga"),
    ("Film ve Video Kulübü", "Kısa film, kurgu, okul tanıtım videoları", "sanat,teknoloji,sahne"),
    ("Grafik Tasarım Kulübü", "Afiş, logo ve dijital tasarım", "sanat,teknoloji"),
    ("Müzik Kulübü", "Enstrüman, okul müzik grubu, konserler", "muzik"),
    ("Koro", "Çok sesli koro çalışmaları ve konserler", "muzik,sahne"),
    ("Tiyatro Kulübü", "Oyun hazırlığı, doğaçlama, sahneleme", "sahne,edebiyat"),
    ("Halk Oyunları Kulübü", "Yöresel oyunlar, gösteriler", "sahne,spor,muzik"),
    ("Sunuculuk ve Diksiyon Kulübü", "Etkili konuşma, tören ve etkinlik sunuculuğu", "sahne,edebiyat"),
    ("Kitap ve Kütüphane Kulübü", "Okuma grupları, yazar söyleşileri", "edebiyat"),
    ("Okul Dergisi ve Gazetecilik Kulübü", "Haber, röportaj, okul dergisi ve sosyal medya", "edebiyat,sanat"),
    ("Yabancı Dil Kulübü", "Konuşma pratiği, film ve kültür etkinlikleri", "edebiyat,toplum"),
    ("Tarih ve Kültür Kulübü", "Tarih gezileri, müze ziyaretleri, araştırma", "edebiyat,strateji"),
    ("Felsefe ve Düşünce Kulübü", "Felsefi tartışmalar, eleştirel düşünme", "strateji,edebiyat"),
    ("Sosyal Yardımlaşma ve Dayanışma Kulübü", "Yardım kampanyaları, gönüllülük", "toplum"),
    ("Kızılay ve İlk Yardım Kulübü", "İlk yardım eğitimi, kan bağışı kampanyaları", "toplum,bilim"),
    ("Çevre ve Sıfır Atık Kulübü", "Geri dönüşüm, ağaçlandırma, çevre kampanyaları", "doga,toplum"),
    ("Doğa Sporları ve İzcilik Kulübü", "Kamp, yürüyüş, yön bulma", "doga,spor"),
    ("Hayvan Hakları ve Barınak Kulübü", "Barınak ziyaretleri, farkındalık çalışmaları", "doga,toplum"),
    ("Spor Kulübü", "Futbol, basketbol, voleybol takımları", "spor"),
    ("Sağlıklı Yaşam ve Beslenme Kulübü", "Beslenme, hareket, sağlık farkındalığı", "spor,toplum,bilim"),
]


def etiketler(ilgiler: str | None) -> list[str]:
    return [x.strip() for x in (ilgiler or "").split(",") if x.strip() in BOYUTLAR]


def puanla(cevaplar: dict) -> dict:
    toplam: dict[str, list[int]] = {b: [] for b in BOYUTLAR}
    for k, v in cevaplar.items():
        b = SORU_BOYUT.get(k)
        if b and isinstance(v, int) and 1 <= v <= 5:
            toplam[b].append(v)
    return {b: round((sum(v) / len(v) - 1) * 25) for b, v in toplam.items() if v}


def kulup_uyumu(puanlar: dict, ilgiler: str) -> int | None:
    e = etiketler(ilgiler)
    if not e:
        return None
    agirlik = [(puanlar.get(b, 50), 1.0 if i == 0 else 0.7) for i, b in enumerate(e)]
    return round(sum(p * w for p, w in agirlik) / sum(w for _, w in agirlik))


def neden(puanlar: dict, ilgiler: str) -> str:
    e = sorted(etiketler(ilgiler), key=lambda b: -puanlar.get(b, 0))
    uygun = [f"{BOYUTLAR[b]['ad'].lower()} (%{puanlar.get(b, 0)})" for b in e if puanlar.get(b, 0) >= 60]
    return ("İlgilerinle örtüşüyor: " + ", ".join(uygun[:2])) if uygun else "Yeni bir alan denemek için"


def okul_kulupleri(db: Session, okul_id: int | None, sadece_aktif: bool = True) -> list[dict]:
    if not okul_id:
        return []
    q = "SELECT id, ad, aciklama, ilgiler, sorumlu, bulusma, aktif, sira FROM okul_kulupleri WHERE okul_id = :o"
    if sadece_aktif:
        q += " AND aktif"
    return [dict(r) for r in db.execute(text(q + " ORDER BY sira, ad"), {"o": okul_id}).mappings().all()]


def ilgi_sonucu(db: Session, ogrenci_id) -> dict | None:
    r = db.execute(text("SELECT cevaplar, puanlar, tamamlanma_zamani FROM ogrenci_ilgi_testleri WHERE ogrenci_id = :i"),
                   {"i": str(ogrenci_id)}).mappings().first()
    if not r:
        return None
    p = r["puanlar"] if isinstance(r["puanlar"], dict) else json.loads(r["puanlar"])
    c = r["cevaplar"] if isinstance(r["cevaplar"], dict) else json.loads(r["cevaplar"])
    return {"puanlar": p, "cevaplar": c, "tamamlanma": r["tamamlanma_zamani"]}


def oneriler(puanlar: dict, kulupler: list[dict], n: int = 5) -> list[dict]:
    sonuc = []
    for k in kulupler:
        u = kulup_uyumu(puanlar, k["ilgiler"])
        if u is None:
            continue
        sonuc.append({**k, "uyum": u, "neden": neden(puanlar, k["ilgiler"]),
                      "ilgi_adlari": [BOYUTLAR[b]["ad"] for b in etiketler(k["ilgiler"])]})
    sonuc.sort(key=lambda x: (-x["uyum"], x["ad"]))
    return sonuc[:n]


def hazir_liste() -> list[dict]:
    return [{"id": None, "ad": a, "aciklama": c, "ilgiler": i, "sorumlu": None, "bulusma": None, "aktif": True, "sira": n}
            for n, (a, c, i) in enumerate(HAZIR_KULUPLER)]


def boyut_listesi() -> list[dict]:
    return [{"kod": k, **v} for k, v in BOYUTLAR.items()]
