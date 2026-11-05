# -*- coding: utf-8 -*-
"""
[2026-11-05] Gelişim listesi — haftalık 3 görevin yerine (kullanıcı kararı).

Kullanıcı: "Haftalık 3 görev lise öğrencisi için fazla; süreli değil, geliştirilmesi gereken alanlarda yapılması
gerekenler listesi ve tamamlanma durumları olsun." Kararlar:
  * Liste hedef bölümün gelişim (odak) alanlarına göre gruplanır: her alanda adımlar, durumları, tamamlanma yüzdesi.
    Süre, hafta, seri YOK. Adımların sırası yol haritasındaki sıradır (başlangıç → pratik → kalıcı alışkanlık).
  * Bölüm keşfi ve 3 soruluk öz değerlendirme İSTEĞE BAĞLI maddelerdir; zorunluluk ve süre yok.
  * Filiz'in büyümesi tamamlanan adıma bağlıdır; eski haftalık görevler de sayılır, kimsenin seviyesi düşmez.
  * Değerlendirme bitmediyse / K5 bekliyorsa / hedef yoksa listenin başında tek bir "önce bunu yap" maddesi çıkar.
  * [2026-11-05] Kullanıcı: "Kişi ordaki istediği geliştirmeye bakarak yaptım yapmadım ve neler yaptım açıklamalarını
    girebilmeli, tarih girebilmeli: şu tarihte şunu yaptım." Her madde: durum (yapmadım / yapıyorum / yaptım) + istediği
    kadar kayıt (tarih + açıklama). "Yaptım" için en az bir kayıt gerekir (rehber öğretmen ne yapıldığını görebilsin).
Eski ogrenci_haftalik_gorev tablosu silinmez (geçmiş kayıt; eski öz değerlendirme cevapları "geçmiş"te görünür).
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.katman_servisi import IsKuraliHatasi
from app.models import Bolum, Katman, Ogrenci, OgrenciGelisimAdimDurumu, OgrenciKatmanOturumu

OZ_DEGERLENDIRME_SORULARI = [
    ("iyi", "Son zamanlarda neyi iyi yaptın?"),
    ("zor", "Nerede zorlandın?"),
    ("hedef", "Sıradaki küçük hedefin ne?"),
]

# Filiz'in büyüme seviyeleri: (gereken puan, ad, ikon)
SEVIYELER = [(0, "Tohum", "🌰"), (30, "Filiz", "🌱"), (80, "Fidan", "🌿"), (160, "Genç Ağaç", "🌳"),
             (280, "Çiçek Açan Ağaç", "🌸"), (450, "Ulu Çınar", "🏆")]
PUAN_ADIM, PUAN_KATMAN, PUAN_ISTEGE_BAGLI = 10, 15, 5
# Eski (haftalık) sistemin puanı: seviye hiçbir zaman eskisinin altına düşmez
_ESKI_PUAN_GOREV, _ESKI_PUAN_ADIM = 10, 5

DURGUN_GUN = 14   # erken uyarı: hedefi ve açık adımı olan öğrenci bu kadar gündür adım tamamlamadıysa


# ----------------------------------------------------------------------------- yardımcılar
def _turkce_baslik(metin: str) -> str:
    from app.core.koclugu_servisi import turkce_baslik
    return turkce_baslik(metin)


def _son_tur(db: Session, ogrenci: Ogrenci):
    from app.models import OgrenciDegerlendirmeTuru
    return (db.query(OgrenciDegerlendirmeTuru).filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id)
            .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())


def on_adim(db: Session, ogrenci: Ogrenci) -> dict | None:
    """Gelişim listesi açılmadan önce yapılması gereken tek adım (değerlendirme / K5 / hedef seçimi)."""
    from app.core.dal_servisi import bekleyen_dal_var_mi
    from app.core.katman_adlari import katman_adi
    from app.core.koclugu_servisi import aktif_hedef_getir
    tur = _son_tur(db, ogrenci)
    if tur is None or tur.durum != "tamamlandi":
        katmanlar = db.query(Katman).filter(Katman.kosullu_mu.is_(False)).order_by(Katman.sira).all()
        biten = set()
        if tur is not None:
            biten = {o.katman_id for o in db.query(OgrenciKatmanOturumu).filter(
                OgrenciKatmanOturumu.ogrenci_id == ogrenci.id, OgrenciKatmanOturumu.tur_id == tur.id,
                OgrenciKatmanOturumu.durum == "tamamlandi").all()}
        sonraki = next((k for k in katmanlar if k.id not in biten), None)
        if sonraki is not None:
            kalan = len([k for k in katmanlar if k.id not in biten])
            return {"tur": "katman", "baslik": f"{katman_adi(sonraki.kod, sonraki.ad)} bölümünü tamamla",
                    "aciklama": f"Bölüm önerilerin ve gelişim listen için {kalan} bölüm kaldı. Samimi cevap ver; doğru ya da yanlış cevap yok.",
                    "link": "/katmanlar"}
        return None
    if bekleyen_dal_var_mi(db, ogrenci, tur):
        return {"tur": "k5", "baslik": "İş türü (K5) sorularını tamamla",
                "aciklama": "Bölüm önerilerin ve gelişim listen bu adımdan sonra hazırlanır.", "link": "/katmanlar"}
    if aktif_hedef_getir(db, ogrenci) is None:
        return {"tur": "hedef", "baslik": "Önerilen bölümlerinden birini hedef seç",
                "aciklama": "Bölümler › Sana uygun listesine bak. Birini hedef seçince, o bölüm için geliştirmen gereken alanlar "
                            "ve her alanda yapılacaklar burada listelenir.", "link": "/bolumler"}
    return None


def _plan(db: Session, ogrenci: Ogrenci):
    """(hedef, plan) — plan hesaplanamazsa (ör. bölüm profili yok) (hedef, None)."""
    from app.core.koclugu_servisi import aktif_hedef_getir, gap_analizi_hesapla, gelisim_plani_olustur
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        return None, None
    tur = _son_tur(db, ogrenci)
    if tur is None or tur.durum != "tamamlandi":
        return hedef, None
    # Kayıt noktası: plan hesaplanamazsa yalnızca bu deneme geri alınır (aynı işlemdeki yeni kayıt / durum yazımları korunur)
    try:
        with db.begin_nested():
            return hedef, gelisim_plani_olustur(db, ogrenci, hedef.bolum_id, gap_analizi_hesapla(db, ogrenci, tur, hedef.bolum_id))
    except Exception:
        return hedef, None


def _adim_kisa(a: dict, asama_ad: dict, kayitlar: dict) -> dict:
    durum = a.get("durum")
    return {"kod": a["kod"], "baslik": a["baslik"], "aciklama": a.get("aciklama"), "olcut": a.get("olcut"), "sure": a.get("sure"),
            "durum": durum if durum in ("devam_ediyor", "tamamlandi") else "bekliyor",
            "asama": a.get("asama"), "asama_ad": asama_ad.get(a.get("asama")), "kazanim": a.get("kazanim"),
            "tur_etiket": a.get("tur_etiket"), "kayitlar": kayitlar.get(a["kod"], [])}


def adim_kayitlari(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int) -> dict[str, list[dict]]:
    """{adim_kodu: [{id, tarih, aciklama}]} (yeniden eskiye). Eski sistemde adımı tamamlarken yazılan "ne yaptım"
    notu da tarihli bir kayıt olarak gösterilir (silinemez)."""
    out: dict[str, list[dict]] = {}
    for r in db.execute(text("""SELECT id, adim_kodu, tarih, aciklama FROM ogrenci_gelisim_kayitlari
                                 WHERE ogrenci_id = :o AND ref_bolum_id = :b AND tur = 'adim_kaydi'
                                 ORDER BY tarih DESC, id DESC"""), {"o": ogrenci.id, "b": hedef_bolum_id}).all():
        out.setdefault(r.adim_kodu, []).append({"id": r.id, "tarih": r.tarih.isoformat(), "aciklama": r.aciklama})
    for k in db.query(OgrenciGelisimAdimDurumu).filter(OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
                                                      OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef_bolum_id,
                                                      OgrenciGelisimAdimDurumu.ne_yaptim.isnot(None)).all():
        metin = k.ne_yaptim + (f" — Öğrendiğim: {k.ne_ogrendim}" if k.ne_ogrendim else "")
        out.setdefault(k.adim_kodu, []).append({"id": None, "tarih": (k.guncelleme_zamani.date().isoformat() if k.guncelleme_zamani else None),
                                                "aciklama": metin, "eski": True})
    return out


def _adim_dogrula(db: Session, ogrenci: Ogrenci, kod: str) -> int:
    """Adım öğrencinin GÜNCEL hedefinin planında mı? Hedef bölüm id'sini döner."""
    hedef, plan = _plan(db, ogrenci)
    if hedef is None or plan is None:
        raise IsKuraliHatasi("Önce bir hedef bölüm seçmelisin.")
    kodlar = {a["kod"] for s in plan.get("asamalar", []) for a in s["adimlar"]} | {
        a["kod"] for g in plan.get("guclu_yonler", []) for a in g["adimlar"]}
    if kod not in kodlar:
        raise IsKuraliHatasi("Bu madde hedef bölümünün listesinde yok.")
    return hedef.bolum_id


