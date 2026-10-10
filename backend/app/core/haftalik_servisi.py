"""
[2026-10-04] Haftalık görevler, seri (streak) ve Filiz seviyesi.

Amaç: öğrencinin sisteme bir kez girip çıkması yerine her hafta düzenli olarak
dönmesi. Her hafta 3 görev:
  1. Yolculuk görevi — öğrencinin o anki durumuna göre TEK somut adım:
       testler bitmediyse sıradaki katman → K5 bekliyorsa alan soruları →
       hedef yoksa hedef seçimi → hedef varsa yol haritasındaki sıradaki adım
  2. Keşif görevi    — bir bölümü inceleyip örnek mesleklerine bakmak
  3. Yansıtma        — 3 kısa soru (neyi iyi yaptın / nerede zorlandın / gelecek hafta hedefin)
Görevler haftanın ilk açılışında oluşturulur, hafta boyunca SABİT kalır
(öğrenci bir adımı bitirince liste kaymaz). Katman, K5, hedef ve yol haritası
görevleri ilgili iş yapıldığında kendiliğinden tamamlanır; keşif görevi öğrenci
o bölümün örnek mesleklerini açınca tamamlanır.
"""
import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote
from zoneinfo import ZoneInfo

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.katman_servisi import IsKuraliHatasi
from app.models import (
    Ogrenci, Katman, Bolum, OgrenciDegerlendirmeTuru, OgrenciKatmanOturumu,
    OgrenciGelisimAdimDurumu, OgrenciHaftalikGorev,
)

try:
    TR_SAAT = ZoneInfo("Europe/Istanbul")
except Exception:  # sunucuda saat dilimi verisi yoksa: Türkiye 2016'dan beri sabit UTC+3
    TR_SAAT = timezone(timedelta(hours=3))
SERI_ESIGI = 2            # bir hafta "seriye sayılır" için en az kaç görev tamamlanmalı
GECMIS_HAFTA = 8          # özet grafiğinde gösterilen hafta sayısı

YANSITMA_SORULARI = [
    ("iyi", "Bu hafta neyi iyi yaptın?"),
    ("zor", "Nerede zorlandın?"),
    ("hedef", "Gelecek hafta için tek bir hedefin ne?"),
]

# Filiz'in büyüme seviyeleri: (gereken puan, ad, ikon)
SEVIYELER = [
    (0, "Tohum", "🌰"),
    (30, "Filiz", "🌱"),
    (80, "Fidan", "🌿"),
    (160, "Genç Ağaç", "🌳"),
    (280, "Çiçek Açan Ağaç", "🌸"),
    (450, "Ulu Çınar", "🏆"),
]
PUAN_GOREV, PUAN_PLAN_ADIMI, PUAN_KATMAN = 10, 5, 15


# ----------------------------------------------------------------------------- tarih
def bugun_tr(simdi: datetime | None = None) -> date:
    return (simdi or datetime.now(timezone.utc)).astimezone(TR_SAAT).date()


def hafta_baslangici(gun: date) -> date:
    return gun - timedelta(days=gun.weekday())  # Pazartesi


def _turkce_baslik(metin: str) -> str:
    from app.core.koclugu_servisi import turkce_baslik
    return turkce_baslik(metin)


# ----------------------------------------------------------------------------- görev üretimi
def _son_tur(db: Session, ogrenci: Ogrenci) -> OgrenciDegerlendirmeTuru | None:
    return (db.query(OgrenciDegerlendirmeTuru)
            .filter(OgrenciDegerlendirmeTuru.ogrenci_id == ogrenci.id)
            .order_by(OgrenciDegerlendirmeTuru.tur_no.desc()).first())


def _ana_katmanlar(db: Session) -> list[Katman]:
    return db.query(Katman).filter(Katman.kosullu_mu.is_(False)).order_by(Katman.sira).all()


def _tamamlanan_katman_idleri(db: Session, ogrenci: Ogrenci, tur_id: int) -> set[int]:
    return {o.katman_id for o in db.query(OgrenciKatmanOturumu).filter(
        OgrenciKatmanOturumu.ogrenci_id == ogrenci.id,
        OgrenciKatmanOturumu.tur_id == tur_id,
        OgrenciKatmanOturumu.durum == "tamamlandi",
    ).all()}


