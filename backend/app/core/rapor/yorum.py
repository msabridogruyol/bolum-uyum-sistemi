"""
[2026-10-12] Rapor yorumları: sayıların yanında "ne anlama geliyor, ne yapmalı, neden kaçınmalı" bölümü.

Kural tabanlıdır (yapay zekâ kullanılmaz, öğrenci verisi dışarı gitmez) ve yalnızca raporda zaten bulunan
verilere dayanır; yeni sayı üretmez, tahmin yapmaz. Aynı çıktı PDF raporlarında ve rapor ekranlarında kullanılır.

Kitleler:
  ogrenci   — öğrencinin kendisi ("sen")
  veli      — veli ("siz", "çocuğunuz")
  ogretmen  — sınıf öğretmeni ("siz"); kişilik ayrıntısı ve duygusal hassasiyet bilgisi İÇERMEZ
  rehber    — rehber öğretmen / okul yetkilisi ("siz"); güven puanı ve görüşme gündemi dahil
Okul düzeyi: okul_yorumu() — yönetici özeti, öncelikli işler (kim / ne zaman), yapılmaması gerekenler.

Özellik bazlı metinler: app/data/rapor_yorumlari.json (31 özellik × yüksek / düşük × kitle).
Çerçeve: K1 değerler ve K4 ilgiler "geliştirilecek eksik" değil, karar verirken dikkate alınacak tercihtir;
K2 kişilik düşük puanı bir çalışma tarzıdır; P4 (duygusal hassasiyet) yüksekse güçlü yön sayılmaz, destek önerilir.
"""
from __future__ import annotations

import json
import pathlib
from functools import lru_cache

from app.core.seviye import GUCLU_ESIK, ORTA_ESIK

_DOSYA = pathlib.Path(__file__).resolve().parents[2] / "data" / "rapor_yorumlari.json"
KITLELER = ("ogrenci", "veli", "ogretmen", "rehber")
HASSASIYET = "P4"           # yüksek puan = stres / kaygıyı daha yoğun hissetme
HASSASIYET_ESIK = 62        # bu ve üstü: destek önerisi (etiket bandıyla aynı: "Güçlü")
UYUM_YUKSEK, UYUM_DUSUK = 60.0, 40.0


@lru_cache(maxsize=1)
def _icerik() -> dict:
    try:
        return json.loads(_DOSYA.read_text("utf-8")).get("degiskenler", {})
    except (OSError, ValueError):
        return {}


def _metin(kod: str | None, yon: str, alan: str) -> str | None:
    return ((_icerik().get(kod or "") or {}).get(yon) or {}).get(alan)


def ozellik_anlami(kod: str | None, yon: str, alan: str = "anlam") -> str | None:
    """Tek bir özelliğin öğrenciye yönelik anlamı / önerisi (PDF'te ve ekranda güçlü ve düşük yönlerin altında)."""
    return _metin(kod, yon, alan)


def _say(x) -> str:
    """Türkçe sayı: 17.0 → '17', 29.92 → '29,92'."""
    if x is None:
        return "—"
    x = round(float(x), 2)
    return (f"{x:.0f}" if x == int(x) else f"{x:.2f}".rstrip("0")).replace(".", ",")


def _bos(baslik: str) -> dict:
    return {"baslik": baslik, "ozet": [], "yap": [], "kacin": [], "gorusme": [], "guclu": [], "destek": [], "notlar": []}


# ----------------------------------------------------------------------------- öğrenci
# Düşük kutupta etiketleyici okunabilecek adlar nötr bir adla gösterilir (ör. "Sorumluluk ve disiplin" → çalışma alışkanlığı).
DUSUK_AD = {"P1": "Sosyal ortam tercihi", "P2": "Uzlaşma ve iş birliği tarzı", "P3": "Planlı çalışma alışkanlığı",
            "P8": "Liderlik rolü tercihi", "I4": "Etik karar verme"}
# Veli ve sınıf öğretmeni raporlarında gelişim alanı olarak gösterilmez (yalnızca öğrenci ve rehber öğretmen görür)
YALNIZ_REHBER = {"I4"}


def _ozellikler(v: dict) -> list[dict]:
    return [o for k in v.get("katmanlar") or [] for o in k.get("ozellikler") or []]


def _hassasiyet(v: dict) -> float | None:
    return next((o["puan"] for o in _ozellikler(v) if o.get("kod") == HASSASIYET), None)


