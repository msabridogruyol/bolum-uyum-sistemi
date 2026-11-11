# -*- coding: utf-8 -*-
"""
[2026-11-11] Toplu hesap açma (öğrenci + okul yetkilisi) ve hoş geldin e-postaları.

Kullanıcı isteği: "toplu mail girilecek, isim soy isim ve görevi ve okulu girilecek. Çıktı olarak hesaplar oluşacak ve
bu kişilerin geçici şifrelerinin bulunduğu Excel'i ileteceğiz. Bu kişilerin her birine mail gönderimi olsun: hoş geldiniz,
sisteminiz aktif hale getirilmiştir … Yetkili için farklı, öğrenciler için farklı tarz; tek tuşla belirlenen okulun
tamamına gitmeli." + "Excel'in içeriği de Filizyol'a özgü olsun, amblemi, kısa açıklaması."

  GET  /yonetim/toplu-hesap/sablon                 markalı Excel şablonu: Ad Soyad · E-posta · Görev · Okul · Sınıf · Şube
  POST /yonetim/toplu-hesap/onizle                 {dosya_adi, icerik_base64, okul_id?} → satır satır ne olacağı
  POST /yonetim/toplu-hesap/olustur                {…, eposta_gonder} → hesaplar + markalı giriş bilgileri Excel'i
  GET  /yonetim/toplu-hesap/hosgeldin/ozet         ?okul_id= → öğrenci / yetkili sayısı, e-posta gönderilmiş olanlar
  GET  /yonetim/toplu-hesap/hosgeldin/onizleme     ?tur=ogrenci|yetkili → e-postanın örnek görünümü
  POST /yonetim/toplu-hesap/hosgeldin              {okul_id, kime: hepsi|ogrenci|yetkili, yalniz_gonderilmemis}
  GET  /yonetim/toplu-hesap/hosgeldin/durum/{is_id}

Kurallar
  * Görev "Öğrenci" (ya da boş) → öğrenci hesabı; başka her görev → okul yetkilisi, görev yazısı unvan olur
    ("Okul yetkilisi" / "Yetkili" yazılırsa unvan boş kalır).
  * Okul sütunu okul adına göre eşlenir (Türkçe karakter / büyük-küçük harf farkı önemsiz; tek bir okulu içeren kısa ad da
    olur). Boşsa ekranda seçilen okul kullanılır.
  * Okul yetkilisi yalnızca kendi okuluna ve yalnızca öğrenci hesabı açar; yetkili hesabını süper admin açar
    (okul_yonetimi.yetkili_ekle ile aynı kural). Hoş geldin e-postasını da yalnızca kendi okulunun öğrencilerine gönderir.
  * Kayıtlı bir e-posta yeniden açılmaz ve değiştirilmez (bilgi güncelleme: Okul paneli › Excel ile toplu).
  * Geçici şifre ilk girişte değiştirilir. E-postada geçici şifre yalnızca hesap hâlâ geçici şifredeyse yer alır;
    şifresini değiştirmiş kişiye "kendi şifren / Şifremi unuttum" yazılır.
  * Gönderim kaydı: öğrencide hesap olay kaydı (hosgeldin_epostasi), yetkilide denetim kaydı. "Yalnız gönderilmemiş"
    seçeneği bu kayıtlara bakar.
"""
from __future__ import annotations

import logging
import os
import re
import threading
import time
import uuid
from collections import Counter

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_yonetimi import (EN_FAZLA_SATIR, SINIFLAR, _EPOSTA, _dosyadan_satirlar, _hizli_hash, _norm,
                                   _satirlari_coz, _unvan)
from app.core.config import settings
from app.core.database import get_db
from app.core.gizli_metin import coz, sifrele
from app.core.hesap_yonetimi import denetim_yaz, gecici_sifre, olay_yaz, simdi, yapan_etiketi
from app.core.zaman import simdi_tr
from app.models import AdminKullanici, AuditLog, Ogrenci, OgrenciHesapOlayi, Okul
from app.schemas.girdi import AD_SOYAD_EN_FAZLA, GirdiModeli