def kayit_ekle(db: Session, ogrenci: Ogrenci, kod: str, tarih: date, aciklama: str) -> dict:
    bugun = datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).date()
    if tarih > bugun:
        raise IsKuraliHatasi("İleri bir tarih giremezsin; yaptığın günün tarihini seç.")
    if tarih < bugun - timedelta(days=400):
        raise IsKuraliHatasi("Tarih bir yıldan daha eski olamaz.")
    metin = " ".join((aciklama or "").split())
    if len(metin) < 10:
        raise IsKuraliHatasi("Ne yaptığını en az bir cümleyle yaz (en az 10 karakter).")
    bid = _adim_dogrula(db, ogrenci, kod)
    r = db.execute(text("""INSERT INTO ogrenci_gelisim_kayitlari (ogrenci_id, tur, ref_bolum_id, adim_kodu, tarih, aciklama)
                           VALUES (:o, 'adim_kaydi', :b, :k, :t, :a) RETURNING id"""),
                   {"o": ogrenci.id, "b": bid, "k": kod, "t": tarih, "a": metin[:1000]}).scalar()
    # İlk kayıt: madde "yapıyorum"a geçer (yaptım ise değişmez)
    from app.core.koclugu_servisi import adim_durumu_guncelle
    mevcut = db.query(OgrenciGelisimAdimDurumu).filter(OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
                                                       OgrenciGelisimAdimDurumu.hedef_bolum_id == bid,
                                                       OgrenciGelisimAdimDurumu.adim_kodu == kod).first()
    if mevcut is None or mevcut.durum not in ("devam_ediyor", "tamamlandi"):
        adim_durumu_guncelle(db, ogrenci, bid, kod, "devam_ediyor")
    db.flush()
    return {"id": r}


