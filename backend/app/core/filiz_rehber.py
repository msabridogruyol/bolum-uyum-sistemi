# -*- coding: utf-8 -*-
"""
[2026-10-10] Filiz Otomatik Rehber — yapay zekâ (API anahtarı) bağlı DEĞİLKEN çalışan kural tabanlı sohbet botu.

- Öğrencinin sistemdeki GERÇEK verilerini kullanır (hedef bölüm, güçlü / gelişim yönleri, yol haritası adımı,
  haftalık görevler, en uyumlu bölümler, ilham kaynakları, kulüp önerileri, takvim, kütüphane).
- Soruyu anahtar kelimelerle bir konuya eşler; eşleşmezse örnek sorular önerir. Serbest sohbet ETMEZ.
- Arayüzde "Otomatik rehber — yapay zekâ bağlı değil" etiketiyle gösterilir. API anahtarı eklenince
  hiçbir kod değişikliği olmadan gerçek yapay zekâya geçilir.
"""
from __future__ import annotations

import random
import re
from datetime import date

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models import Bolum, Ogrenci

# [2026-10-10] "Sorabileceklerin" sekmesi: kategorili örnek sorular. Her soru otomatik rehberde bir konuya eşlenir.
SORU_KATEGORILERI = [
    {"ad": "Başlangıç", "ikon": "👋", "sorular": [
        "Filiz, sen kimsin?", "Sistem nasıl çalışıyor?", "Testi nasıl cevaplamalıyım?", "Değerlendirmede neredeyim?"]},
    {"ad": "Sonuçlarım", "ikon": "🧭", "sorular": [
        "Güçlü yönlerim neler?", "Hangi yönlerimi geliştirmeliyim?", "Bana hangi bölümler uygun?", "Uyum yüzdesi ne demek?"]},
    {"ad": "Hedef ve yol haritası", "ikon": "🎯", "sorular": [
        "Hedef bölümüm bana uygun mu?", "Hedef bölümüm hakkında bilgi verir misin?", "Yol haritamda sıradaki adım ne?",
        "Bu hafta neye odaklanmalıyım?", "Hedef bölümümü değiştirebilir miyim?"]},
    {"ad": "Gelişim", "ikon": "🌱", "sorular": [
        "Okuyabileceğim bir kitap önerir misin?", "İzleyebileceğim bir belgesel önerir misin?",
        "Kütüphanemde neler var?", "Hangi kulübe katılmalıyım?"]},
    {"ad": "Motivasyon ve çalışma", "ikon": "💪", "sorular": [
        "Sınav kaygısıyla nasıl başa çıkarım?", "Nasıl daha verimli ders çalışırım?",
        "Motivasyonum düştü, ne yapmalıyım?", "Bölüm seçiminde kararsızım, ne yapmalıyım?"]},
    {"ad": "Destek", "ikon": "🤝", "sorular": [
        "Bir eğitim koçuyla nasıl görüşürüm?", "Takvimimde ne var?", "Rehber öğretmenime nasıl ulaşırım?"]},
]
ORNEK_SORULAR = [
    "Bu hafta neye odaklanmalıyım?", "Güçlü yönlerim neler?", "Hangi yönlerimi geliştirmeliyim?",
    "Hedef bölümüm bana uygun mu?", "Bana hangi bölümler uygun?", "Okuyabileceğim bir kitap önerir misin?",
    "Sınav kaygısıyla nasıl başa çıkarım?", "Hangi kulübe katılmalıyım?", "Bir eğitim koçuyla nasıl görüşürüm?",
]


def _sade(m: str) -> str:
    t = str(m).replace("İ", "i").replace("I", "ı").lower()
    for a, b in (("ı", "i"), ("ğ", "g"), ("ü", "u"), ("ş", "s"), ("ö", "o"), ("ç", "c"), ("â", "a")):
        t = t.replace(a, b)
    return " ".join(t.split())


def _kucuk(m: str | None) -> str:
    """Türkçe küçük harf (İ → i, I → ı)."""
    return (m or "").replace("İ", "i").replace("I", "ı").lower()


def _baslik(m: str | None) -> str:
    try:
        from app.core.koclugu_servisi import turkce_baslik
        return turkce_baslik(m or "")
    except Exception:
        return m or ""