def _kod(o: dict) -> str:
    return str(o.get("kod") or "")


def _guclu_yonler(v: dict, kitle: str) -> list[dict]:
    """Değerler (K1) hariç güçlü yönler; değerler ayrı cümlede 'önem verdiğin değerler' olarak verilir."""
    sirali = sorted((o for o in _ozellikler(v) if _kod(o) != HASSASIYET and not _kod(o).startswith("D")), key=lambda o: -o["puan"])
    if kitle == "ogretmen":   # sınıf öğretmeni: kişilik (K2) ayrıntısı verilmez
        sirali = [o for o in sirali if not _kod(o).startswith("P")]
    return [o for o in sirali if o["puan"] >= GUCLU_ESIK][:3]


def _degerler(v: dict) -> list[dict]:
    return sorted((o for o in _ozellikler(v) if _kod(o).startswith("D") and o["puan"] >= GUCLU_ESIK), key=lambda o: -o["puan"])[:2]


def _gelisim_yonleri(v: dict, kitle: str) -> list[dict]:
    sirali = sorted((o for o in _ozellikler(v) if _kod(o) != HASSASIYET), key=lambda o: o["puan"])
    if kitle == "ogretmen":
        sirali = [o for o in sirali if not _kod(o).startswith("P")]
    if kitle in ("veli", "ogretmen"):
        sirali = [o for o in sirali if _kod(o) not in YALNIZ_REHBER]
    # Önce geliştirilebilir yetkinlikler ve çalışma tarzı (K3, K2), sonra ilgi ve değerler (dikkate alınacak tercih)
    oncelik = {"I": 0, "P": 1, "A": 2, "D": 3}
    dusukler = [o for o in sirali if o["puan"] < ORTA_ESIK]
    dusukler.sort(key=lambda o: (oncelik.get(_kod(o)[:1], 9), o["puan"]))
    return dusukler[:3]


def _hedef_durumu(v: dict) -> tuple[str, dict | None]:
    """'yok' | 'uyumlu' | 'kismen' | 'farkli'"""
    h = v.get("hedef")
    if not h:
        return "yok", None
    uyum = h.get("uyum")
    ilk10 = any(b.get("ad", "").lower() == (h.get("ad") or "").lower() for b in v.get("bolumler") or [])
    if ilk10 or (uyum is not None and uyum >= UYUM_YUKSEK):
        return "uyumlu", h
    if uyum is not None and uyum < UYUM_DUSUK:
        return "farkli", h
    return "kismen", h


def _net_ozeti(v: dict) -> dict:
    n = v.get("netler") or {}
    oturumlar = [o for o in n.get("oturumlar") or [] if (o.get("sayi") or 0) >= 1]
    kiyas = n.get("kiyas") or {}
    satirlar = [s for s in kiyas.get("satirlar") or [] if s.get("fark") is not None]
    en_acik = min(satirlar, key=lambda s: s["fark"]) if satirlar else None
    if en_acik is not None and en_acik["fark"] >= 0:
        en_acik = None
    dersler = [d for d in n.get("dersler") or [] if d.get("soru") and d.get("ort3") is not None]
    en_dusuk = min(dersler, key=lambda d: d["ort3"] / d["soru"]) if dersler else None
    return {"oturumlar": oturumlar, "en_acik": en_acik, "en_dusuk": en_dusuk,
            "dusus": [o for o in oturumlar if (o.get("sayi") or 0) >= 2 and (o.get("degisim") or 0) < 0],
            "artis": [o for o in oturumlar if (o.get("sayi") or 0) >= 2 and (o.get("degisim") or 0) > 0]}


