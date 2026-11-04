# -*- coding: utf-8 -*-
"""
[2026-11-04] Veri Kaynakları › "Otomatik çek" (kullanıcı isteği: her kaynağın yanında buton; hata olursa hata bilgisi
görünsün, olmazsa yönetici kaynak bağlantısından elle günceller).

Otomatik çekilebilenler (TÜİK Veri Portalı'nın veri tarayıcısı — databrowser2.tuik.gov.tr; portalın kendi ekranlarının
kullandığı JSON-stat adresi, resmî ve belgelenmiş bir API DEĞİL: biçim değişirse anlaşılır bir hata verilir, veri yazılmaz):
  * tufe          — TÜFE genel endeksi (2025=100, DF_TUFE_SDMX_TT10): eksik aylar eklenir. Gece bakımı da her ay dener.
  * tuik_istihdam — Yükseköğretim İstihdam Göstergeleri, lisans bölüm tabloları (DF_LM_KIO_BOLUM, DF_LM_B_IIB_SURE,
                    DF_LSNS_MEZ_BOL_AOK): en son ortak yıl yüklenir. Bölüm eşleşmesi: önce aynı programın daha önce
                    kaydedilmiş (yöneticinin elle düzelttiği dahil) bölümü, yoksa yalnızca kesin ("otomatik") eşleşme;
                    öneriler bağlanmaz, eşleşmesiz kalır (İş Hayatı Verileri ekranından bağlanır).
Diğer kaynakların herkese açık bir veri servisi yok (TÜRK-İŞ PDF, kamu maaşları haber, ÖSYM takvimi…): buton nedenini yazar.
Ekran taraması (scraping) bilinçli olarak yapılmaz: sayfa değişince sessizce yanlış veri üretebilir.
"""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from sqlalchemy import text
from sqlalchemy.orm import Session

TUIK_VERI = "https://databrowser2.tuik.gov.tr/api/core/nodes/1/datasets/TR,{id},1.0/data"
TUIK_TARAYICI = "https://databrowser2.tuik.gov.tr/#/tr/tuik/TR,{id},1.0"
ZAMAN_ASIMI = 45
EN_FAZLA_BAYT = 20 * 1024 * 1024


class CekmeHatasi(Exception):
    """Yöneticiye aynen gösterilen, ne olduğunu ve ne yapılacağını söyleyen hata."""