# ----------------------------------------------------------------------------- veri
class Baglam:
    def __init__(self, db: Session, o: Ogrenci):
        self.db, self.o = db, o
        self.ad = (o.ad_soyad or "").split()[0] if o.ad_soyad else ""
        self.hedef = None
        self.plan = None
        self._yukle_plan()

    def _yukle_plan(self):
        try:
            from app.core.koclugu_servisi import aktif_hedef_getir, gap_analizi_hesapla, gelisim_plani_olustur
            from app.core.katman_servisi import son_tur_getir
            h = aktif_hedef_getir(self.db, self.o)
            if h is None:
                return
            b = self.db.get(Bolum, h.bolum_id)
            self.hedef = {"id": h.bolum_id, "ad": _baslik(b.ad if b else "")}
            tur = son_tur_getir(self.db, self.o)
            if tur.durum != "tamamlandi":
                return
            satirlar = gap_analizi_hesapla(self.db, self.o, tur, h.bolum_id)
            if satirlar:
                self.plan = gelisim_plani_olustur(self.db, self.o, h.bolum_id, satirlar)
        except Exception:
            self.db.rollback()

    def degerlendirme(self) -> dict:
        from app.models import Katman, OgrenciKatmanOturumu
        try:
            from app.core.katman_servisi import son_tur_getir
            tur = son_tur_getir(self.db, self.o)
        except Exception:
            return {"durum": "yok", "biten": 0, "toplam": 4}
        toplam = self.db.query(Katman).filter(Katman.kosullu_mu.is_(False)).count() or 4
        biten = (self.db.query(OgrenciKatmanOturumu).join(Katman, Katman.id == OgrenciKatmanOturumu.katman_id)
                 .filter(OgrenciKatmanOturumu.ogrenci_id == self.o.id, OgrenciKatmanOturumu.tur_id == tur.id,
                         OgrenciKatmanOturumu.durum == "tamamlandi", Katman.kosullu_mu.is_(False)).count())
        return {"durum": tur.durum, "biten": biten, "toplam": toplam, "tur": tur}

    def ilk_bolumler(self, n=3) -> list[tuple[str, int]]:
        d = self.degerlendirme()
        if d["durum"] != "tamamlandi":
            return []
        try:
            from app.core.skor_motoru import siralama_getir
            return [(_baslik(self.db.get(Bolum, s.bolum_id).ad), round(float(s.toplam_uyum)))
                    for s in siralama_getir(self.db, self.o, d["tur"], ilk_n=n)]
        except Exception:
            self.db.rollback()
            return []

    def simdiki_adim(self) -> dict | None:
        a = (self.plan or {}).get("siradaki_adim")
        return {**a, "alan": a.get("degisken_adi")} if a else None

    def gorevler(self) -> list:
        try:
            from app.core.haftalik_servisi import haftanin_gorevleri
            return haftanin_gorevleri(self.db, self.o)
        except Exception:
            self.db.rollback()
            return []

    def kaynak(self, tip: str | None = None) -> list[dict]:
        if not self.plan:
            return []
        from app.models import GelisimKaynakOnerisi
        alanlar = [(a["degisken_id"], a["degisken_adi"]) for a in self.plan.get("odak_alanlari", []) + self.plan.get("guclu_yonler", [])]
        if not alanlar:
            return []
        q = self.db.query(GelisimKaynakOnerisi).filter(GelisimKaynakOnerisi.degisken_id.in_([a for a, _ in alanlar]))
        if tip:
            q = q.filter(GelisimKaynakOnerisi.kaynak_tipi == tip)
        ad = dict(alanlar)
        return [{"baslik": k.baslik, "aciklama": k.aciklama, "alan": ad.get(k.degisken_id), "tip": k.kaynak_tipi}
                for k in q.order_by(GelisimKaynakOnerisi.sira).limit(6).all()]


# ----------------------------------------------------------------------------- konular
def _liste(adlar: list[str]) -> str:
    adlar = [a for a in adlar if a]
    if len(adlar) <= 1:
        return "".join(adlar)
    return ", ".join(adlar[:-1]) + " ve " + adlar[-1]


