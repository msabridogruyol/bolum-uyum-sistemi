# -*- coding: utf-8 -*-
"""
[2026-10-10] Koçluk motoru — yol haritasını "yapılacaklar listesi" olmaktan çıkarıp geri bildirim alan,
öğrenciye uyum sağlayan ve gelişimi ölçen bir döngüye çevirir.

1. Alan türü: değer (K1) / kişilik (K2) / beceri (K3) / ilgi (K4). Değerler "geliştirilecek eksik" DEĞİL,
   bilinçli karar konusu olarak sunulur; beceri ve kişilik alanlarında gelişim beklenir.
2. "Sana ne katar?": her adım için adım türü + alan türünden üretilen somut kazanım cümlesi.
3. Geri bildirim: adım tamamlanırken ne yaptım / ne öğrendim / fayda (1-5) / zorluk.
4. Uyarlama: son geri bildirime ve hareketsizliğe göre sıradaki adıma kısa öneri.
5. Tekrar ölçüm: bir alanda her 3 adımda bir, öğrencinin ilk değerlendirmede cevapladığı AYNI sorulardan
   en fazla 5'i yeniden sorulur; aynı sorular üzerinden önce/sonra puanı karşılaştırılır (eğilim göstergesi).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

from sqlalchemy.orm import Session

from app.models import Degisken, Ogrenci, OgrenciAlanOlcumu, OgrenciCevap, OgrenciGelisimAdimDurumu, SjtSecenekDegiskenAgirlik, Soru, SoruSecenegi

OLCUM_ADIM_ARALIGI = 3
OLCUM_SORU_SAYISI = 5

ALAN_TURU = {"D": "deger", "P": "aliskanlik", "I": "beceri", "A": "egilim"}
ALAN_TURU_BILGI = {
    "deger": ("Değer · farkındalık",
              "Bu bir değer; değiştirmen gerekmiyor. Amaç, bölümün bu yönünün sana uyup uymadığını bilerek karar vermek."),
    "aliskanlik": ("Kişilik · esneyebilir",
                   "Kişilik özellikleri yavaş değişir ama küçük, düzenli alışkanlıklarla esneyebilir."),
    "beceri": ("Beceri · çalıştıkça gelişir",
               "Bu bir beceri; çalıştıkça gelişir. Her 3 adımda bir kısa tekrar ölçümle farkı görebilirsin."),
    "egilim": ("İlgi · keşfet",
               "Bu bir ilgi alanı. Amaç zorla sevmek değil; deneyip gerçekten ilgini çekip çekmediğini görmek."),
}
OLCULEN_TURLER = {"aliskanlik", "beceri", "egilim"}

TUR_KAZANIM = {
    "arastirma": "Tahmin yerine gerçek bilgiyle karar verirsin.",
    "gorusme": "Alanı içeriden yaşayan birinden, hiçbir tanıtımda yazmayan şeyleri öğrenirsin.",
    "deneyim": "Kendini gerçek bir durumda denersin; \"bana uyar mı?\" sorusunun cevabını yaşayarak bulursun.",
    "proje": "Elinde gösterebileceğin somut bir iş olur.",
    "aliskanlik": "Küçük ama düzenli bir alışkanlık kazanırsın; sınav döneminde de işine yarar.",
    "okuma": "Konuya farklı bir bakış ve sohbetlerde kullanabileceğin fikirler kazanırsın.",
    "kurs": "Kalıcı bir beceri ve özgeçmişine yazabileceğin bir belge kazanırsın.",
    "yansitma": "Kendini daha net tanırsın; kararlarının arkasındaki \"neden\"i söyleyebilirsin.",
}
ALAN_KAZANIM = {
    "deger": "{alan} senin için ne kadar önemli, netleşir; bölüm kararını bilerek verirsin.",
    "aliskanlik": "{alan} tarafında esneklik kazanırsın; {bolum} ortamına alışman kolaylaşır.",
    "beceri": "{alan} becerin güçlenir; {bolum} okurken ve iş hayatında doğrudan işine yarar.",
    "egilim": "{alan} alanını gerçekten sevip sevmediğini keşfedersin.",
}
GUCLU_KAZANIM = "Güçlü yanını görünür kılarsın; kendini anlatırken öne çıkarabileceğin somut bir örneğin olur."


def alan_turu(degisken_kod: str) -> str | None:
    return ALAN_TURU.get((degisken_kod or "")[:1])


def _kucuk(m: str) -> str:
    return (m or "").replace("İ", "i").replace("I", "ı").lower()


def kazanim(adim: dict, bolum: str) -> str:
    tur = alan_turu(adim["degisken_kod"])
    ilk = TUR_KAZANIM.get(adim.get("tur"), "")
    if "-U-" in adim["kod"]:
        return f"{ilk} {GUCLU_KAZANIM}".strip()
    alan = ALAN_KAZANIM.get(tur, "").format(alan=adim["degisken_adi"], bolum=bolum)
    alan = alan[:1].upper() + alan[1:] if alan else ""
    return f"{ilk} {alan}".strip()


# ----------------------------------------------------------------------------- geri bildirim ve uyarlama
def _kayitlar(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int) -> list[OgrenciGelisimAdimDurumu]:
    return db.query(OgrenciGelisimAdimDurumu).filter(
        OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
        OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef_bolum_id).all()


def _gb(k: OgrenciGelisimAdimDurumu) -> dict | None:
    if not any([k.ne_yaptim, k.ne_ogrendim, k.fayda, k.zorluk]):
        return None
    return {"ne_yaptim": k.ne_yaptim, "ne_ogrendim": k.ne_ogrendim, "fayda": k.fayda, "zorluk": k.zorluk}


def uyarlama_metni(kayitlar: list[OgrenciGelisimAdimDurumu]) -> str | None:
    biten = sorted([k for k in kayitlar if k.durum == "tamamlandi" and k.guncelleme_zamani],
                   key=lambda k: k.guncelleme_zamani, reverse=True)
    if not biten:
        return None
    son = biten[0]
    zaman = son.guncelleme_zamani if son.guncelleme_zamani.tzinfo else son.guncelleme_zamani.replace(tzinfo=timezone.utc)
    if datetime.now(timezone.utc) - zaman > timedelta(days=14):
        return ("İki haftadır yeni adım yok, sorun değil. Bugün sadece 10 dakika ayır ve bu adımın yalnızca ilk maddesini yap. "
                "Küçük başlamak, hiç başlamamaktan iyidir.")
    if son.zorluk == "zor" or (son.fayda is not None and son.fayda <= 2):
        neden = "zor buldun" if son.zorluk == "zor" else "pek faydalı bulmadın"
        return (f"Son adımı {neden}. Bu adımı küçült: önce yalnızca ilk maddeyi yap, 15-20 dakika yeter. "
                "Takılırsan Filiz'e sor ya da rehber öğretmeninle konuş.")
    if son.zorluk == "kolay" and (son.fayda or 0) >= 4:
        return "Son adımı kolay ve faydalı buldun 👏 İstersen bu hafta bir adım daha ekleyebilirsin."
    return None


def geri_bildirim_kaydet(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int, kod: str, istek) -> None:
    k = db.query(OgrenciGelisimAdimDurumu).filter(
        OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id, OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef_bolum_id,
        OgrenciGelisimAdimDurumu.adim_kodu == kod).first()
    if k is None:
        return
    if istek.ne_yaptim is not None:
        k.ne_yaptim = istek.ne_yaptim.strip()[:600] or None
    if istek.ne_ogrendim is not None:
        k.ne_ogrendim = istek.ne_ogrendim.strip()[:600] or None
    if istek.fayda is not None:
        k.fayda = max(1, min(5, int(istek.fayda)))
    if istek.zorluk in ("kolay", "uygun", "zor"):
        k.zorluk = istek.zorluk
    db.flush()


# ----------------------------------------------------------------------------- tekrar ölçüm
def _olcumler(db: Session, ogrenci: Ogrenci) -> dict[int, list[OgrenciAlanOlcumu]]:
    d: dict[int, list] = {}
    for o in (db.query(OgrenciAlanOlcumu).filter(OgrenciAlanOlcumu.ogrenci_id == ogrenci.id)
              .order_by(OgrenciAlanOlcumu.olusturulma_zamani).all()):
        d.setdefault(o.degisken_id, []).append(o)
    return d


def _olcum_ozeti(liste: list[OgrenciAlanOlcumu], ters: bool) -> dict | None:
    if not liste:
        return None
    ilk, son = liste[0], liste[-1]
    fark = float(son.yeni_puan) - float(ilk.onceki_puan)
    return {"onceki": float(ilk.onceki_puan), "yeni": float(son.yeni_puan),
            "gelisim": round(-fark if ters else fark, 1), "ters_yonlu": ters,
            "zaman": son.olusturulma_zamani.isoformat() if son.olusturulma_zamani else None, "olcum_sayisi": len(liste)}


def plani_zenginlestir(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int, plan: dict) -> dict:
    """gelisim_plani_olustur çıktısına alan türü, kazanım, geri bildirim, uyarlama ve ölçüm durumunu ekler."""
    try:
        kayitlar = _kayitlar(db, ogrenci, hedef_bolum_id)
        gb = {k.adim_kodu: _gb(k) for k in kayitlar}
        bolum = plan.get("hedef_bolum_adi") or "bölüm"

        def adim_ekle(a: dict):
            a["kazanim"] = kazanim(a, bolum)
            a["alan_turu"] = alan_turu(a["degisken_kod"])
            a["geri_bildirim"] = gb.get(a["kod"])

        for asama in plan.get("asamalar", []):
            for a in asama["adimlar"]:
                adim_ekle(a)
        for g in plan.get("guclu_yonler", []):
            for a in g["adimlar"]:
                adim_ekle(a)

        olcumler = _olcumler(db, ogrenci)
        ters = {d.id: bool(d.ters_yonlu) for d in db.query(Degisken).filter(
            Degisken.id.in_([o["degisken_id"] for o in plan.get("odak_alanlari", [])] or [-1])).all()}
        tum = [x for a in plan.get("asamalar", []) for x in a["adimlar"]]
        for o in plan.get("odak_alanlari", []):
            tur = alan_turu(o["degisken_kod"])
            o["alan_turu"] = tur
            o["alan_turu_etiket"], o["alan_turu_aciklama"] = ALAN_TURU_BILGI.get(tur, (None, None))
            if tur not in OLCULEN_TURLER:
                o["olcum"] = None
                continue
            biten = sum(1 for x in tum if x["degisken_kod"] == o["degisken_kod"] and x["durum"] == "tamamlandi")
            liste = olcumler.get(o["degisken_id"], [])
            gereken = OLCUM_ADIM_ARALIGI * (len(liste) + 1)
            o["olcum"] = {"tamamlanan_adim": biten, "gereken": gereken, "acik": biten >= gereken,
                          "son": _olcum_ozeti(liste, ters.get(o["degisken_id"], False))}

        sira = plan.get("siradaki_adim")
        if sira:
            sira["uyarlama"] = uyarlama_metni(kayitlar)
    except Exception:
        db.rollback()
    return plan


def _baz_cevaplar(db: Session, ogrenci: Ogrenci, degisken_id: int):
    """Öğrencinin son tamamlanan turunda bu değişkene puan veren sorulara verdiği cevaplar (en etkili 5 soru)."""
    from app.core.katman_servisi import son_tur_getir
    tur = son_tur_getir(db, ogrenci)
    agirlik = (db.query(SoruSecenegi.soru_id, SjtSecenekDegiskenAgirlik.agirlik)
               .join(SjtSecenekDegiskenAgirlik, SjtSecenekDegiskenAgirlik.secenek_id == SoruSecenegi.id)
               .filter(SjtSecenekDegiskenAgirlik.degisken_id == degisken_id).all())
    etki: dict[int, float] = {}
    for sid, w in agirlik:
        etki[sid] = max(etki.get(sid, 0.0), abs(float(w)))
    for s in db.query(Soru.id).filter((Soru.degisken_id == degisken_id) | (Soru.b_ucu_degisken_id == degisken_id)).all():
        etki[s.id] = max(etki.get(s.id, 0.0), 1.0)
    if not etki:
        return tur, []
    cevaplar = (db.query(OgrenciCevap).filter(OgrenciCevap.ogrenci_id == ogrenci.id, OgrenciCevap.tur_id == tur.id,
                                             OgrenciCevap.soru_id.in_(list(etki))).all())
    cevaplar.sort(key=lambda c: etki.get(c.soru_id, 0), reverse=True)
    return tur, cevaplar[:OLCUM_SORU_SAYISI]


def _yedek_sorular(db: Session, degisken_id: int) -> list[int]:
    """Cevap kaydı olmayan (ör. örnek veriyle oluşturulmuş) hesaplar için: bu değişkene en çok etki eden aktif sorular."""
    agirlik = (db.query(SoruSecenegi.soru_id, SjtSecenekDegiskenAgirlik.agirlik)
               .join(SjtSecenekDegiskenAgirlik, SjtSecenekDegiskenAgirlik.secenek_id == SoruSecenegi.id)
               .join(Soru, Soru.id == SoruSecenegi.soru_id)
               .filter(SjtSecenekDegiskenAgirlik.degisken_id == degisken_id, Soru.aktif_mi.is_(True)).all())
    etki: dict[int, float] = {}
    for sid, w in agirlik:
        etki[sid] = max(etki.get(sid, 0.0), abs(float(w)))
    return sorted(etki, key=lambda k: etki[k], reverse=True)[:OLCUM_SORU_SAYISI]


def _kayitli_puan(db: Session, ogrenci: Ogrenci, tur_id: int, degisken_id: int) -> float | None:
    from app.models import OgrenciDegiskenSkoru
    k = (db.query(OgrenciDegiskenSkoru).filter(OgrenciDegiskenSkoru.ogrenci_id == ogrenci.id,
                                               OgrenciDegiskenSkoru.tur_id == tur_id,
                                               OgrenciDegiskenSkoru.degisken_id == degisken_id)
         .order_by(OgrenciDegiskenSkoru.olusturulma_zamani.desc()).first())
    return round(float(k.puan), 1) if k else None


def olcum_sorulari(db: Session, ogrenci: Ogrenci, degisken_id: int) -> dict:
    d = db.get(Degisken, degisken_id)
    _, cevaplar = _baz_cevaplar(db, ogrenci, degisken_id)
    soru_idler = [c.soru_id for c in cevaplar] or _yedek_sorular(db, degisken_id)
    sorular = []
    for sid in soru_idler:
        s = db.get(Soru, sid)
        sec = db.query(SoruSecenegi).filter(SoruSecenegi.soru_id == s.id).order_by(SoruSecenegi.secenek_sirasi).all()
        sorular.append({"id": s.id, "metin": s.soru_metni, "tip": s.soru_tipi, "cevap_bicimi": s.cevap_bicimi or "tek",
                        "secenekler": [{"id": x.id, "metin": x.secenek_metni} for x in sec]})
    return {"degisken_id": degisken_id, "degisken_adi": d.ad if d else "", "sorular": sorular}


def _ortalama(db: Session, sorular: dict, cevaplar: list, degisken_id: int) -> float | None:
    from app.core.katman_servisi import cevaplari_puanla
    p = cevaplari_puanla(db, sorular, cevaplar).get(degisken_id, [])
    return round(sum(p) / len(p), 1) if p else None


def olcum_kaydet(db: Session, ogrenci: Ogrenci, degisken_id: int, hedef_bolum_id: int | None, yeni: list[dict]) -> dict:
    from app.core.katman_servisi import IsKuraliHatasi
    tur, baz = _baz_cevaplar(db, ogrenci, degisken_id)
    izinli = {c.soru_id for c in baz} or set(_yedek_sorular(db, degisken_id))
    yeni = [y for y in yeni if y.get("soru_id") in izinli]
    if not izinli or len(yeni) < len(izinli):
        raise IsKuraliHatasi("Lütfen tüm soruları cevapla.")
    sorular = {s.id: s for s in db.query(Soru).filter(Soru.id.in_(list(izinli))).all()}
    for y in yeni:
        gecerli = {s.id for s in db.query(SoruSecenegi.id).filter(SoruSecenegi.soru_id == y["soru_id"]).all()}
        if y.get("secenek_id") not in gecerli or (y.get("en_az_secenek_id") not in (None, *gecerli)):
            raise IsKuraliHatasi("Geçersiz cevap.")
        if (sorular[y["soru_id"]].cevap_bicimi or "tek") == "encok_enaz" and (
                not y.get("en_az_secenek_id") or y["en_az_secenek_id"] == y["secenek_id"]):
            raise IsKuraliHatasi("Her soruda hem 'en çok' hem 'en az' uyan şıkkı seç.")
    # Önce: aynı sorulara ilk değerlendirmedeki cevaplar; cevap kaydı yoksa kayıtlı değişken puanı (yaklaşık)
    onceki = _ortalama(db, sorular, baz, degisken_id) if baz else _kayitli_puan(db, ogrenci, tur.id, degisken_id)
    simdi = _ortalama(db, sorular, [SimpleNamespace(soru_id=y["soru_id"], secenek_id=y["secenek_id"],
                                                     en_az_secenek_id=y.get("en_az_secenek_id")) for y in yeni], degisken_id)
    if onceki is None or simdi is None:
        raise IsKuraliHatasi("Bu alan için ölçüm yapılamadı.")
    db.add(OgrenciAlanOlcumu(ogrenci_id=ogrenci.id, degisken_id=degisken_id, hedef_bolum_id=hedef_bolum_id,
                             onceki_puan=onceki, yeni_puan=simdi, soru_sayisi=len(yeni), cevaplar={"cevaplar": yeni}))
    db.flush()
    d = db.get(Degisken, degisken_id)
    ters = bool(d.ters_yonlu) if d else False
    gelisim = round((onceki - simdi) if ters else (simdi - onceki), 1)
    if gelisim >= 5:
        yorum = "Aynı sorulara bu kez daha güçlü cevaplar verdin. Attığın adımlar karşılık buluyor 🌱"
    elif gelisim <= -5:
        yorum = ("Bu kez puanın biraz düştü. Bu normal; bazen bir konuyu tanıdıkça kendimizi daha gerçekçi değerlendiririz. "
                 "Adımlara devam et, bir sonraki ölçümde tekrar bakalım.")
    else:
        yorum = "Belirgin bir değişim yok. Kişilik ve beceriler yavaş değişir; düzenli adımlarla fark zamanla görünür."
    return {"onceki": onceki, "yeni": simdi, "gelisim": gelisim, "ters_yonlu": ters, "yorum": yorum}