def _tuik_veri(veri_id: str) -> dict:
    """TÜİK veri tarayıcısından bir tabloyu JSON-stat olarak alır (Türkçe etiketlerle). Yalnızca *.tuik.gov.tr."""
    from app.core.tuik_baglanti import BaglantiHatasi, _alan_uygun_mu, _GuvenliYonlendirme
    url = TUIK_VERI.format(id=veri_id)
    try:
        _alan_uygun_mu(url)
    except BaglantiHatasi as e:
        raise CekmeHatasi(f"TÜİK sunucusuna ulaşılamadı: {e}")
    istek = urllib.request.Request(url, data=b"[]", method="POST", headers={
        "Content-Type": "application/json", "Accept": "application/json", "UserLang": "tr",
        "User-Agent": "Filizyol/1.0 (istatistik verisi icin)"})
    try:
        with urllib.request.build_opener(_GuvenliYonlendirme()).open(istek, timeout=ZAMAN_ASIMI) as y:
            ham = y.read(EN_FAZLA_BAYT + 1)
    except urllib.error.HTTPError as e:
        raise CekmeHatasi(f"TÜİK sunucusu {veri_id} tablosunu vermedi (HTTP {e.code}). Tablo adı ya da adres değişmiş olabilir.")
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise CekmeHatasi(f"TÜİK sunucusuna bağlanılamadı ya da yanıt {ZAMAN_ASIMI} sn içinde gelmedi ({type(e).__name__}).")
    if len(ham) > EN_FAZLA_BAYT:
        raise CekmeHatasi("TÜİK yanıtı beklenenden çok büyük; işlem durduruldu.")
    try:
        j = json.loads(ham.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise CekmeHatasi(f"TÜİK yanıtı okunamadı ({veri_id}): veri yerine başka bir sayfa döndü. Portalın biçimi değişmiş olabilir.")
    if not isinstance(j, dict) or not {"id", "size", "value", "dimension"} <= set(j):
        raise CekmeHatasi(f"TÜİK yanıtının biçimi beklenen gibi değil ({veri_id}). Portalın biçimi değişmiş olabilir.")
    return j


def _hucreler(j: dict, sabit: dict[str, str], satir: str, sutun: str) -> dict[tuple[str, str], str]:
    """JSON-stat → {(satır kodu, sütun kodu): değer}. sabit: diğer boyutların seçilen kodu (tek kodlu boyutlar kendiliğinden)."""
    boyut = j["id"]
    boy = j["size"]
    kod = {d: j["dimension"][d]["category"]["index"] for d in boyut}
    if isinstance(next(iter(kod.values()), None), dict):   # index sözlük biçiminde de gelebilir
        kod = {d: sorted(v, key=v.get) if isinstance(v, dict) else v for d, v in kod.items()}
    secim = {}
    for d in boyut:
        if d in (satir, sutun):
            continue
        if d in sabit:
            if sabit[d] not in kod[d]:
                raise CekmeHatasi(f"TÜİK tablosunda beklenen '{d}={sabit[d]}' seçeneği yok. Portalın biçimi değişmiş olabilir.")
            secim[d] = kod[d].index(sabit[d])
        elif len(kod[d]) == 1:
            secim[d] = 0
        else:
            raise CekmeHatasi(f"TÜİK tablosunda beklenmeyen boyut: {d}. Portalın biçimi değişmiş olabilir.")
    deger = j["value"]
    out = {}
    for i, a in enumerate(kod[satir]):
        for k, b in enumerate(kod[sutun]):
            konum = {**secim, satir: i, sutun: k}
            n = 0
            for d, s in zip(boyut, boy):
                n = n * s + konum[d]
            v = deger[n] if isinstance(deger, list) and n < len(deger) else (deger.get(str(n)) if isinstance(deger, dict) else None)
            if v not in (None, ""):
                out[(a, b)] = v
    return out


# ----------------------------------------------------------------------------------------------------------- TÜFE
TUFE_ID = "DF_TUFE_SDMX_TT10"


def tufe_cek(db: Session, yon=None) -> dict:
    j = _tuik_veri(TUFE_ID)
    for d in ("DEGISIM", "TIME_PERIOD"):
        if d not in j["id"]:
            raise CekmeHatasi(f"TÜFE tablosunda '{d}' boyutu yok. Portalın biçimi değişmiş olabilir.")
    endeks = _hucreler(j, {"DEGISIM": "1"}, "TIME_PERIOD", "DEGISIM")
    yillik = _hucreler(j, {"DEGISIM": "4"}, "TIME_PERIOD", "DEGISIM")
    aylar = sorted({a for a, _ in endeks if re.fullmatch(r"\d{4}-\d{2}", a)})
    if not aylar:
        raise CekmeHatasi("TÜFE tablosunda aylık endeks bulunamadı.")
    kaynak = f"TÜİK, Tüketici Fiyat Endeksi (2025=100), Veri Portalı tablo {TUFE_ID} (otomatik çekildi) — {TUIK_TARAYICI.format(id=TUFE_ID)}"
    mevcut = {r[0]: float(r[1]) for r in db.execute(text("SELECT donem, endeks FROM tufe_endeksi")).all()}
    eklenen, farkli = [], []
    for a in aylar:
        e = float(endeks[(a, "1")])
        if a in mevcut:
            if abs(mevcut[a] - e) > 0.005:
                farkli.append(a)   # TÜİK geçmiş ayı düzeltmişse yazılmaz, yöneticiye bildirilir
            continue
        y = yillik.get((a, "4"))
        db.execute(text("INSERT INTO tufe_endeksi (donem, endeks, yillik_degisim, kaynak) VALUES (:d, :e, :y, :k) ON CONFLICT (donem) DO NOTHING"),
                   {"d": a, "e": e, "y": float(y) if y is not None else None, "k": kaynak})
        eklenen.append(a)
    db.commit()
    son = aylar[-1]
    mesaj = (f"{len(eklenen)} yeni ay eklendi ({eklenen[0]} – {eklenen[-1]}). " if eklenen else "Yeni ay yok; sistem güncel. ") + \
            f"TÜİK'teki son ay: {son} (endeks {float(endeks[(son, '1')]):.2f})."
    if farkli:
        mesaj += f" Dikkat: {len(farkli)} ayın değeri sistemdekinden farklı ({', '.join(farkli[:5])}); değiştirilmedi, kontrol edin."
    return {"mesaj": mesaj, "eklenen": len(eklenen), "son_donem": son, "farkli": farkli}


# --------------------------------------------------------------------------------------------- TÜİK istihdam
ISTIHDAM_TABLOLARI = [("DF_LM_KIO_BOLUM", "istihdam_orani", "kayıtlı istihdam oranı"),
                      ("DF_LM_B_IIB_SURE", "is_bulma_suresi_ay", "ilk iş bulma süresi"),
                      ("DF_LSNS_MEZ_BOL_AOK", "kazanc_grubu", "aylık ortalama kazanç grupları")]


def istihdam_cek(db: Session, yon=None) -> dict:
    from app.api.admin_is_hayati import IstihdamKaydet, IstihdamSatiri, istihdam_kaydet
    from app.core import is_hayati_servisi as ihs
    tablolar = {}
    for veri_id, alan, _ in ISTIHDAM_TABLOLARI:
        j = _tuik_veri(veri_id)
        if "BOLUM" not in j["id"] or "TIME_PERIOD" not in j["id"]:
            raise CekmeHatasi(f"{veri_id} tablosunda bölüm ya da yıl boyutu yok. Portalın biçimi değişmiş olabilir.")
        hucre = _hucreler(j, {}, "BOLUM", "TIME_PERIOD")
        etiket = j["dimension"]["BOLUM"]["category"].get("label") or {}
        tablolar[alan] = (hucre, etiket)
    ortak = set.intersection(*({y for _, y in h} for h, _ in tablolar.values()))
    if not ortak:
        raise CekmeHatasi("Üç tabloda ortak yıl yok; TÜİK tabloları farklı yıllarda güncellenmiş olabilir. Bir süre sonra tekrar deneyin.")
    yil = max(ortak)
    if not re.fullmatch(r"\d{4}", str(yil)):
        raise CekmeHatasi(f"Yıl biçimi beklenmedik: {yil}.")
    # Program kodları: L1, L2… (Toplam "_T" ve üst düzey "L" atlanır)
    satirlar: dict[str, dict] = {}
    for alan, (hucre, etiket) in tablolar.items():
        for (kod, y), v in hucre.items():
            if y != yil or not re.fullmatch(r"L\d+", kod):
                continue
            ad = " ".join(str(etiket.get(kod) or "").split())
            if not ad:
                continue
            # Tablolar program adıyla birleştirilir (kodlar tablodan tabloya farklı numaralanabilir)
            s = satirlar.setdefault(ihs.program_anahtari(ad), {"program_adi_kaynak": ad, "duzey": "lisans"})
            if alan == "kazanc_grubu":
                s[alan] = ihs.kazanc_grubu_coz(v)
            else:
                s[alan] = round(float(v), 2)
    if not satirlar:
        raise CekmeHatasi(f"{yil} yılı için program satırı bulunamadı.")
    # Bölüm: önce bu programın daha önce kaydedilmiş bölümü (yöneticinin elle bağladığı dahil), yoksa yalnızca kesin eşleşme
    onceki = {}
    for r in db.execute(text("""SELECT program_adi_kaynak, bolum_id FROM istihdam_gostergeleri
                                 WHERE duzey = 'lisans' AND bolum_id IS NOT NULL ORDER BY veri_yili, id""")).all():
        onceki[ihs.program_anahtari(r.program_adi_kaynak)] = r.bolum_id
    gecerli = {r[0] for r in db.execute(text("SELECT id FROM bolumler")).all()}
    adaylar = ihs.bolum_adaylari(db)
    yeni_eslesen = eslesmeyen = 0
    liste = []
    for s in satirlar.values():
        bid = onceki.get(ihs.program_anahtari(s["program_adi_kaynak"]))
        if bid not in gecerli:
            bid = None
            e = ihs.program_eslestir(s["program_adi_kaynak"], adaylar, duzey="lisans")
            if e.get("durum") == "otomatik":
                bid, yeni_eslesen = e.get("bolum_id"), yeni_eslesen + 1
        eslesmeyen += bid is None
        liste.append(IstihdamSatiri(**{**s, "bolum_id": bid}))
    kaynak = (f"TÜİK, Yükseköğretim İstihdam Göstergeleri, {yil} (Veri Portalı; lisans bölüm tabloları: "
              + ", ".join(a for _, _, a in ISTIHDAM_TABLOLARI) + "; otomatik çekildi)")
    sonuc = istihdam_kaydet(IstihdamKaydet(dosya_adi="TÜİK Veri Portalı (otomatik çekme)", veri_yili=int(yil), kaynak=kaynak,
                                           satirlar=liste), db, yon)
    mesaj = (f"{yil} verisi: {len(liste)} program ({sonuc['eklenen']} yeni, {sonuc['guncellenen']} güncellendi). "
             f"{len(liste) - eslesmeyen} program bir bölüme bağlı" + (f", {yeni_eslesen} tanesi yeni kesin eşleşme" if yeni_eslesen else "")
             + (f"; {eslesmeyen} program eşleşmesiz — İş Hayatı Verileri › TÜİK İstihdam ekranında bağlayabilirsiniz." if eslesmeyen else "."))
    return {"mesaj": mesaj, "yil": int(yil), **sonuc}


# ------------------------------------------------------------------------------------------------ kayıt defteri
CEKICILER = {"tufe": tufe_cek, "tuik_istihdam": istihdam_cek}

# Otomatik çekilemeyenler: neden + ne yapılmalı (butona basınca aynen gösterilir)
NEDENLER = {
    "tuik_kazanc": "TÜİK Kazanç Yapısı'nın sistemin kullandığı meslek ana grubu tablosu yalnızca bültenin Excel ekinde var; "
                   "veri tarayıcısında yalnızca 4 haneli meslek ayrıntısı bulunuyor. Kaynak bağlantısındaki bültenden tabloyu indirip "
                   "İş Hayatı Verileri › Kazanç Yapısı sekmesinden yükleyin.",
    "kamu_maaslari": "Kadro bazında net maaşlar resmî bir veri servisinde yayımlanmıyor (haberlerle duyuruluyor). Kaynak bağlantısından "
                     "yeni dönemin tablosunu açıp Kamu Maaşları sekmesinde güncelleyin.",
    "yasam_giderleri": "TÜRK-İŞ yaşam maliyetini her ay PDF ve basın açıklamasıyla duyuruyor; veri servisi yok. Kaynak bağlantısından "
                       "yeni ayın rakamını alıp Yaşam maliyeti tablosuna ekleyin.",
    "asgari_ucret": "Asgari ücret Resmî Gazete'de yayımlanıyor; veri servisi yok. Yılda bir kez Asgari ücret tablosuna yeni dönemi ekleyin.",
    "yks_tarihi": "ÖSYM sınav takvimi için veri servisi yok. Takvim açıklanınca Genel Takvim'e YKS günlerini ekleyin.",
    "yokatlas": "YÖK Atlas verisi zaten otomatik: bölüm penceresi açıldıkça çekilir ve 7 günde bir yenilenir.",
}


def neden(kod: str) -> str:
    if kod in NEDENLER:
        return NEDENLER[kod]
    return ("Bu veri dış bir kaynaktan çekilmiyor (sistemin kendi pipeline'ı ya da içerik ekranlarıyla güncellenir). "
            "\"Nasıl güncellenir?\" adımlarını izleyin.")


def cek(db: Session, kod: str, yon=None) -> dict:
    """Başarılıysa {"mesaj", ...}; değilse CekmeHatasi (yöneticiye gösterilecek metin)."""
    f = CEKICILER.get(kod)
    if f is None:
        raise CekmeHatasi("Otomatik çekme yok: " + neden(kod))
    try:
        return f(db, yon)
    except CekmeHatasi:
        db.rollback()
        raise
    except Exception as e:   # beklenmeyen: veri yazılmaz, kısa teknik bilgiyle bildirilir
        db.rollback()
        raise CekmeHatasi(f"Beklenmeyen hata, veri yazılmadı: {type(e).__name__}: {str(e).splitlines()[0][:200] if str(e) else ''}")


def gece_tufe(db: Session, bugun) -> dict:
    """Gece bakımı: ayın 4'ünden sonra bir önceki ayın TÜFE'si sistemde yoksa otomatik çekmeyi dener."""
    y, a = bugun.year, bugun.month - (1 if bugun.day >= 4 else 2)
    while a < 1:
        y, a = y - 1, a + 12
    beklenen = f"{y}-{a:02d}"
    son = db.execute(text("SELECT MAX(donem) FROM tufe_endeksi")).scalar()
    if son and son >= beklenen:
        return {"atlandi": f"güncel (son ay {son})"}
    try:
        return {"mesaj": tufe_cek(db)["mesaj"]}
    except CekmeHatasi as e:
        db.rollback()
        return {"hata": str(e)}