def _hedefsiz(b: Baglam) -> str:
    d = b.degerlendirme()
    if d["durum"] == "yok":
        return "Önce değerlendirmeye başlaman gerekiyor. Sol menüdeki 📝 Değerlendirme'den K1 (Değerler) ile başlayabilirsin; sonuçların çıkınca sana çok daha net şeyler söyleyebilirim."
    if d["durum"] != "tamamlandi":
        return f"Değerlendirmenin {d['biten']}/{d['toplam']} bölümünü tamamladın. Kalanları bitirince güçlü yönlerin ve sana uygun bölümler ortaya çıkacak — o zaman birlikte daha çok konuşabiliriz."
    ilk = b.ilk_bolumler()
    ek = f" Sistemin sana en uyumlu bulduğu bölümler: {_liste([f'{a} (%{p})' for a, p in ilk])}." if ilk else ""
    return "Henüz bir hedef bölüm seçmemişsin." + ek + " Bölümler sayfasında bunları inceleyip birini hedef seçersen sana özel bir yol haritası hazırlanır."


def k_selam(b: Baglam, m: str) -> str:
    giris = random.choice(["Merhaba", "Selam", "Hoş geldin"]) + (f" {b.ad}" if b.ad else "") + "! 🌱"
    if b.hedef:
        adim = b.simdiki_adim()
        devam = f" Hedefin {b.hedef['ad']}." + (f" Yol haritandaki şimdiki adımın: \"{adim['baslik']}\"." if adim else "")
    else:
        devam = " " + _hedefsiz(b)
    return f"{giris}{devam} Bugün neyi konuşmak istersin?"


def k_tesekkur(b: Baglam, m: str) -> str:
    return random.choice(["Rica ederim! 🌱 Başka merak ettiğin bir şey olursa buradayım.",
                          "Ne demek, her zaman! Küçük adımlar büyük farklar yaratır, devam et. 💪"])


def k_hafta(b: Baglam, m: str) -> str:
    g = b.gorevler()
    bekleyen = [x for x in g if x.durum != "tamamlandi"]
    parca = []
    if bekleyen:
        parca.append(f"Bu hafta seni bekleyen {len(bekleyen)} görev var: {_liste([x.baslik for x in bekleyen])}.")
    elif g:
        parca.append("Bu haftanın görevlerinin hepsini tamamlamışsın, harika! 🎉")
    adim = b.simdiki_adim()
    if adim:
        parca.append(f"Yol haritanda sıradaki adım \"{adim['baslik']}\" ({adim.get('alan')}). {adim.get('aciklama') or ''}".strip())
    if not parca:
        return _hedefsiz(b)
    return " ".join(parca) + " Haftada 1-2 adım yeterli; acele etme. Görevlerim sayfasından ilerleyebilirsin."


def k_guclu(b: Baglam, m: str) -> str:
    if not b.plan:
        return _hedefsiz(b)
    g = b.plan.get("guclu_yonler", [])
    if not g:
        return f"{b.hedef['ad']} için belirgin biçimde öne çıkan bir güçlü yönün şu an görünmüyor; bu kötü bir şey değil, birçok özelliğin bölümün beklediği düzeyde. Profilim sayfasında tüm özelliklerini görebilirsin."
    ilk = g[0]
    return (f"{b.hedef['ad']} açısından en güçlü yönlerin: {_liste([x['degisken_adi'] for x in g[:3]])}. "
            f"Örneğin {_kucuk(ilk['degisken_adi'])}: {ilk.get('neden_onemli') or ''} "
            "Koçluğum → Güçlü Yönlerin sekmesinde bunları görünür bir başarıya çevirecek adımlar var.").replace("  ", " ")


def k_gelisim(b: Baglam, m: str) -> str:
    if not b.plan:
        return _hedefsiz(b)
    o = b.plan.get("odak_alanlari", [])
    if not o:
        return f"Harika haber: {b.hedef['ad']} için öncelikli bir gelişim alanın görünmüyor. Güçlü yönlerini büyütmeye odaklanabilirsin."
    ilk = o[0]
    adim = b.simdiki_adim()
    return (f"{b.hedef['ad']} için odaklanman önerilen alanlar: {_liste([x['degisken_adi'] for x in o[:3]])}. "
            f"En öncelikli olan {_kucuk(ilk['degisken_adi'])}. "
            + (f"Başlamak için şu adımı deneyebilirsin: \"{adim['baslik']}\". " if adim else "")
            + "Gelişime açık olmak eksik olmak demek değil; bunlar biraz emekle büyüyebilecek yönlerin.")


