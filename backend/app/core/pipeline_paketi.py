# -*- coding: utf-8 -*-
"""
[2026-11-01] Pipeline'ın sistemden kurulması ve yıllık sayaç.

Kod      : backend/pipeline/ (depo; her değişiklik PR'la gelir). Bilgisayar her çalıştırmada eksik / değişen kodu indirir.
Veri     : Supabase Storage (app/core/pipeline_depo.py). Her çalıştırmanın sonunda bilgisayar veriyi gönderir
           (pipeline_surumleri); başka bir bilgisayar bir sonraki çalıştırmada en son sürümü alır.
Anahtar  : süper admin "Bu bilgisayara kur" dediğinde 24 saat geçerli, tek kullanımlık kurulum anahtarı üretilir ve
           kurulum dosyasına yazılır. Kurulum bunu bir bilgisayar anahtarıyla değiştirir (C:\\pipeline\\ayar.json).
           Anahtarların kendisi saklanmaz; yalnızca SHA-256 özetleri tutulur. Bilgisayar ekrandan iptal edilebilir.
Canlı    : bölüm listesi, özellik listesi ve K5 cümleleri her çalıştırmada canlı sistemden alınır (ad uyuşmazlığı olmaz).
Sayaç    : bölüm profilleri en son ne zaman canlıya alındı + 365 gün; süre dolmadan gerekli olan durumlar ayrıca gösterilir.
"""
import hashlib
import json
import re
import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import pipeline_depo as depo
from app.core.hesap_yonetimi import simdi

KOD_DIZINI = Path(__file__).resolve().parents[2] / "pipeline"
KURULUM_SABLONU = KOD_DIZINI / "_kurulum_sablonu.ps1"
GUNCELLIK_GUN = 365
UYARI_GUN = 30
KURULUM_GECERLILIK_SAAT = 24
SAKLANAN_SURUM = 5
EN_FAZLA_DOSYA = 3000
YEREL = ZoneInfo("Europe/Istanbul")
VERI_KLASORLERI = ("veri", "onet", "onbellek", "cikti")   # depoda yalnızca bunlar; kod yalnızca sistemden gelir
SAKLAMA_GUN = 30            # son 5 sürüme ek olarak son 30 günün sürümlerinin parçaları da silinmez
YENI_PARCA_SAAT = 6         # yeni yüklenmiş (henüz sürüme girmemiş olabilecek) parçalar budanmaz
KILIT_ANAHTARI = 2026110188
K5_KOD_DESENI = "^U[0-9]{2}_"   # yeni K5 iş türü değişkenleri (veri_yukleme._k5_kodlari ile aynı)
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_YASAK_KARAKTER = re.compile(r'[\x00-\x1f\\:*?"<>|]')   # ekranda / dosyada gösterilen tarih ve saatler


class PaketHatasi(Exception):
    pass


def _sha(veri: bytes) -> str:
    return hashlib.sha256(veri).hexdigest()


# ---------------------------------------------------------------------------------------------- kod
def kod_manifesti() -> list[dict]:
    """Bilgisayara gidecek kod dosyaları. '_' ile başlayan dosyalar (kurulum şablonu) ve önbellekler hariç."""
    dosyalar = []
    for p in sorted(KOD_DIZINI.rglob("*")):
        if not p.is_file() or "__pycache__" in p.parts or p.name.startswith("_") or p.suffix == ".pyc":
            continue
        veri = p.read_bytes()
        dosyalar.append({"yol": p.relative_to(KOD_DIZINI).as_posix(), "sha256": _sha(veri), "boyut": len(veri)})
    return dosyalar


def kod_surumu(manifest: list[dict] | None = None) -> str:
    m = manifest if manifest is not None else kod_manifesti()
    return _sha("\n".join(f"{d['yol']}:{d['sha256']}" for d in m).encode())[:12]


