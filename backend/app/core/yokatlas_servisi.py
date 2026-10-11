"""
[2026-10-08] YÖK Atlas'tan bölümün üniversite/program bilgilerini (kontenjan, taban puan, başarı sırası)
çeker ve veritabanında önbellekler.

Kaynak: yokatlas.yok.gov.tr tercih kılavuzu JSON uç noktaları (yokatlas-py kütüphanesi üzerinden).
ÖNEMLİ: Bu, YÖK Atlas'ın resmî olarak belgelenmiş/açık bir API'si değildir; site yapısı değişirse
çalışmayabilir. Bu yüzden:
  - Sonuçlar YOKATLAS_ONBELLEK_GUN gün veritabanında tutulur (YÖK Atlas'a bölüm başına haftada en fazla 1 istek).
  - Hata olursa son başarılı veri döner; hiç veri yoksa ekranda kibar bir mesaj gösterilir.
  - Özellik, sistem parametresi 'yokatlas_aktif' = 'false' yapılarak kapatılabilir.
"""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.models import Bolum, YokatlasOnbellek
from app.core.katman_servisi import parametre_oku

YOKATLAS_ONBELLEK_GUN = 7
MAKS_PROGRAM = 600          # bir bölüm için en fazla bu kadar program satırı saklanır
_istemci = None
_kilit = threading.Lock()
_log = logging.getLogger("yokatlas")
son_hata: str | None = None   # tanı ekranı için en son hata


def baglanti_tani() -> dict:
    """YÖK Atlas'a bağlantıyı adım adım dener; hangi adımda takıldığını döner (yalnızca teknik tanı için)."""
    sonuc = {"kutuphane": None, "program_gruplari": None, "ornek_arama": None, "son_hata": son_hata}
    try:
        import yokatlas_py  # noqa: F401
        sonuc["kutuphane"] = "yüklü"
    except Exception as e:
        sonuc["kutuphane"] = f"YOK: {type(e).__name__}: {e}"
        return sonuc
    try:
        gruplar = _istemci_al().list_program_groups()
        sonuc["program_gruplari"] = f"{len(gruplar)} grup alındı"
    except Exception as e:
        sonuc["program_gruplari"] = f"HATA: {type(e).__name__}: {str(e)[:400]}"
        return sonuc
    try:
        ids = _program_grubu_idleri("TIP")
        s = _istemci_al().search({"birim_grup_id": ids}, size=3, smart_search=False) if ids else None
        sonuc["ornek_arama"] = f"TIP için {s.total_elements} program" if s else "TIP grubu bulunamadı"
    except Exception as e:
        sonuc["ornek_arama"] = f"HATA: {type(e).__name__}: {str(e)[:400]}"
    return sonuc


def _normalize(metin: str) -> str:
    tablo = str.maketrans("ÇĞİIÖŞÜçğıöşüÂâÎîÛû", "cgiiosucgiosuaaiiuu")
    return " ".join((metin or "").translate(tablo).lower().split())


def _istemci_al():
    global _istemci
    with _kilit:
        if _istemci is None:
            from yokatlas_py import YokAtlasClient  # gecikmeli import: kütüphane yoksa uygulama yine açılır
            from yokatlas_py.config import Settings
            _istemci = YokAtlasClient(settings=Settings(timeout=15, max_retries=1, lookup_cache_ttl=86400))
        return _istemci


_ESLESME_SURUMU = 2          # eşleştirme mantığı değişince eski "eşleşme yok" önbellekleri yenilensin
OZEL_YETENEK_ALANLARI = ("U05", "U12", "U13")   # Spor, Sanat & Tasarım, Müzik & Sahne — çoğu özel yetenekle alır


def _anahtar(metin: str) -> str:
    """Eşleştirme anahtarı: Türkçe-normalize, parantez içi ve noktalama atılır, '&' → 've'."""
    import re
    t = _normalize(re.sub(r"\(.*?\)", " ", metin or "").replace("&", " ve "))
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", t).split())


def _kelime_kumesi(metin: str) -> frozenset:
    return frozenset(w for w in _anahtar(metin).split() if w not in ("ve", "bolumu", "programi"))


def grup_listesi() -> list:
    return list(_istemci_al().list_program_groups())


def otomatik_eslesme(bolum_adi: str, gruplar: list) -> list:
    """1) Birebir aynı ad  2) aynı kelimeler (sıra/noktalama/parantez farkı)  — benzer ama FARKLI bölüm eşleşmesin
    diye bulanık eşleşme otomatik KULLANILMAZ; o adaylar yönetim ekranında öneri olarak gösterilir."""
    hedef = _normalize(bolum_adi)
    birebir = [g for g in gruplar if _normalize(g.birim_grup_adi) == hedef]
    if birebir:
        return birebir
    k = _anahtar(bolum_adi)
    anahtar = [g for g in gruplar if _anahtar(g.birim_grup_adi) == k]
    if anahtar:
        return anahtar
    kume = _kelime_kumesi(bolum_adi)
    return [g for g in gruplar if kume and _kelime_kumesi(g.birim_grup_adi) == kume]


