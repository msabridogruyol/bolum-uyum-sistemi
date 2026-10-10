# -*- coding: utf-8 -*-
"""
[2026-10-10] İş Hayatı Verileri — süper admin yönetimi (pages/admin/IsHayatiVerileriSayfasi.jsx).

Özet
  GET    /admin/is-hayati/ozet                         — tablo sayıları, veri yılları, güncel asgari ücret, ISCO grupları, gider kalemleri
Dosya yükleme (Excel .xlsx / CSV, base64 JSON — okul öğrenci yüklemesiyle aynı kalıp)
  POST   /admin/is-hayati/dosya/oku                    — {tur, dosya_adi, icerik_base64, baslik_satiri?} → başlıklar, örnek satırlar, otomatik sütun önerisi
  POST   /admin/is-hayati/istihdam/onizle              — sütun eşleştirmesiyle satırlar + program adı → bölüm eşleşmesi (otomatik / öneri / yok)
  POST   /admin/is-hayati/istihdam/kaydet              — {veri_yili, kaynak, satirlar[], ayni_yili_degistir} (kaynak + yıl zorunlu)
  POST   /admin/is-hayati/kazanc/onizle                — meslek grubu (ISCO) + brüt kazanç (aylık / yıllık)
  POST   /admin/is-hayati/kazanc/kaydet                — {veri_yili, kaynak, asgari_brut_o_yil, satirlar[]}
  GET    /admin/is-hayati/yuklemeler                   — yükleme geçmişi
  DELETE /admin/is-hayati/yuklemeler/{id}              — yüklemeyi geri al (istihdam satırları birlikte silinir)
Elle düzenleme (tablo: istihdam_gostergeleri, kazanc_meslek_gruplari, kamu_maaslari, asgari_ucret, yasam_giderleri)
  GET    /admin/is-hayati/kayit/{tablo}?q=&veri_yili=
  POST   /admin/is-hayati/kayit/{tablo}                — {veri: {...}}
  PUT    /admin/is-hayati/kayit/{tablo}/{id}           — {veri: {...}} (yalnızca gönderilen alanlar)
  DELETE /admin/is-hayati/kayit/{tablo}/{id}
Meslek → ISCO eşleştirmesi
  GET    /admin/is-hayati/meslek-isco?q=&filtre=       — filtre: hepsi | bos | orta | yuksek | elle | eksik
  PUT    /admin/is-hayati/meslek-isco                  — {meslek_adi, isco_kodu|null}
  POST   /admin/is-hayati/meslek-isco/json-yukle       — app/data/meslek_isco.json'daki eksik meslekleri ekle (var olanlara dokunmaz)

Her değişiklik denetim kaydına yazılır (hesap_yonetimi.denetim_yaz).
"""
from __future__ import annotations

import json
import re
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_super_admin
from app.api.okul_yonetimi import _dosyadan_satirlar
from app.core import is_hayati_servisi as ihs
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.yokatlas_servisi import _normalize
from app.models import AdminKullanici

router = APIRouter(prefix="/admin/is-hayati", tags=["Admin — İş Hayatı Verileri"])

# ---------------------------------------------------------------- dosya okuma ve sütun önerisi

ALANLAR = {
    "istihdam": [
        {"kod": "program_adi", "ad": "Program / bölüm adı", "zorunlu": True},
        {"kod": "duzey", "ad": "Düzey (lisans / önlisans)", "zorunlu": False},
        {"kod": "istihdam_orani", "ad": "İstihdam oranı (%)", "zorunlu": False},
        {"kod": "is_bulma_suresi_ay", "ad": "İş bulma süresi (ay)", "zorunlu": False},
        {"kod": "alan_uyum_orani", "ad": "Alanında çalışma / uyum oranı (%)", "zorunlu": False},
        {"kod": "kazanc_grubu", "ad": "Kazanç grubu (Çok yüksek … Çok düşük)", "zorunlu": False},
        {"kod": "kazanc_tl", "ad": "Kazanç (TL)", "zorunlu": False},
    ],
    "kazanc": [
        {"kod": "ad", "ad": "Meslek grubu adı", "zorunlu": True},
        {"kod": "isco_kodu", "ad": "Meslek grubu kodu (ISCO-08, 1–2 hane; boşsa addaki rakamdan bulunur)", "zorunlu": False},
        {"kod": "brut", "ad": "Ortalama brüt kazanç (TL)", "zorunlu": True},
    ],
}
# Başlık anahtar kelimeleri (Türkçe-normalize, boşluksuz) — ilk eşleşen sütun önerilir
_IPUCU = {
    "program_adi": ["programadi", "program", "bolumadi", "bolum", "alanadi", "birim"],
    "duzey": ["duzey", "ogrenimduzeyi", "egitimduzeyi", "derece", "lisansonlisans"],
    "istihdam_orani": ["istihdamorani", "istihdam"],
    "is_bulma_suresi_ay": ["isbulmasuresi", "ilkisbulma", "isbulma", "sure"],
    "alan_uyum_orani": ["alanuyum", "alanindacalis", "alanilecalis", "uyum", "iliskili"],
    "kazanc_grubu": ["kazancgrubu", "kazancduzeyi", "gelirgrubu", "kazanc", "gelir"],
    "kazanc_tl": ["kazanctl", "ortalamakazanc", "ucret", "maas"],
    "isco_kodu": ["isco", "meslekkodu", "kod"],
    "ad": ["meslekgrubu", "meslek", "ad"],
    "brut": ["brutkazanc", "ortalamabrut", "brut", "kazanc", "ucret"],
}