def kod_dosyasi(yol: str) -> bytes:
    if yol not in {d["yol"] for d in kod_manifesti()}:
        raise PaketHatasi("Bu dosya pipeline paketinde yok.")
    return (KOD_DIZINI / yol).read_bytes()


# ---------------------------------------------------------------------------------------------- anahtarlar
def _anahtar_kaydet(db: Session, tur: str, cihaz_adi: str, admin=None, gecerlilik=None, kurulum_id=None) -> str:
    ham = secrets.token_urlsafe(32)
    db.execute(text("INSERT INTO pipeline_anahtarlari (tur, ozet, cihaz_adi, olusturan_admin_id, olusturan, son_gecerlilik, "
                    "kurulum_anahtari_id) VALUES (:t, :o, :c, :a, :ad, :g, :k)"),
               {"t": tur, "o": _sha(ham.encode()), "c": cihaz_adi, "a": getattr(admin, "id", None),
                "ad": getattr(admin, "ad_soyad", None), "g": gecerlilik, "k": kurulum_id})
    return ham


def kurulum_anahtari_olustur(db: Session, admin, cihaz_adi: str) -> str:
    return _anahtar_kaydet(db, "kurulum", cihaz_adi, admin, simdi() + timedelta(hours=KURULUM_GECERLILIK_SAAT))


def kurulumu_etkinlestir(db: Session, kurulum_ham: str) -> tuple[str, str]:
    """Tek kullanımlık kurulum anahtarını bilgisayar anahtarına çevirir. (bilgisayar_anahtari, cihaz_adi)"""
    r = db.execute(text("SELECT id, cihaz_adi, olusturan_admin_id, olusturan, son_gecerlilik, kullanilma_zamani, iptal_zamani "
                        "FROM pipeline_anahtarlari WHERE tur = 'kurulum' AND ozet = :o FOR UPDATE"),
                   {"o": _sha(kurulum_ham.encode())}).mappings().first()
    if r is None or r["iptal_zamani"] is not None:
        raise PaketHatasi("Kurulum anahtarı geçersiz. Admin panelinden yeni kurulum dosyası indirin.")
    if r["kullanilma_zamani"] is not None:
        raise PaketHatasi("Bu kurulum dosyası daha önce kullanıldı. Admin panelinden yeni kurulum dosyası indirin.")
    if r["son_gecerlilik"] is not None and r["son_gecerlilik"] < simdi():
        raise PaketHatasi("Kurulum dosyasının süresi dolmuş (24 saat). Admin panelinden yeni kurulum dosyası indirin.")
    db.execute(text("UPDATE pipeline_anahtarlari SET kullanilma_zamani = now() WHERE id = :i"), {"i": r["id"]})

    class _Olusturan:  # kurulumu başlatan admin bilgisi bilgisayar anahtarına aktarılır
        id, ad_soyad = r["olusturan_admin_id"], r["olusturan"]
    return _anahtar_kaydet(db, "cihaz", r["cihaz_adi"], _Olusturan, None, r["id"]), r["cihaz_adi"]


def cihazi_dogrula(db: Session, ham: str | None) -> dict | None:
    if not ham:
        return None
    r = db.execute(text("SELECT id, cihaz_adi FROM pipeline_anahtarlari WHERE tur = 'cihaz' AND ozet = :o "
                        "AND iptal_zamani IS NULL"), {"o": _sha(ham.encode())}).mappings().first()
    if r is None:
        return None
    db.execute(text("UPDATE pipeline_anahtarlari SET son_kullanim = now() WHERE id = :i"), {"i": r["id"]})
    db.commit()
    return dict(r)


def cihazlar(db: Session) -> list[dict]:
    rows = db.execute(text("SELECT id, cihaz_adi, olusturan, olusturma_zamani, son_kullanim FROM pipeline_anahtarlari "
                           "WHERE tur = 'cihaz' AND iptal_zamani IS NULL ORDER BY olusturma_zamani DESC")).mappings().all()
    return [dict(r) for r in rows]