def benzer_adaylar(bolum_adi: str, gruplar: list, n: int = 5) -> list[tuple[str, int]]:
    from difflib import SequenceMatcher
    a = _anahtar(bolum_adi)
    ka = _kelime_kumesi(bolum_adi)
    puanli = []
    for g in gruplar:
        b = _anahtar(g.birim_grup_adi)
        oran = SequenceMatcher(None, a, b).ratio()
        kb = _kelime_kumesi(g.birim_grup_adi)
        ortak = len(ka & kb) / max(1, len(ka | kb))
        icerme = 0.6 if ka and kb and (ka <= kb or kb <= ka) else 0.0   # 'Tezhip' ⊂ 'Tezhip Minyatür ve Ebru'
        puanli.append((max(oran, ortak, icerme), g.birim_grup_adi))
    puanli.sort(reverse=True)
    return [(ad, round(p * 100)) for p, ad in puanli[:n] if p >= 0.55]


def _program_grubu_idleri(bolum_adi: str, elle: list[str] | None = None) -> list[int]:
    """Yönetimin elle seçtiği YÖK Atlas program grupları varsa onlar; yoksa otomatik eşleşme."""
    gruplar = grup_listesi()
    if elle:
        istenen = {_normalize(x) for x in elle}
        return [g.birim_grup_id for g in gruplar if _normalize(g.birim_grup_adi) in istenen]
    return [g.birim_grup_id for g in otomatik_eslesme(bolum_adi, gruplar)]


def elle_gruplar(bolum: Bolum) -> list[str]:
    d = bolum.detay if isinstance(bolum.detay, dict) else {}
    return [x for x in (d.get("yokatlas_gruplari") or []) if isinstance(x, str) and x.strip()]


def _int(v):
    try:
        return int(float(v)) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _float(v):
    try:
        if isinstance(v, str):
            v = v.strip().replace(".", "").replace(",", ".") if "," in v else v.strip()
        return float(v) if v not in (None, "") else None
    except (TypeError, ValueError):
        return None


def _satir(d: dict) -> dict | None:
    """Ham YÖK Atlas satırını (camelCase sözlük) kendi biçimimize çevirir. Kütüphanenin katı modelleri
    yerine toleranslı okuma yapılır: beklenmeyen bir değer (ör. KKTC üniversitesi türü) tüm sayfayı düşürmesin."""
    if not isinstance(d, dict) or d.get("kilavuzKodu") is None:
        return None
    yil = _int(d.get("yil")) or 0
    gecmis = []
    for k in (1, 2, 3):
        g = {"yil": yil - k if yil else None, "kontenjan": _int(d.get(f"kontenjan{k}")),
             "taban_puan": _float(d.get(f"minPuan{k}")), "basari_sirasi": _int(d.get(f"basariSirasi{k}"))}
        if g["kontenjan"] or g["taban_puan"] or g["basari_sirasi"]:
            gecmis.append(g)
    tur = (d.get("universiteTuru") or "").upper()
    birim_turu = (d.get("birimTuruAdi") or "").upper()
    return {
        "kilavuz_kodu": _int(d.get("kilavuzKodu")),
        "universite": d.get("universiteAdi") or "",
        "universite_turu": tur or None,
        "il": d.get("uniIlAdi") or d.get("ilAdi"),
        "fakulte": d.get("fymkAdi"),
        "program": d.get("birimAdi"),
        "puan_turu": d.get("puanTuru"),
        "ogrenim_dili": d.get("ogrenimDiliAdi"),
        "burs": d.get("bursOraniAdi"),
        "ogrenim_turu": d.get("ogrenimTuruAdi"),
        "ogrenim_suresi": _int(d.get("ogrenimSuresi")) or (2 if "LISANS" in birim_turu and birim_turu.startswith(("ÖN", "ON")) else None),
        "yil": yil or None,
        "kontenjan": _int(d.get("kontenjan")),
        "yerlesen": _int(d.get("gkY")),
        "taban_puan": _float(d.get("minPuan")),
        "basari_sirasi": _int(d.get("basariSirasi")),
        "gecmis": gecmis,
    }


def _ham_ara(istemci, gruplar: list[int], sayfa: int, boyut: int) -> dict:
    govde = {
        "filters": {"puanTuru": None, "universiteId": [], "birimGrupId": list(gruplar), "ilKodu": [],
                    "birimTuruId": None, "universiteTuru": None, "bursOraniId": None, "ogrenimTuruId": None,
                    "kilavuzKodu": None, "minBasariSirasi": None, "maxBasariSirasi": None},
        "page": sayfa, "size": boyut, "sortBy": "basariSirasi", "direction": "ASC",
    }
    return istemci._http.post_json("/api/tercih-kilavuz/search", json_body=govde)


