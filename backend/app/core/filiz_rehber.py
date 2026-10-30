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
    # [2026-10-31] Bilgi katmanı (filiz_bilgi): sistemdeki bölüm ve meslek içeriğinden kaynaklı cevap
    {"ad": "Bölümler ve meslekler", "ikon": "📖", "sorular": [
        "Hukuk bölümünde hangi dersler var?", "Psikoloji mezunları nerelerde çalışır?",
        "Mimarlık hakkında bilgi verir misin?", "Tekstil mühendisi bir günde ne yapar?"]},
    {"ad": "Gelişim", "ikon": "🌱", "sorular": [
        "Okuyabileceğim bir kitap önerir misin?", "İzleyebileceğim bir belgesel önerir misin?",
        "Mülakat Simülasyonu nedir?", "Düşünme Atölyesi nedir?",
        "Kütüphanemde neler var?", "Hangi kulübe katılmalıyım?", "Netlerim hedefime göre nasıl?"]},
    {"ad": "Motivasyon ve çalışma", "ikon": "💪", "sorular": [
        "YKS'ye kaç gün kaldı?", "Sınav kaygısıyla nasıl başa çıkarım?", "Nasıl daha verimli ders çalışırım?",
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
        return "Önce değerlendirmeye başlaman gerekiyor. Sol menüden 📝 Değerlendirme'yi aç ve K1 (Değerler) ile başla. Sonuçların çıkınca sana daha net şeyler söyleyebilirim."
    if d["durum"] != "tamamlandi":
        return f"Değerlendirmenin {d['biten']}/{d['toplam']} bölümünü bitirdin. Kalanları da bitir. O zaman güçlü yönlerini ve sana uygun bölümleri görürsün, daha çok konuşabiliriz."
    ilk = b.ilk_bolumler()
    ek = f" Sana en uyumlu bölümler: {_liste([f'{a} (%{p})' for a, p in ilk])}." if ilk else ""
    return "Henüz bir hedef bölüm seçmemişsin." + ek + " Bunlara Bölümler sayfasında bak. Birini hedef seçersen sana özel bir yol haritan olur."


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
                          "Ne demek! Küçük adımlar büyük fark yaratır. Devam et! 💪"])


def k_hafta(b: Baglam, m: str) -> str:
    g = b.gorevler()
    bekleyen = [x for x in g if x.durum != "tamamlandi"]
    parca = []
    if bekleyen:
        parca.append(f"Bu hafta seni bekleyen {len(bekleyen)} görev var: {_liste([x.baslik for x in bekleyen])}.")
    elif g:
        parca.append("Bu haftanın tüm görevlerini bitirmişsin, harika! 🎉")
    adim = b.simdiki_adim()
    if adim:
        parca.append(f"Yol haritanda sıradaki adım \"{adim['baslik']}\" ({adim.get('alan')}). {adim.get('aciklama') or ''}".strip())
    if not parca:
        return _hedefsiz(b)
    return " ".join(parca) + " Haftada 1-2 adım yeterli, acele etme. Görevlerim sayfasından devam edebilirsin."


def k_guclu(b: Baglam, m: str) -> str:
    if not b.plan:
        return _hedefsiz(b)
    g = b.plan.get("guclu_yonler", [])
    if not g:
        return f"{b.hedef['ad']} için şu an çok öne çıkan bir güçlü yönün görünmüyor. Bu kötü değil: birçok özelliğin bölümün beklediği düzeyde. Tüm özelliklerini Profilim sayfasında görebilirsin."
    ilk = g[0]
    return (f"{b.hedef['ad']} için en güçlü yönlerin: {_liste([x['degisken_adi'] for x in g[:3]])}. "
            f"Örneğin {_kucuk(ilk['degisken_adi'])}: {ilk.get('neden_onemli') or ''} "
            "Koçluğum → Güçlü Yönlerin sekmesinde bunları başarıya çevirecek adımlar var.").replace("  ", " ")