def _yolculuk_gorevi(db: Session, ogrenci: Ogrenci) -> dict | None:
    """Öğrencinin şu anki durumuna göre en önemli tek adım."""
    from app.core.dal_servisi import bekleyen_dal_var_mi
    from app.core.koclugu_servisi import aktif_hedef_getir, gap_analizi_hesapla, gelisim_plani_olustur

    tur = _son_tur(db, ogrenci)
    katmanlar = _ana_katmanlar(db)
    if tur is None or tur.durum != "tamamlandi":
        biten = _tamamlanan_katman_idleri(db, ogrenci, tur.id) if tur else set()
        sonraki = next((k for k in katmanlar if k.id not in biten), None)
        if sonraki is not None:
            return {"tur": "katman", "baslik": f"{sonraki.kod} · {sonraki.ad} katmanını tamamla",
                    "aciklama": "Yaklaşık 5 dakika. Samimi cevap ver, doğru ya da yanlış cevap yok.",
                    "ref_kod": sonraki.kod, "link": "/katmanlar"}
        return None
    if bekleyen_dal_var_mi(db, ogrenci, tur):
        return {"tur": "k5", "baslik": "Sana açılan alan (K5) sorularını tamamla",
                "aciklama": "Bölüm önerilerin ve koçluk planın bu adımdan sonra hazırlanıyor.",
                "ref_kod": "K5", "link": "/katmanlar"}
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef is None:
        return {"tur": "hedef", "baslik": "Önerilen bölümlerinden birini hedef seç",
                "aciklama": "Hedef seçince sana özel adım adım bir gelişim planı hazırlanır.",
                "link": "/koclugu"}
    try:
        satirlar = gap_analizi_hesapla(db, ogrenci, tur, hedef.bolum_id)
        plan = gelisim_plani_olustur(db, ogrenci, hedef.bolum_id, satirlar)
    except Exception:  # plan hesaplanamıyorsa (ör. bölüm ağırlığı yok) görev üretimi durmasın
        return None
    adim = plan.get("siradaki_adim")
    if adim is None:  # tüm gelişim adımları bitti → güçlü yön adımlarından devam
        adim = next((a for g in plan.get("guclu_yonler", []) for a in g["adimlar"] if a["durum"] != "tamamlandi"), None)
    if adim is None:
        return None
    return {"tur": "plan_adimi", "baslik": adim["baslik"],
            "aciklama": f"{adim['degisken_adi']} · {adim['sure']}. Başarı ölçütü: {adim['olcut']}",
            "ref_kod": adim["kod"], "ref_bolum_id": hedef.bolum_id, "link": "/koclugu"}


def _kesif_gorevi(db: Session, ogrenci: Ogrenci, hafta: date, haric: set | None = None) -> dict | None:
    """Daha önce keşif görevi olarak verilmemiş bir bölüm seçer. Sonuçlar hazırsa önerilenlerden."""
    from app.core.koclugu_servisi import aktif_hedef_getir
    verilmis = {g.ref_bolum_id for g in db.query(OgrenciHaftalikGorev).filter(
        OgrenciHaftalikGorev.ogrenci_id == ogrenci.id, OgrenciHaftalikGorev.tur == "kesif").all()}
    verilmis |= set(haric or ())
    hedef = aktif_hedef_getir(db, ogrenci)
    if hedef:
        verilmis.add(hedef.bolum_id)

    aday_idler, sira_bilgisi = [], {}
    tur = _son_tur(db, ogrenci)
    if tur is not None and tur.durum == "tamamlandi":
        try:
            from app.core.skor_motoru import siralama_getir
            for i, s in enumerate(siralama_getir(db, ogrenci, tur, ilk_n=20), 1):
                aday_idler.append(s.bolum_id)
                sira_bilgisi[s.bolum_id] = (i, s.toplam_uyum)
        except Exception:
            aday_idler = []
    aday_idler = [b for b in aday_idler if b not in verilmis]

    if aday_idler:
        bolum = db.get(Bolum, aday_idler[0])
    else:  # sonuç yoksa ya da öneriler bitti: yayındaki bölümlerden öğrenciye ve haftaya göre sabit bir seçim
        havuz = [b for b in db.query(Bolum).filter(Bolum.durum == "yayinda").order_by(Bolum.id).all() if b.id not in verilmis]
        if not havuz:
            return None
        tohum = int(hashlib.sha1(f"{ogrenci.id}-{hafta.isoformat()}".encode()).hexdigest()[:8], 16)
        bolum = havuz[tohum % len(havuz)]
    if bolum is None:
        return None
    ad = _turkce_baslik(bolum.ad)
    if bolum.id in sira_bilgisi:
        sira, uyum = sira_bilgisi[bolum.id]
        aciklama = f"Önerilerinde {sira}. sırada (%{round(uyum)} uyum). Profiline ve örnek mesleklerine bak."
    else:
        aciklama = "Bölümün profiline ve örnek mesleklerine bak; ilgini çekiyor mu, düşün."
    return {"tur": "kesif", "baslik": f"Keşfet: {ad}", "aciklama": aciklama, "ref_bolum_id": bolum.id,
            "link": f"/bolumler/tum?bolum={bolum.id}&ara={quote(bolum.ad)}"}