def k_hedef(b: Baglam, m: str) -> str:
    if not b.hedef:
        return _hedefsiz(b)
    ilk = b.ilk_bolumler(10)
    sira = next((i for i, (a, _) in enumerate(ilk, 1) if a == b.hedef["ad"]), None)
    uyum = next((p for a, p in ilk if a == b.hedef["ad"]), None)
    if sira:
        return (f"Hedefin {b.hedef['ad']}, sana en uyumlu bölümler arasında {sira}. sırada (%{uyum} uyum). "
                "Bu iyi bir eşleşme. Koçluğum → Sen ve Bölümün sekmesinde hangi yönlerde bölümle örtüştüğünü ayrıntılı görebilirsin.")
    return (f"Hedefin {b.hedef['ad']}, ilk 10 önerin arasında değil — ama bu \"yapamazsın\" demek değil. Bazı özelliklerin bölümün "
            "beklentisinden farklı; yol haritan tam olarak bu farkları kapatmak için hazırlandı. İstersen öne çıkan diğer bölümlere de "
            "Bölümler sayfasından göz at; karar her zaman senin.")


def k_bolum_oner(b: Baglam, m: str) -> str:
    ilk = b.ilk_bolumler(5)
    if not ilk:
        return _hedefsiz(b)
    return (f"Değerlendirmene göre sana en uyumlu bölümler: {_liste([f'{a} (%{p})' for a, p in ilk])}. "
            "Uyum yüzdesi profilinin o bölümde mutlu ve başarılı olanlara ne kadar benzediğini gösterir. "
            "Bölümler sayfasında her birinin ne okuttuğunu ve hangi üniversitelerde olduğunu inceleyebilir, Karşılaştır ile yan yana koyabilirsin.")


def k_kaynak(b: Baglam, m: str) -> str:
    t = _sade(m)
    tip = "kitap" if "kitap" in t or "oku" in t else "film" if any(x in t for x in ("film", "belgesel", "dizi", "izle")) else None
    k = b.kaynak(tip)
    if k:
        x = random.choice(k[:3])
        return (f"Sana \"{x['baslik']}\" önerebilirim; {_kucuk(x['alan']) if x['alan'] else 'gelişimin'} alanında işine yarar. {x['aciklama']} "
                "Koçluğum → İlham Kaynakları'nda daha fazlası var; beğendiklerini tek tıkla Kütüphanem'e ekleyebilirsin.")
    return ("Senin alanların için ilham kaynakları henüz hazırlanıyor. O zamana kadar ilgini çeken bir kitap ya da belgeseli "
            "Kütüphanem'e ekleyip okuduktan sonra \"ne öğrendim\" notunu yazmayı dene — rehber öğretmeninle konuşurken çok işe yarar.")


def k_sinav(b: Baglam, m: str) -> str:
    return random.choice([
        "Sınav kaygısı çok yaygın ve tamamen normal. İşe yarayan birkaç şey: çalışmayı 25-30 dakikalık bloklara bölmek, her bloktan sonra kısa mola, "
        "deneme sınavlarını gerçek sınav koşullarında çözmek ve uykunu düzenli tutmak. Kaygı günlük hayatını zorlaştırıyorsa rehber öğretmeninle "
        "ya da Eğitim Koçları sayfasındaki bir koçla görüşmeni öneririm.",
        "Düzenli ve küçük adımlar, son dakikadaki büyük çabadan daha etkilidir. Haftalık bir plan yap, her gün aynı saatte kısa bir tekrar ekle ve "
        "yaptıklarını Takvim'ine not al. Motivasyonun düştüğünde neden bu hedefi istediğini hatırlamak iyi gelir. Desteğe ihtiyacın olursa Eğitim Koçları sayfasından görüşme talebi bırakabilirsin.",
    ])


def k_kulup(b: Baglam, m: str) -> str:
    try:
        from app.core import kulup_servisi as ks
        s = ks.ilgi_sonucu(b.db, b.o.id)
        if not s:
            return "Kulüplerim sayfasındaki 20 soruluk kısa ilgi testini çözersen okulundaki kulüplerden sana en uygun olanları önerebilirim. Yaklaşık 3 dakika sürüyor."
        kulupler = ks.okul_kulupleri(b.db, b.o.okul_id) or ks.hazir_liste()
        on = ks.oneriler(s["puanlar"], kulupler, n=3)
        adlar = [f"{x['ad']} (%{x['uyum']})" for x in on]
        return (f"İlgi testine göre sana en uygun kulüpler: {_liste(adlar)}. "
                "Ayrıntılar ve danışman öğretmen bilgisi Kulüplerim sayfasında.")
    except Exception:
        b.db.rollback()
        return "Kulüplerim sayfasından ilgi testini çözüp sana uygun kulüpleri görebilirsin."