def _bn(v) -> str:
    return re.sub(r"[^a-z0-9]", "", _normalize(str(v or "")))


class DosyaIstek(BaseModel):
    tur: str = Field(pattern="^(istihdam|kazanc)$")
    dosya_adi: str = Field(max_length=200)
    icerik_base64: str
    baslik_satiri: int | None = Field(None, ge=0, le=50)


def _baslik_bul(satirlar: list[list], tur: str) -> int:
    """İlk 20 satırda en çok anahtar kelime içeren satır (TÜİK tablolarının üstündeki başlık / not satırları atlanır)."""
    kelimeler = [k for a in ALANLAR[tur] for k in _IPUCU.get(a["kod"], [])]
    en, en_puan = 0, -1
    for i, r in enumerate(satirlar[:20]):
        hucre = [_bn(c) for c in r if str(c).strip()]
        if len(hucre) < 2:
            continue
        puan = sum(1 for h in hucre if any(k in h for k in kelimeler)) + 0.01 * sum(1 for c in r if isinstance(c, str) and c.strip())
        if puan > en_puan:
            en, en_puan = i, puan
    return en


def _oneri(basliklar: list[str], tur: str, ornek: list[list]) -> dict:
    kullanilan, oneri = set(), {}
    for alan in ALANLAR[tur]:
        for k in _IPUCU.get(alan["kod"], []):
            bul = next((i for i, b in enumerate(basliklar) if i not in kullanilan and k in _bn(b)), None)
            if bul is not None:
                oneri[alan["kod"]] = bul
                kullanilan.add(bul)
                break
    # kazanç sütunu sayısal ve büyükse TL, metinse grup
    if tur == "istihdam" and "kazanc_grubu" in oneri and "kazanc_tl" not in oneri:
        i = oneri["kazanc_grubu"]
        degerler = [ihs.sayi(r[i]) for r in ornek if i < len(r) and str(r[i]).strip()]
        if degerler and all(d is not None and d > 100 for d in degerler):
            oneri["kazanc_tl"] = oneri.pop("kazanc_grubu")
    return oneri


def _tablo(istek_dosya_adi: str, icerik: str, tur: str, baslik_satiri: int | None):
    satirlar = [r for r in _dosyadan_satirlar(istek_dosya_adi, icerik)]
    satirlar = [list(r) for r in satirlar]
    if not any(any(str(c).strip() for c in r) for r in satirlar):
        raise HTTPException(400, "Dosyada satır bulunamadı.")
    b = _baslik_bul(satirlar, tur) if baslik_satiri is None else baslik_satiri
    if b >= len(satirlar):
        raise HTTPException(400, "Başlık satırı dosyanın dışında.")
    basliklar = [str(c).strip() if str(c).strip() else f"Sütun {i + 1}" for i, c in enumerate(satirlar[b])]
    govde = [r for r in satirlar[b + 1:] if any(str(c).strip() for c in r)]
    return b, basliklar, govde, satirlar