def _yansitma_gorevi() -> dict:
    return {"tur": "yansitma", "baslik": "Haftanı 2 dakikada değerlendir",
            "aciklama": "3 kısa soru: neyi iyi yaptın, nerede zorlandın, gelecek hafta hedefin ne?"}


def _gorevleri_olustur(db: Session, ogrenci: Ogrenci, hafta: date) -> None:
    tanimlar = [t for t in (_yolculuk_gorevi(db, ogrenci), _kesif_gorevi(db, ogrenci, hafta)) if t]
    if len(tanimlar) < 2:  # yolculuk görevi çıkmadıysa ikinci bir keşif ekle
        ikinci = _kesif_gorevi(db, ogrenci, hafta, haric={t.get("ref_bolum_id") for t in tanimlar})
        if ikinci:
            tanimlar.append(ikinci)
    tanimlar.append(_yansitma_gorevi())
    try:
        with db.begin_nested():  # aynı anda iki istek gelirse benzersizlik kısıtı korur
            for sira, t in enumerate(tanimlar, 1):
                db.add(OgrenciHaftalikGorev(ogrenci_id=ogrenci.id, hafta_baslangic=hafta, sira=sira, **t))
            db.flush()
    except IntegrityError:
        pass  # diğer istek oluşturdu; aşağıda okunur


def _otomatik_tamamla(db: Session, ogrenci: Ogrenci, gorevler: list[OgrenciHaftalikGorev]) -> None:
    """Katman / K5 / hedef / yol haritası görevlerini gerçek duruma göre işaretler."""
    from app.core.dal_servisi import bekleyen_dal_var_mi
    from app.core.koclugu_servisi import aktif_hedef_getir
    bekleyen = [g for g in gorevler if g.durum == "bekliyor" and g.tur in ("katman", "k5", "hedef", "plan_adimi")]
    if not bekleyen:
        return
    tur = _son_tur(db, ogrenci)
    for g in bekleyen:
        bitti = False
        if g.tur == "katman" and tur is not None:
            kat = db.query(Katman).filter(Katman.kod == g.ref_kod).first()
            bitti = kat is not None and kat.id in _tamamlanan_katman_idleri(db, ogrenci, tur.id)
        elif g.tur == "k5" and tur is not None:
            bitti = tur.durum == "tamamlandi" and not bekleyen_dal_var_mi(db, ogrenci, tur)
        elif g.tur == "hedef":
            bitti = aktif_hedef_getir(db, ogrenci) is not None
        elif g.tur == "plan_adimi":
            kayit = db.query(OgrenciGelisimAdimDurumu).filter(
                OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id,
                OgrenciGelisimAdimDurumu.hedef_bolum_id == g.ref_bolum_id,
                OgrenciGelisimAdimDurumu.adim_kodu == g.ref_kod,
            ).first()
            bitti = kayit is not None and kayit.durum == "tamamlandi"
        if bitti:
            g.durum = "tamamlandi"
            g.tamamlanma_zamani = datetime.now(timezone.utc)
    db.flush()