def ogrenci_yorumu(v: dict, kitle: str = "ogrenci") -> dict:
    """Öğrenci raporu verisinden (rapor/veri.ogrenci_raporu_verisi) kitleye uygun yorum ve öneriler."""
    kitle = kitle if kitle in KITLELER else "ogrenci"
    sen = kitle == "ogrenci"
    basliklar = {"ogrenci": "Sonuçların ne anlatıyor, şimdi ne yapmalısın?",
                 "veli": "Sonuçlar ne anlatıyor, evde nasıl destek olabilirsiniz?",
                 "ogretmen": "Sınıfta nasıl destek olabilirsiniz?",
                 "rehber": "Değerlendirme ve öneriler"}
    y = _bos(basliklar[kitle])
    tur = v.get("tur") or {}
    durum = v.get("durum")

    if durum != "tamamlandi":
        y["ozet"].append("Değerlendirmen henüz tamamlanmadı; yorumlar tüm bölümler bitince hazırlanır." if sen else
                         "Değerlendirme henüz tamamlanmadı; yorumlar tüm bölümler bitince hazırlanır.")
        y["yap"].append(("Kalan bölümleri sakin bir zamanda, tek oturumda bitir." if durum == "devam" else
                         "Sana özel açılan alan sorularını (K5) tamamla; önerilerin bunlarla netleşir.") if sen else
                        "Öğrencinin kalan bölümleri tamamlaması için uygun bir zaman planlanmalı.")
        return y

    guclu = _guclu_yonler(v, kitle)
    degerler = _degerler(v)
    gelisim = _gelisim_yonleri(v, kitle)
    bolumler = v.get("bolumler") or []
    alanlar = list(dict.fromkeys(b.get("alan") for b in bolumler[:5] if b.get("alan")))[:2]
    hd, h = _hedef_durumu(v)
    net = _net_ozeti(v)
    hassas = _hassasiyet(v)
    hassas_yuksek = hassas is not None and hassas >= HASSASIYET_ESIK
    akt = v.get("aktivite") or {}
    guven_dusuk = tur.get("gecerli") is False

    # --- Özet: durum → analiz → sonuç. Listeler " · " ile ayrılır (adların içinde virgül / "ve" geçebilir; ekran çevirisi
    # her adı ayrı çevirir).
    if guven_dusuk:
        y["ozet"].append({"ogrenci": "Bazı yanıtların birbiriyle tam tutarlı görünmüyor; ilgili bölümü sakin bir zamanda yeniden yanıtlarsan sonuçların seni daha doğru yansıtır.",
                          "veli": "Bu değerlendirmenin bazı bölümleri yeniden yanıtlanacak; aşağıdaki sonuçlar şimdilik ön bilgi niteliğindedir.",
                          "ogretmen": "Bu değerlendirmenin bazı bölümleri yeniden yanıtlanacak; aşağıdaki sonuçlar şimdilik ön bilgi niteliğindedir.",
                          "rehber": "Bu değerlendirmenin güven puanı eşiğin altında; sonuçlar temkinli yorumlanmalı."}[kitle])
    adlar = " · ".join(g["ad"] for g in guclu)
    if adlar:
        y["ozet"].append({"ogrenci": f"Değerlendirmene göre öne çıkan yönlerin: {adlar}.",
                          "veli": f"Değerlendirmeye göre çocuğunuzun öne çıkan yönleri: {adlar}.",
                          "ogretmen": f"Öğrencinin öne çıkan yönleri: {adlar}.",
                          "rehber": f"Öne çıkan yönler: {adlar}."}[kitle])
    dadlar = " · ".join(g["ad"] for g in degerler)
    if dadlar and kitle != "ogretmen":
        y["ozet"].append({"ogrenci": f"Bir işte en çok önem verdiğin değerler: {dadlar}.",
                          "veli": f"Bir işte en çok önem verdiği değerler: {dadlar}.",
                          "rehber": f"Önem verdiği değerler: {dadlar}."}[kitle])
    if bolumler:
        b1 = bolumler[0]["ad"]
        alan_m = " · ".join(alanlar) or "—"
        y["ozet"].append({"ogrenci": f"Bölüm uyumunda en öne çıkan alanlar: {alan_m}. En uyumlu bölümün: {b1}.",
                          "veli": f"Bölüm uyumunda en öne çıkan alanlar: {alan_m}. En uyumlu görünen bölüm: {b1}.",
                          "ogretmen": f"Bölüm uyumunda en öne çıkan alanlar: {alan_m}.",
                          "rehber": f"Bölüm uyumunda en öne çıkan alanlar: {alan_m}. İlk öneri: {b1}."}[kitle])
    if hd == "uyumlu":
        y["ozet"].append(f"Seçtiğin hedef ({h['ad']}) profilinle uyumlu; şimdi önemli olan bu hedef için düzenli çalışmak." if sen else
                         f"Seçilen hedef ({h['ad']}) profille uyumlu; şimdi önemli olan bu hedef için düzenli çalışmak.")
    elif hd == "farkli":
        y["ozet"].append(f"Seçtiğin hedef ({h['ad']}) ile profilin arasında belirgin farklar var. Bu, hedefin yanlış olduğu anlamına gelmez; "
                         "farkların nereden geldiğini rehber öğretmeninle konuşman karar vermeni kolaylaştırır." if sen else
                         f"Seçilen hedef ({h['ad']}) ile profil arasında belirgin farklar var. Bu, hedefin yanlış olduğu anlamına gelmez; "
                         "farkların öğrenciyle birlikte, yargılamadan konuşulması önerilir.")
    elif hd == "kismen":
        y["ozet"].append(f"Seçtiğin hedef ({h['ad']}) profilinle kısmen örtüşüyor; güçlü yanlarını bu hedefte nasıl kullanabileceğini keşfet." if sen else
                         f"Seçilen hedef ({h['ad']}) profille kısmen örtüşüyor.")
    else:
        y["ozet"].append("Henüz bir hedef bölüm seçmedin; önerilerinden birkaçını yakından tanıyarak başlayabilirsin." if sen else
                         "Henüz bir hedef bölüm seçilmedi.")
    for o in net["artis"][:1]:
        y["ozet"].append(f"Denemelerde yükseliştesin ({o['oturum']}: ilk {_say(o['ilk'])}, son {_say(o['son'])} net); bu düzeni koru." if sen else
                         f"Denemelerde yükseliş var ({o['oturum']}: ilk {_say(o['ilk'])}, son {_say(o['son'])} net).")
    for o in net["dusus"][:1]:
        y["ozet"].append(f"Son {o['oturum']} denemesinde ilk denemeye göre düşüş var ({_say(o['ilk'])} → {_say(o['son'])} net); "
                         "tek denemeye göre değil, gidişata göre değerlendir." if sen else
                         f"Son {o['oturum']} denemesinde ilk denemeye göre düşüş var ({_say(o['ilk'])} → {_say(o['son'])} net); "
                         "tek denemeye göre değil, gidişata göre değerlendirilmeli.")

    # --- Güçlü yönleri kullanma
    alan_g = {"ogrenci": "ogrenci", "veli": "veli", "ogretmen": "ogretmen", "rehber": "ogretmen"}[kitle]
    for g in guclu[:3]:
        m = _metin(g.get("kod"), "yuksek", alan_g)
        if m:
            y["guclu"].append({"ad": g["ad"], "metin": m})

    # --- Gelişim / destek (düşük kutupta nötr adlar)
    alan_d = {"ogrenci": "yap", "veli": "veli", "ogretmen": "ogretmen", "rehber": "ogretmen"}[kitle]
    for g in gelisim:
        m = _metin(g.get("kod"), "dusuk", alan_d)
        if m:
            y["destek"].append({"ad": DUSUK_AD.get(_kod(g), g["ad"]), "metin": m})
    if hassas_yuksek and kitle != "ogretmen":
        m = _metin(HASSASIYET, "yuksek", {"ogrenci": "ogrenci", "veli": "veli", "rehber": "rehber"}[kitle])
        if m:
            y["destek"].append({"ad": "Stresle baş etme", "metin": m})

    # --- Yapılacaklar (öncelik sırasıyla)
    if guven_dusuk and kitle in ("ogrenci", "rehber"):
        y["yap"].append("Tutarsız görünen bölümü sakin bir zamanda yeniden yanıtla." if sen else
                        "Öğrenciyle görüşüp güven puanı düşük çıkan bölümü yeniden çözmesini sağlayın (öğrenci detayı → Değerlendirme).")
    if hd == "yok" and bolumler:
        ilk3 = " · ".join(b["ad"] for b in bolumler[:3])
        y["yap"].append({"ogrenci": f"İlk üç önerini ({ilk3}) ders programı ve örnek meslekleriyle incele; ilgini en çok çekeni deneme hedefi olarak belirleyebilirsin (istediğin zaman değiştirebilirsin).",
                         "veli": f"Önerilen ilk üç bölümü ({ilk3}) çocuğunuzla birlikte inceleyin; acele etmeden bir deneme hedefi belirlemesine yardımcı olun.",
                         "ogretmen": "Öğrencinin bir hedef bölüm belirlemesi için rehber öğretmenle görüşmesini teşvik edin.",
                         "rehber": f"Hedef seçimi için kısa bir görüşme planlayın; ilk üç öneri: {ilk3}."}[kitle])
    elif hd == "farkli" and bolumler:
        b1 = bolumler[0]["ad"]
        y["yap"].append({"ogrenci": f"«{h['ad']}» ile «{b1}» için birer sayfalık artı / eksi listesi hazırla, rehber öğretmeninle birlikte değerlendir.",
                         "veli": f"Çocuğunuza {h['ad']} hedefini neden seçtiğini sorun ve gerekçelerini dinleyin; {b1} gibi önerileri de birlikte tanıyın.",
                         "ogretmen": "Hedef ile profil arasındaki farklar için öğrenciyi rehber öğretmene yönlendirin.",
                         "rehber": f"Hedef ({h['ad']}) ile ilk öneri ({b1}) arasındaki farkları konuşun; hedefin nasıl oluştuğunu (kendi ilgisi, aile ya da çevre etkisi) açık uçlu sorularla ele alın."}[kitle])
    if h and h.get("siradaki") and kitle in ("ogrenci", "veli"):
        y["yap"].append(f"Yol haritandaki sıradaki adımı ({h['siradaki']}) bu hafta tamamla." if sen else
                        f"Yol haritasındaki sıradaki adımı ({h['siradaki']}) sorun ve tamamladığında takdir edin.")
    if net["en_acik"] is not None:
        s = net["en_acik"]
        y["yap"].append({"ogrenci": f"Hedef programla en büyük farkın {s['ad']} dersinde ({_say(abs(s['fark']))} net); haftalık planına bu dersin konularını öncelikli yaz.",
                         "veli": f"Hedefe göre en çok desteğe ihtiyaç duyulan ders {s['ad']}; çalışma planında bu derse düzenli zaman ayrılmasını destekleyin.",
                         "ogretmen": f"Hedef programa göre en büyük fark {s['ad']} dersinde; öğrencinin bilgisiyle ders öğretmeniyle paylaşılabilir.",
                         "rehber": f"Hedef programa göre en büyük net farkı {s['ad']} dersinde ({_say(abs(s['fark']))} net); çalışma planında önceliklendirilmeli."}[kitle])
    elif net["en_dusuk"] is not None:
        d = net["en_dusuk"]
        y["yap"].append(f"{d['oturum']} {d['ad']} dersinde netlerin soru sayısına göre en düşük; bu dersin eksik konularından başla." if sen else
                        f"{d['oturum']} {d['ad']} dersi, soru sayısına göre netin en düşük olduğu ders; çalışma planında öne alınmalı.")
    elif not net["oturumlar"] and kitle in ("ogrenci", "rehber"):
        y["yap"].append("Deneme netlerini Net Takibi'ne girersen gidişatını birlikte izleyebiliriz." if sen else
                        "Öğrencinin deneme sonuçlarını Net Takibi'ne girmesi, gidişatın izlenmesi için önerilir.")
    toplam, son4 = akt.get("gorev_toplam") or 0, akt.get("son4_hafta") or 0
    if toplam and son4 < 2 and kitle in ("ogrenci", "rehber", "veli"):
        y["yap"].append({"ogrenci": "Haftalık görevlerini düzenli yap; her hafta en az birini bitirmek bile fark yaratır.",
                         "veli": "Haftalık görevlerini sorun; bitirdiklerini fark edip takdir edin.",
                         "rehber": f"Son 4 haftada tamamlanan haftalık görev: {son4}; düzenli katılım için kısa bir hatırlatma yapılabilir."}[kitle])
    y["yap"] = list(dict.fromkeys(y["yap"]))[:6]

    # --- Kaçınılacaklar
    if kitle == "ogrenci":
        y["kacin"].append("Bölümünü yalnızca uyum yüzdesine bakarak seçme; yüzde bir başarı tahmini değil, profilinin bölümle örtüşmesidir.")
        if hd == "farkli":
            y["kacin"].append("Uyum düşük çıktı diye hedefinden hemen vazgeçme; önce farkları anlamaya çalış.")
        if net["dusus"]:
            y["kacin"].append("Tek bir kötü denemeye göre kendini yargılama; gidişata bak.")
        elif net["oturumlar"]:
            y["kacin"].append("Yanlışlarını incelemeden bir sonraki denemeye geçme; aynı hatayı tekrar yapmamak en kolay kazanılan nettir.")
        for g in gelisim[:2]:
            m = _metin(g.get("kod"), "dusuk", "kacin")
            if m:
                y["kacin"].append(m)
    elif kitle == "veli":
        y["kacin"] += ["Sonuçları bir başarı ya da zekâ ölçüsü gibi yorumlamayın; doğru ya da yanlış cevabı olmayan bir eğilim değerlendirmesidir.",
                       "Çocuğunuzu kardeşleri ya da arkadaşlarıyla karşılaştırmayın.",
                       "Bölüm kararını onun yerine vermeyin; seçenekleri birlikte tanıyın, kararı birlikte verin."]
        if net["dusus"]:
            y["kacin"].append("Tek bir düşük deneme sonucuna sert tepki vermeyin; yorgunluk, uyku ve stres durumunu birlikte konuşun.")
    elif kitle == "ogretmen":
        y["kacin"] += ["Öğrencinin sonuçlarını sınıfta ya da diğer öğrencilerin yanında paylaşmayın.",
                       "Önerilen bölümleri kesin yönlendirme gibi sunmayın; yönlendirme rehber öğretmenle birlikte yapılır."]
    else:
        y["kacin"] += ["Uyum yüzdesini öğrenciyi etiketlemek ya da sıralamak için kullanmayın.",
                       "Görüşmede hedefi değiştirmesi için baskı kurmayın; kararın sahibi öğrenci ve ailesidir."]
        if guven_dusuk:
            y["kacin"].append("Güven puanı düşük değerlendirmeye dayanarak yönlendirme yapmayın.")
    y["kacin"] = list(dict.fromkeys(y["kacin"]))[:4]

    # --- Görüşmede konuşulacaklar
    if kitle == "ogrenci":
        y["gorusme"] = ["Sonuçlar seni ne kadar anlatıyor? Katılmadığın bir nokta varsa rehber öğretmenine söyle."]
        if hd == "farkli":
            y["gorusme"].append(f"{h['ad']} hedefini seçme nedenlerin ve profilinle arasındaki farklar.")
        if net["en_acik"] is not None or net["en_dusuk"] is not None:
            y["gorusme"].append("Deneme sonuçlarına göre hangi derse öncelik vermen gerektiği.")
        if hassas_yuksek:
            y["gorusme"].append("Yoğun dönemlerde stresle nasıl baş edebileceğin.")
        y["gorusme"].append("Önerilen bölümlerden merak ettiklerini tanımak için atabileceğin ilk adım (kampüs gezisi, meslek sahibiyle görüşme).")
    elif kitle == "veli":
        y["gorusme"] = ["Sonuçlar, çocuğumun okuldaki gözlemlerinizle örtüşüyor mu?"]
        if hd == "farkli":
            y["gorusme"].append("Seçtiği hedef ile profili arasındaki farkları nasıl değerlendirmeliyiz?")
        if h:
            y["gorusme"].append("Hedef bölüm için hangi derslere ve puan türüne odaklanmalı?")
        else:
            y["gorusme"].append("Önerilen bölümleri tanımak için okulda hangi etkinlikler var?")
        if y["destek"]:
            y["gorusme"].append("Gelişime açık alanlarda okul içinde hangi etkinliklere katılabilir?")
    elif kitle == "rehber":
        y["gorusme"] = ["Öğrencinin sonuçlara katılıp katılmadığı; katılmadığı noktalar."]
        if hd == "yok":
            y["gorusme"].append("Hedef bölüm seçimi: ilk üç öneriden hangisi ilgisini çekiyor?")
        elif hd == "farkli":
            y["gorusme"].append("Hedefin nasıl oluştuğu (kendi ilgisi, aile ya da çevre etkisi) ve profille farkları.")
        if net["oturumlar"]:
            y["gorusme"].append("Deneme gidişatı ve öncelikli ders için haftalık plan.")
        if hassas_yuksek:
            y["gorusme"].append("Sınav dönemi stresi ve baş etme yolları.")
        if guven_dusuk:
            y["gorusme"].append("Güven puanı düşük çıkan bölümün yeniden yanıtlanması.")
    y["gorusme"] = y["gorusme"][:5]

    y["notlar"].append("Bu yorumlar değerlendirme sonuçlarından otomatik hazırlanan bir özettir, yönlendirme kararı değildir; "
                       "son karar öğrenci, ailesi ve rehber öğretmenin birlikte değerlendirmesiyle verilir.")
    return y