log = logging.getLogger(__name__)
router = APIRouter(prefix="/yonetim/toplu-hesap", tags=["Toplu hesap"])

OGRENCI_GOREVLERI = {"", "ogrenci", "ogr", "student"}
GENEL_YETKILI = {"yetkili", "okulyetkilisi", "okulyetkili"}
KOLONLAR = ["Ad Soyad", "E-posta", "Görev", "Okul", "Sınıf", "Şube"]


# ----------------------------------------------------------------------------- yardımcılar
def _giris_adresi() -> str:
    site = (settings.FRONTEND_URL or "").rstrip("/")
    return f"{site}/giris" if site else "/giris"


def _okul_eslestir(okullar: list[Okul], ad: str) -> tuple[Okul | None, str | None]:
    n = _norm(ad)
    if not n:
        return None, None
    tam = [o for o in okullar if _norm(o.ad) == n]
    if len(tam) == 1:
        return tam[0], None
    if len(n) >= 4:
        icerir = [o for o in okullar if n in _norm(o.ad)]
        if len(icerir) == 1:
            return icerir[0], None
        if len(icerir) > 1:
            return None, f"Okul adı birden fazla okula uyuyor ('{ad}') — tam adını yazın"
    return None, f"Okul bulunamadı ('{ad}')"


def _tur(gorev: str) -> tuple[str, str | None]:
    n = _norm(gorev)
    if n in OGRENCI_GOREVLERI:
        return "ogrenci", None
    return "yetkili", (None if n in GENEL_YETKILI else _unvan(gorev))


def _cozumle(db: Session, yon: AdminKullanici, dosya_adi: str, icerik_b64: str, okul_id: int | None) -> list[dict]:
    satirlar = _satirlari_coz(_dosyadan_satirlar(dosya_adi, icerik_b64))
    okullar = db.query(Okul).all()
    secili = None
    if yon.rol == "okul_yetkilisi":
        secili = db.get(Okul, yon.okul_id)
    elif okul_id:
        secili = db.get(Okul, okul_id)
        if secili is None:
            raise HTTPException(status_code=404, detail="Seçilen okul bulunamadı.")
    gorulen = Counter(s["email"].lower() for s in satirlar if s["email"])
    epostalar = list(gorulen)
    kayitli = set()
    if epostalar:
        kayitli |= {e.lower() for (e,) in db.query(Ogrenci.email).filter(func.lower(Ogrenci.email).in_(epostalar)).all()}
        kayitli |= {e.lower() for (e,) in db.query(AdminKullanici.email).filter(func.lower(AdminKullanici.email).in_(epostalar)).all()}
    for s in satirlar:
        hatalar, uyarilar = [], []
        s["tur"], s["unvan"] = _tur(s.get("gorev", ""))
        s["kayitli"] = False
        if not s.get("gorev"):
            uyarilar.append("Görev boş — öğrenci olarak açılacak")
        # okul
        okul, okul_hata = _okul_eslestir(okullar, s.get("okul", "")) if s.get("okul") else (None, None)
        if okul_hata:
            hatalar.append(okul_hata)
        elif yon.rol == "okul_yetkilisi":
            if okul is not None and okul.id != yon.okul_id:
                hatalar.append("Yalnızca kendi okulunuza hesap açabilirsiniz")
            okul = secili
        elif okul is None:
            okul = secili
            if okul is None:
                hatalar.append("Okul yazılmamış ve ekranda okul seçilmedi")
        s["okul_id"], s["okul_ad"] = (okul.id, okul.ad) if okul else (None, s.get("okul") or None)
        # kişi
        if len(s["ad_soyad"]) < 3:
            hatalar.append("Ad soyad eksik")
        elif len(s["ad_soyad"]) > AD_SOYAD_EN_FAZLA:
            hatalar.append(f"Ad soyad en fazla {AD_SOYAD_EN_FAZLA} karakter olabilir")
        e = s["email"].lower()
        if not e:
            hatalar.append("E-posta eksik")
        elif not _EPOSTA.match(s["email"]):
            hatalar.append("E-posta geçersiz")
        elif gorulen[e] > 1:
            hatalar.append("E-posta dosyada birden fazla kez geçiyor")
        elif e.endswith("@ornek.com"):
            hatalar.append("Şablondaki örnek satır — silin")
        elif e in kayitli:
            s["kayitli"] = True
            uyarilar.append("Bu e-postayla hesap zaten var — yeniden açılmaz")
        if s.get("sifre") and len(s["sifre"]) < 6:
            hatalar.append("Şifre en az 6 karakter olmalı")
        if s["tur"] == "yetkili":
            if yon.rol != "super_admin":
                hatalar.append("Okul yetkilisi hesabını yalnızca süper admin açabilir")
            s["sinif"] = s["sube"] = None
        elif not s["sinif"]:
            uyarilar.append("Sınıf boş — öğrenci ilk girişte seçer")
        elif s["sinif"] not in SINIFLAR:
            uyarilar.append(f"Sınıf tanınmadı ('{s['sinif']}'), olduğu gibi kaydedilecek")
        s["hata"] = "; ".join(hatalar) or None
        s["uyari"] = "; ".join(uyarilar) or None
    return satirlar