def k_gelisim(b: Baglam, m: str) -> str:
    if not b.plan:
        return _hedefsiz(b)
    o = b.plan.get("odak_alanlari", [])
    if not o:
        return f"{b.hedef['ad']} için bölümün senden daha fazla beklediği öncelikli bir alan görünmüyor. Bölümün beklediğinden fazla olduğun yönler varsa Koçluğum → Sen ve Bölümün sekmesine bak: bunlar bu bölümde daha az kullanabileceğin yönlerin, sana uyup uymadığını sına."
    ilk = o[0]
    adim = b.simdiki_adim()
    return (f"{b.hedef['ad']} için odaklanmanı önerdiğim alanlar: {_liste([x['degisken_adi'] for x in o[:3]])}. "
            f"En önemlisi {_kucuk(ilk['degisken_adi'])}. "
            + (f"Şu adımla başlayabilirsin: \"{adim['baslik']}\". " if adim else "")
            + "Bunlar bölümün senden daha fazla beklediği yönler. Becerilerin çalıştıkça gelişir; kişilik yönlerin küçük alışkanlıklarla esneyebilir; ilgileri ise deneyerek keşfedersin."
            # [2026-10-17] değerler büyütülecek bir beceri değil: farkı bilerek karar verilir
            + (" Listedeki değerlerde ise amaç değiştirmek değil, bölümün bu yönünün sana uyup uymadığını bilerek karar vermek."
               if any(str(x.get("degisken_kod") or "").startswith("D") for x in o[:3]) else ""))


def k_hedef(b: Baglam, m: str) -> str:
    if not b.hedef:
        return _hedefsiz(b)
    ilk = b.ilk_bolumler(10)
    sira = next((i for i, (a, _) in enumerate(ilk, 1) if a == b.hedef["ad"]), None)
    uyum = next((p for a, p in ilk if a == b.hedef["ad"]), None)
    if sira:
        return (f"Hedefin {b.hedef['ad']}. Sana en uyumlu bölümler arasında {sira}. sırada (%{uyum} uyum). "
                "Bu iyi bir eşleşme. Bölüme hangi yönlerde uyduğunu Koçluğum → Sen ve Bölümün sekmesinde görebilirsin.")
    return (f"Hedefin {b.hedef['ad']}, ilk 10 önerin arasında değil. Ama bu \"yapamazsın\" demek değil. Bazı özelliklerin bölümün "
            "beklediğinden farklı. Yol haritan, bölümün senden daha fazla beklediği yönlere odaklanır; bölümün beklediğinden fazla olduğun yönlerde ve değerlerinde ise amaç farkı kapatmak değil, sana uyup uymadığını sınamak. İstersen Bölümler sayfasında öne çıkan diğer "
            "bölümlere de bak. Karar her zaman senin.")


def k_bolum_oner(b: Baglam, m: str) -> str:
    ilk = b.ilk_bolumler(5)
    if not ilk:
        return _hedefsiz(b)
    return (f"Değerlendirmene göre sana en uyumlu bölümler: {_liste([f'{a} (%{p})' for a, p in ilk])}. "
            "Uyum puanı, bütün bölümleri profiline yakınlığına göre sıralar: 100 sana en yakın bölüm, 0 en uzak bölüm. "
            "Bölümler sayfasında her bölümün derslerine ve üniversitelerine bakabilirsin. Karşılaştır ile bölümleri yan yana da koyabilirsin.")


def k_kaynak(b: Baglam, m: str) -> str:
    t = _sade(m)
    tip = "kitap" if "kitap" in t or "oku" in t else "film" if any(x in t for x in ("film", "belgesel", "dizi", "izle")) else None
    k = b.kaynak(tip)
    if k:
        x = random.choice(k[:3])
        return (f"Sana \"{x['baslik']}\" önerebilirim. Bu kaynak {_kucuk(x['alan']) if x['alan'] else 'gelişimin'} alanında işine yarar. {x['aciklama']} "
                "Daha fazlası Koçluğum → İlham Kaynakları'nda. Beğendiklerini tek tıkla Kütüphanem'e ekleyebilirsin.")
    return ("İlgini çeken bir kitabı ya da belgeseli Kütüphanem'e ekle. Bitirince kısa bir \"ne öğrendim\" notu yaz. "
            "Bu not, rehber öğretmeninle konuşurken çok işe yarar.")


def k_sinav(b: Baglam, m: str) -> str:
    return random.choice([
        "Sınav kaygısı çok yaygın ve tamamen normal. Şunlar işe yarar: 25-30 dakika çalış, sonra kısa bir mola ver. "
        "Denemeleri gerçek sınav gibi, süre tutarak çöz. Uykunu düzenli tut. Kaygı günlük hayatını zorlaştırıyorsa rehber öğretmeninle konuş. "
        "Eğitim Koçları sayfasındaki bir koçla da görüşebilirsin.",
        "Her gün küçük adımlar atmak, son dakikadaki büyük çabadan daha etkilidir. Haftalık bir plan yap. Her gün aynı saatte kısa bir tekrar ekle. "
        "Yaptıklarını Takvim'ine not al. Motivasyonun düşünce bu hedefi neden istediğini hatırla. Desteğe ihtiyacın olursa Eğitim Koçları sayfasından görüşme talebi bırakabilirsin.",
    ])