def k_koc(b: Baglam, m: str) -> str:
    return ("Eğitim Koçları sayfasında okulunun anlaşmalı koçlarını görebilirsin; ilgilendiğin alana uygun olanlar üstte işaretli. "
            "Bir koç seçip görüşme talebi bırakırsan talebin Filizyol koordinatörüne gider; görüşme planlanınca tarih ve saat Takvim'inde görünür.")


def k_takvim(b: Baglam, m: str) -> str:
    try:
        r = b.db.execute(text("""
            SELECT baslik, baslangic FROM takvim_etkinlikleri
             WHERE baslangic >= :b AND ((okul_id IS NULL AND ogrenci_id IS NULL) OR (okul_id = :ok AND ogrenci_id IS NULL) OR ogrenci_id = :o)
               AND (hedef_sinif IS NULL OR hedef_sinif = :sf)
             ORDER BY baslangic LIMIT 1"""), {"b": date.today(), "ok": b.o.okul_id or -1, "o": b.o.id, "sf": b.o.sinif or ""}).first()
    except Exception:
        b.db.rollback()
        r = None
    if r:
        gun = (r[1] - date.today()).days
        return f"Takviminde sıradaki etkinlik: \"{r[0]}\" — {r[1].strftime('%d.%m.%Y')} ({'bugün' if gun == 0 else f'{gun} gün sonra'}). Tüm tarihler Takvim sayfasında."
    return "Takviminde yaklaşan bir etkinlik görünmüyor. Kendi hatırlatmalarını Takvim sayfasından ekleyebilirsin."


def k_test(b: Baglam, m: str) -> str:
    if "cevapla" in _sade(m):
        return ("Doğru ya da yanlış cevap yok. \"Olmak istediğin\" kişiye göre değil, şu anki hâline göre cevap ver; çok düşünmeden ilk "
                "aklına gelen genelde en doğrusudur. \"En çok / en az\" sorularında önce sana en çok, sonra en az uyan şıkkı seçersin. "
                "Ara verirsen cevapların kaydedilir, döndüğünde kaldığın yerden devam edersin.")
    d = b.degerlendirme()
    if d["durum"] == "tamamlandi":
        return "Değerlendirmeni tamamladın. Sonuçların Profilim ve Bölümler sayfalarında. Belli bir süre sonra yeni tur açılınca kendindeki değişimi de görebileceksin."
    if d["durum"] == "yok":
        return "Değerlendirmeye henüz başlamadın. Doğru ya da yanlış cevap yok; içinden geldiği gibi cevaplaman en doğru sonucu verir. Ara verirsen cevapların kaydedilir."
    return f"Değerlendirmenin {d['biten']}/{d['toplam']} bölümünü bitirdin. Ara verdiğinde cevapların kaydedilir; döndüğünde kaldığın sorudan devam edersin."


def k_uyum(b: Baglam, m: str) -> str:
    return ("Uyum yüzdesi, profilinin o bölümde mutlu ve başarılı olan kişilerin özelliklerine ne kadar benzediğini gösterir. "
            "Bir başarı tahmini değildir ve tek başına karar vermek için kullanılmamalı; ilgini, hayallerini ve ailenle konuştuklarını da hesaba kat.")


def k_kim(b: Baglam, m: str) -> str:
    return ("Ben Filiz, bölüm ve meslek yolculuğunda sana eşlik eden rehberinim. 🌱 Şu an otomatik rehber modunda çalışıyorum: "
            "sistemdeki sonuçlarına göre hazır cevaplar veriyorum. Serbest sohbet edemiyorum ama aşağıdaki gibi sorulara yardımcı olabilirim.")


def k_sistem(b: Baglam, m: str) -> str:
    return ("Filizyol dört adımda ilerler: 1) Değerlendirme — değerlerin, kişiliğin, sevdiğin iş ortamı ve ilgi alanların. "
            "2) Sonuçlar — Profilim'de güçlü yönlerin, Bölümler'de sana en uyumlu bölümler. 3) Hedef — bir bölüm seçersin, "
            "Koçluğum'da sana özel yol haritası çıkar. 4) Gelişim — haftalık görevler, kulüpler, kütüphanen ve takvimin. "
            "Ayrıntılar sol menüdeki Sistem Hakkında sayfasında.")