def cihazi_iptal_et(db: Session, cihaz_id: int) -> str:
    r = db.execute(text("UPDATE pipeline_anahtarlari SET iptal_zamani = now() WHERE id = :i AND tur = 'cihaz' "
                        "AND iptal_zamani IS NULL RETURNING cihaz_adi"), {"i": cihaz_id}).scalar()
    if r is None:
        raise PaketHatasi("Bilgisayar bulunamadı ya da erişimi zaten kaldırılmış.")
    return r


# ---------------------------------------------------------------------------------------------- canlı listeler
def _ozet(satirlar: list) -> str:
    return _sha(json.dumps(satirlar, ensure_ascii=False, sort_keys=True).encode())[:16]


def canli_listeler(db: Session) -> dict:
    """Pipeline'ın canlıdan aldığı listeler ve her birinin özeti (sayaç, 'son çalıştırmadan beri değişti mi' için)."""
    bolumler = [dict(r) for r in db.execute(text(
        "SELECT id, ad, COALESCE(kisa_aciklama, '') AS kisa_aciklama, durum FROM bolumler ORDER BY id")).mappings()]
    degiskenler = [dict(r) for r in db.execute(text(
        "SELECT d.kod, d.ad, COALESCE(d.aciklama, '') AS aciklama, k.kod AS katman FROM degiskenler d "
        "JOIN katmanlar k ON k.id = d.katman_id WHERE d.dal_id IS NULL ORDER BY k.sira, d.sira")).mappings()]
    # K5 iş türleri: yeni K5 değişkenleri (kod U01_A biçiminde) — sistemin her yerinde aynı kural (veri_yukleme, veri_kaynaklari).
    # Dala bağlı eski K5 değişkenleri (C1, E1 …) canlıda duruyor ama artık kullanılmıyor; pipeline'a gitmez.
    eksenler = [dict(r) for r in db.execute(text(
        f"SELECT d.kod, COALESCE(a.ad, '') AS alan, d.ad FROM degiskenler d LEFT JOIN dallar a ON a.id = d.dal_id "
        f"WHERE d.dal_id IS NOT NULL AND d.kod ~ '{K5_KOD_DESENI}' ORDER BY d.kod")).mappings()]
    cumleler = [dict(r) for r in db.execute(text(
        f"SELECT d.kod, c.sira, c.metin FROM k5_cumleleri c JOIN degiskenler d ON d.id = c.degisken_id "
        f"WHERE c.aktif_mi AND d.kod ~ '{K5_KOD_DESENI}' ORDER BY d.kod, c.sira")).mappings()]
    return {
        "ozet": {"bolumler": _ozet([[b["id"], b["ad"], b["kisa_aciklama"]] for b in bolumler]),
                 "degiskenler": _ozet([[d["kod"], d["ad"], d["aciklama"]] for d in degiskenler]),
                 "k5": _ozet([[e["kod"], e["ad"]] for e in eksenler] + [[c["kod"], c["sira"], c["metin"]] for c in cumleler])},
        "bolumler": bolumler, "degiskenler": degiskenler, "k5_eksenleri": eksenler, "k5_cumleleri": cumleler,
    }


# ---------------------------------------------------------------------------------------------- veri sürümleri
def son_surum(db: Session) -> dict | None:
    r = db.execute(text("SELECT id, zaman, cihaz_adi, dosyalar, girdi_ozeti, toplam_bayt, aciklama FROM pipeline_surumleri "
                        "ORDER BY id DESC LIMIT 1")).mappings().first()
    return dict(r) if r else None


def surumler(db: Session, adet: int = SAKLANAN_SURUM) -> list[dict]:
    rows = db.execute(text("SELECT id, zaman, cihaz_adi, toplam_bayt, aciklama, (SELECT COUNT(*) FROM jsonb_object_keys(dosyalar)) AS dosya_sayisi "
                           "FROM pipeline_surumleri ORDER BY id DESC LIMIT :n"), {"n": adet}).mappings().all()
    return [dict(r) for r in rows]