def k_kulup(b: Baglam, m: str) -> str:
    try:
        from app.core import kulup_servisi as ks
        s = ks.ilgi_sonucu(b.db, b.o.id)
        if not s:
            return "Kulüplerim sayfasında 20 soruluk kısa bir ilgi testi var, yaklaşık 3 dakika sürüyor. Testi çözersen okulundaki kulüplerden sana en uygun olanları önerebilirim."
        kulupler = ks.okul_kulupleri(b.db, b.o.okul_id) or ks.hazir_liste()
        on = ks.oneriler(s["puanlar"], kulupler, n=3)
        adlar = [f"{x['ad']} (%{x['uyum']})" for x in on]
        return (f"İlgi testine göre sana en uygun kulüpler: {_liste(adlar)}. "
                "Ayrıntılar ve danışman öğretmen bilgisi Kulüplerim sayfasında.")
    except Exception:
        b.db.rollback()
        return "Kulüplerim sayfasından ilgi testini çözüp sana uygun kulüpleri görebilirsin."


def k_koc(b: Baglam, m: str) -> str:
    return ("Filizyol'un anlaşmalı, okulun için onaylanmış eğitim koçlarını Eğitim Koçları sayfasında görebilirsin. İlgi alanına uygun olanlar üstte işaretli. "
            "Bir koç seç ve görüşme talebi bırak. Talebin Filizyol koordinatörüne gider. Görüşme planlanınca tarih ve saati Takvim'inde görürsün.")


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
        return ("Doğru ya da yanlış cevap yok. \"Olmak istediğin\" kişiye göre değil, şu anki hâline göre cevap ver. Çok düşünme; ilk "
                "aklına gelen genelde en doğrusudur. \"En çok / en az\" sorularında önce sana en çok uyan şıkkı, sonra en az uyanı seç. "
                "Ara verirsen cevapların kaydedilir. Döndüğünde kaldığın yerden devam edersin.")
    d = b.degerlendirme()
    if d["durum"] == "tamamlandi":
        return ("Değerlendirmeni tamamladın. Sonuçların Profilim ve Bölümler sayfalarında. Yaklaşık 3 ay sonra yeni tur açılınca kendindeki "
                "değişimi de görebileceksin. Bazı cevapların tutarsız bulunduysa beklemen gerekmez: yalnızca o bölümü yeniden yanıtlarsın.")
    if d["durum"] == "yok":
        return "Değerlendirmeye henüz başlamadın. Doğru ya da yanlış cevap yok. İçinden geldiği gibi cevap ver; en doğru sonuç böyle çıkar. Ara verirsen cevapların kaydedilir."
    return f"Değerlendirmenin {d['biten']}/{d['toplam']} bölümünü bitirdin. Ara verdiğinde cevapların kaydedilir. Döndüğünde kaldığın sorudan devam edersin."


def k_uyum(b: Baglam, m: str) -> str:
    return ("Her bölümün mezunları belli mesleklerde çalışır ve bu meslekler bazı özellikler ister. Sistem senin özelliklerini tüm bölümlerin "
            "beklentisiyle karşılaştırır ve bölümleri sana yakınlığına göre sıralar: 100 sana en yakın bölüm, 0 en uzak bölüm. "
            "Yani puan, bölümün senin için diğer bölümlere göre nerede durduğunu gösterir. Bu bir başarı tahmini değildir. Karar verirken ilgini, hayallerini ve ailenle konuştuklarını da düşün.")


def k_kim(b: Baglam, m: str) -> str:
    return ("Ben Filiz! 🌱 Bölüm ve meslek seçerken yanındayım. Sonuçlarına, hedef bölümüne ve "
            "görevlerine bakarak sana yol gösteriyorum. \"Sorabileceklerin\" sekmesindeki sorularla başlayabilirsin.")


def k_sistem(b: Baglam, m: str) -> str:
    return ("Filizyol dört adımda ilerler: 1) Değerlendirme — değerlerin, kişiliğin, iş ortamı yetkinliklerin ve ilgi alanların; uyumu 70 ve üzeri bölümlerin varsa son adımda iş türü tercihlerin bu bölümleri kendi aralarında yeniden sıralar. "
            "2) Sonuçlar — Profilim'de güçlü yönlerin, önem verdiğin değerler ve bunların Maarif Modeli'ndeki karşılıkları; Bölümler'de sana en uyumlu bölümler ve nedenleri. "
            "3) Hedef — bir bölüm seçersin; Koçluğum'da kendini bu bölümle karşılaştırırsın ve sana özel bir yol haritası çıkar. 4) Gelişim — haftalık görevler, kulüpler, kütüphanen ve takvimin. "
            "Okulunda açıksa İş Hayatı sayfasında Mülakat Simülasyonu ve Düşünme Atölyesi de var. "
            "Ayrıntılar sol menüdeki Sistem Hakkında sayfasında.")


