# -*- coding: utf-8 -*-
"""
[2026-11-01] Veri kaynakları takibi (süper admin › Sistem › Veri Kaynakları).

Sistemin kullandığı dış veriler (TÜİK, YÖK Atlas, asgari ücret, kamu maaşları, bölüm profilleri, takvim…) için tek ekran:
  * sistemde var mı (kayıt sayısı), hangi döneme ait, en son ne zaman güncellendi (verinin kendi tablosundan okunur),
  * süper adminin en son ne zaman kontrol ettiği (veri_kaynagi_kontrolleri: "kontrol ettim / güncelledim / sorun var"),
  * durum: yok | bekleniyor (yeni dönem verisi beklenir ama yüklü değil) | sorun | kontrol_zamani | guncel.

"kontrol_araligi_gun" bir yayımlanma takvimi iddiası DEĞİLDİR; süper adminin o kaynağı ne sıklıkla gözden geçirmesi
gerektiğini gösterir. Yalnızca kodda zaten tanımlı kurallar "bekleniyor" üretir (ör. TÜİK istihdam: tuik_baglanti).
Her ölçüm kendi try bloğundadır: tablo yoksa ya da sorgu hata verirse kaynak "yok" görünür, ekran düşmez.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.orm import Session

_VERI = Path(__file__).resolve().parent.parent / "data"
SONUCLAR = {"guncel": "Kontrol ettim, güncel", "guncellendi": "Güncelledim", "sorun": "Sorun var"}


def _tek(db: Session, sql: str, p: dict | None = None):
    try:
        return db.execute(text(sql), p or {}).mappings().first() or {}
    except Exception:
        db.rollback()
        return None


def _zaman(x) -> datetime | None:
    if x is None:
        return None
    if isinstance(x, datetime):
        return x if x.tzinfo else x.replace(tzinfo=timezone.utc)
    if isinstance(x, date):
        return datetime(x.year, x.month, x.day, tzinfo=timezone.utc)
    m = re.match(r"^(\d{4})-(\d{2})(?:-(\d{2}))?", str(x))
    if m:
        return datetime(int(m[1]), int(m[2]), int(m[3] or 1), tzinfo=timezone.utc)
    return None


def _en_yeni(*xs) -> datetime | None:
    z = [_zaman(x) for x in xs if _zaman(x) is not None]
    return max(z) if z else None


def _dosya(ad: str) -> dict:
    try:
        return json.loads((_VERI / ad).read_text(encoding="utf-8"))
    except Exception:
        return {}


# ------------------------------------------------------------------------------------------------- ölçümler
# Her ölçüm: {"kayit": int, "son_guncelleme": datetime|None, "donem": str|None, "kaynak": str|None, "ayrinti": str|None,
#             "bekleniyor": str|None}. None dönerse tablo okunamadı (yok sayılır).
def _kaynak_metni(db: Session, tablo: str) -> str | None:
    try:
        rows = db.execute(text(f"SELECT DISTINCT kaynak FROM {tablo} WHERE kaynak IS NOT NULL LIMIT 3")).all()
        return " · ".join(str(r[0]) for r in rows) or None
    except Exception:
        db.rollback()
        return None


def _tuik_istihdam(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, MAX(veri_yili) y, MAX(olusturulma) z, COUNT(DISTINCT bolum_id) b FROM istihdam_gostergeleri")
    if r is None:
        return None
    from app.core.tuik_baglanti import guncelleme_durumu
    d = guncelleme_durumu(db, bugun)
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": f"{r['y']} veri yılı" if r["y"] else None,
            "kaynak": _kaynak_metni(db, "istihdam_gostergeleri"), "ayrinti": f"{r['b']} bölümle eşleşmiş" if r["n"] else None,
            "bekleniyor": None if d["guncel"] or not r["n"] else f"{d['beklenen_veri_yili']} veri yılı yayımlanmış olabilir"}


def _tuik_kazanc(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, MAX(veri_yili) y, MAX(olusturulma) z FROM kazanc_meslek_gruplari")
    if r is None:
        return None
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": f"{r['y']} veri yılı" if r["y"] else None,
            "kaynak": _kaynak_metni(db, "kazanc_meslek_gruplari")}


def _asgari(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, MAX(yururluk_tarihi) t, MAX(olusturulma) z FROM asgari_ucret")
    if r is None:
        return None
    son = (_tek(db, "SELECT donem FROM asgari_ucret ORDER BY yururluk_tarihi DESC NULLS LAST LIMIT 1") or {}).get("donem")
    t = r["t"]
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": f"{son} (yürürlük {t.isoformat()})" if son and t else son,
            "kaynak": _kaynak_metni(db, "asgari_ucret"),
            "bekleniyor": f"{bugun.year} yılı için kayıt yok" if r["n"] and t and t.year < bugun.year else None}


def _kamu(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, MAX(COALESCE(guncelleme, olusturulma)) z, MAX(donem) d FROM kamu_maaslari")
    if r is None:
        return None
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": r["d"], "kaynak": _kaynak_metni(db, "kamu_maaslari")}


def _giderler(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, MAX(tarih) t, MAX(olusturulma) z, COUNT(DISTINCT il) il FROM yasam_giderleri")
    if r is None:
        return None
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": f"veri tarihi {r['t'].isoformat()}" if r["t"] else None,
            "kaynak": _kaynak_metni(db, "yasam_giderleri"), "ayrinti": f"Türkiye geneli + {r['il']} il" if r["n"] else None}


def _yokatlas(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, COUNT(*) FILTER (WHERE hata IS NULL) ok, MAX(guncellenme) z, MIN(guncellenme) e FROM yokatlas_onbellek")
    if r is None:
        return None
    b = (_tek(db, "SELECT COUNT(*) n FROM bolumler WHERE durum = 'yayinda'") or {}).get("n") or 0
    net = (_tek(db, "SELECT COUNT(*) n, MAX(guncellenme) z FROM yokatlas_net_onbellek") or {})
    return {"kayit": r["n"], "son_guncelleme": _en_yeni(r["z"], net.get("z")),
            "donem": f"en eski kayıt {_zaman(r['e']).date().isoformat()}" if r["e"] else None, "kaynak": "YÖK Atlas (önbellek)",
            "ayrinti": (f"{r['ok']}/{b} bölüm önbellekte, {r['n'] - r['ok']} hatalı; net önbelleği {net.get('n') or 0} bölüm. "
                        "Önbellek bölüm penceresi açıldıkça 7 günde bir yenilenir.")}


def _meslek_isco(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, COUNT(isco_kodu) k, MAX(guncelleme) z FROM meslek_isco")
    if r is None:
        return None
    return {"kayit": r["n"], "son_guncelleme": r["z"], "kaynak": _kaynak_metni(db, "meslek_isco"),
            "ayrinti": f"{r['k']} meslek ISCO kodlu" if r["n"] else None}


def _ai_etkisi(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, MAX(veri_yili) y, MAX(COALESCE(guncelleme, olusturulma)) z FROM meslek_grubu_ai_etkisi")
    if r is None:
        return None
    dosya = _dosya("ai_etkisi_gruplar.json")
    return {"kayit": r["n"], "son_guncelleme": _en_yeni(r["z"], dosya.get("son_kontrol")),
            "donem": f"{r['y']} veri yılı" if r["y"] else None, "kaynak": _kaynak_metni(db, "meslek_grubu_ai_etkisi") or dosya.get("kaynak")}


def _bolum_profili(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(DISTINCT bolum_id) b, MAX(versiyon) v, MAX(olusturulma_zamani) z, COUNT(*) n FROM bolum_agirliklari")
    if r is None:
        return None
    toplam = (_tek(db, "SELECT COUNT(*) n FROM bolumler WHERE durum = 'yayinda'") or {}).get("n") or 0
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": f"sürüm {r['v']}" if r["v"] is not None else None,
            "kaynak": "Offline pipeline (O*NET, ESCO, TÜİK, SIOPS)",
            "ayrinti": f"{r['b']}/{toplam} yayındaki bölümün profili var" if r["n"] else None,
            "bekleniyor": f"{toplam - r['b']} yayındaki bölümün profili yok" if r["n"] and r["b"] < toplam else None}


def _k5_baglari(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, COUNT(DISTINCT kb.bolum_id) b FROM bolum_k5_baglari kb "
                 "JOIN degiskenler d ON d.id = kb.degisken_id WHERE d.kod ~ '^U[0-9]{2}_'")
    if r is None:
        return None
    from app.core.veri_yukleme import son_yukleme
    toplam = (_tek(db, "SELECT COUNT(*) n FROM bolumler WHERE durum = 'yayinda'") or {}).get("n") or 0
    return {"kayit": r["n"], "son_guncelleme": son_yukleme(db, "k5_baglari"), "kaynak": "Offline pipeline (a8)",
            "ayrinti": f"{r['b']}/{toplam} yayındaki bölümün iş türü bağı var" if r["n"] else None,
            "bekleniyor": f"{toplam - r['b']} yayındaki bölümün iş türü bağı yok" if r["n"] and r["b"] < toplam else None}


def _ornek_meslekler(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, COUNT(DISTINCT bolum_id) b FROM bolum_ornek_meslekler")
    if r is None:
        return None
    from app.core.veri_yukleme import son_yukleme
    toplam = (_tek(db, "SELECT COUNT(*) n FROM bolumler WHERE durum = 'yayinda'") or {}).get("n") or 0
    return {"kayit": r["n"], "son_guncelleme": son_yukleme(db, "ornek_meslekler"), "kaynak": "Offline pipeline (b3)",
            "ayrinti": f"{r['b']}/{toplam} yayındaki bölümün örnek meslek listesi var" if r["n"] else None,
            "bekleniyor": f"{toplam - r['b']} yayındaki bölümün örnek meslek listesi yok" if r["n"] and r["b"] < toplam else None}


def _meslekler(db: Session, bugun: date):
    r = _tek(db, "SELECT (SELECT COUNT(*) FROM meslekler) n, (SELECT MAX(olusturulma_zamani) FROM meslek_degisken_skorlari) z, "
                 "(SELECT COUNT(DISTINCT meslek_id) FROM meslek_degisken_skorlari) s")
    if r is None:
        return None
    return {"kayit": r["n"], "son_guncelleme": r["z"], "kaynak": _kaynak_metni(db, "meslekler"),
            "ayrinti": f"{r['s']} mesleğin özellik puanı var" if r["n"] else None}


def _bolum_icerik(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, COUNT(*) FILTER (WHERE detay IS NOT NULL AND detay::text NOT IN ('{}', 'null')) d "
                 "FROM bolumler WHERE durum = 'yayinda'")
    if r is None:
        return None
    a = _tek(db, "SELECT MAX(zaman) z FROM audit_log WHERE hedef_tablo = 'bolumler'") or {}
    return {"kayit": r["n"], "son_guncelleme": a.get("z"), "kaynak": "Bölüm tanıtımları (ders, meslek, süre, puan türü)",
            "ayrinti": f"{r['d']}/{r['n']} bölümün tanıtımı dolu. Son güncelleme yönetim kayıtlarından (audit log) okunur."}


def _sinav_konulari(db: Session, bugun: date):
    r = _tek(db, "SELECT COUNT(*) n, COUNT(DISTINCT ders) d, MAX(olusturulma_zamani) z FROM sinav_konulari WHERE okul_id IS NULL")
    if r is None:
        return None
    return {"kayit": r["n"], "son_guncelleme": r["z"], "kaynak": "YKS konu listesi (Net Takibi)",
            "ayrinti": f"{r['d']} ders" if r["n"] else None}


def _yks_tarihi(db: Session, bugun: date):
    yil = bugun.year + 1 if bugun.month >= 7 else bugun.year
    r = _tek(db, "SELECT COUNT(*) n, MAX(baslangic) t, MAX(olusturulma_zamani) z FROM takvim_etkinlikleri "
                 "WHERE okul_id IS NULL AND ogrenci_id IS NULL AND tur = 'sinav' AND (baslik ILIKE '%YKS%' OR baslik ILIKE '%TYT%')")
    if r is None:
        return None
    var = _tek(db, "SELECT 1 x FROM takvim_etkinlikleri WHERE okul_id IS NULL AND ogrenci_id IS NULL AND tur = 'sinav' "
                   "AND (baslik ILIKE '%YKS%' OR baslik ILIKE '%TYT%') AND EXTRACT(YEAR FROM baslangic) = :y", {"y": yil})
    return {"kayit": r["n"], "son_guncelleme": r["z"], "donem": f"son kayıt {r['t'].isoformat()}" if r["t"] else None,
            "kaynak": "Genel Takvim (ÖSYM sınav takvimi)",
            "ayrinti": "Takvimde kayıt yoksa geri sayım tahmini tarihle (Haziran'ın 3. cumartesisi) gösterilir.",
            "bekleniyor": None if var else f"{yil} YKS tarihi Genel Takvim'de yok (tahmini tarih kullanılıyor)"}


def _dosya_olcumu(dosyalar: list[tuple[str, str]], kaynak: str):
    def olc(db: Session, bugun: date):
        tarihler, adet = [], 0
        for ad, alan in dosyalar:
            d = _dosya(ad)
            if not d:
                continue
            adet += 1
            tarihler.append(d.get("son_kontrol") or d.get("surum"))
        return {"kayit": adet, "son_guncelleme": _en_yeni(*tarihler), "kaynak": kaynak,
                "ayrinti": "Kodla birlikte gelir; değişiklik kod güncellemesiyle (PR) yapılır. Tarih dosyadaki son kontrol / sürüm alanıdır."}
    return olc


def _kaynakca(db: Session, bugun: date):
    d = _dosya("kaynakca.json")
    return {"kayit": len(d.get("kaynaklar") or []), "son_guncelleme": None, "kaynak": "Kaynakça (kaynakca.json)",
            "ayrinti": "Akademik kaynaklar ve resmî metinler; bağlantıların erişilebilirliği elle kontrol edilir."}


# ------------------------------------------------------------------------------------------------- kayıt defteri
KAYNAKLAR = [
    # kod, ad, grup, nerede kullanılır, kontrol aralığı (gün), güncelleme ekranı, ölçüm
    ("tuik_istihdam", "Yükseköğretim istihdam göstergeleri", "TÜİK",
     "İş Hayatı, Karşılaştır: istihdam oranı, iş bulma süresi, alan uyumu, kazanç düzeyi", 365, "/admin/is-hayati-verileri", _tuik_istihdam),
    ("tuik_kazanc", "Meslek gruplarına göre kazanç", "TÜİK",
     "İş Hayatı: meslek gruplarının ortalama brüt kazancı", 365, "/admin/is-hayati-verileri", _tuik_kazanc),
    ("asgari_ucret", "Asgari ücret", "Resmî",
     "İş Hayatı: kazançların asgari ücretle karşılaştırılması", 180, "/admin/is-hayati-verileri", _asgari),
    ("kamu_maaslari", "Kamu kadro maaşları", "Resmî",
     "İş Hayatı: kamu kadrolarının net maaş aralıkları", 180, "/admin/is-hayati-verileri", _kamu),
    ("yasam_giderleri", "Yaşam giderleri", "Resmî",
     "İş Hayatı: aylık gider hesabı", 365, "/admin/is-hayati-verileri", _giderler),
    ("yokatlas", "YÖK Atlas: üniversiteler, taban puan, başarı sırası, netler", "YÖK Atlas",
     "Bölüm penceresi, Karşılaştır, Net Takibi", 365, "/admin/yokatlas", _yokatlas),
    ("yks_tarihi", "YKS tarihi", "ÖSYM",
     "Öğrenci geri sayımı, Filiz", 365, "/admin/takvim", _yks_tarihi),
    ("sinav_konulari", "YKS konu listesi", "ÖSYM",
     "Net Takibi › Konu Takibi", 365, "/admin/konular", _sinav_konulari),
    ("bolum_profili", "Bölüm profilleri (uyum hesabının özellik ağırlıkları)", "Pipeline",
     "Uyum yüzdesi, öneriler, raporlar", 365, "/admin/pipeline", _bolum_profili),
    ("k5_baglari", "K5 iş türü bağları (bölüm → iş türü)", "Pipeline",
     "K5 iş türü soruları ve sıralamadaki küme içi düzenleme", 365, "/admin/pipeline", _k5_baglari),
    ("ornek_meslekler", "Bölümlerin örnek meslekleri", "Pipeline",
     "Bölüm sayfası › Meslekler, Karşılaştır", 365, "/admin/pipeline", _ornek_meslekler),
    ("meslekler", "Meslekler ve özellik puanları", "Pipeline",
     "Bölüm profillerinin hesaplanması", 365, "/admin/pipeline", _meslekler),
    ("meslek_isco", "Meslek → ISCO eşleşmesi", "İş Hayatı",
     "Kazanç ve yapay zekâ etkisi verilerinin mesleklere bağlanması", 365, "/admin/is-hayati-verileri", _meslek_isco),
    ("ai_etkisi", "Meslek gruplarında yapay zekâ etkisi", "İş Hayatı",
     "İş Hayatı › Gelecekte Bu Meslek", 365, "/admin/is-hayati-verileri", _ai_etkisi),
    ("bolum_icerik", "Bölüm tanıtımları", "İçerik",
     "Bölüm sayfaları, Filiz, sözlük", 365, "/admin/bolumler", _bolum_icerik),
    ("is_hayati_icerik", "İş Hayatı içerikleri (dersler, CV, mesleğe giden yol, zor günler)", "İçerik",
     "İş Hayatı sekmeleri, Filiz", 365, None,
     _dosya_olcumu([("is_hayati_dersler.json", ""), ("cv_rehberi.json", ""), ("meslege_yol.json", ""), ("zor_gunler.json", "")],
                   "Sistem içerik dosyaları")),
    ("kaynakca", "Kaynakça", "İçerik", "Kaynakça sayfası, Sistem Hakkında", 365, "/admin/kaynakca", _kaynakca),
]
# [2026-11-01] "Nasıl güncellenir?" — Veri Kaynakları ekranında her kaynağın ayrıntısında numaralı adımlar olarak görünür.
_PIPELINE_ADIM = ["Bilgisayarınızda Komut İstemi'ni açıp pipeline çalıştırma komutunu yapıştırın (Claude son komutu verir).",
                  "Çalıştırma bitince çıktıları kontrol ettirin; \"yükleyebilirsiniz\" onayını bekleyin."]
ADIMLAR = {
    "tuik_istihdam": ["data.tuik.gov.tr › Eğitim, Kültür, Spor ve Turizm › Yükseköğretim İstihdam Göstergeleri sayfasını açın.",
                      "\"Lisans mezunlarının bölümlere göre…\" ile başlayan 3 tabloyu (.xls) indirin: kayıtlı istihdam oranı, ilk iş bulma süresi, aylık ortalama kazanç grupları.",
                      "İş Hayatı Verileri › 📊 TÜİK İstihdam Göstergeleri sekmesinde \"TÜİK istihdam göstergelerini yükle\" kutusunda 3 dosyayı birlikte seçin; önizlemeye bakıp kaydedin."],
    "tuik_kazanc": ["TÜİK Kazanç Yapısı Araştırması'nın meslek gruplarına göre kazanç tablosunu indirin (4 yılda bir yayımlanır).",
                    "İş Hayatı Verileri › 💰 Kazanç Yapısı sekmesinden tabloyu yükleyin; o yılın asgari brüt ücretini girip önizlemeyi kontrol edin."],
    "asgari_ucret": ["Resmî Gazete'de yeni asgari ücret yayımlandığında İş Hayatı Verileri › 🧾 Asgari Ücret ve Yaşam Giderleri sekmesinde \"Asgari ücret\" tablosuna yeni dönemi (yürürlük tarihi, brüt, net, kaynak) ekleyin."],
    "kamu_maaslari": ["Yeni memur maaş dönemi (Ocak / Temmuz) açıklandığında İş Hayatı Verileri › 🏛️ Kamu Maaşları sekmesinde kadroların net tutarlarını ve kaynağını güncelleyin."],
    "yasam_giderleri": ["İş Hayatı Verileri › 🧾 Asgari Ücret ve Yaşam Giderleri sekmesinde \"Yaşam giderleri\" tablosuna kira ve temel gider kalemlerini kaynağıyla girin."],
    "yokatlas": ["YÖK Atlas verisi elle yüklenmez: bölüm penceresi açıldıkça YÖK Atlas'tan çekilir ve 7 günde bir yenilenir.",
                 "YÖK Atlas Eşleştirme ekranında \"✗ Eşleşmedi\" görünen bölümleri önerilen program grubuna bağlayın."],
    "yks_tarihi": ["ÖSYM yeni YKS tarihini açıklayınca Genel Takvim › \"+ Etkinlik ekle\" ile sınav türünde, başlığında YKS ya da TYT geçen etkinlikleri (TYT ve AYT/YDT günleri) ekleyin."],
    "sinav_konulari": ["ÖSYM konu listesi değişirse Konu Listesi ekranında dersleri ve konuları güncelleyin."],
    "bolum_profili": _PIPELINE_ADIM + ["Pipeline Sonuçları › 1. adım: C:\\pipeline\\cikti\\bolum_agirliklari.xlsx dosyasını yükleyin, önizlemeye bakıp \"Yayına Al\" deyin. Tüm öğrencilerin sonuçları kendiliğinden yeniden hesaplanır."],
    "k5_baglari": _PIPELINE_ADIM + ["Pipeline Sonuçları › 2. adım: C:\\pipeline\\cikti\\k5_baglari_veri.sql dosyasını seçin, önizlemeye bakıp \"Canlıya al\" deyin. Önceki hâl yedeklenir; gerekirse aynı ekrandan geri dönülür."],
    "ornek_meslekler": _PIPELINE_ADIM + ["Pipeline Sonuçları › 3. adım: C:\\pipeline\\cikti\\ornek_meslekler_veri.sql dosyasını seçin, önizlemeye bakıp \"Canlıya al\" deyin. Önceki hâl yedeklenir."],
    "meslekler": _PIPELINE_ADIM + ["Pipeline Sonuçları › Gelişmiş › Meslek listesi alanından meslek dosyasını yükleyin (yalnızca meslek listesi değiştiyse)."],
    "meslek_isco": ["İş Hayatı Verileri › 🔗 Meslek – ISCO sekmesinde eşleşmeyen meslekleri listeden bir ISCO grubuna bağlayın."],
    "ai_etkisi": ["İş Hayatı Verileri › 🔭 Yapay zekâ etkisi sekmesinde meslek grubu satırlarını yeni çalışmanın verisiyle ve kaynağıyla güncelleyin."],
    "bolum_icerik": ["Bölümler ekranında ilgili bölümü açın, tanıtım metnini düzenleyip kaydedin."],
    "is_hayati_icerik": ["Bu içerikler sistemle birlikte gelir; değişiklik için Claude'dan güncelleme isteyin (kod değişikliğiyle yayınlanır)."],
    "kaynakca": ["Kaynakça ekranından kaynak ekleyin ya da düzenleyin."],
}
_SIRA = {"yok": 0, "sorun": 1, "bekleniyor": 2, "kontrol_zamani": 3, "guncel": 4}


def _kontroller(db: Session, kod: str | None = None, adet: int = 5) -> dict[str, list[dict]]:
    try:
        sql = ("SELECT id, kaynak_kodu, sonuc, notlar, kontrol_eden, zaman FROM ("
               " SELECT *, ROW_NUMBER() OVER (PARTITION BY kaynak_kodu ORDER BY zaman DESC, id DESC) s FROM veri_kaynagi_kontrolleri"
               + (" WHERE kaynak_kodu = :k" if kod else "") + ") x WHERE s <= :a ORDER BY kaynak_kodu, zaman DESC")
        rows = db.execute(text(sql), {"k": kod, "a": adet}).mappings().all()
    except Exception:
        db.rollback()
        return {}
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r["kaynak_kodu"], []).append({
            "id": r["id"], "sonuc": r["sonuc"], "sonuc_ad": SONUCLAR.get(r["sonuc"], r["sonuc"]), "notlar": r["notlar"],
            "kontrol_eden": r["kontrol_eden"], "zaman": _zaman(r["zaman"]).isoformat()})
    return out


def durum_hesapla(olcum: dict | None, son_kontrol: dict | None, aralik: int, simdi: datetime) -> tuple[str, str]:
    """(durum, açıklama). Sıra: yok → sorun → bekleniyor → kontrol zamanı → güncel."""
    if not olcum or not olcum.get("kayit"):
        return "yok", "Sistemde bu veri yok."
    son_veri = _zaman(olcum.get("son_guncelleme"))
    kz = _zaman(son_kontrol["zaman"]) if son_kontrol else None
    if son_kontrol and son_kontrol["sonuc"] == "sorun" and (son_veri is None or son_veri <= kz):
        return "sorun", f"Son kontrolde sorun bildirildi{': ' + son_kontrol['notlar'] if son_kontrol.get('notlar') else ''}."
    if olcum.get("bekleniyor"):
        return "bekleniyor", olcum["bekleniyor"] + "."
    referans = _en_yeni(son_veri, kz if son_kontrol and son_kontrol["sonuc"] in ("guncel", "guncellendi") else None)
    if referans is None:
        return "kontrol_zamani", "Güncelleme zamanı kayıtlı değil; kontrol edip kayıt bırakın."
    gecen = (simdi - referans).days
    if gecen > aralik:
        return "kontrol_zamani", f"Son güncelleme / kontrol {gecen} gün önce (kontrol aralığı {aralik} gün)."
    return "guncel", f"Son güncelleme / kontrol {gecen} gün önce."


def liste(db: Session, bugun: date | None = None) -> dict:
    bugun = bugun or date.today()
    simdi = datetime.now(timezone.utc)
    kontroller = _kontroller(db)
    out = []
    for kod, ad, grup, kullanim, aralik, ekran, olc in KAYNAKLAR:
        try:
            o = olc(db, bugun)
        except Exception:
            db.rollback()
            o = None
        ks = kontroller.get(kod, [])
        durum, aciklama = durum_hesapla(o, ks[0] if ks else None, aralik, simdi)
        o = o or {}
        out.append({"kod": kod, "ad": ad, "grup": grup, "kullanim": kullanim, "kontrol_araligi_gun": aralik, "ekran": ekran,
                    "kayit": o.get("kayit") or 0, "donem": o.get("donem"), "kaynak": o.get("kaynak"), "ayrinti": o.get("ayrinti"),
                    "son_guncelleme": _zaman(o.get("son_guncelleme")).isoformat() if _zaman(o.get("son_guncelleme")) else None,
                    "son_kontrol": ks[0] if ks else None, "kontroller": ks, "durum": durum, "aciklama": aciklama,
                    "adimlar": ADIMLAR.get(kod, [])})
    ozet = {d: sum(1 for x in out if x["durum"] == d) for d in _SIRA}
    out.sort(key=lambda x: (_SIRA[x["durum"]], KAYNAKLAR.index(next(k for k in KAYNAKLAR if k[0] == x["kod"]))))
    return {"kaynaklar": out, "ozet": ozet, "zaman": simdi.isoformat()}


def kontrol_kaydet(db: Session, kod: str, sonuc: str, notlar: str | None, admin) -> dict:
    if kod not in {k[0] for k in KAYNAKLAR}:
        raise KeyError(kod)
    if sonuc not in SONUCLAR:
        raise ValueError(sonuc)
    r = db.execute(text("INSERT INTO veri_kaynagi_kontrolleri (kaynak_kodu, sonuc, notlar, kontrol_eden, admin_id) "
                        "VALUES (:k, :s, :n, :e, :a) RETURNING id, zaman"),
                   {"k": kod, "s": sonuc, "n": (notlar or "").strip()[:1000] or None, "e": getattr(admin, "ad_soyad", None),
                    "a": getattr(admin, "id", None)}).first()
    return {"id": r.id, "zaman": _zaman(r.zaman).isoformat()}


def gecmis(db: Session, kod: str, adet: int = 50) -> list[dict]:
    return _kontroller(db, kod, adet).get(kod, [])


def hatirlat(db: Session, bugun: date | None = None) -> int:
    """Sistemde olmayan, yeni dönemi beklenen ya da kontrol zamanı geçmiş kaynaklar için süper adminlere ayda en çok bir
    özet bildirim (tek_seferlik_gocler işaretiyle). TÜİK istihdamın kendi yıllık hatırlatması (tuik_baglanti) ayrıca sürer."""
    bugun = bugun or date.today()
    v = liste(db, bugun)
    sorunlu = [k for k in v["kaynaklar"] if k["durum"] in ("yok", "bekleniyor", "kontrol_zamani", "sorun")]
    if not sorunlu:
        return 0
    isaret = f"veri_kaynagi_hatirlatma_{bugun.year}_{bugun.month:02d}"
    eklendi = db.execute(text("INSERT INTO tek_seferlik_gocler (ad) VALUES (:a) ON CONFLICT (ad) DO NOTHING RETURNING ad"),
                         {"a": isaret}).first()
    if not eklendi:
        db.rollback()
        return 0
    from app.core.bildirim import bildir
    idler = [r[0] for r in db.execute(text(
        "SELECT id FROM admin_kullanicilar WHERE rol = 'super_admin' AND COALESCE(aktif_mi, TRUE)")).all()]
    ad = {"yok": "sistemde yok", "bekleniyor": "yeni dönem bekleniyor", "kontrol_zamani": "kontrol zamanı geçti", "sorun": "sorun bildirildi"}
    metin = "; ".join(f"{k['ad']} ({ad[k['durum']]})" for k in sorunlu[:8]) + ("…" if len(sorunlu) > 8 else "")
    bildir(db, "yonetim", idler, "sistem", f"{len(sorunlu)} veri kaynağı kontrol bekliyor", metin + ".",
           link="/admin/veri-kaynaklari", eposta=False)
    db.commit()
    return len(sorunlu)