def kayit_sil(db: Session, ogrenci: Ogrenci, kayit_id: int) -> None:
    n = db.execute(text("DELETE FROM ogrenci_gelisim_kayitlari WHERE id = :i AND ogrenci_id = :o AND tur = 'adim_kaydi'"),
                   {"i": kayit_id, "o": ogrenci.id}).rowcount
    if not n:
        raise IsKuraliHatasi("Kayıt bulunamadı.")


def durum_degistir(db: Session, ogrenci: Ogrenci, kod: str, durum: str) -> None:
    """durum: bekliyor (yapmadım) | devam_ediyor (yapıyorum) | tamamlandi (yaptım — en az bir kayıt gerekir)."""
    if durum not in ("bekliyor", "devam_ediyor", "tamamlandi"):
        raise IsKuraliHatasi("Geçersiz durum.")
    bid = _adim_dogrula(db, ogrenci, kod)
    if durum == "tamamlandi" and not adim_kayitlari(db, ogrenci, bid).get(kod):
        raise IsKuraliHatasi("“Yaptım” demeden önce ne yaptığını tarihiyle bir kayıt olarak ekle.")
    from app.core.koclugu_servisi import adim_durumu_guncelle
    # "yapmadım": kayıt silinmez, 'planlandi'ya döner (eski "ne yaptım" notları korunur)
    adim_durumu_guncelle(db, ogrenci, bid, kod, "planlandi" if durum == "bekliyor" else durum)
    db.flush()