# [2026-10-19] Maarif Modeli karşılıkları ve iş türü soruları
def k_maarif(b: Baglam, m: str) -> str:
    return ("Okulunda uygulanan Türkiye Yüzyılı Maarif Modeli değerler, eğilimler (merak, sorumluluk, empati gibi) ve beceriler "
            "(iş birliği, karar verme gibi) tanımlar. Filizyol, her özelliğinin bu kavramlardan hangilerine yakın olduğunu gösterir: "
            "Profilim'deki \"Güçlü yönlerinin Maarif Modeli'ndeki karşılıkları\" kartında ve katman sayfalarında. "
            "Bu yorumsal bir ilişkilendirmedir; puanlarını ve bölüm önerilerini etkilemez.")


def k_is_turu(b: Baglam, m: str) -> str:
    return ("İş türü soruları (K5), ilk dört bölümü bitirdiğinde sana en yakın çıkan bölümler (uyumu 70 ve üzeri olanlar; en az 5, "
            "en fazla 20) için açılır. Bu bölümlerde yapılan işlerden hangilerini daha çok seçtiğine göre bölümler yalnızca kendi "
            "aralarında yer değiştirir; bu yüzden ilk 10 listende küçük değişiklikler olabilir. Diğer bölümler etkilenmez; asıl "
            "belirleyici ilk dört bölümdür.")


# [2026-10-13] Yeni özellikler: mülakat simülasyonu, düşünme atölyesi, dil, sonuç e-postası
def k_mulakat_sim(b: Baglam, m: str) -> str:
    return ("Mülakat Simülasyonu'nda seçtiğin bölüm için kısa bir iş görüşmesi canlandırılır: mülakatçı o mesleğe özgü bir durum sorar, "
            "iki aday farklı cevap verir, sen daha iyi cevabı seçersin. Sonra iki cevabın gerekçesini ve o meslekte işin nasıl yapıldığını görürsün. "
            "Alanı bilmen gerekmez; adayların gerekçelerinden mantıkla seçebilirsin. İş Hayatı sayfasında (okulunda açıksa).")


def k_dusunme(b: Baglam, m: str) -> str:
    return ("Düşünme Atölyesi'nde her derste ve meslekte işine yarayacak araçları yaparak öğrenirsin: kök nedeni bulmak, birlikte değişmek ile "
            "neden olmayı ayırmak, algoritmik düşünmek, ikiye bölerek aramak, tercih verisini doğru okumak ve kendini sınayarak öğrenmek. "
            "Her biri 5–7 dakika; önce kendin denersin, sonra aracı öğrenirsin. \"Öğrenmeyi öğren\" deneyinin ikinci ölçümü en erken 12 saat sonra açılır. "
            "İş Hayatı sayfasında (okulunda açıksa).")


def k_dil(b: Baglam, m: str) -> str:
    return ("Filizyol'u Türkçe dışında 12 dilde daha kullanabilirsin. Dilini giriş ekranından ya da Ayarlar'dan seçebilirsin; seçimin hesabına kaydedilir. "
            "PDF raporlar, e-postalar ve KVKK metinlerinin asılları Türkçedir.")


def k_eposta(b: Baglam, m: str) -> str:
    return ("Değerlendirmenin son bölümünü bitirdiğinde hesabındaki e-posta adresine kısa bir sonuç e-postası gider; okulunda öğrenci raporları "
            "açıksa raporun PDF olarak eklenir. Bazı cevapların tutarsız bulunduysa önce o bölümü yeniden yanıtlaman gerekir. E-posta gelmediyse "
            "istenmeyen (spam) klasörüne bak ya da rehber öğretmenine söyle; o yeniden gönderebilir.")


def k_adim(b: Baglam, m: str) -> str:
    adim = b.simdiki_adim()
    if not adim:
        return _hedefsiz(b) if not b.plan else "Yol haritandaki tüm adımları tamamlamışsın, tebrikler! 🎉 Güçlü Yönlerin sekmesindeki adımlarla devam edebilirsin."
    nasil = adim.get("nasil") or []
    ilk = f" Önce şunu yap: {nasil[0]}" if nasil else ""
    return (f"Sıradaki adımın \"{adim['baslik']}\" ({adim.get('alan')}, yaklaşık {adim.get('sure') or 'kısa bir süre'}). "
            f"{adim.get('aciklama') or ''}{ilk} Bitirince Koçluğum → Yol Haritam'da \"Yaptım\"ı işaretle.").replace("  ", " ")