class SurumCakismasi(PaketHatasi):
    pass


def veri_yolu_gecerli_mi(yol) -> bool:
    """Depodaki dosya yolu: veri / onet / onbellek / cikti altında, göreli, '..' ve Windows'ta yasak karakter içermeyen."""
    if not isinstance(yol, str) or not yol or len(yol) > 300 or _YASAK_KARAKTER.search(yol):
        return False
    parcalar = yol.split("/")
    return parcalar[0] in VERI_KLASORLERI and len(parcalar) >= 2 and all(p and p not in (".", "..") and p == p.strip()
                                                                          and not p.endswith(".") for p in parcalar)


def _dosyalari_dogrula(dosyalar: dict) -> list[str]:
    if not isinstance(dosyalar, dict) or not dosyalar or len(dosyalar) > EN_FAZLA_DOSYA:
        raise PaketHatasi("Dosya listesi boş ya da çok uzun.")
    parcalar = []
    for yol, d in dosyalar.items():
        if not veri_yolu_gecerli_mi(yol) or not isinstance(d, dict):
            raise PaketHatasi(f"Geçersiz dosya yolu: {str(yol)[:120]!r} (yalnızca {', '.join(VERI_KLASORLERI)} klasörleri)")
        p = d.get("parcalar")
        if (not isinstance(p, list) or not p and int(d.get("boyut", 0)) != 0 or len(p) > 50
                or not all(isinstance(x, str) and _HEX64.match(x) for x in p) or not _HEX64.match(str(d.get("sha256", "")))):
            raise PaketHatasi(f"Geçersiz parça listesi: {yol}")
        parcalar += p
    return parcalar


def gonderim_baslat(parcalar: list[dict]) -> dict:
    """Bilgisayarın göndermek istediği parçalardan depoda olmayanlar için yükleme adresleri."""
    for p in parcalar:
        if not _HEX64.match(str(p.get("sha256", ""))) or not 0 <= int(p.get("boyut", -1)) <= depo.PARCA_BOYUTU:
            raise PaketHatasi("Geçersiz parça (özet ya da boyut).")
    depo.kova_hazirla()
    var = depo.mevcut_parcalar()
    eksik = sorted({p["sha256"] for p in parcalar} - set(var))
    return {"eksik": {o: depo.yukleme_adresi(o) for o in eksik}, "var_olan": len(parcalar) - len(eksik)}


def parca_bozuk_bildir(sha256: str) -> bool:
    if not _HEX64.match(sha256 or ""):
        raise PaketHatasi("Geçersiz parça özeti.")
    return depo.parca_bozuk_mu(sha256)


def gonderim_tamamla(db: Session, cihaz: dict, dosyalar: dict, girdi_ozeti: dict | None, aciklama: str | None,
                     taban_surum_id: int | None = None, zorla: bool = False) -> dict:
    parcalar = _dosyalari_dogrula(dosyalar)
    # Aynı anda iki gönderim: kontrol + kayıt + budama tek sırada (biri ötekinin parçalarını silmesin)
    db.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": KILIT_ANAHTARI})
    son = son_surum(db)
    if son and not zorla and son["id"] != taban_surum_id:
        raise SurumCakismasi(
            f"Bu çalıştırma başladıktan sonra başka bir bilgisayar daha yeni sonuç gönderdi (sürüm {son['id']}, "
            f"{son.get('cihaz_adi') or '?'}). Üzerine yazılmadı.")
    var = depo.mevcut_parcalar()
    eksik = sorted(set(parcalar) - set(var))
    if eksik:
        raise PaketHatasi(f"{len(eksik)} parça depoya ulaşmamış; gönderim yarım kaldı. Pipeline'ı tekrar çalıştırın.")
    toplam = sum(int(d.get("boyut", 0)) for d in dosyalar.values())
    surum_id = db.execute(text(
        "INSERT INTO pipeline_surumleri (cihaz_id, cihaz_adi, dosyalar, girdi_ozeti, toplam_bayt, aciklama) "
        "VALUES (:c, :ca, CAST(:d AS JSONB), CAST(:g AS JSONB), :t, :a) RETURNING id"),
        {"c": cihaz["id"], "ca": cihaz["cihaz_adi"], "d": json.dumps(dosyalar, ensure_ascii=False),
         "g": json.dumps(girdi_ozeti or {}, ensure_ascii=False), "t": toplam, "a": (aciklama or "")[:500]}).scalar()
    silinen = budama(db, var)
    db.commit()
    return {"surum_id": surum_id, "toplam_bayt": toplam, "silinen_parca": silinen}