def _ozet(satirlar: list[dict]) -> dict:
    acilacak = [s for s in satirlar if not s["hata"] and not s["kayitli"]]
    return {"toplam": len(satirlar), "hatali": sum(1 for s in satirlar if s["hata"]),
            "kayitli": sum(1 for s in satirlar if not s["hata"] and s["kayitli"]),
            "acilacak_ogrenci": sum(1 for s in acilacak if s["tur"] == "ogrenci"),
            "acilacak_yetkili": sum(1 for s in acilacak if s["tur"] == "yetkili"),
            "okullar": sorted({s["okul_ad"] for s in acilacak if s["okul_ad"]})}


def _disari(s: dict) -> dict:
    return {k: s.get(k) for k in ("satir", "ad_soyad", "email", "gorev", "tur", "unvan", "okul_id", "okul_ad", "sinif", "sube",
                                  "kayitli", "hata", "uyari")}


def _giris_xlsx(kayitlar: list[dict], baslik_okul: str) -> str:
    from app.core.filizyol_excel import GIRIS_ACIKLAMASI, GIZLILIK, markali_xlsx_b64
    sirali = sorted(kayitlar, key=lambda k: (k["okul_ad"] or "", k["tur"] != "yetkili", k.get("sinif") or "", k.get("sube") or "",
                                             k["ad_soyad"]))
    return markali_xlsx_b64(
        "Hesap Giriş Bilgileri", ["Ad Soyad", "Görev", "Okul", "Sınıf", "Şube", "E-posta", "Geçici Şifre"],
        [[k["ad_soyad"], k.get("gorev") or ("Öğrenci" if k["tur"] == "ogrenci" else "Okul yetkilisi"), k["okul_ad"] or "",
          k.get("sinif") or "", k.get("sube") or "", k["email"], k["gecici_sifre"]] for k in sirali],
        alt_baslik=f"{baslik_okul} · {simdi_tr():%d.%m.%Y %H:%M} · {len(kayitlar)} hesap",
        aciklama=[GIRIS_ACIKLAMASI[0], GIRIS_ACIKLAMASI[1],
                  f"1) Giriş adresi: {_giris_adresi()}  ·  Öğrenciler ve okul yetkilileri aynı giriş ekranını kullanır; "
                  "okul yetkilileri giriş yapınca okul paneline yönlendirilir.",
                  "2) Geçici şifre yalnızca ilk giriş içindir; ilk girişte kişi kendi şifresini belirler. Unutulursa giriş "
                  "ekranındaki \"Şifremi unuttum\" kullanılır.",
                  "3) Hoş geldin e-postası seçildiyse herkese giriş bilgileri ayrıca e-postayla gönderilir."],
        sayfa_adi="Giriş Bilgileri", gizlilik=GIZLILIK, genislikler={"Geçici Şifre": 16})