def k_hedef_degis(b: Baglam, m: str) -> str:
    from app.core.koclugu_servisi import hedef_hak_durumu
    h = hedef_hak_durumu(b.o)
    if h["kalan_hak"] > 0:
        return (f"Evet. Hedefini {h['kalan_hak']} kez daha değiştirebilirsin. Bunu Ayarlar sayfasındaki Hedef Bölümüm kartından yaparsın. "
                "Değiştirmeden önce Bölümler → Karşılaştır'da şimdiki hedefini yeni bölümle yan yana koy. Hedefi değiştirince yol haritan yeni hedefe göre baştan hazırlanır.")
    return ("Hedef değiştirme hakların bitmiş. Yine de değiştirmek istiyorsan rehber öğretmenine danış. Okulun sana ek hak verebilir.")


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
    parca.append("Bölüm adına tıkla; açılan pencerede dersleri ve üniversiteleri de görürsün.")
    return " ".join(p for p in parca if p)


def k_motivasyon(b: Baglam, m: str) -> str:
    gorev = next((x for x in b.gorevler() if x.durum != "tamamlandi"), None)
    kucuk = f" Bugün sadece şunu dene: \"{gorev.baslik}\" — 10 dakikanı alır." if gorev else ""
    return ("Motivasyonun inip çıkması çok normal. Kimse her gün aynı enerjide değildir. Büyük hedefi küçük parçalara böl. "
            "Bugün yapabileceğin tek ve küçük bir şey seç. Bitirince kendini tebrik et." + kucuk +
            " Uzun süredir böyle hissediyorsan rehber öğretmeninle konuş.")


def k_kararsiz(b: Baglam, m: str) -> str:
    ilk = b.ilk_bolumler(3)
    ek = f" Sana en uyumlu üç bölüm: {_liste([a for a, _ in ilk])}." if ilk else ""
    return ("Kararsızlık, seçeneklerini ciddiye aldığını gösterir. Şöyle ilerleyebilirsin: 1) İlgini çeken 2-3 bölümü Listem'e ekle, "
            "2) Bölümler → Karşılaştır ile yan yana koy, 3) her bölüm için o mesleği yapan biriyle konuş, mümkünse onu bir gün işinde izle." + ek +
            " Karar verirken uyum yüzdesi kadar ilgini ve hayallerini de düşün.")


def k_rehber(b: Baglam, m: str) -> str:
    return ("Rehber öğretmenine okulundaki rehberlik servisinden ulaşabilirsin. Görüşmeye giderken Profilim'deki güçlü yönlerini ve "
            "hedef bölümünü yanına al; bu, konuşmayı kolaylaştırır. Rehber öğretmenin sonuçlarını ve raporunu sistemden de görebilir.")


def k_kutuphane(b: Baglam, m: str) -> str:
    try:
        r = b.db.execute(text("""SELECT kategori, COUNT(*) FILTER (WHERE durum = 'bitti'), COUNT(*) FILTER (WHERE durum = 'istek')
                                   FROM ogrenci_kutuphane WHERE ogrenci_id = :o GROUP BY kategori"""), {"o": b.o.id}).all()
    except Exception:
        b.db.rollback()
        r = []
    if not r:
        return "Kütüphanen henüz boş. Okuduğun bir kitabı ya da izlediğin bir belgeseli Kütüphanem sayfasına ekleyerek başla. Birkaç cümlelik bir \"ne öğrendim\" notu da çok işe yarar."
    ad = {"kitap": "kitap", "izleme": "film / dizi / belgesel", "kurs": "kurs", "etkinlik": "etkinlik"}
    bitti = [f"{n} {ad.get(k, k)}" for k, n, _ in r if n]
    istek = sum(x[2] for x in r)
    return ("Kütüphanende " + (_liste(bitti) + " tamamlanmış" if bitti else "henüz tamamlanmış kayıt yok")
            + (f". Listende seni bekleyen {istek} kayıt daha var" if istek else "") + ". Gelişimini Kütüphanem sayfasındaki grafiklerden izleyebilirsin.")