def budama(db: Session, depodaki: dict[str, str] | None = None) -> int:
    """Hiçbir saklanan sürümün kullanmadığı parçaları depodan kaldırır (ücretsiz plan sınırında kalınsın).
    Saklanan: son SAKLANAN_SURUM sürüm + son SAKLAMA_GUN günün sürümleri. Son YENI_PARCA_SAAT saatte yüklenen parça
    (başka bir bilgisayarın süren gönderimine ait olabilir) silinmez."""
    kalan = db.execute(text("SELECT dosyalar FROM pipeline_surumleri WHERE id IN (SELECT id FROM pipeline_surumleri "
                            "ORDER BY id DESC LIMIT :n) OR zaman > now() - make_interval(days => :g)"),
                       {"n": SAKLANAN_SURUM, "g": SAKLAMA_GUN}).scalars().all()
    if not kalan:
        return 0
    gerekli = {p for d in kalan for f in (d or {}).values() for p in f.get("parcalar", [])}
    sinir = simdi() - timedelta(hours=YENI_PARCA_SAAT)
    try:
        depodaki = depodaki if depodaki is not None else depo.mevcut_parcalar()
        artik = []
        for o, zaman in depodaki.items():
            if o in gerekli:
                continue
            try:
                eski = datetime.fromisoformat(zaman.replace("Z", "+00:00")) < sinir
            except (ValueError, AttributeError):
                eski = False   # zamanı bilinmeyen parça silinmez
            if eski:
                artik.append(o)
        return depo.parcalari_sil(sorted(artik)) if artik else 0
    except depo.DepoHatasi:
        return 0   # budama bir sonraki gönderimde yeniden denenir; sürüm kaydı geçerli


# ---------------------------------------------------------------------------------------------- sayaç
def _tarih(db: Session, sql: str):
    try:
        return db.execute(text(sql)).scalar()
    except Exception:
        db.rollback()
        return None