# ----------------------------------------------------------------------------- şablon / önizleme / oluşturma
@router.get("/sablon")
def sablon(yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.core.filizyol_excel import markali_xlsx_b64
    ornek = [["Ayşe Yılmaz", "ayse.yilmaz@ornek.com", "Öğrenci", "", "11", "A"],
             ["Mehmet Demir", "mehmet.demir@ornek.com", "Öğrenci", "", "12", "B"]]
    if yon.rol == "super_admin":
        ornek.append(["Zeynep Kaya", "zeynep.kaya@ornek.com", "Rehber Öğretmen", "", "", ""])
    aciklama = [
        "Filizyol toplu hesap açma şablonu. Örnek satırları silip kişileri yazın; her satır bir hesap açar.",
        "Görev: \"Öğrenci\" yazılan satırlar öğrenci hesabı olur." + (
            " Başka bir görev (ör. Rehber Öğretmen, Müdür Yardımcısı) yazılırsa okul yetkilisi hesabı açılır ve görev unvan olarak kaydedilir."
            if yon.rol == "super_admin" else " Okul yetkilisi hesaplarını süper admin açar."),
        "Okul: boş bırakılırsa ekranda seçtiğiniz okul kullanılır" + (
            "; birden fazla okul için okul adını yazın." if yon.rol == "super_admin" else "; hesaplar kendi okulunuza açılır."),
        "Sınıf (9, 10, 11, 12 veya Mezun) ve şube yalnızca öğrenciler içindir ve isteğe bağlıdır.",
        "Başlık satırını ve sütun adlarını değiştirmeyin; üstteki Filizyol satırları yüklemede atlanır.",
    ]
    return {"dosya_adi": "filizyol_toplu_hesap_sablonu.xlsx",
            "icerik_base64": markali_xlsx_b64("Toplu Hesap Açma Şablonu", KOLONLAR, ornek, aciklama=aciklama, sayfa_adi="Hesaplar",
                                              genislikler={"Ad Soyad": 24, "E-posta": 30, "Görev": 20, "Okul": 30})}


class DosyaIstek(GirdiModeli):
    dosya_adi: str
    icerik_base64: str = Field(max_length=20000000)
    okul_id: int | None = None


class OlusturIstek(DosyaIstek):
    eposta_gonder: bool = False


@router.post("/onizle")
def onizle(istek: DosyaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    satirlar = _cozumle(db, yon, istek.dosya_adi, istek.icerik_base64, istek.okul_id)
    return {"satirlar": [_disari(s) for s in satirlar], "ozet": _ozet(satirlar)}


@router.post("/olustur")
def olustur(istek: OlusturIstek, arka_plan: BackgroundTasks, db: Session = Depends(get_db),
            yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    """Dosya sunucuda yeniden çözülür ve doğrulanır (önizlemedeki tablo istemciden geri alınmaz)."""
    satirlar = _cozumle(db, yon, istek.dosya_adi, istek.icerik_base64, istek.okul_id)
    acilacak = [s for s in satirlar if not s["hata"] and not s["kayitli"]]
    if not acilacak:
        raise HTTPException(status_code=400, detail="Açılacak yeni hesap yok (satırlar hatalı ya da hesaplar zaten kayıtlı).")
    if len(acilacak) > EN_FAZLA_SATIR:
        raise HTTPException(status_code=400, detail=f"Tek seferde en fazla {EN_FAZLA_SATIR} hesap.")
    from concurrent.futures import ThreadPoolExecutor
    for s in acilacak:
        s["gecici_sifre"] = s.get("sifre") or gecici_sifre()
    with ThreadPoolExecutor(max_workers=4) as havuz:
        karmalar = list(havuz.map(lambda x: _hizli_hash(x["gecici_sifre"]), acilacak))
    yapan, an, yid = yapan_etiketi(yon), simdi(), yon.id
    alicilar, okul_sayac = [], Counter()
    for s, karma in zip(acilacak, karmalar):
        if s["tur"] == "ogrenci":
            o = Ogrenci(id=uuid.uuid4(), ad_soyad=s["ad_soyad"], email=s["email"], sifre_hash=karma, sinif=s["sinif"],
                        sube=s["sube"], okul_id=s["okul_id"], okul=s["okul_ad"], sifre_degistirmeli=True,
                        olusturulma_zamani=an, gecici_sifre_sifreli=sifrele(s["gecici_sifre"]),
                        ogrenci_no=(s.get("ogrenci_no") or None))
            db.add(o)
            olay_yaz(db, o.id, "hesap_acildi", f"{s['okul_ad']} — toplu hesap açma", yapan)
            alicilar.append(("ogrenci", o.id))
        else:
            y = AdminKullanici(id=uuid.uuid4(), ad_soyad=s["ad_soyad"], email=s["email"], sifre_hash=karma, rol="okul_yetkilisi",
                               okul_id=s["okul_id"], aktif_mi=True, sifre_degistirmeli=True, olusturulma_zamani=an,
                               gecici_sifre_sifreli=sifrele(s["gecici_sifre"]), unvan=s["unvan"])
            db.add(y)
            denetim_yaz(db, yon, "okul_yetkilisi_ekle", "admin_kullanicilar", y.id, f"{s['ad_soyad']} <{s['email']}>", s["okul_id"])
            alicilar.append(("yetkili", y.id))
        okul_sayac[(s["okul_id"], s["tur"])] += 1
    for okul_id in {k[0] for k in okul_sayac}:
        denetim_yaz(db, yon, "toplu_hesap_ac", "hesaplar", okul_id,
                    f"{okul_sayac[(okul_id, 'ogrenci')]} öğrenci, {okul_sayac[(okul_id, 'yetkili')]} okul yetkilisi hesabı açıldı"
                    + (" · hoş geldin e-postası gönderiliyor" if istek.eposta_gonder else ""), okul_id)
    # aynı okula süren bir gönderim varsa (409) hiçbir hesap yazılmadan döner
    is_id = _is_baslat(alicilar, yon, okul_idleri={k[0] for k in okul_sayac}) if istek.eposta_gonder else None
    db.commit()
    if is_id:
        arka_plan.add_task(_arka_planda_gonder, is_id, alicilar, yid, yapan)
    okul_adlari = sorted({s["okul_ad"] for s in acilacak})
    baslik_okul = okul_adlari[0] if len(okul_adlari) == 1 else f"{len(okul_adlari)} okul"
    return {"ozet": _ozet(satirlar), "olusturulan": len(acilacak),
            "atlanan": [_disari(s) for s in satirlar if s["hata"] or s["kayitli"]], "eposta_is_id": is_id,
            "dosya_adi": f"filizyol_giris_bilgileri_{re.sub(r'[^0-9A-Za-zÇĞİÖŞÜçğıöşü]+', '_', baslik_okul)}_{simdi_tr():%Y%m%d_%H%M}.xlsx",
            "icerik_base64": _giris_xlsx(acilacak, baslik_okul)}


# ----------------------------------------------------------------------------- hoş geldin e-postası
ISLER: dict[str, dict] = {}          # süreç içi ilerleme (tek süreç; kalıcı kayıt hesap olay / denetim kayıtlarında)
_KILIT = threading.Lock()


def _bekleme() -> float:
    """Gönderimler arası bekleme (sn). Gmail gibi sağlayıcıların dakikalık sınırına takılmamak için; testte 0."""
    if os.environ.get("TEST_EPOSTA_KAYDI") == "1":
        return 0.0
    try:
        return max(0.0, float(os.environ.get("HOSGELDIN_EPOSTA_ARALIK_SN", "0.6")))
    except ValueError:
        return 0.6


def _is_baslat(alicilar: list[tuple[str, uuid.UUID]], yon: AdminKullanici, okul_idleri: set) -> str:
    with _KILIT:
        for i in ISLER.values():
            if not i["bitti"] and i["okullar"] & okul_idleri:
                raise HTTPException(status_code=409, detail="Bu okula gönderim zaten sürüyor; bitince tekrar deneyin.")
        is_id = uuid.uuid4().hex[:12]
        ISLER[is_id] = {"toplam": len(alicilar), "gonderilen": 0, "hatali": 0, "bitti": False, "okullar": set(okul_idleri),
                        "baslangic": simdi().isoformat(), "yapan": str(yon.id), "hatalilar": []}
        if len(ISLER) > 50:   # eski biten işler
            for k in [k for k, v in ISLER.items() if v["bitti"]][:len(ISLER) - 50]:
                ISLER.pop(k, None)
    return is_id


def _oturum_ac() -> Session:
    from app.core.database import SessionLocal
    return SessionLocal()


def _arka_planda_gonder(is_id: str, alicilar: list[tuple[str, uuid.UUID]], yapan_id, yapan: str) -> None:
    db = _oturum_ac()
    try:
        hosgeldin_gonder(db, is_id, alicilar, yapan_id, yapan)
    except Exception as hata:   # arka plan işi hiçbir hatayı dışarı sızdırmaz
        log.error("Hoş geldin e-postası işi durdu (%s): %s: %s", is_id, type(hata).__name__, hata)
    finally:
        if is_id in ISLER:
            ISLER[is_id]["bitti"] = True
        db.close()


def hosgeldin_gonder(db: Session, is_id: str | None, alicilar: list[tuple[str, uuid.UUID]], yapan_id, yapan: str) -> dict:
    from app.core import eposta_servisi as ep
    adres, bekle = _giris_adresi(), _bekleme()
    okul_adlari = {o.id: o.ad for o in db.query(Okul).all()}
    from app.core.paketler import okul_modulleri
    paket: dict = {}   # okul_id → modüller (e-postada yalnızca okulun paketindeki özellikler anılır)
    sayac = {"gonderilen": 0, "hatali": 0}
    for n, (tur, kid) in enumerate(alicilar):
        k = db.get(Ogrenci if tur == "ogrenci" else AdminKullanici, kid)
        if k is None:
            continue
        sifre = coz(k.gecici_sifre_sifreli) if k.sifre_degistirmeli and k.gecici_sifre_sifreli else None
        okul = okul_adlari.get(k.okul_id)
        if k.okul_id not in paket:
            paket[k.okul_id] = okul_modulleri(db, k.okul_id) if k.okul_id else None
        if tur == "ogrenci":
            konu, html, metin = ep.ogrenci_hosgeldin_epostasi(k.ad_soyad, okul, k.email, sifre, adres, paket[k.okul_id])
        else:
            konu, html, metin = ep.yetkili_hosgeldin_epostasi(k.ad_soyad, okul, getattr(k, "unvan", None), k.email, sifre, adres,
                                                          paket[k.okul_id])
        basarili = ep.eposta_gonder(k.email, konu, html, metin)
        sayac["gonderilen" if basarili else "hatali"] += 1
        islem = "hosgeldin_epostasi" if basarili else "hosgeldin_epostasi_hata"
        aciklama = ("Hoş geldin e-postası gönderildi" if basarili else "Hoş geldin e-postası gönderilemedi") + \
                   (" (geçici şifreyle)" if sifre else "")
        if tur == "ogrenci":
            olay_yaz(db, k.id, islem, aciklama, yapan)
        else:
            db.add(AuditLog(admin_id=yapan_id, islem=islem, hedef_tablo="admin_kullanicilar", hedef_id=str(k.id),
                            gerekce=f"{k.ad_soyad} <{k.email}> — {aciklama}", okul_id=k.okul_id, yapan_ad=yapan.split(" (")[0],
                            zaman=simdi()))
        if is_id in ISLER:
            ISLER[is_id]["gonderilen"], ISLER[is_id]["hatali"] = sayac["gonderilen"], sayac["hatali"]
            if not basarili and len(ISLER[is_id]["hatalilar"]) < 200:
                ISLER[is_id]["hatalilar"].append(k.email)
        if n % 20 == 19:
            db.commit()
        if bekle and n < len(alicilar) - 1:
            time.sleep(bekle)
    db.commit()
    if is_id in ISLER:
        ISLER[is_id]["bitti"] = True
    return sayac


def _gonderilmis(db: Session, okul_id: int) -> tuple[set, set]:
    ogr = {i for (i,) in db.query(OgrenciHesapOlayi.ogrenci_id).join(Ogrenci, Ogrenci.id == OgrenciHesapOlayi.ogrenci_id)
           .filter(Ogrenci.okul_id == okul_id, OgrenciHesapOlayi.olay == "hosgeldin_epostasi").distinct().all()}
    yet = {uuid.UUID(h) for (h,) in db.query(AuditLog.hedef_id).filter(AuditLog.islem == "hosgeldin_epostasi",
                                                                         AuditLog.okul_id == okul_id).distinct().all()}
    return ogr, yet


def _okul_yetkisi(db: Session, yon: AdminKullanici, okul_id: int) -> Okul:
    if yon.rol == "okul_yetkilisi" and okul_id != yon.okul_id:
        raise HTTPException(status_code=403, detail="Yalnızca kendi okulunuza gönderebilirsiniz.")
    okul = db.get(Okul, okul_id)
    if okul is None:
        raise HTTPException(status_code=404, detail="Okul bulunamadı.")
    return okul


def _kisiler(db: Session, okul_id: int, kime: str) -> tuple[list[Ogrenci], list[AdminKullanici]]:
    ogr = db.query(Ogrenci).filter(Ogrenci.okul_id == okul_id).filter(Ogrenci.test_hesabi.isnot(True)).all() \
        if kime in ("hepsi", "ogrenci") else []
    yet = db.query(AdminKullanici).filter(AdminKullanici.okul_id == okul_id, AdminKullanici.rol == "okul_yetkilisi",
                                          AdminKullanici.aktif_mi.is_(True)).filter(AdminKullanici.test_hesabi.isnot(True)).all() \
        if kime in ("hepsi", "yetkili") else []
    return ogr, yet


@router.get("/hosgeldin/ozet")
def hosgeldin_ozet(okul_id: int = Query(...), db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.core.eposta_servisi import eposta_yapilandirildi_mi
    okul = _okul_yetkisi(db, yon, okul_id)
    ogr, yet = _kisiler(db, okul_id, "hepsi" if yon.rol == "super_admin" else "ogrenci")
    g_ogr, g_yet = _gonderilmis(db, okul_id)
    calisan = next(({"is_id": k, **{a: v[a] for a in ("toplam", "gonderilen", "hatali")}} for k, v in ISLER.items()
                    if not v["bitti"] and okul_id in v["okullar"]), None)
    return {"okul": okul.ad, "eposta_hazir": eposta_yapilandirildi_mi(), "yetkili_gonderebilir": yon.rol == "super_admin",
            "ogrenci": {"toplam": len(ogr), "gonderilmis": sum(1 for o in ogr if o.id in g_ogr),
                        "gecici_sifreli": sum(1 for o in ogr if o.sifre_degistirmeli)},
            "yetkili": {"toplam": len(yet), "gonderilmis": sum(1 for y in yet if y.id in g_yet),
                        "gecici_sifreli": sum(1 for y in yet if y.sifre_degistirmeli)},
            "calisan_is": calisan}


@router.get("/hosgeldin/onizleme")
def hosgeldin_onizleme(tur: str = Query("ogrenci", pattern="^(ogrenci|yetkili)$"), okul_id: int | None = None,
                       db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.core import eposta_servisi as ep
    okul = (db.get(Okul, okul_id) if okul_id else None) or (db.get(Okul, yon.okul_id) if yon.okul_id else None)
    ad = okul.ad if okul else "Örnek Lisesi"
    from app.core.paketler import TUMU, okul_modulleri
    moduller = okul_modulleri(db, okul.id) if okul else TUMU   # okul seçilmediyse tüm paket örneği
    if tur == "ogrenci":
        konu, html, _ = ep.ogrenci_hosgeldin_epostasi("Ayşe Yılmaz", ad, "ayse.yilmaz@ornek.com", "kemr-4827", _giris_adresi(), moduller)
    else:
        konu, html, _ = ep.yetkili_hosgeldin_epostasi("Zeynep Kaya", ad, "Rehber Öğretmen", "zeynep.kaya@ornek.com", "kemr-4827",
                                                      _giris_adresi(), moduller)
    return {"konu": konu, "html": html}


class HosgeldinIstek(GirdiModeli):
    okul_id: int
    kime: str = Field("hepsi", pattern="^(hepsi|ogrenci|yetkili)$")
    yalniz_gonderilmemis: bool = True


@router.post("/hosgeldin")
def hosgeldin(istek: HosgeldinIstek, arka_plan: BackgroundTasks, db: Session = Depends(get_db),
              yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.core.eposta_servisi import eposta_yapilandirildi_mi
    okul = _okul_yetkisi(db, yon, istek.okul_id)
    kime = istek.kime
    if yon.rol != "super_admin":
        if kime == "yetkili":
            raise HTTPException(status_code=403, detail="Okul yetkililerine hoş geldin e-postasını süper admin gönderir.")
        kime = "ogrenci"
    if not eposta_yapilandirildi_mi():
        raise HTTPException(status_code=400, detail="E-posta gönderimi yapılandırılmamış (Render ortam değişkenleri).")
    ogr, yet = _kisiler(db, istek.okul_id, kime)
    if istek.yalniz_gonderilmemis:
        g_ogr, g_yet = _gonderilmis(db, istek.okul_id)
        ogr, yet = [o for o in ogr if o.id not in g_ogr], [y for y in yet if y.id not in g_yet]
    alicilar = [("yetkili", y.id) for y in sorted(yet, key=lambda y: y.ad_soyad)] + \
               [("ogrenci", o.id) for o in sorted(ogr, key=lambda o: (o.sinif or "", o.sube or "", o.ad_soyad))]
    if not alicilar:
        raise HTTPException(status_code=400, detail="Gönderilecek kişi yok" + (" (hepsine daha önce gönderilmiş)."
                                                                               if istek.yalniz_gonderilmemis else "."))
    is_id = _is_baslat(alicilar, yon, {istek.okul_id})
    denetim_yaz(db, yon, "hosgeldin_toplu", "okullar", okul.id,
                f"{len(yet)} okul yetkilisi, {len(ogr)} öğrenciye hoş geldin e-postası"
                + (" (yalnız gönderilmemişler)" if istek.yalniz_gonderilmemis else ""), okul.id)
    yid, yapan = yon.id, yapan_etiketi(yon)   # commit sonrası nesneye dokunulmaz (oturum yeniden açılmasın)
    db.commit()
    arka_plan.add_task(_arka_planda_gonder, is_id, alicilar, yid, yapan)
    return {"is_id": is_id, "toplam": len(alicilar), "ogrenci": len(ogr), "yetkili": len(yet)}


@router.get("/hosgeldin/durum/{is_id}")
def hosgeldin_durum(is_id: str, yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    i = ISLER.get(is_id)
    if i is None:
        raise HTTPException(status_code=404, detail="Gönderim bulunamadı (sunucu yeniden başlamış olabilir; özetten kontrol edin).")
    if yon.rol != "super_admin" and i["yapan"] != str(yon.id):
        raise HTTPException(status_code=403, detail="Bu gönderimi siz başlatmadınız.")
    return {k: i[k] for k in ("toplam", "gonderilen", "hatali", "bitti", "baslangic", "hatalilar")}