def k_adim(b: Baglam, m: str) -> str:
    adim = b.simdiki_adim()
    if not adim:
        return _hedefsiz(b) if not b.plan else "Yol haritandaki tüm adımları tamamlamışsın, tebrikler! 🎉 Güçlü Yönlerin sekmesindeki adımlarla devam edebilirsin."
    nasil = adim.get("nasil") or []
    ilk = f" İlk iş olarak: {nasil[0]}" if nasil else ""
    return (f"Sıradaki adımın \"{adim['baslik']}\" ({adim.get('alan')}, yaklaşık {adim.get('sure') or 'kısa bir süre'}). "
            f"{adim.get('aciklama') or ''}{ilk} Bitirdiğinde Koçluğum → Yol Haritam'da \"Yaptım\"ı işaretle.").replace("  ", " ")


def k_hedef_degis(b: Baglam, m: str) -> str:
    from app.core.koclugu_servisi import hedef_hak_durumu
    h = hedef_hak_durumu(b.o)
    if h["kalan_hak"] > 0:
        return (f"Evet. Hedefini {h['kalan_hak']} kez daha değiştirebilirsin; bunu Ayarlar sayfasındaki Hedef Bölümüm kartından yaparsın. "
                "Değiştirmeden önce Bölümler → Karşılaştır ile mevcut hedefini yeni bölümle yan yana koymanı öneririm; yol haritan yeni hedefe göre yeniden hazırlanır.")
    return ("Hedef değiştirme hakların bitmiş. Gerçekten değiştirmek istiyorsan rehber öğretmenine danış; okulun sana ek hak tanıyabilir.")


def k_bolum_bilgi(b: Baglam, m: str) -> str:
    if not b.hedef:
        return _hedefsiz(b)
    bolum = b.db.get(Bolum, b.hedef["id"])
    d = (bolum.detay if bolum is not None and isinstance(bolum.detay, dict) else {}) or {}
    ozet = d.get("ozet") or (bolum.kisa_aciklama if bolum is not None else "") or ""
    meslek = [x.get("ad") for x in (d.get("meslekler") or []) if isinstance(x, dict) and x.get("ad")][:3]
    sure = d.get("ogrenim_suresi")
    parca = [f"{b.hedef['ad']}: {ozet}".strip()]
    if meslek:
        parca.append(f"Mezunlar örneğin şu işleri yapar: {_liste(meslek)}.")
    if sure:
        parca.append(f"Öğrenim süresi: {sure}.")
    parca.append("Bölüm adına tıklayınca açılan pencerede dersler ve üniversiteler de var.")
    return " ".join(p for p in parca if p)


def k_motivasyon(b: Baglam, m: str) -> str:
    gorev = next((x for x in b.gorevler() if x.durum != "tamamlandi"), None)
    kucuk = f" Bugün sadece şunu dene: \"{gorev.baslik}\" — 10 dakikanı alır." if gorev else ""
    return ("Motivasyonun dalgalanması çok normal; kimse her gün aynı enerjide değildir. Büyük hedefi küçük parçalara bölmek "
            "işe yarar: bugün yapabileceğin tek ve küçük bir şey seç, bitirince kendini takdir et." + kucuk +
            " Uzun süredir böyle hissediyorsan rehber öğretmeninle konuşmanı öneririm.")


def k_kararsiz(b: Baglam, m: str) -> str:
    ilk = b.ilk_bolumler(3)
    ek = f" Sistemin sana en uyumlu bulduğu üç bölüm: {_liste([a for a, _ in ilk])}." if ilk else ""
    return ("Kararsızlık, seçeneklerini ciddiye aldığını gösterir. Şöyle ilerleyebilirsin: 1) İlgini çeken 2-3 bölümü Listem'e ekle, "
            "2) Bölümler → Karşılaştır ile yan yana koy, 3) her biri için o mesleği yapan biriyle konuşmaya ya da bir gün izlemeye çalış." + ek +
            " Karar verirken uyum yüzdesi kadar ilgini ve hayallerini de hesaba kat.")


def k_rehber(b: Baglam, m: str) -> str:
    return ("Rehber öğretmenine okulunda, rehberlik servisinden ulaşabilirsin. Görüşmeye giderken Profilim sayfandaki güçlü yönlerini ve "
            "hedef bölümünü yanında götürmen konuşmayı kolaylaştırır; rehber öğretmenin sonuçlarını ve raporunu sistemden de görebilir.")