def haftanin_gorevleri(db: Session, ogrenci: Ogrenci, bugun: date | None = None) -> list[OgrenciHaftalikGorev]:
    hafta = hafta_baslangici(bugun or bugun_tr())

    def oku():
        return (db.query(OgrenciHaftalikGorev)
                .filter(OgrenciHaftalikGorev.ogrenci_id == ogrenci.id, OgrenciHaftalikGorev.hafta_baslangic == hafta)
                .order_by(OgrenciHaftalikGorev.sira).all())
    gorevler = oku()
    if not gorevler:
        _gorevleri_olustur(db, ogrenci, hafta)
        gorevler = oku()
    _otomatik_tamamla(db, ogrenci, gorevler)
    return gorevler


# ----------------------------------------------------------------------------- tamamlama
def gorevi_tamamla(db: Session, ogrenci: Ogrenci, gorev_id: int, yanit: dict | None = None,
                   bugun: date | None = None) -> OgrenciHaftalikGorev:
    g = db.get(OgrenciHaftalikGorev, gorev_id)
    if g is None or g.ogrenci_id != ogrenci.id:
        raise IsKuraliHatasi("Görev bulunamadı.")
    if g.hafta_baslangic != hafta_baslangici(bugun or bugun_tr()):
        raise IsKuraliHatasi("Yalnızca bu haftanın görevleri işaretlenebilir.")
    if g.durum == "tamamlandi":
        return g
    if g.tur in ("katman", "k5", "hedef"):
        raise IsKuraliHatasi("Bu görev, ilgili adımı tamamladığında kendiliğinden işaretlenir.")
    if g.tur == "yansitma":
        temiz = {}
        for anahtar, _soru in YANSITMA_SORULARI:
            metin = str((yanit or {}).get(anahtar) or "").strip()
            if len(metin) < 3:
                raise IsKuraliHatasi("Lütfen üç soruyu da kısaca cevapla.")
            temiz[anahtar] = metin[:600]
        g.yanit = json.dumps(temiz, ensure_ascii=False)
    if g.tur == "plan_adimi" and g.ref_bolum_id and g.ref_kod:
        from app.core.koclugu_servisi import adim_durumu_guncelle
        adim_durumu_guncelle(db, ogrenci, g.ref_bolum_id, g.ref_kod, "tamamlandi")  # yol haritasıyla eşitlenir
    g.durum = "tamamlandi"
    g.tamamlanma_zamani = datetime.now(timezone.utc)
    db.flush()
    return g


def kesif_isaretle(db: Session, ogrenci: Ogrenci, bolum_id: int, bugun: date | None = None) -> bool:
    """Öğrenci bir bölümün örnek mesleklerini açtığında çağrılır. Bu haftanın keşif görevi o bölümse tamamlar."""
    hafta = hafta_baslangici(bugun or bugun_tr())
    g = db.query(OgrenciHaftalikGorev).filter(
        OgrenciHaftalikGorev.ogrenci_id == ogrenci.id,
        OgrenciHaftalikGorev.hafta_baslangic == hafta,
        OgrenciHaftalikGorev.tur == "kesif",
        OgrenciHaftalikGorev.ref_bolum_id == bolum_id,
        OgrenciHaftalikGorev.durum == "bekliyor",
    ).first()
    if g is None:
        return False
    g.durum = "tamamlandi"
    g.tamamlanma_zamani = datetime.now(timezone.utc)
    db.flush()
    return True


# ----------------------------------------------------------------------------- seri + seviye
def _haftalik_sayimlar(db: Session, ogrenci: Ogrenci) -> dict[date, tuple[int, int]]:
    sayim: dict[date, list[int]] = {}
    for g in db.query(OgrenciHaftalikGorev).filter(OgrenciHaftalikGorev.ogrenci_id == ogrenci.id).all():
        s = sayim.setdefault(g.hafta_baslangic, [0, 0])
        s[1] += 1
        if g.durum == "tamamlandi":
            s[0] += 1
    return {h: (t, n) for h, (t, n) in sayim.items()}