# [2026-10-10] İlham Kaynakları → "Filiz'e sor": '"Başlık" (Tip) bana <alan> konusunda ... ' kalıbındaki soruya özel cevap.
_KAYNAK_SORU = re.compile(r'["“](?P<baslik>[^"”]{2,200})["”]\s*\((?P<tip>[^)]{2,40})\)(?:.*?bana\s+(?P<alan>.+?)\s+konusunda)?', re.S)
_TIP_ADI = {"kitap": "kitap", "film / belgesel": "film", "film": "film", "belgesel": "film", "ilham veren kisi": "rol_model",
            "onemli olay": "olay", "yaklasim": "psikolojik_yaklasim", "aktivite": "aktivite"}
_NASIL_BASLA = {
    "kitap": ("Günde 15-20 sayfa oku. Her bölümün sonunda kendine sor: \"{alan} açısından bu bana ne söylüyor?\" Cevabını 1-2 cümleyle not al. "
              "Kitap bitince aklında kalan 3 fikri yaz. Bunları bu hafta nasıl deneyebileceğini de yaz."),
    "film": ("İzlerken {alan} ile ilgili 3 sahneyi not al: karakter ne yaptı, sen olsan ne yapardın? "
             "Bitince 5 dakika ayır. En çok etkilendiğin anı ve ondan çıkardığın dersi yaz."),
    "rol_model": ("Bu kişinin hayatına kısaca bak: hangi zorluklarla karşılaştı, hangi kararları verdi? "
                  "{alan} konusunda ondan öğrenebileceğin bir davranış seç. Bu hafta onu küçük bir şekilde kendin dene."),
    "olay": ("Önce olayın kısa bir özetini oku: ne oldu, kimler hangi kararları verdi? Sonra kendine sor: \"{alan} açısından buradan ne ders "
             "çıkarırım?\" Cevabını 3 madde olarak yaz."),
    "psikolojik_yaklasim": ("Önce yaklaşımın ana fikrini öğren. Sonra bu hafta günlük hayatında bir kez uygula. "
                            "Hafta sonunda {alan} konusunda neyin değiştiğini kısaca not et."),
    "aktivite": ("Bu aktiviteyi bu hafta için küçük bir deneme olarak takvimine ekle. "
                 "Yaptıktan sonra 2-3 cümle yaz: Nasıl hissettin? {alan} konusunda ne fark ettin?"),
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
    parcalar.append(f"Neden işine yarar: bu kaynak sana {alan_k} konusunda yeni bir bakış ve somut örnekler verir.")
    parcalar.append("Nasıl başlarsın: " + _NASIL_BASLA.get(tip or "", _NASIL_BASLA["kitap"]).format(alan=alan_k))
    parcalar.append("İstersen İlham Kaynakları'ndaki \"Kütüphaneme ekle\" ile listene kaydet. Bitirince kısa bir not yaz. Gelişimini Kütüphanem'deki grafiklerde görürsün.")
    return " ".join(parcalar)


def k_yks(b: Baglam, m: str) -> str:
    """[2026-10-10] YKS geri sayımı (Genel Takvim'de resmî tarih yoksa tahmini)."""
    from app.api.motivasyon import haftalik_mesaj, yks_bilgisi
    y = yks_bilgisi(b.db, b.o.sinif)
    if not y:
        return "Profilinde sınıf bilgin yok, bu yüzden hangi YKS'ye gireceğini hesaplayamadım. Ayarlar'dan sınıfını eklersen geri sayımı gösterebilirim."
    tah = "" if y["resmi"] else " (ÖSYM tarihi henüz açıklamadı, bu bir tahmin)"
    return (f"{y['ad']}'ye {y['gun']} gün, yani yaklaşık {y['hafta']} hafta var{tah}. {haftalik_mesaj(y)} "
            "Ana sayfadaki sayaçtan her gün takip edebilirsin.")


def k_net(b: Baglam, m: str) -> str:
    """[2026-10-10] Net takibi özeti: son denemeler ve hedef programa göre en büyük açık."""
    from app.api.net_takibi import kiyas_hesapla
    from sqlalchemy import text as _t
    sayi = b.db.execute(_t("SELECT count(*) FROM ogrenci_denemeleri WHERE ogrenci_id = :o"), {"o": b.o.id}).scalar() or 0
    if not sayi:
        return ("Henüz deneme kaydın yok. Çözdüğün denemenin doğru ve yanlış sayılarını Net Takibi sayfasına gir. "
                "Netlerini grafikte izleyebilirsin. Ben de onları hedef üniversitene geçen yıl yerleşen öğrenciyle karşılaştırırım.")
    k = kiyas_hesapla(b.db, b.o)
    h = k.get("hedef")
    if not h or k.get("toplam_ben") is None or k.get("toplam_hedef") is None:
        return (f"{sayi} deneme kaydın var. Net Takibi → Hedefe Göre'den hedef üniversiteni seç. O zaman netlerini, "
                "bu programa geçen yıl yerleşen son öğrenciyle ders ders karşılaştırırım.")
    acik = round(k["toplam_hedef"] - k["toplam_ben"], 2)
    ilk = (k.get("en_buyuk_acik") or [None])[0]
    if acik <= 0:
        return (f"Son denemelerinin ortalaması {k['toplam_ben']} net. Bu, {k.get('yil')} yılında {h['universite']} {h['program']} programına "
                "yerleşen son öğrencinin netinden yüksek 👏 Bu tempoyu korumak için düzenli deneme çözmeye devam et.")
    return (f"Son denemelerinin ortalaması {k['toplam_ben']} net. {k.get('yil')} yılında {h['universite']} programına yerleşen son "
            f"öğrenci {k['toplam_hedef']} netle girdi. Aradaki fark {acik} net."
            + (f" En büyük açık {ilk['ad']} dersinde ({ilk['fark']})." if ilk else "")
            + " Net Takibi → Konu Takibi'nde bu dersin bitmemiş konularından başla."
              " Unutma: bu netler tek bir kişiye ait. Yerleşmede diploma notu da etkili. Bu netleri yol gösteren bir hedef olarak düşün.")


KONULAR = [
    (("netlerim", "netim ", "netimi", "netlerimi", "net artir", "denemelerim", "deneme sonuc", "net takib", "kac net", "hedef net"), k_net),
    (("yks'ye kac", "yksye kac", "yks kac", "yks ne zaman", "yks'ye ne kadar", "sinava kac", "sinava ne kadar", "yks geri sayim"), k_yks),
    (("tesekkur", "sagol", "sag ol", "eyvallah", "cok iyi", "super"), k_tesekkur),
    (("mulakat simul", "iki aday", "mulakat oyun"), k_mulakat_sim),
    (("dusunme atolye", "kok neden", "korelasyon", "algoritmik", "ikiye bol", "ogrenmeyi ogren", "ikinci olcum"), k_dusunme),
    (("dil degistir", "baska dil", "ingilizce kullan", "dilini degistir", "hangi dillerde", "dil sec"), k_dil),
    (("sonuc e-posta", "sonuc eposta", "sonuc maili", "e-posta gelmedi", "eposta gelmedi", "mail gelmedi", "raporum mail", "raporum e-posta"), k_eposta),
    (("maarif",), k_maarif),
    (("is turu soru", "is turu tercih", "k5 nedir", "k5 ne"), k_is_turu),
    (("kimsin", "sen kim", "nesin", "yapay zeka"), k_kim),
    (("sistem nasil", "nasil calisiyor", "filizyol nedir", "filizyol ne ise yarar", "sistem ne ise yarar", "bu site ne ise yarar"), k_sistem),
    (("motivasyon", "motive", "motivem", "isteksiz", "bikkin", "yoruldum", "canim istemiyor", "hevesim", "istegim yok"), k_motivasyon),
    (("kararsiz", "karar veremiyorum", "emin degilim", "secemiyorum", "secmeli miyim", "secsem mi", "tercih etmeli",
      "bilmiyorum", "kafam karisik", "kafam cok karisik", "kafam", "karar veremedim", "emin olamiyorum", "hangisini secsem", "hangisi iyi",
      "hangisi daha iyi", "ne secsem", "ne okusam", "hicbir sey bilmiyorum", "aklim karisik"), k_kararsiz),
    (("sinav", "kaygi", "stres", "verimli", "ders calis", "nasil calis", "yks", "tyt", "ayt"), k_sinav),
    (("degistir", "degisebilir", "baska bolum sec"), k_hedef_degis),
    (("hakkinda bilgi", "ne okutuyor", "bolum hakkinda", "bolumu anlat", "mezunlar"), k_bolum_bilgi),
    (("siradaki adim", "yol harita", "sonraki adim", "adimim"), k_adim),
    (("bu hafta", "hafta", "gorev", "ne yapay", "nereden basla", "simdi ne", "odaklan"), k_hafta),
    (("kutuphanem", "kutuphane"), k_kutuphane),
    (("kitap", "film", "belgesel", "dizi", "kaynak", "okuyabil", "izleyebil"), k_kaynak),
    (("kulup", "kulub", "topluluk", "ilgi testi"), k_kulup),
    (("rehber ogretmen", "rehberlik servis", "psikolojik danisman"), k_rehber),
    (("koc", "kocla gorus", "koc ile gorus", "gorusme talebi", "randevu"), k_koc),   # [2026-10-31] "iş görüşmesi" koçluğa gitmesin
    (("takvim", "tarih", "ne zaman", "etkinlik"), k_takvim),
    (("guclu", "iyi oldugum", "yetenek", "avantaj"), k_guclu),
    (("gelistir", "gelisim", "zayif", "eksik", "zorlan"), k_gelisim),
    (("uyum yuzde", "yuzde", "% ", "uyum puan", "uyum ne demek"), k_uyum),   # [2026-10-31] "ne demek" tek başına sözlük/bilgi sorusu
    (("hedef", "bana uygun mu", "dogru bolum", "uygun mu"), k_hedef),
    (("hangi bolum", "bolum oner", "uygun bolum", "meslek", "bolumler"), k_bolum_oner),
    (("test", "degerlendirme", "katman", "soru", "cevaplamali", "neredeyim"), k_test),
    (("merhaba", "selam", "gunaydin", "iyi aksam", "hey", "naber", "nasilsin"), k_selam),
]


def otomatik_yanit_kaynakli(db: Session, ogrenci: Ogrenci, metin: str, moduller: set[str] | None = None):
    """[2026-10-31] Katmanlı rehber. Döner: filiz_anlama.Cevap(yanit, kaynak, secenekler).
    kaynak: 'sabit' (gizlilik) | 'icerik' (sistem içeriği) | 'rehber' (öğrencinin kendi verisi) | 'netlestirme'
    ("Şunu mu demek istedin?") | 'bilinmiyor'.
    Sıra: gizlilik → ilham kaynağı sorusu → anlama (karşılaştırma, meslek yolu, bilgi sorusu) → kişisel konular →
    netleştirme / içerik araması → bilinmiyor. Soru önce düzeltilir (konuşma dili, kısaltmalar)."""
    from app.core.filiz_gizlilik import ogrenci_dizini, ogrenci_hiyerarsi_yaniti
    from app.core import filiz_bilgi as fb
    from app.core.filiz_anlama import Cevap, onceden_anla, sonradan_netlestir
    ret = ogrenci_hiyerarsi_yaniti(metin, ogrenci_dizini(db, ogrenci), ogrenci.ad_soyad)
    if ret:
        return Cevap(ret, "sabit")
    if moduller is None:
        from app.core.paketler import okul_modulleri
        moduller = set(okul_modulleri(db, ogrenci.okul_id))
    t = fb.duzelt(metin)
    b = Baglam(db, ogrenci)
    if _KAYNAK_SORU.search(metin or ""):
        try:
            c = k_kaynak_soru(b, metin)
            if c:
                return Cevap(c, "rehber")
        except Exception:
            db.rollback()
    try:
        c = onceden_anla(db, metin, moduller)
        if c:
            return c
    except Exception:
        db.rollback()
    for anahtarlar, f in KONULAR:
        if any(a in t for a in anahtarlar):
            try:
                return Cevap(f(b, metin), "rehber")
            except Exception:
                db.rollback()
                break
    try:
        c = sonradan_netlestir(db, metin, moduller)
        if c:
            return c
    except Exception:
        db.rollback()
    ornek = random.sample(ORNEK_SORULAR, 3)
    return Cevap("Bunu tam anlayamadım. 🌱 Sonuçların, hedefin, görevlerin ve gelişiminle ilgili sorularda; bölümler, meslekler ve "
                 "sözlükteki kavramlar hakkında da yardım edebilirim. Şunlardan birini deneyebilirsin:", "bilinmiyor", ornek)


def otomatik_yanit(db: Session, ogrenci: Ogrenci, metin: str) -> str:
    return otomatik_yanit_kaynakli(db, ogrenci, metin).yanit


def katman_tahmini(db: Session, metin: str, moduller: set[str] | None):
    """[2026-10-31] Öğrenci olmadan yönlendirme (ölçüm testleri için): otomatik_yanit_kaynakli ile aynı sıra, kişisel
    konularda konu fonksiyonu çağrılmaz. Döner: (kaynak, Cevap | konu_adı | None)."""
    from app.core import filiz_bilgi as fb
    from app.core.filiz_anlama import onceden_anla, sonradan_netlestir
    c = onceden_anla(db, metin, moduller)
    if c:
        return c.kaynak, c
    t = fb.duzelt(metin)
    for anahtarlar, f in KONULAR:
        if any(a in t for a in anahtarlar):
            return "rehber", f.__name__
    c = sonradan_netlestir(db, metin, moduller)
    if c:
        return c.kaynak, c
    return "bilinmiyor", None