def k_kutuphane(b: Baglam, m: str) -> str:
    try:
        r = b.db.execute(text("""SELECT kategori, COUNT(*) FILTER (WHERE durum = 'bitti'), COUNT(*) FILTER (WHERE durum = 'istek')
                                   FROM ogrenci_kutuphane WHERE ogrenci_id = :o GROUP BY kategori"""), {"o": b.o.id}).all()
    except Exception:
        b.db.rollback()
        r = []
    if not r:
        return "Kütüphanen henüz boş. Okuduğun bir kitabı ya da izlediğin bir belgeseli Kütüphanem sayfasına ekleyerek başlayabilirsin; birkaç cümlelik \"ne öğrendim\" notu çok değerli olur."
    ad = {"kitap": "kitap", "izleme": "film / dizi / belgesel", "kurs": "kurs", "etkinlik": "etkinlik"}
    bitti = [f"{n} {ad.get(k, k)}" for k, n, _ in r if n]
    istek = sum(x[2] for x in r)
    return ("Kütüphanende " + (_liste(bitti) + " tamamlanmış" if bitti else "henüz tamamlanmış kayıt yok")
            + (f"; {istek} kayıt da listende seni bekliyor" if istek else "") + ". Kütüphanem sayfasındaki grafiklerden gelişimini izleyebilirsin.")


# [2026-10-10] İlham Kaynakları → "Filiz'e sor": '"Başlık" (Tip) bana <alan> konusunda ... ' kalıbındaki soruya özel cevap.
_KAYNAK_SORU = re.compile(r'["“](?P<baslik>[^"”]{2,200})["”]\s*\((?P<tip>[^)]{2,40})\)(?:.*?bana\s+(?P<alan>.+?)\s+konusunda)?', re.S)
_TIP_ADI = {"kitap": "kitap", "film / belgesel": "film", "film": "film", "belgesel": "film", "ilham veren kisi": "rol_model",
            "onemli olay": "olay", "yaklasim": "psikolojik_yaklasim", "aktivite": "aktivite"}
_NASIL_BASLA = {
    "kitap": ("Günde 15-20 sayfa okumayı hedefle; her bölümün sonunda \"{alan} açısından bu bana ne söylüyor?\" sorusuna 1-2 cümlelik not yaz. "
              "Kitabı bitirince aklında kalan 3 fikri ve bunları bu hafta nasıl deneyebileceğini yaz."),
    "film": ("İzlerken {alan} ile ilgili 3 sahneyi not al: karakter ne yaptı, sen olsan ne yapardın? "
             "Bittikten sonra 5 dakika ayırıp en etkilendiğin anı ve bundan çıkardığın dersi yaz."),
    "rol_model": ("Bu kişinin hayatına kısaca bak: hangi zorluklarla karşılaştı, hangi kararları verdi? "
                  "{alan} konusunda ondan öğrenebileceğin bir davranışı seç ve bu hafta küçük bir örneğini kendin dene."),
    "olay": ("Önce olayın kısa bir özetini oku: ne oldu, kimler hangi kararları verdi? Sonra \"{alan} açısından buradan ne ders çıkarılır?\" "
             "sorusuna 3 maddelik cevap yaz."),
    "psikolojik_yaklasim": ("Yaklaşımın temel fikrini kısaca öğren, sonra bir hafta boyunca günlük hayatında bir kez uygula. "
                            "Hafta sonunda {alan} konusunda neyin değiştiğini kısaca not et."),
    "aktivite": ("Bu aktiviteyi takvimine bu hafta için tek bir küçük deneme olarak ekle. "
                 "Yaptıktan sonra nasıl hissettiğini ve {alan} konusunda ne fark ettiğini 2-3 cümleyle yaz."),
}