# ----------------------------------------------------------------------------- okul
def _oran(a, b) -> float | None:
    return (100.0 * a / b) if a is not None and b else None


def okul_yorumu(ov: dict, moduller: set[str] | None = None) -> dict:
    """Okul / sınıf / şube raporu verisinden (rapor/veri.okul_raporu_verisi) yönetici özeti ve öncelikli işler.
    'isler': [{metin, kim, ne_zaman, oncelik}] — kim: Rehber öğretmen / Sınıf öğretmenleri / Okul idaresi.
    Ortak özelliklerde kişilik (K2) ve duygusal hassasiyet kullanılmaz (sınıf düzeyinde bireysel veriye yaklaşır)."""
    oz = ov.get("ozet") or {}
    ks = ov.get("kapsam") or {}
    moduller = moduller if moduller is not None else set(oz.get("moduller") or [])
    y = _bos("Değerlendirme ve öncelikli işler")
    y["isler"] = []
    toplam, tamam = oz.get("toplam") or 0, oz.get("tamamlayan") or 0
    if not toplam:
        y["ozet"].append("Bu kapsamda henüz öğrenci yok.")
        return y
    t_oran = _oran(tamam, toplam)
    giris_yok = next((d.get("sayi") for d in oz.get("durumlar") or [] if d.get("kod") == "giris_yok"), 0) or 0
    hedef = oz.get("hedef_secen") or 0
    h_oran = _oran(hedef, tamam) if tamam else None
    siniflar = [s for s in oz.get("siniflar") or [] if not s.get("gizli") and s.get("ogrenci") and s.get("tamamlayan") is not None]
    subeler = [s for s in oz.get("subeler") or [] if not s.get("gizli") and s.get("ogrenci") and s.get("tamamlayan") is not None
               and s.get("sube")]
    on_iki = next((s for s in siniflar if s.get("sinif") == "12. Sınıf"), None)
    if ks.get("sinif") and ks.get("sinif") != "12. Sınıf":
        on_iki = None
    dusuk_sube = sorted([s for s in subeler if (_oran(s["tamamlayan"], s["ogrenci"]) or 0) < 50],
                        key=lambda s: _oran(s["tamamlayan"], s["ogrenci"]) or 0)[:3] if not ks.get("sube") else []
    erken = (ks.get("sinif") or "") in ("9. Sınıf", "10. Sınıf")

    def ekle(metin, kim, ne_zaman, oncelik):
        y["isler"].append({"metin": metin, "kim": kim, "ne_zaman": ne_zaman, "oncelik": oncelik})

    # Durum → analiz
    y["ozet"].append(f"Değerlendirmeyi tamamlayan öğrenci: {tamam} / {toplam} (%{_say(round(t_oran))}).")
    if t_oran < 50:
        y["ozet"].append("Tamamlama oranı yarının altında; bölüm önerileri ve toplu yorumlar bu kapsamdaki öğrencilerin küçük bir kısmını yansıtıyor.")
    elif t_oran < 80:
        y["ozet"].append("Tamamlama oranı orta düzeyde; kalan öğrencilerin tamamlaması bu kapsamdaki sonuçları daha güvenilir kılar.")
    else:
        y["ozet"].append("Tamamlama oranı yüksek; toplu sonuçlar bu kapsamdaki öğrencilerin büyük çoğunluğunu yansıtıyor.")
    if on_iki and on_iki["ogrenci"]:
        o12 = _oran(on_iki["tamamlayan"], on_iki["ogrenci"])
        if o12 is not None and o12 < 60:
            y["ozet"].append(f"12. sınıflarda tamamlama %{_say(round(o12))}; tercih dönemi yaklaştığı için öncelikli konu bu.")
            ekle(f"12. sınıfların değerlendirmeyi tamamlaması için sınıf saatinde bir oturum planlayın ({on_iki['ogrenci'] - on_iki['tamamlayan']} öğrenci kaldı).",
                 "Rehber öğretmen + 12. sınıf öğretmenleri", "Bu hafta", 1)
    if giris_yok:
        ekle(f"Sisteme hiç giriş yapmamış {giris_yok} öğrenciye giriş bilgilerini yeniden ulaştırın (Öğrenciler → Giriş listesi).",
             "Sınıf öğretmenleri", "Bu hafta", 1)
    for s in dusuk_sube:
        ekle(f"{s.get('etiket') or (s.get('sinif', '') + ' ' + s['sube']).strip()} şubesinde tamamlama %{_say(round(_oran(s['tamamlayan'], s['ogrenci'])))}; "
             "rehberlik saatinde birlikte tamamlama oturumu yapın.", "Sınıf öğretmeni + rehber öğretmen", "Bu ay", 2)
    if h_oran is not None and tamam >= 5 and h_oran < 50:
        if erken:
            y["ozet"].append(f"Hedef bölüm seçen öğrenci sayısı {hedef} (tamamlayanların %{_say(round(h_oran))}); bu sınıf düzeyinde beklenen bir durum, öncelik keşif etkinlikleri.")
            ekle("Öğrencilerin önerilen bölümleri tanıması için meslek tanıtımı ya da bölüm keşfi etkinliği planlayın.",
                 "Rehber öğretmen", "Bu ay", 2)
        else:
            y["ozet"].append(f"Hedef bölüm seçen öğrenci sayısı {hedef} (tamamlayanların %{_say(round(h_oran))}); kişisel yol haritası ve koçluk adımları hedef seçildiğinde oluşur.")
            ekle("Hedef seçmemiş öğrencilerle kısa bir hedef belirleme atölyesi yapın: ilk üç önerilerini birlikte incelesinler.",
                 "Rehber öğretmen", "Bu ay", 2)
    net = ov.get("net") or {}
    if "net_takibi" in moduller and net.get("giren") is not None:
        n_oran = _oran(net.get("giren"), toplam)
        if n_oran is not None and n_oran < 30:
            y["ozet"].append("Bu kapsamda Net Takibi'ni kullanan öğrenci henüz yok." if not net.get("giren") else
                             f"Net Takibi'ni {net.get('giren')} öğrenci kullanıyor; deneme gidişatı ve hedef karşılaştırması bu öğrencilerle sınırlı.")
            ekle("Okul denemelerini sisteme yükleyin ya da öğrencilerden deneme netlerini girmelerini isteyin; hedef programla karşılaştırma bu verilerle yapılır.",
                 "Okul idaresi + ders öğretmenleri", "Dönem içinde", 3)
    if ov.get("gecersiz"):
        ekle(f"Güven puanı düşük çıkan {ov['gecersiz']} değerlendirme var; bu öğrencilerle görüşüp ilgili bölümü yeniden yanıtlamalarını sağlayın.",
             "Rehber öğretmen", "Bu hafta", 1)
    alanlar = ov.get("alanlar") or []
    ana_alan = next((a["alan"] for a in alanlar if a.get("alan") and a["alan"] != "Diğer" and a.get("sayi") is not None), None)
    if ana_alan:
        y["ozet"].append(f"Öğrencilerin en yüksek uyum gösterdiği alan: {ana_alan}.")
        ekle(f"{ana_alan} alanında bir meslek tanıtım günü, mezun söyleşisi ya da kampüs gezisi planlayın.",
             "Rehber öğretmen + okul idaresi", "Dönem içinde", 3)
    # Ortak özellikler → grup etkinliği önerisi (kişilik ve duygusal hassasiyet hariç)
    uygun = lambda g: g.get("kod") and not str(g["kod"]).startswith("P")
    for g in [g for g in ov.get("ortak_gelisim") or [] if uygun(g)][:2]:
        m = _metin(g.get("kod"), "dusuk", "grup")
        if m:
            y["destek"].append({"ad": DUSUK_AD.get(g["kod"], g["ad"]), "metin": m})
    for g in [g for g in ov.get("ortak_guclu") or [] if uygun(g)][:2]:
        m = _metin(g.get("kod"), "yuksek", "grup")
        if m:
            y["guclu"].append({"ad": g["ad"], "metin": m})
    y["isler"].sort(key=lambda i: i["oncelik"])
    y["isler"] = y["isler"][:7]
    y["yap"] = [i["metin"] for i in y["isler"]]
    y["kacin"] = ["Öğrenci sonuçlarını sınıfta, panoda ya da veli gruplarında paylaşmayın; sonuçlar kişiseldir.",
                  "Uyum yüzdelerini öğrencileri sıralamak ya da etiketlemek için kullanmayın.",
                  "Bölüm önerilerini kesin yönlendirme gibi sunmayın; karar öğrenci ve ailesiyle birlikte verilir.",
                  "Deneme ortalamalarını şubeleri yarıştırmak için kullanmayın; destek planlamak için kullanın."]
    y["notlar"].append("Öneriler bu rapordaki sayılardan otomatik çıkarılır; okulun koşullarına göre rehberlik servisi uyarlamalıdır.")
    return y