def sayac_durumu(db: Session) -> dict:
    bugun = simdi()
    profil = _tarih(db, "SELECT MAX(olusturulma_zamani) FROM bolum_agirliklari")
    k5 = _tarih(db, "SELECT MAX(zaman) FROM veri_yedekleri WHERE tur = 'k5_baglari'")
    ornek = _tarih(db, "SELECT MAX(zaman) FROM veri_yedekleri WHERE tur = 'ornek_meslekler'")
    son = son_surum(db)
    nedenler, notlar = [], []

    def eksik_bolumler(tablo: str) -> list[str]:
        try:
            return list(db.execute(text(
                f"SELECT b.ad FROM bolumler b WHERE b.durum = 'yayinda' AND NOT EXISTS "
                f"(SELECT 1 FROM {tablo} t WHERE t.bolum_id = b.id) ORDER BY b.ad")).scalars())
        except Exception:
            db.rollback()
            return []

    eksik_nedeni = 0
    for tablo, ad in (("bolum_agirliklari", "bölüm profili"), ("bolum_k5_baglari", "K5 iş türü bağı"),
                      ("bolum_ornek_meslekler", "örnek meslek listesi")):
        eksik = eksik_bolumler(tablo)
        if eksik:
            nedenler.append(f"{len(eksik)} yayındaki bölümün {ad} yok: " + ", ".join(eksik[:5]) + (" …" if len(eksik) > 5 else ""))
            eksik_nedeni += 1

    canli = canli_listeler(db)
    if son and son.get("girdi_ozeti"):
        g = son["girdi_ozeti"]
        if g.get("bolumler") and g["bolumler"] != canli["ozet"]["bolumler"]:
            nedenler.append("Son pipeline çalıştırmasından sonra bölüm listesi ya da bölüm kısa açıklamaları değişti.")
        if g.get("k5") and g["k5"] != canli["ozet"]["k5"]:
            nedenler.append("Son pipeline çalıştırmasından sonra K5 iş türleri ya da etkinlik cümleleri değişti.")
        if g.get("degiskenler") and g["degiskenler"] != canli["ozet"]["degiskenler"]:
            notlar.append("Özellik adı / tanımı değişti. Puanlar özellik kutup cümlelerinden (veri/degisken_kutuplari.csv) "
                          "hesaplandığı için pipeline'ı yeniden çalıştırmak gerekmez; kutup cümlelerinin yeni tanıma uygunluğu "
                          "kontrol edilmeli.")
    elif son is None:
        notlar.append("Pipeline henüz bu sistemden kurulup çalıştırılmadı; ilk çalıştırmadan sonra değişiklik takibi başlar.")
    # Çalıştırma yapılmış ama çıktıları canlıya alınmamışsa gereken iş "çalıştır" değil "canlıya al"dır; ayrı durum.
    bekleyen = bool(son and (profil is None or son["zaman"] > profil))
    if bekleyen:
        nedenler.append(f"Son pipeline çalıştırmasının çıktıları ({son['zaman'].astimezone(YEREL):%d.%m.%Y %H:%M}) henüz canlıya "
                        "alınmadı: aşağıdaki 1–3. adımla canlıya alın.")

    sonraki = profil + timedelta(days=GUNCELLIK_GUN) if profil else None
    kalan = (sonraki - bugun).days if sonraki else None
    # Bekleyen çıktı varsa eksik profil / bağ nedenleri büyük olasılıkla o çıktıyla kapanır: yapılacak iş önce canlıya almak
    calistirma_gerekli = len(nedenler) - int(bekleyen) - (eksik_nedeni if bekleyen else 0) > 0
    if profil is None:
        nedenler.insert(0, "Bölüm profilleri hiç canlıya alınmamış.")
    elif kalan <= 0:
        nedenler.insert(0, f"Yıllık güncelleme süresi doldu (son güncelleme {profil.astimezone(YEREL):%d.%m.%Y}).")
    if calistirma_gerekli or ((profil is None or kalan <= 0) and not bekleyen):
        durum = "gerekli"
    elif bekleyen:
        durum = "canliya_al"
    elif kalan <= UYARI_GUN:
        durum = "yaklasiyor"
    else:
        durum = "guncel"
    return {"durum": durum, "son_guncelleme": profil, "sonraki_guncelleme": sonraki, "kalan_gun": kalan,
            "guncellik_gun": GUNCELLIK_GUN, "nedenler": nedenler, "notlar": notlar,
            "canliya_alma": {"bolum_profili": profil, "k5_baglari": k5, "ornek_meslekler": ornek}}


# ---------------------------------------------------------------------------------------------- kurulum dosyası
def kurulum_dosyasi(api_adresi: str, kurulum_ham: str, cihaz_adi: str) -> str:
    sablon = KURULUM_SABLONU.read_text(encoding="utf-8-sig")
    for anahtar, deger in (("__API_ADRESI__", api_adresi.rstrip("/")), ("__KURULUM_ANAHTARI__", kurulum_ham),
                           ("__CIHAZ_ADI__", cihaz_adi.replace("'", "").replace('"', "")),
                           ("__OLUSTURMA__", f"{simdi().astimezone(YEREL):%d.%m.%Y %H:%M}")):
        sablon = sablon.replace(anahtar, deger)
    return "\ufeff" + sablon   # PowerShell 5 Türkçe karakterleri doğru okusun (UTF-8 BOM)