def seri_hesapla(sayimlar: dict[date, tuple[int, int]], bu_hafta: date) -> tuple[int, int]:
    """(güncel seri, en uzun seri). Bu hafta henüz eşiğe ulaşmadıysa seri bozulmuş sayılmaz."""
    basarili = {h for h, (t, _n) in sayimlar.items() if t >= SERI_ESIGI}
    hafta = bu_hafta if bu_hafta in basarili else bu_hafta - timedelta(days=7)
    guncel = 0
    while hafta in basarili:
        guncel += 1
        hafta -= timedelta(days=7)
    en_uzun, sayac, onceki = 0, 0, None
    for h in sorted(basarili):
        sayac = sayac + 1 if onceki is not None and h - onceki == timedelta(days=7) else 1
        en_uzun = max(en_uzun, sayac)
        onceki = h
    return guncel, en_uzun


def seviye_hesapla(db: Session, ogrenci: Ogrenci, toplam_gorev: int) -> dict:
    plan_adimi = db.query(OgrenciGelisimAdimDurumu).filter(
        OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id, OgrenciGelisimAdimDurumu.durum == "tamamlandi").count()
    katman = (db.query(OgrenciKatmanOturumu).join(Katman, Katman.id == OgrenciKatmanOturumu.katman_id)
              .filter(OgrenciKatmanOturumu.ogrenci_id == ogrenci.id, OgrenciKatmanOturumu.durum == "tamamlandi").count())
    puan = PUAN_GOREV * toplam_gorev + PUAN_PLAN_ADIMI * plan_adimi + PUAN_KATMAN * katman
    no = max(i for i, (esik, _a, _i) in enumerate(SEVIYELER) if puan >= esik)
    esik, ad, ikon = SEVIYELER[no]
    sonraki = SEVIYELER[no + 1] if no + 1 < len(SEVIYELER) else None
    return {
        "no": no + 1, "ad": ad, "ikon": ikon, "puan": puan,
        "sonraki_ad": sonraki[1] if sonraki else None,
        "sonraki_esik": sonraki[0] if sonraki else None,
        "ilerleme_yuzde": 100 if sonraki is None else round(100 * (puan - esik) / (sonraki[0] - esik)),
    }


def haftalik_ozet(db: Session, ogrenci: Ogrenci, bugun: date | None = None) -> dict:
    bugun = bugun or bugun_tr()
    hafta = hafta_baslangici(bugun)
    gorevler = haftanin_gorevleri(db, ogrenci, bugun)
    sayimlar = _haftalik_sayimlar(db, ogrenci)
    guncel, en_uzun = seri_hesapla(sayimlar, hafta)
    toplam = sum(t for t, _n in sayimlar.values())
    gecmis = []
    for i in range(GECMIS_HAFTA - 1, -1, -1):
        h = hafta - timedelta(days=7 * i)
        t, n = sayimlar.get(h, (0, 0))
        gecmis.append({"hafta_baslangic": h.isoformat(), "tamamlanan": t, "toplam": n, "seriye_sayildi": t >= SERI_ESIGI})
    return {
        "hafta_baslangic": hafta.isoformat(),
        "hafta_bitis": (hafta + timedelta(days=6)).isoformat(),
        "kalan_gun": 6 - bugun.weekday(),
        "gorevler": [_gorev_dict(g) for g in gorevler],
        "tamamlanan": sum(1 for g in gorevler if g.durum == "tamamlandi"),
        "toplam": len(gorevler),
        "seri_esigi": SERI_ESIGI,
        "seri": {"guncel": guncel, "en_uzun": en_uzun, "toplam_tamamlanan": toplam},
        "gecmis": gecmis,
        "seviye": seviye_hesapla(db, ogrenci, toplam),
        "yansitma_sorulari": [{"anahtar": a, "soru": s} for a, s in YANSITMA_SORULARI],
    }


def _gorev_dict(g: OgrenciHaftalikGorev) -> dict:
    return {
        "id": g.id, "sira": g.sira, "tur": g.tur, "baslik": g.baslik, "aciklama": g.aciklama,
        "link": g.link, "durum": g.durum,
        "elle_tamamlanabilir": g.tur in ("plan_adimi", "kesif", "yansitma"),
        "yanit": json.loads(g.yanit) if g.yanit else None,
        "tamamlanma_zamani": g.tamamlanma_zamani.isoformat() if g.tamamlanma_zamani else None,
    }