def alanlar(plan: dict | None, kayitlar: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Plan → (gelişim alanları, güçlü yönler). Her alan: adımlar (yol haritası sırasıyla), tamamlanan / toplam / yüzde."""
    if not plan:
        return [], []
    kayitlar = kayitlar or {}
    from app.core.koclugu_servisi import ASAMA_BILGI
    asama_ad = {k: v[0].split(" · ", 1)[-1] for k, v in ASAMA_BILGI.items()}
    tum = [a for s in plan.get("asamalar", []) for a in s["adimlar"]]   # aşama sırası korunur

    def say(adimlar):
        t = sum(1 for a in adimlar if a["durum"] == "tamamlandi")
        return {"tamamlanan": t, "toplam": len(adimlar), "yuzde": round(100 * t / len(adimlar)) if adimlar else 0}

    out = []
    for o in plan.get("odak_alanlari", []):
        adimlar = [_adim_kisa(a, asama_ad, kayitlar) for a in tum if a["degisken_kod"] == o["degisken_kod"]]
        out.append({"degisken_kod": o["degisken_kod"], "ad": o["degisken_adi"], "oncelik": o.get("oncelik_sirasi"),
                    "tur_etiket": o.get("alan_turu_etiket"), "neden": o.get("neden_onemli"), "olcum": o.get("olcum"),
                    "adimlar": adimlar, **say(adimlar)})
    guclu = []
    for g in plan.get("guclu_yonler", []):
        adimlar = [_adim_kisa(a, asama_ad, kayitlar) for a in g["adimlar"]]
        guclu.append({"degisken_kod": g["degisken_kod"], "ad": g["degisken_adi"], "neden": g.get("neden_onemli"),
                      "adimlar": adimlar, **say(adimlar)})
    return out, guclu


# ----------------------------------------------------------------------------- isteğe bağlı maddeler
def kesif_kaydet(db: Session, ogrenci: Ogrenci, bolum_id: int) -> bool:
    """Öğrenci bir bölümün bilgi kartını / örnek mesleklerini açınca: o bölüm 'keşfedildi' (bölüm başına bir kez)."""
    r = db.execute(text("""INSERT INTO ogrenci_gelisim_kayitlari (ogrenci_id, tur, ref_bolum_id)
                           SELECT :o, 'kesif', :b
                            WHERE NOT EXISTS (SELECT 1 FROM ogrenci_gelisim_kayitlari
                                               WHERE ogrenci_id = :o AND tur = 'kesif' AND ref_bolum_id = :b)"""),
                   {"o": ogrenci.id, "b": bolum_id})
    return bool(r.rowcount)


def _kesfedilenler(db: Session, ogrenci: Ogrenci) -> set[int]:
    yeni = {r[0] for r in db.execute(text("SELECT ref_bolum_id FROM ogrenci_gelisim_kayitlari WHERE ogrenci_id = :o AND tur = 'kesif'"),
                                     {"o": ogrenci.id}).all()}
    eski = {r[0] for r in db.execute(text("""SELECT ref_bolum_id FROM ogrenci_haftalik_gorev
                                              WHERE ogrenci_id = :o AND tur = 'kesif' AND durum = 'tamamlandi'"""),
                                     {"o": ogrenci.id}).all()}
    return {b for b in yeni | eski if b}


def kesif_onerisi(db: Session, ogrenci: Ogrenci, hedef_bolum_id: int | None) -> dict | None:
    """Önerilerindeki (ilk 20) henüz keşfedilmemiş en üst bölüm. Sonuç yoksa öneri yok (rastgele bölüm verilmez)."""
    tur = _son_tur(db, ogrenci)
    if tur is None or tur.durum != "tamamlandi":
        return None
    kesfedilen = _kesfedilenler(db, ogrenci)
    try:
        from app.core.skor_motoru import siralama_getir
        with db.begin_nested():   # hata olursa yalnızca bu deneme geri alınır
            sira = siralama_getir(db, ogrenci, tur, ilk_n=20)
    except Exception:
        return None
    for i, s in enumerate(sira, 1):
        if s.bolum_id in kesfedilen or s.bolum_id == hedef_bolum_id:
            continue
        b = db.get(Bolum, s.bolum_id)
        if b is None:
            continue
        return {"bolum_id": b.id, "ad": _turkce_baslik(b.ad), "sira": i, "uyum": round(float(s.toplam_uyum)),
                "aciklama": f"Önerilerinde {i}. sırada. Bilgi kartını aç; mezunların ne iş yaptığına ve 'Meslek Dili'nden birkaç terime bak.",
                "link": f"/bolumler/tum?bolum={b.id}&ara={quote(b.ad)}", "kesfedilen": len(kesfedilen)}
    return None


def oz_degerlendirme_kaydet(db: Session, ogrenci: Ogrenci, yanit: dict | None) -> None:
    temiz = {}
    for anahtar, _ in OZ_DEGERLENDIRME_SORULARI:
        metin = str((yanit or {}).get(anahtar) or "").strip()
        if len(metin) < 3:
            raise IsKuraliHatasi("Lütfen üç soruyu da kısaca cevapla.")
        temiz[anahtar] = metin[:600]
    db.execute(text("INSERT INTO ogrenci_gelisim_kayitlari (ogrenci_id, tur, yanit) VALUES (:o, 'oz_degerlendirme', CAST(:y AS JSONB))"),
               {"o": ogrenci.id, "y": json.dumps(temiz, ensure_ascii=False)})


def oz_degerlendirmeler(db: Session, ogrenci: Ogrenci, adet: int = 30) -> list[dict]:
    """Yeni öz değerlendirmeler + eski haftalık yansıtma cevapları (geçmiş kayıt), yeniden eskiye."""
    out = [{"zaman": r.zaman.isoformat(), "yanit": r.yanit if isinstance(r.yanit, dict) else json.loads(r.yanit or "{}")}
           for r in db.execute(text("""SELECT zaman, yanit FROM ogrenci_gelisim_kayitlari WHERE ogrenci_id = :o AND tur = 'oz_degerlendirme'
                                        ORDER BY zaman DESC LIMIT :n"""), {"o": ogrenci.id, "n": adet}).all()]
    for r in db.execute(text("""SELECT tamamlanma_zamani AS zaman, yanit FROM ogrenci_haftalik_gorev
                                 WHERE ogrenci_id = :o AND tur = 'yansitma' AND durum = 'tamamlandi' AND yanit IS NOT NULL
                                 ORDER BY tamamlanma_zamani DESC LIMIT :n"""), {"o": ogrenci.id, "n": adet}).all():
        try:
            y = json.loads(r.yanit)
        except (TypeError, ValueError):
            continue
        out.append({"zaman": r.zaman.isoformat() if r.zaman else None, "yanit": y})
    out.sort(key=lambda x: x["zaman"] or "", reverse=True)
    return out[:adet]


# ----------------------------------------------------------------------------- seviye
def seviye_hesapla(db: Session, ogrenci: Ogrenci) -> dict:
    p = {"o": ogrenci.id}
    adim = db.query(OgrenciGelisimAdimDurumu).filter(OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
                                                     OgrenciGelisimAdimDurumu.durum == "tamamlandi").count()
    katman = (db.query(OgrenciKatmanOturumu).filter(OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
                                                   OgrenciKatmanOturumu.durum == "tamamlandi").count())
    istege = db.execute(text("SELECT count(*) FROM ogrenci_gelisim_kayitlari WHERE ogrenci_id = :o AND tur IN ('kesif', 'oz_degerlendirme')"),
                        p).scalar() or 0
    eski = db.execute(text("""SELECT count(*), count(*) FILTER (WHERE tur IN ('kesif', 'yansitma'))
                                FROM ogrenci_haftalik_gorev WHERE ogrenci_id = :o AND durum = 'tamamlandi'"""), p).first()
    eski_tum, eski_istege = (eski[0] or 0, eski[1] or 0) if eski else (0, 0)
    yeni_puan = PUAN_ADIM * adim + PUAN_KATMAN * katman + PUAN_ISTEGE_BAGLI * (istege + eski_istege)
    eski_puan = _ESKI_PUAN_GOREV * eski_tum + _ESKI_PUAN_ADIM * adim + PUAN_KATMAN * katman
    puan = max(yeni_puan, eski_puan)
    no = max(i for i, (esik, _a, _i) in enumerate(SEVIYELER) if puan >= esik)
    esik, ad, ikon = SEVIYELER[no]
    sonraki = SEVIYELER[no + 1] if no + 1 < len(SEVIYELER) else None
    return {"no": no + 1, "ad": ad, "ikon": ikon, "puan": puan,
            "sonraki_ad": sonraki[1] if sonraki else None, "sonraki_esik": sonraki[0] if sonraki else None,
            "ilerleme_yuzde": 100 if sonraki is None else round(100 * (puan - esik) / (sonraki[0] - esik)),
            "kural": f"Gelişim adımı +{PUAN_ADIM} · Değerlendirme bölümü +{PUAN_KATMAN} · Keşif ya da öz değerlendirme +{PUAN_ISTEGE_BAGLI}"}


# ----------------------------------------------------------------------------- liste
def liste(db: Session, ogrenci: Ogrenci) -> dict:
    hedef, plan = _plan(db, ogrenci)
    gelisim, guclu = alanlar(plan, adim_kayitlari(db, ogrenci, hedef.bolum_id) if hedef else {})
    tum = [a for x in gelisim for a in x["adimlar"]]
    son = db.execute(text("""SELECT max(guncelleme_zamani) FROM ogrenci_gelisim_adim_durumu
                              WHERE ogrenci_id = :o AND durum = 'tamamlandi'"""), {"o": ogrenci.id}).scalar()
    son_oz = db.execute(text("""SELECT max(zaman) FROM ogrenci_gelisim_kayitlari WHERE ogrenci_id = :o AND tur = 'oz_degerlendirme'"""),
                        {"o": ogrenci.id}).scalar()
    hb = db.get(Bolum, hedef.bolum_id) if hedef else None
    tamam = sum(1 for a in tum if a["durum"] == "tamamlandi")
    return {
        "on_adim": on_adim(db, ogrenci),
        "hedef": {"bolum_id": hb.id, "ad": _turkce_baslik(hb.ad)} if hb else None,
        "alanlar": gelisim,
        "guclu_yonler": guclu,
        "ozet": {"tamamlanan": tamam, "toplam": len(tum), "yuzde": round(100 * tamam / len(tum)) if tum else 0,
                 "devam_eden": sum(1 for a in tum if a["durum"] == "devam_ediyor"),
                 "alan_sayisi": len(gelisim), "son_ilerleme": son.isoformat() if son else None},
        "istege_bagli": {
            "kesif": kesif_onerisi(db, ogrenci, hedef.bolum_id if hedef else None),
            "oz_degerlendirme": {"sorular": [{"anahtar": a, "soru": s} for a, s in OZ_DEGERLENDIRME_SORULARI],
                                 "son": son_oz.isoformat() if son_oz else None},
        },
        "seviye": seviye_hesapla(db, ogrenci),
    }


def filiz_ozeti(db: Session, ogrenci: Ogrenci) -> str:
    """Filiz / yapay zekâ koçu için kısa metin: önce yapılacak ya da alan bazında tamamlanma ve sıradaki adımlar."""
    try:
        with db.begin_nested():
            v = liste(db, ogrenci)
    except Exception:
        return ""
    if v["on_adim"]:
        return f"Önce yapılacak: {v['on_adim']['baslik']}."
    if not v["alanlar"]:
        return ""
    satir = []
    for a in v["alanlar"]:
        sira = next((x["baslik"] for x in a["adimlar"] if x["durum"] != "tamamlandi"), None)
        satir.append(f"- {a['ad']}: {a['tamamlanan']}/{a['toplam']} adım tamam" + (f"; sıradaki: {sira}" if sira else "; hepsi tamam"))
    return "Gelişim listesi (süre yok; öğrenci kendi hızında ilerler):\n" + "\n".join(satir)


# ----------------------------------------------------------------------------- okul tarafı (toplu)
def son_hareketler(db: Session, ogrenci_idler: list) -> dict:
    """Hedef bölümü olan öğrencilerin gelişim listesindeki SON HAREKETİ {ogrenci_id: zaman}: madde durumu değişikliği
    (yapıyorum / yaptım), girilen kayıt (madde kaydı, keşif, öz değerlendirme) ya da hedefin seçildiği an — hangisi en yeniyse.
    Okul özeti ("durgun") ve rehberlik erken uyarısı ("gelisim_durgun") aynı tanımı buradan kullanır."""
    if not ogrenci_idler:
        return {}
    rows = db.execute(text("""
        SELECT h.ogrenci_id, GREATEST(max(h.secim_zamani),
                                      (SELECT max(a.guncelleme_zamani) FROM ogrenci_gelisim_adim_durumu a
                                        WHERE a.ogrenci_id = h.ogrenci_id AND a.durum IN ('devam_ediyor', 'tamamlandi')),
                                      (SELECT max(k.zaman) FROM ogrenci_gelisim_kayitlari k WHERE k.ogrenci_id = h.ogrenci_id)) AS son
          FROM ogrenci_hedef_bolum h WHERE h.ogrenci_id = ANY(:ids) AND h.aktif_mi GROUP BY h.ogrenci_id"""), {"ids": ogrenci_idler}).all()
    return {r.ogrenci_id: r.son for r in rows}


def okul_ozeti(db: Session, ogrenci_idler: list) -> dict:
    """Okul paneli / istatistik (toplu; öğrenci başına plan hesaplanmaz): hedefi olan öğrenci, adım tamamlayan, toplam adım,
    adım dağılımı ve "durgun" (hedefi var, son_hareketler'e göre DURGUN_GUN gündür hareket yok)."""
    if not ogrenci_idler:
        return {"hedefli": 0, "adim_yapan": 0, "toplam_adim": 0, "durgun": 0, "dagilim": [], "durgun_gun": DURGUN_GUN}
    p = {"ids": ogrenci_idler}
    hedefli = son_hareketler(db, ogrenci_idler)
    say = {r.ogrenci_id: r.n for r in db.execute(text("""
        SELECT ogrenci_id, count(*) AS n FROM ogrenci_gelisim_adim_durumu
         WHERE ogrenci_id = ANY(:ids) AND durum = 'tamamlandi' GROUP BY 1"""), p).all()}
    simdi = datetime.now(timezone.utc)
    durgun = sum(1 for son in hedefli.values() if son is not None and (simdi - son).days >= DURGUN_GUN)
    dagilim = [{"ad": ad, "deger": sum(1 for i in hedefli if lo <= say.get(i, 0) <= hi)}
               for ad, lo, hi in (("0 adım", 0, 0), ("1–3 adım", 1, 3), ("4–9 adım", 4, 9), ("10+ adım", 10, 10**6))]
    return {"hedefli": len(hedefli), "adim_yapan": sum(1 for i in hedefli if say.get(i, 0) > 0),
            "toplam_adim": sum(say.values()), "durgun": durgun, "dagilim": dagilim, "durgun_gun": DURGUN_GUN}