def k_kaynak_soru(b: Baglam, m: str) -> str | None:
    r = _KAYNAK_SORU.search(m or "")
    if not r:
        return None
    baslik = r.group("baslik").strip()
    tip = _TIP_ADI.get(_sade(r.group("tip")).strip())
    alan = (r.group("alan") or "").strip()
    aciklama = ""
    try:
        from app.models import Degisken, GelisimKaynakOnerisi
        q = b.db.query(GelisimKaynakOnerisi).filter(GelisimKaynakOnerisi.baslik == baslik)
        if tip:
            q = q.filter(GelisimKaynakOnerisi.kaynak_tipi == tip)
        k = q.order_by(GelisimKaynakOnerisi.sira).first()
        if k:
            aciklama = k.aciklama or ""
            tip = tip or k.kaynak_tipi
            if not alan:
                d = b.db.get(Degisken, k.degisken_id)
                alan = d.ad if d else ""
    except Exception:
        b.db.rollback()
    alan_k = _kucuk(alan) or "bu alan"
    parcalar = [f"\"{baslik}\" iyi bir seçim."]
    if aciklama:
        parcalar.append(aciklama.rstrip(".") + ".")
    parcalar.append(f"Neden işine yarar: {alan_k} profilinde öne çıkan alanlardan biri; bu kaynak sana o konuda farklı bir bakış ve somut örnekler sunar.")
    parcalar.append("Nereden başlamalısın: " + _NASIL_BASLA.get(tip or "", _NASIL_BASLA["kitap"]).format(alan=alan_k))
    parcalar.append("İstersen İlham Kaynakları'ndaki \"Kütüphaneme ekle\" ile listene kaydet; bitirince kısa notunu da yazarsan gelişimini Kütüphanem'deki grafiklerde görürsün.")
    return " ".join(parcalar)


KONULAR = [
    (("tesekkur", "sagol", "sag ol", "eyvallah", "cok iyi", "super"), k_tesekkur),
    (("kimsin", "sen kim", "nesin", "yapay zeka"), k_kim),
    (("sistem nasil", "nasil calisiyor", "filizyol nedir", "ne ise yarar"), k_sistem),
    (("motivasyon", "isteksiz", "bikkin", "yoruldum", "canim istemiyor", "hevesim"), k_motivasyon),
    (("kararsiz", "karar veremiyorum", "emin degilim", "secemiyorum"), k_kararsiz),
    (("sinav", "kaygi", "stres", "verimli", "ders calis", "nasil calis", "yks", "tyt", "ayt"), k_sinav),
    (("degistir", "degisebilir", "baska bolum sec"), k_hedef_degis),
    (("hakkinda bilgi", "ne okutuyor", "bolum hakkinda", "bolumu anlat", "mezunlar"), k_bolum_bilgi),
    (("siradaki adim", "yol harita", "sonraki adim", "adimim"), k_adim),
    (("bu hafta", "hafta", "gorev", "ne yapay", "nereden basla", "simdi ne", "odaklan"), k_hafta),
    (("kutuphanem", "kutuphane"), k_kutuphane),
    (("kitap", "film", "belgesel", "dizi", "kaynak", "okuyabil", "izleyebil"), k_kaynak),
    (("kulup", "kulub", "topluluk", "ilgi testi"), k_kulup),
    (("rehber ogretmen", "rehberlik servis", "psikolojik danisman"), k_rehber),
    (("koc", "gorusme", "randevu"), k_koc),
    (("takvim", "tarih", "ne zaman", "etkinlik"), k_takvim),
    (("guclu", "iyi oldugum", "yetenek", "avantaj"), k_guclu),
    (("gelistir", "gelisim", "zayif", "eksik", "zorlan"), k_gelisim),
    (("uyum yuzde", "yuzde", "% ", "ne demek"), k_uyum),
    (("hedef", "bana uygun mu", "dogru bolum", "uygun mu"), k_hedef),
    (("hangi bolum", "bolum oner", "uygun bolum", "meslek", "bolumler"), k_bolum_oner),
    (("test", "degerlendirme", "katman", "soru", "cevaplamali", "neredeyim"), k_test),
    (("merhaba", "selam", "gunaydin", "iyi aksam", "hey", "naber", "nasilsin"), k_selam),
]


def otomatik_yanit(db: Session, ogrenci: Ogrenci, metin: str) -> str:
    t = _sade(metin)
    b = Baglam(db, ogrenci)
    if _KAYNAK_SORU.search(metin or ""):
        try:
            c = k_kaynak_soru(b, metin)
            if c:
                return c
        except Exception:
            db.rollback()
    for anahtarlar, f in KONULAR:
        if any(a in t for a in anahtarlar):
            try:
                return f(b, metin)
            except Exception:
                db.rollback()
                break
    ornek = random.sample(ORNEK_SORULAR, 3)
    return ("Bunu tam anlayamadım. 🌱 Şu an otomatik rehber modundayım; sistemdeki sonuçlarına dayanan sorulara cevap verebiliyorum. "
            "Örneğin şunları sorabilirsin: " + " · ".join(f"\"{x}\"" for x in ornek))