@router.post("/dosya/oku")
def dosya_oku(istek: DosyaIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    b, basliklar, govde, ham = _tablo(istek.dosya_adi, istek.icerik_base64, istek.tur, istek.baslik_satiri)
    return {
        "baslik_satiri": b, "basliklar": [{"i": i, "ad": a} for i, a in enumerate(basliklar)],
        "ust_satirlar": [[str(c) for c in r][:12] for r in ham[:min(b + 1, 20)]],
        "ornek": [[("" if c is None else str(c)) for c in r] for r in govde[:8]], "satir_sayisi": len(govde),
        "oneri": _oneri(basliklar, istek.tur, govde[:30]), "alanlar": ALANLAR[istek.tur],
    }


def _hucre(r: list, i: int | None):
    if i is None or i < 0 or i >= len(r):
        return None
    v = r[i]
    return None if v is None or (isinstance(v, str) and not v.strip()) else v


class OnizleIstek(DosyaIstek):
    eslesme: dict[str, int | None]
    varsayilan_duzey: str | None = Field(None, pattern="^(lisans|onlisans)$")
    tutar_turu: str = Field("aylik", pattern="^(aylik|yillik)$")


_TOPLAM = re.compile(r"^(toplam|genel toplam|turkiye|total|tum programlar)\b")


@router.post("/istihdam/onizle")
def istihdam_onizle(istek: OnizleIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    if istek.tur != "istihdam":
        raise HTTPException(400, "tur: istihdam olmalı.")
    e = istek.eslesme
    if e.get("program_adi") is None:
        raise HTTPException(400, "Program adı sütununu seçin.")
    _, _, govde, _ = _tablo(istek.dosya_adi, istek.icerik_base64, "istihdam", istek.baslik_satiri)
    # oran sütunları 0–1 aralığındaysa yüzdeye çevrilir (sütun bazında karar)
    carpan = {}
    for alan in ("istihdam_orani", "alan_uyum_orani"):
        degerler = [ihs.sayi(_hucre(r, e.get(alan))) for r in govde]
        degerler = [d for d in degerler if d is not None]
        carpan[alan] = 100.0 if degerler and max(degerler) <= 1.0 else 1.0
    adaylar = ihs.bolum_adaylari(db)
    satirlar, uyarilar = [], []
    for no, r in enumerate(govde, start=1):
        ad = _hucre(r, e.get("program_adi"))
        if ad is None or _TOPLAM.match(_normalize(str(ad))):
            continue
        ad = " ".join(str(ad).split())
        hatalar = []
        duzey = ihs.duzey_coz(_hucre(r, e.get("duzey"))) if e.get("duzey") is not None else None
        duzey = duzey or istek.varsayilan_duzey
        s = {"no": no, "program_adi_kaynak": ad, "duzey": duzey}
        for alan in ("istihdam_orani", "alan_uyum_orani"):
            v = ihs.sayi(_hucre(r, e.get(alan)))
            v = None if v is None else round(v * carpan[alan], 2)
            if v is not None and not (0 <= v <= 100):
                hatalar.append(f"{alan}: {v} 0–100 dışında"); v = None
            s[alan] = v
        v = ihs.sayi(_hucre(r, e.get("is_bulma_suresi_ay")))
        if v is not None and not (0 <= v <= 240):
            hatalar.append(f"İş bulma süresi {v} ay olamaz"); v = None
        s["is_bulma_suresi_ay"] = v
        ham_grup = _hucre(r, e.get("kazanc_grubu"))
        s["kazanc_grubu"] = ihs.kazanc_grubu_coz(ham_grup)
        if ham_grup is not None and s["kazanc_grubu"] is None:
            hatalar.append(f"Kazanç grubu tanınmadı: “{ham_grup}”")
        v = ihs.sayi(_hucre(r, e.get("kazanc_tl")))
        s["kazanc_tl"] = v if v is None or v >= 0 else None
        s.update(ihs.program_eslestir(ad, adaylar))
        s["hatalar"] = hatalar
        satirlar.append(s)
    if not satirlar:
        raise HTTPException(400, "Program adı sütununda veri bulunamadı. Başlık satırını ve sütun seçimini kontrol edin.")
    if any(c == 100.0 for c in carpan.values()):
        uyarilar.append("Oran sütunlarındaki değerler 0–1 aralığında olduğu için yüzdeye çevrildi.")
    if not any(s["duzey"] for s in satirlar):
        uyarilar.append("Düzey bilgisi yok: düzey sütunu seçin ya da varsayılan düzeyi belirtin.")
    say = {k: sum(1 for s in satirlar if s["durum"] == k) for k in ("otomatik", "oneri", "yok")}
    return {"satirlar": satirlar, "ozet": {"toplam": len(satirlar), **say, "hatali": sum(1 for s in satirlar if s["hatalar"])},
            "uyarilar": uyarilar, "bolumler": [{"id": b["id"], "ad": b["ad"]} for b in adaylar]}


class IstihdamSatiri(BaseModel):
    program_adi_kaynak: str = Field(min_length=1, max_length=300)
    duzey: str | None = Field(None, pattern="^(lisans|onlisans)$")
    istihdam_orani: float | None = Field(None, ge=0, le=100)
    is_bulma_suresi_ay: float | None = Field(None, ge=0, le=240)
    alan_uyum_orani: float | None = Field(None, ge=0, le=100)
    kazanc_grubu: str | None = Field(None, pattern="^(cok_yuksek|yuksek|orta|dusuk|cok_dusuk)$")
    kazanc_tl: float | None = Field(None, ge=0)
    bolum_id: int | None = None


class IstihdamKaydet(BaseModel):
    dosya_adi: str | None = Field(None, max_length=200)
    veri_yili: int = Field(ge=2000, le=2100)
    kaynak: str = Field(min_length=3, max_length=500)
    ayni_yili_degistir: bool = True
    satirlar: list[IstihdamSatiri] = Field(min_length=1, max_length=20000)


def _yukleme(db: Session, yon: AdminKullanici, tur: str, dosya_adi, satir: int, eslesen: int, eslesmeyen: list, veri_yili, kaynak) -> int:
    return db.execute(text("""INSERT INTO veri_yuklemeleri (tur, dosya_adi, satir, eslesen, eslesmeyen, veri_yili, kaynak, yukleyen)
                              VALUES (:t, :d, :s, :e, CAST(:em AS JSONB), :y, :k, :u) RETURNING id"""),
                      {"t": tur, "d": dosya_adi, "s": satir, "e": eslesen, "em": json.dumps(eslesmeyen[:2000], ensure_ascii=False),
                       "y": veri_yili, "k": kaynak, "u": yon.ad_soyad}).scalar()


@router.post("/istihdam/kaydet")
def istihdam_kaydet(istek: IstihdamKaydet, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    gecerli = {r[0] for r in db.execute(text("SELECT id FROM bolumler")).all()}
    for s in istek.satirlar:
        if s.bolum_id is not None and s.bolum_id not in gecerli:
            raise HTTPException(400, f"Geçersiz bölüm: {s.bolum_id} ({s.program_adi_kaynak})")
    kaynak = istek.kaynak.strip()
    silinen = 0
    if istek.ayni_yili_degistir:
        silinen = db.execute(text("DELETE FROM istihdam_gostergeleri WHERE veri_yili = :y"), {"y": istek.veri_yili}).rowcount
    eslesmeyen = [s.program_adi_kaynak for s in istek.satirlar if s.bolum_id is None]
    yid = _yukleme(db, yon, "istihdam", istek.dosya_adi, len(istek.satirlar), len(istek.satirlar) - len(eslesmeyen), eslesmeyen,
                   istek.veri_yili, kaynak)
    db.execute(text("""INSERT INTO istihdam_gostergeleri (bolum_id, program_adi_kaynak, duzey, istihdam_orani, is_bulma_suresi_ay,
                          alan_uyum_orani, kazanc_grubu, kazanc_tl, veri_yili, kaynak, yukleme_id)
                       VALUES (:bolum_id, :program_adi_kaynak, :duzey, :istihdam_orani, :is_bulma_suresi_ay, :alan_uyum_orani,
                          :kazanc_grubu, :kazanc_tl, :y, :k, :yid)"""),
               [{**s.model_dump(), "y": istek.veri_yili, "k": kaynak, "yid": yid} for s in istek.satirlar])
    denetim_yaz(db, yon, "is_hayati_istihdam_yukle", "istihdam_gostergeleri", yid,
                f"{istek.veri_yili} · {len(istek.satirlar)} satır ({len(eslesmeyen)} eşleşmesiz) · önceki {silinen} satır silindi · {kaynak[:120]}")
    db.commit()
    return {"yukleme_id": yid, "eklenen": len(istek.satirlar), "eslesen": len(istek.satirlar) - len(eslesmeyen),
            "eslesmeyen": len(eslesmeyen), "silinen": silinen}


def _isco_bul(kod_hucre, ad: str) -> str | None:
    """Kod sütunundan ya da adın başındaki rakamlardan ('2 Profesyonel …', 'OC21') ya da ISCO adından 1–2 haneli kod."""
    for kaynak in (kod_hucre, ad):
        if kaynak is None:
            continue
        if isinstance(kaynak, (int, float)) and not isinstance(kaynak, bool):
            if float(kaynak).is_integer() and 0 <= kaynak < 100:
                return str(int(kaynak))
            continue
        m = re.match(r"^\s*(?:isco[-\s]*(?:08)?\s*|oc)?(\d{1,2})(?!\d)", str(kaynak), re.I)
        if m:
            return m.group(1)
    hedef = _bn(ad)
    s = ihs.isco_sozlugu()
    for kod, isim in list(s["alt"].items()) + list(s["ana"].items()):
        if _bn(isim) == hedef:
            return kod
    return None


@router.post("/kazanc/onizle")
def kazanc_onizle(istek: OnizleIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    e = istek.eslesme
    if e.get("ad") is None or e.get("brut") is None:
        raise HTTPException(400, "Meslek grubu adı ve brüt kazanç sütunlarını seçin.")
    _, _, govde, _ = _tablo(istek.dosya_adi, istek.icerik_base64, "kazanc", istek.baslik_satiri)
    satirlar = []
    for no, r in enumerate(govde, start=1):
        ad = _hucre(r, e.get("ad"))
        if ad is None:
            continue
        ad = " ".join(str(ad).split())
        if _TOPLAM.match(_normalize(ad)):
            continue
        brut = ihs.sayi(_hucre(r, e.get("brut")))
        hatalar = []
        if brut is not None and istek.tutar_turu == "yillik":
            brut = round(brut / 12, 2)
        if brut is None or brut <= 0:
            hatalar.append("Brüt kazanç okunamadı")
        kod = _isco_bul(_hucre(r, e.get("isco_kodu")), ad)
        if kod is None:
            hatalar.append("ISCO kodu bulunamadı — elle girin")
        temiz_ad = re.sub(r"^\s*\d{1,2}\s*[-–.:)]?\s*", "", ad) or ad
        satirlar.append({"no": no, "isco_kodu": kod, "ad": temiz_ad, "brut_aylik_ortalama_tl": brut, "isco_adi": ihs.isco_adi(kod), "hatalar": hatalar})
    if not satirlar:
        raise HTTPException(400, "Meslek grubu sütununda veri bulunamadı.")
    kodlar = [s["isco_kodu"] for s in satirlar if s["isco_kodu"]]
    tekrar = {k for k in kodlar if kodlar.count(k) > 1}
    for s in satirlar:
        if s["isco_kodu"] in tekrar:
            s["hatalar"].append("Bu kod dosyada birden fazla kez geçiyor")
    return {"satirlar": satirlar, "ozet": {"toplam": len(satirlar), "hatali": sum(1 for s in satirlar if s["hatalar"])},
            "isco": ihs.isco_sozlugu()["alt"] | ihs.isco_sozlugu()["ana"]}


class KazancSatiri(BaseModel):
    isco_kodu: str = Field(pattern=r"^[0-9]{1,2}$")
    ad: str = Field(min_length=1, max_length=300)
    brut_aylik_ortalama_tl: float = Field(gt=0)


class KazancKaydet(BaseModel):
    dosya_adi: str | None = Field(None, max_length=200)
    veri_yili: int = Field(ge=2000, le=2100)
    kaynak: str = Field(min_length=3, max_length=500)
    asgari_brut_o_yil: float = Field(gt=0)
    satirlar: list[KazancSatiri] = Field(min_length=1, max_length=500)


@router.post("/kazanc/kaydet")
def kazanc_kaydet(istek: KazancKaydet, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    kodlar = [s.isco_kodu for s in istek.satirlar]
    if len(set(kodlar)) != len(kodlar):
        raise HTTPException(400, "Aynı ISCO kodu birden fazla satırda var.")
    kaynak = istek.kaynak.strip()
    yid = _yukleme(db, yon, "kazanc", istek.dosya_adi, len(istek.satirlar), len(istek.satirlar), [], istek.veri_yili, kaynak)
    db.execute(text("""INSERT INTO kazanc_meslek_gruplari (isco_kodu, ad, brut_aylik_ortalama_tl, veri_yili, asgari_brut_o_yil, kaynak, yukleme_id)
                       VALUES (:isco_kodu, :ad, :brut_aylik_ortalama_tl, :y, :a, :k, :yid)
                       ON CONFLICT (isco_kodu, veri_yili) DO UPDATE SET ad = EXCLUDED.ad, brut_aylik_ortalama_tl = EXCLUDED.brut_aylik_ortalama_tl,
                         asgari_brut_o_yil = EXCLUDED.asgari_brut_o_yil, kaynak = EXCLUDED.kaynak, yukleme_id = EXCLUDED.yukleme_id"""),
               [{**s.model_dump(), "y": istek.veri_yili, "a": istek.asgari_brut_o_yil, "k": kaynak, "yid": yid} for s in istek.satirlar])
    denetim_yaz(db, yon, "is_hayati_kazanc_yukle", "kazanc_meslek_gruplari", yid,
                f"{istek.veri_yili} · {len(istek.satirlar)} meslek grubu · asgari brüt {istek.asgari_brut_o_yil} · {kaynak[:120]}")
    db.commit()
    return {"yukleme_id": yid, "kaydedilen": len(istek.satirlar)}


@router.get("/yuklemeler")
def yuklemeler(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    rows = db.execute(text("SELECT * FROM veri_yuklemeleri ORDER BY zaman DESC LIMIT 100")).mappings().all()
    return [{**dict(r), "eslesmeyen": (r["eslesmeyen"] or [])[:200], "zaman": r["zaman"].isoformat()} for r in rows]


@router.delete("/yuklemeler/{yukleme_id}")
def yukleme_sil(yukleme_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    r = db.execute(text("SELECT tur, veri_yili, dosya_adi FROM veri_yuklemeleri WHERE id = :i"), {"i": yukleme_id}).first()
    if r is None:
        raise HTTPException(404, "Yükleme bulunamadı.")
    n = 0
    if r.tur == "kazanc":   # kazanç satırları elle düzenlenmiş olabilir; yüklemeyle gelenler silinir
        n = db.execute(text("DELETE FROM kazanc_meslek_gruplari WHERE yukleme_id = :i"), {"i": yukleme_id}).rowcount
    else:
        n = db.execute(text("SELECT COUNT(*) FROM istihdam_gostergeleri WHERE yukleme_id = :i"), {"i": yukleme_id}).scalar()
    db.execute(text("DELETE FROM veri_yuklemeleri WHERE id = :i"), {"i": yukleme_id})   # istihdam satırları CASCADE
    denetim_yaz(db, yon, "is_hayati_yukleme_sil", "veri_yuklemeleri", yukleme_id, f"{r.tur} {r.veri_yili} · {r.dosya_adi or ''} · {n} satır silindi")
    db.commit()
    return {"silinen_satir": n}


# ---------------------------------------------------------------- elle düzenleme (genel CRUD)

def _metin(v, zorunlu=False, en_fazla=500):
    t = None if v is None else " ".join(str(v).split())
    if zorunlu and not t:
        raise ValueError("zorunlu")
    if t and len(t) > en_fazla:
        raise ValueError(f"en fazla {en_fazla} karakter")
    return t or None


def _sayi(v, zorunlu=False, en_az=None, en_cok=None):
    s = ihs.sayi(v)
    if s is None:
        if zorunlu:
            raise ValueError("sayı girin")
        return None
    if (en_az is not None and s < en_az) or (en_cok is not None and s > en_cok):
        raise ValueError(f"{en_az}–{en_cok} aralığında olmalı")
    return s


def _tarih(v, zorunlu=True):
    if v in (None, ""):
        if zorunlu:
            raise ValueError("tarih girin")
        return None
    try:
        return date.fromisoformat(str(v)[:10])
    except ValueError:
        raise ValueError("YYYY-AA-GG biçiminde olmalı")


def _yil(v, zorunlu=True):
    s = _sayi(v, zorunlu, 2000, 2100)
    return None if s is None else int(s)


def _liste(v):
    if v is None:
        return "[]"
    if isinstance(v, str):
        v = [x for x in re.split(r"[,;\n]", v)]
    return json.dumps([" ".join(str(x).split()) for x in v if str(x).strip()][:50], ensure_ascii=False)


def _isco(v, zorunlu=True):
    t = _metin(v, zorunlu)
    if t is not None and not re.fullmatch(r"[0-9]{1,2}", t):
        raise ValueError("1–2 haneli ISCO kodu")
    return t


def _grup(v):
    if v in (None, ""):
        return None
    g = ihs.kazanc_grubu_coz(v) or (v if v in ihs.KAZANC_GRUPLARI else None)
    if g is None:
        raise ValueError("Çok yüksek / Yüksek / Orta / Düşük / Çok düşük")
    return g


def _duzey(v):
    if v in (None, ""):
        return None
    d = v if v in ihs.DUZEYLER else ihs.duzey_coz(v)
    if d is None:
        raise ValueError("lisans / onlisans")
    return d


def _bolum(v):
    if v in (None, ""):
        return None
    return int(v)


TABLOLAR = {
    "istihdam_gostergeleri": {
        "ad": "TÜİK yükseköğretim istihdam göstergeleri", "sira": "veri_yili DESC, program_adi_kaynak", "ara": ["program_adi_kaynak"],
        "alanlar": {"bolum_id": _bolum, "program_adi_kaynak": lambda v: _metin(v, True, 300), "duzey": _duzey,
                    "istihdam_orani": lambda v: _sayi(v, False, 0, 100), "is_bulma_suresi_ay": lambda v: _sayi(v, False, 0, 240),
                    "alan_uyum_orani": lambda v: _sayi(v, False, 0, 100), "kazanc_grubu": _grup, "kazanc_tl": lambda v: _sayi(v, False, 0),
                    "veri_yili": _yil, "kaynak": lambda v: _metin(v, True)},
    },
    "kazanc_meslek_gruplari": {
        "ad": "Kazanç yapısı (meslek grubu)", "sira": "veri_yili DESC, isco_kodu", "ara": ["ad", "isco_kodu"],
        "alanlar": {"isco_kodu": _isco, "ad": lambda v: _metin(v, True, 300), "brut_aylik_ortalama_tl": lambda v: _sayi(v, True, 1),
                    "veri_yili": _yil, "asgari_brut_o_yil": lambda v: _sayi(v, True, 1), "kaynak": lambda v: _metin(v, True)},
    },
    "kamu_maaslari": {
        "ad": "Kamu maaşları", "sira": "kadro_adi", "ara": ["kadro_adi", "aciklama"], "json": ["anahtar_kelimeler"], "guncelleme": True,
        "alanlar": {"kadro_adi": lambda v: _metin(v, True, 300), "anahtar_kelimeler": _liste, "net_min": lambda v: _sayi(v, False, 0),
                    "net_max": lambda v: _sayi(v, False, 0), "donem": lambda v: _metin(v, True, 40), "kaynak": lambda v: _metin(v, True),
                    "aciklama": lambda v: _metin(v, False, 2000)},
    },
    "asgari_ucret": {
        "ad": "Asgari ücret", "sira": "yururluk_tarihi DESC", "ara": ["donem"],
        "alanlar": {"donem": lambda v: _metin(v, True, 20), "brut": lambda v: _sayi(v, True, 1), "net": lambda v: _sayi(v, True, 1),
                    "kaynak": lambda v: _metin(v, True), "yururluk_tarihi": _tarih},
    },
    "yasam_giderleri": {
        "ad": "Yaşam giderleri", "sira": "il NULLS FIRST, kalem_kodu", "ara": ["il", "ad", "kalem_kodu"],
        "alanlar": {"il": lambda v: _metin(v, False, 60), "kalem_kodu": lambda v: (_metin(v, True, 40) or "").lower().replace(" ", "_"),
                    "ad": lambda v: _metin(v, True, 120), "aylik_tutar": lambda v: _sayi(v, True, 0), "kaynak": lambda v: _metin(v, True),
                    "tarih": _tarih},
    },
}


def _spec(tablo: str) -> dict:
    s = TABLOLAR.get(tablo)
    if s is None:
        raise HTTPException(404, "Tablo bulunamadı.")
    return s


def _dogrula(spec: dict, veri: dict, tam: bool) -> dict:
    out, hatalar = {}, []
    for alan, f in spec["alanlar"].items():
        if not tam and alan not in veri:
            continue
        try:
            out[alan] = f(veri.get(alan))
        except (ValueError, TypeError) as e:
            hatalar.append(f"{alan}: {e}")
    if hatalar:
        raise HTTPException(400, "; ".join(hatalar))
    if "net_min" in out and "net_max" in out and out["net_min"] and out["net_max"] and out["net_min"] > out["net_max"]:
        raise HTTPException(400, "net_min, net_max'tan büyük olamaz.")
    return out


def _satir_json(r: dict) -> dict:
    o = {}
    for k, v in r.items():
        if isinstance(v, date):
            o[k] = v.isoformat()
        elif hasattr(v, "is_finite"):   # Decimal
            o[k] = float(v)
        else:
            o[k] = v
    return o


@router.get("/kayit/{tablo}")
def kayit_listele(tablo: str, q: str | None = Query(None, max_length=100), veri_yili: int | None = None, limit: int = Query(1000, le=5000),
                  db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    spec = _spec(tablo)
    kosul, p = ["TRUE"], {"lim": limit}
    if q:
        kosul.append("(" + " OR ".join(f"t.{a}::text ILIKE :q" for a in spec["ara"]) + ")")
        p["q"] = f"%{q.strip()}%"
    if veri_yili and "veri_yili" in spec["alanlar"]:
        kosul.append("t.veri_yili = :y")
        p["y"] = veri_yili
    ek = ", b.ad AS bolum_ad" if tablo == "istihdam_gostergeleri" else ""
    katil = " LEFT JOIN bolumler b ON b.id = t.bolum_id" if tablo == "istihdam_gostergeleri" else ""
    sira = ", ".join(f"t.{x.strip()}" for x in spec["sira"].split(","))
    rows = db.execute(text(f"SELECT t.*{ek} FROM {tablo} t{katil} WHERE {' AND '.join(kosul)} ORDER BY {sira} LIMIT :lim"), p).mappings().all()
    toplam = db.execute(text(f"SELECT COUNT(*) FROM {tablo}")).scalar()
    out = [_satir_json(dict(r)) for r in rows]
    if tablo == "istihdam_gostergeleri":
        for r in out:
            r["bolum_ad"] = ihs.tr_baslik(r.get("bolum_ad")) if r.get("bolum_ad") else None
    return {"tablo": tablo, "ad": spec["ad"], "alanlar": list(spec["alanlar"]), "satirlar": out, "toplam": toplam}


class KayitIstek(BaseModel):
    veri: dict


@router.post("/kayit/{tablo}")
def kayit_ekle(tablo: str, istek: KayitIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    spec = _spec(tablo)
    v = _dogrula(spec, istek.veri, tam=True)
    kolonlar = list(v)
    deger = [f"CAST(:{k} AS JSONB)" if k in spec.get("json", []) else f":{k}" for k in kolonlar]
    try:
        yeni = db.execute(text(f"INSERT INTO {tablo} ({', '.join(kolonlar)}) VALUES ({', '.join(deger)}) RETURNING id"), v).scalar()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu kayıt zaten var (aynı dönem / il + kalem / ISCO kodu + yıl) ya da bağlı bölüm geçersiz.")
    denetim_yaz(db, yon, "is_hayati_kayit_ekle", tablo, yeni, json.dumps(istek.veri, ensure_ascii=False, default=str)[:400])
    db.commit()
    return {"id": yeni}


@router.put("/kayit/{tablo}/{kayit_id}")
def kayit_duzenle(tablo: str, kayit_id: int, istek: KayitIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    spec = _spec(tablo)
    v = _dogrula(spec, istek.veri, tam=False)
    if not v:
        raise HTTPException(400, "Değişiklik yok.")
    ata = [f"{k} = CAST(:{k} AS JSONB)" if k in spec.get("json", []) else f"{k} = :{k}" for k in v]
    if spec.get("guncelleme"):
        ata.append("guncelleme = now()")
    try:
        n = db.execute(text(f"UPDATE {tablo} SET {', '.join(ata)} WHERE id = :_id"), {**v, "_id": kayit_id}).rowcount
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "Bu değerlerle başka bir kayıt var ya da bağlı bölüm geçersiz.")
    if not n:
        raise HTTPException(404, "Kayıt bulunamadı.")
    denetim_yaz(db, yon, "is_hayati_kayit_duzenle", tablo, kayit_id, json.dumps(istek.veri, ensure_ascii=False, default=str)[:400])
    db.commit()
    return {"ok": True}


@router.delete("/kayit/{tablo}/{kayit_id}")
def kayit_sil(tablo: str, kayit_id: int, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    _spec(tablo)
    r = db.execute(text(f"DELETE FROM {tablo} WHERE id = :i RETURNING *"), {"i": kayit_id}).mappings().first()
    if r is None:
        raise HTTPException(404, "Kayıt bulunamadı.")
    denetim_yaz(db, yon, "is_hayati_kayit_sil", tablo, kayit_id, json.dumps(_satir_json(dict(r)), ensure_ascii=False, default=str)[:400])
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------- meslek → ISCO

def _bolum_meslekleri(db: Session) -> dict:
    """{meslek_adi (küçük harf): [bölüm adları]}"""
    out = {}
    for r in db.execute(text("SELECT ad, detay FROM bolumler WHERE durum = 'yayinda'")).all():
        d = r.detay if isinstance(r.detay, dict) else json.loads(r.detay or "{}")
        for m in d.get("meslekler") or []:
            k = ihs.tr_kucuk((m or {}).get("ad") or "")
            if k:
                out.setdefault(k, []).append(ihs.tr_baslik(r.ad))
    return out


@router.get("/meslek-isco")
def meslek_isco(q: str | None = Query(None, max_length=100), filtre: str = Query("hepsi", pattern="^(hepsi|bos|orta|yuksek|elle|eksik)$"),
                db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    bm = _bolum_meslekleri(db)
    rows = {r["meslek_adi"]: dict(r) for r in db.execute(text("SELECT * FROM meslek_isco")).mappings().all()}
    eksik = sorted(set(bm) - set(rows))
    satirlar = []
    for ad in sorted(set(rows) | set(eksik)):
        r = rows.get(ad)
        s = {"meslek_adi": ad, "isco_kodu": r["isco_kodu"] if r else None, "guven": r["guven"] if r else None,
             "kaynak": r["kaynak"] if r else "eksik", "guncelleyen": r["guncelleyen"] if r else None,
             "bolumler": bm.get(ad, [])[:6], "bolum_sayisi": len(bm.get(ad, [])), "kullanimda": ad in bm}
        satirlar.append(s)
    toplam = {"toplam": len(satirlar), "kodlu": sum(1 for s in satirlar if s["isco_kodu"]),
              "yuksek": sum(1 for s in satirlar if s["guven"] == "yuksek" and s["kaynak"] != "elle"),
              "orta": sum(1 for s in satirlar if s["guven"] == "orta"),
              "bos": sum(1 for s in satirlar if not s["isco_kodu"]), "elle": sum(1 for s in satirlar if s["kaynak"] == "elle"),
              "eksik": len(eksik)}
    if filtre == "bos":
        satirlar = [s for s in satirlar if not s["isco_kodu"]]
    elif filtre in ("orta", "yuksek"):
        satirlar = [s for s in satirlar if s["guven"] == filtre and s["kaynak"] != "elle"]
    elif filtre in ("elle", "eksik"):
        satirlar = [s for s in satirlar if s["kaynak"] == filtre]
    if q:
        n = _normalize(q)
        satirlar = [s for s in satirlar if n in _normalize(s["meslek_adi"]) or any(n in _normalize(b) for b in s["bolumler"])
                    or (s["isco_kodu"] or "") == q.strip()]
    s = ihs.isco_sozlugu()
    return {"satirlar": satirlar, "ozet": toplam, "isco": [{"kod": k, "ad": v} for k, v in sorted(s["alt"].items())]}


class IscoIstek(BaseModel):
    meslek_adi: str = Field(min_length=1, max_length=300)
    isco_kodu: str | None = Field(None, pattern=r"^[0-9]{1,2}$")


@router.put("/meslek-isco")
def meslek_isco_duzenle(istek: IscoIstek, db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    ad = ihs.tr_kucuk(istek.meslek_adi)
    once = db.execute(text("SELECT isco_kodu FROM meslek_isco WHERE meslek_adi = :m"), {"m": ad}).scalar()
    db.execute(text("""INSERT INTO meslek_isco (meslek_adi, isco_kodu, guven, kaynak, guncelleyen, guncelleme)
                       VALUES (:m, :k, :g, 'elle', :u, now())
                       ON CONFLICT (meslek_adi) DO UPDATE SET isco_kodu = EXCLUDED.isco_kodu, guven = EXCLUDED.guven, kaynak = 'elle',
                         guncelleyen = EXCLUDED.guncelleyen, guncelleme = now()"""),
               {"m": ad, "k": istek.isco_kodu, "g": "yuksek" if istek.isco_kodu else None, "u": yon.ad_soyad})
    denetim_yaz(db, yon, "is_hayati_meslek_isco", "meslek_isco", ad[:60], f"{ad}: {once or '—'} → {istek.isco_kodu or 'boş'}")
    db.commit()
    return {"ok": True}


@router.post("/meslek-isco/json-yukle")
def meslek_isco_json(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    ihs.isco_sozlugu.cache_clear()
    veri = ihs.isco_sozlugu()["eslesme"]
    satirlar = [{"m": ad, "k": v.get("isco_kodu"), "g": v.get("guven")} for ad, v in veri.items()]
    n = 0
    for s in satirlar:
        n += db.execute(text("INSERT INTO meslek_isco (meslek_adi, isco_kodu, guven, kaynak) VALUES (:m, :k, :g, 'otomatik') "
                             "ON CONFLICT (meslek_adi) DO NOTHING"), s).rowcount
    denetim_yaz(db, yon, "is_hayati_meslek_isco_json", "meslek_isco", "-", f"JSON'dan {n} eksik meslek eklendi")
    db.commit()
    return {"eklenen": n}


# ---------------------------------------------------------------- özet

@router.get("/ozet")
def ozet(db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_super_admin)):
    def say(sql):
        return [dict(r) for r in db.execute(text(sql)).mappings().all()]
    s = ihs.isco_sozlugu()
    return {
        "istihdam": say("SELECT veri_yili, COUNT(*) AS satir, COUNT(bolum_id) AS eslesen, COUNT(DISTINCT bolum_id) AS bolum, MAX(kaynak) AS kaynak "
                        "FROM istihdam_gostergeleri GROUP BY veri_yili ORDER BY veri_yili DESC"),
        "kazanc": say("SELECT veri_yili, COUNT(*) AS satir, MAX(asgari_brut_o_yil)::float AS asgari_brut_o_yil, MAX(kaynak) AS kaynak "
                      "FROM kazanc_meslek_gruplari GROUP BY veri_yili ORDER BY veri_yili DESC"),
        "meslek_isco": say("SELECT COUNT(*) AS toplam, COUNT(isco_kodu) AS kodlu, COUNT(*) FILTER (WHERE kaynak = 'elle') AS elle FROM meslek_isco")[0],
        "kamu": db.execute(text("SELECT COUNT(*) FROM kamu_maaslari")).scalar(),
        "asgari": [_satir_json(r) for r in say("SELECT donem, brut, net, kaynak, yururluk_tarihi FROM asgari_ucret ORDER BY yururluk_tarihi DESC")],
        "guncel_asgari": ihs.guncel_asgari(db),
        "giderler": say("SELECT COALESCE(il, 'Türkiye geneli') AS il, COUNT(*) AS kalem, MAX(tarih)::text AS tarih FROM yasam_giderleri GROUP BY 1 ORDER BY 1"),
        "isco_alt": s["alt"], "isco_ana": s["ana"], "kazanc_gruplari": ihs.KAZANC_GRUPLARI, "gider_kalemleri": ihs.GIDER_KALEMLERI,
    }