def _yokatlastan_cek(bolum_adi: str, elle: list[str] | None = None) -> dict:
    gruplar = _program_grubu_idleri(bolum_adi, elle)
    if not gruplar:
        return {"eslesme": False, "programlar": [], "yil": None, "surum": _ESLESME_SURUMU}
    istemci = _istemci_al(); satirlar = []; yil = None; sayfa = 0; boyut = 50
    while len(satirlar) < MAKS_PROGRAM and sayfa < 30:
        try:
            ham = _ham_ara(istemci, gruplar, sayfa, boyut)
        except Exception:
            if sayfa == 0 and boyut > 20:   # sayfa boyutu reddedildiyse küçük sayfayla dene
                boyut = 20
                continue
            if satirlar:                    # sonraki sayfada hata: o ana kadar gelenleri kullan
                break
            raise
        icerik = (ham or {}).get("content") or []
        yil = yil or _int((ham or {}).get("yil"))
        satirlar += [x for x in (_satir(d) for d in icerik) if x]
        if (ham or {}).get("last", True) or not icerik:
            break
        sayfa += 1
    yil = yil or next((s["yil"] for s in satirlar if s.get("yil")), None)
    return {"eslesme": True, "programlar": satirlar, "yil": yil, "surum": _ESLESME_SURUMU}


def bolum_universiteleri(db: Session, bolum: Bolum) -> dict:
    """Önbellek tazeyse onu, değilse YÖK Atlas'tan yenisini döner. Hata durumunda eski veri korunur."""
    kayit = db.get(YokatlasOnbellek, bolum.id)
    simdi = datetime.now(timezone.utc)
    taze = kayit is not None and kayit.veri is not None and kayit.guncellenme is not None and \
        (simdi - kayit.guncellenme.replace(tzinfo=kayit.guncellenme.tzinfo or timezone.utc)) < timedelta(days=YOKATLAS_ONBELLEK_GUN)
    if taze and not (kayit.veri or {}).get("programlar") and (kayit.veri or {}).get("surum") != _ESLESME_SURUMU:
        taze = False   # eski eşleştirme mantığıyla "bulunamadı" denmiş — yeniden dene
    aktif = (parametre_oku(db, "yokatlas_aktif", "true") or "true").lower() != "false"

    if not taze and aktif:
        try:
            veri = _yokatlastan_cek(bolum.ad, elle_gruplar(bolum))
            if kayit is None:
                kayit = YokatlasOnbellek(bolum_id=bolum.id)
                db.add(kayit)
            kayit.veri = veri; kayit.guncellenme = simdi; kayit.hata = None
            db.commit()
        except Exception as e:  # ağ hatası, YÖK Atlas yapı değişikliği vb.
            global son_hata
            son_hata = f"{type(e).__name__}: {str(e)[:500]}"
            _log.warning("YÖK Atlas hatası (%s): %s", bolum.ad, son_hata)
            db.rollback()
            kayit = db.get(YokatlasOnbellek, bolum.id)
            if kayit is None:
                return {"durum": "hata", "mesaj": "Üniversite bilgileri şu anda YÖK Atlas'tan alınamıyor. Daha sonra tekrar dene.",
                        "programlar": [], "yil": None, "kaynak": "YÖK Atlas"}
            kayit.hata = str(e)[:500]; db.commit()

    if kayit is None or kayit.veri is None:
        return {"durum": "kapali", "mesaj": "Üniversite bilgileri şu anda gösterilemiyor.", "programlar": [], "yil": None, "kaynak": "YÖK Atlas"}
    v = kayit.veri
    if not v.get("eslesme") or not v.get("programlar"):
        if _ozel_yetenek_mi(db, bolum):
            return {"durum": "ozel_yetenek", "programlar": [], "yil": None, "kaynak": "YÖK Atlas",
                    "mesaj": "Bu bölüm üniversitelerin çoğunda özel yetenek sınavıyla öğrenci alır; bu yüzden ÖSYM tercih "
                             "kılavuzunda taban puanı ve başarı sırası yer almaz. Başvuru için üniversitelerin özel yetenek "
                             "sınavı duyurularını (genellikle Haziran–Ağustos) takip et; çoğunda TYT'den baraj puanı istenir."}
        return {"durum": "eslesme_yok", "mesaj": "Bu bölümün programları YÖK Atlas'ta farklı bir adla yer alıyor olabilir. "
                "YÖK Atlas'ta bölüm adıyla arayabilir ya da rehber öğretmenine sorabilirsin.",
                "programlar": [], "yil": None, "kaynak": "YÖK Atlas"}
    return {"durum": "tamam", "mesaj": None, "programlar": v.get("programlar", []), "yil": v.get("yil"),
            "guncellenme": kayit.guncellenme.isoformat() if kayit.guncellenme else None, "kaynak": "YÖK Atlas"}


def _ozel_yetenek_mi(db: Session, bolum: Bolum) -> bool:
    from sqlalchemy import text
    try:
        kod = db.execute(text("SELECT d.kod FROM bolum_dal_eslesme e JOIN dallar d ON d.id = e.dal_id WHERE e.bolum_id = :b"),
                         {"b": bolum.id}).scalar()
    except Exception:
        db.rollback()
        return False
    return kod in OZEL_YETENEK_ALANLARI
