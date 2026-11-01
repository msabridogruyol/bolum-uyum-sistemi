# -*- coding: utf-8 -*-
"""
[2026-11-01] Pipeline veri deposu. İki tür (ayar: PIPELINE_DEPO):
  * "supabase" (varsayılan): Supabase Storage'da gizli kova — bu dosya.
  * "disk": sunucunun kendi diskindeki klasör (PIPELINE_DEPO_DIZINI) — app/core/pipeline_depo_disk.py.
    Kendi sunucuya taşınınca kullanılır; Render / Supabase gerekmez.
İki tür de aynı işlevleri sunar (hazir_mi, kova_hazirla, mevcut_parcalar, indirme_adresleri, yukleme_adresi,
parcalari_sil, parca_bozuk_mu); sistemin geri kalanı hangisinin kullanıldığını bilmez.

Pipeline'ın veri, önbellek ve çıktı dosyaları (~220 MB) kod deposunda değil, Storage'da tutulur.
  * Dosyalar en fazla PARCA_BOYUTU'luk parçalara bölünür. Supabase ücretsiz planında tek dosya sınırı 50 MB;
    en büyük önbellek dosyası bu sınıra yakın ve büyüyor.
  * Her parça içeriğinin SHA-256 özetiyle saklanır: parca/<sha256>. Değişmeyen parça bir daha gönderilmez.
    Hangi dosyanın hangi parçalardan oluştuğu pipeline_surumleri tablosunda durur.
  * Bilgisayar dosyaları sunucu üzerinden geçirmez; sunucu kısa süreli imzalı adres verir, bilgisayar doğrudan
    Storage'a yükler ya da Storage'dan indirir (Render'ın bellek ve süre sınırına takılmaz).
Anahtarlar yalnızca Render Environment'tadır (SUPABASE_URL, SUPABASE_SERVICE_KEY). Ek kütüphane gerekmez.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from app.core.config import settings

PARCA_BOYUTU = 20 * 1024 * 1024
PARCA_ONEKI = "parca/"


class DepoHatasi(Exception):
    pass


def tur() -> str:
    return (settings.PIPELINE_DEPO or "supabase").strip().lower()


def _disk():
    from app.core import pipeline_depo_disk
    return pipeline_depo_disk


def _disk_mi() -> bool:
    return tur() == "disk"


def hazir_mi() -> bool:
    if _disk_mi():
        return _disk().hazir_mi()
    return bool(settings.SUPABASE_URL.strip() and settings.SUPABASE_SERVICE_KEY.strip())


def eksik_ayar_metni() -> str:
    """Depo hazır değilse ekranda gösterilecek: ne eksik."""
    if _disk_mi():
        return f"Disk deposu klasörü yazılamıyor ya da yok: {settings.PIPELINE_DEPO_DIZINI}"
    return "SUPABASE_URL ve SUPABASE_SERVICE_KEY ortam değişkenleri tanımlı değil."


def baglanti_sina() -> str | None:
    """Depoya gerçekten bağlanılabiliyor mu (ayar var ama anahtar ya da adres yanlış olabilir). Sorun yoksa None,
    varsa ekranda gösterilecek açıklama. Admin panelindeki "bağlı ✓" buna dayanır."""
    if not hazir_mi():
        return eksik_ayar_metni()
    if _disk_mi():
        return None
    try:
        kova_hazirla()          # anahtar / adres yanlışsa burada ya da listede hata verir
        mevcut_parcalar()
    except DepoHatasi as e:
        return str(e)
    return None


def _kova() -> str:
    return (settings.PIPELINE_DEPO_KOVA or "pipeline").strip()


def _taban() -> str:
    """Yalnızca proje adresi kullanılır: sonuna /rest/v1, / gibi ekler yapıştırılmış olsa da https://<proje>.supabase.co."""
    u = urllib.parse.urlparse(settings.SUPABASE_URL.strip())
    return f"{u.scheme or 'https'}://{u.netloc or u.path.strip('/')}/storage/v1"


def _kimlik_basliklari() -> dict:
    """Supabase iki tür sunucu anahtarı verir:
      * eski service_role anahtarı (JWT, "eyJ..." ile başlar): apikey + Authorization: Bearer
      * yeni gizli anahtar ("sb_secret_..."): YALNIZCA apikey başlığında (Supabase belgesi: Bearer'da kullanılmaz)."""
    anahtar = settings.SUPABASE_SERVICE_KEY.strip()
    if anahtar.startswith("eyJ"):
        return {"Authorization": f"Bearer {anahtar}", "apikey": anahtar}
    return {"apikey": anahtar}


def _istek(yontem: str, yol: str, govde=None, zaman_asimi: int = 30, ek_baslik: dict | None = None):
    if not hazir_mi():
        raise DepoHatasi("Pipeline deposu yapılandırılmamış (Render → Environment: SUPABASE_URL ve SUPABASE_SERVICE_KEY).")
    veri = None if govde is None else json.dumps(govde).encode("utf-8")
    istek = urllib.request.Request(_taban() + yol, data=veri, method=yontem,
                                   headers={**_kimlik_basliklari(), "Content-Type": "application/json", **(ek_baslik or {})})
    try:
        with urllib.request.urlopen(istek, timeout=zaman_asimi) as yanit:
            ham = yanit.read()
            return yanit.status, (json.loads(ham) if ham else None)
    except urllib.error.HTTPError as e:
        ham = e.read()
        try:
            icerik = json.loads(ham) if ham else None
        except ValueError:
            icerik = {"message": ham[:200].decode("utf-8", "replace")}
        return e.code, icerik
    except (urllib.error.URLError, TimeoutError) as e:
        raise DepoHatasi(f"Depoya ulaşılamadı: {e}")


def _mutlak(adres: str) -> str:
    """Storage bazen tam, bazen /object/... biçiminde göreli adres döner; ikisi de tam adrese çevrilir."""
    if adres.startswith("http://") or adres.startswith("https://"):
        return adres
    return _taban() + (adres if adres.startswith("/") else "/" + adres)


def kova_hazirla() -> None:
    """Kova yoksa gizli olarak oluşturur (tekrar çağırmak güvenli)."""
    if _disk_mi():
        return _disk().kova_hazirla()
    durum, _ = _istek("GET", f"/bucket/{_kova()}")
    if durum == 200:
        return
    durum, icerik = _istek("POST", "/bucket", {"id": _kova(), "name": _kova(), "public": False})
    if durum not in (200, 201) and "already exists" not in json.dumps(icerik or {}).lower():
        raise DepoHatasi(f"Depo kovası oluşturulamadı ({durum}): {icerik}")


def parca_yolu(sha256: str) -> str:
    return PARCA_ONEKI + sha256


def mevcut_parcalar() -> dict[str, str]:
    """Depodaki tüm parçalar: özet → oluşturma zamanı (ISO metin; bilinmiyorsa boş)."""
    if _disk_mi():
        return _disk().mevcut_parcalar()
    sonuc, kayma = {}, 0
    while True:
        durum, icerik = _istek("POST", f"/object/list/{_kova()}",
                               {"prefix": PARCA_ONEKI.rstrip("/"), "limit": 1000, "offset": kayma,
                                "sortBy": {"column": "name", "order": "asc"}})
        if durum != 200:
            raise DepoHatasi(f"Depo listelenemedi ({durum}): {icerik}")
        kayitlar = [x for x in (icerik or []) if x.get("name")]
        for x in kayitlar:
            sonuc[x["name"].rsplit("/", 1)[-1]] = x.get("created_at") or ""
        if len(kayitlar) < 1000:
            return sonuc
        kayma += 1000


def indirme_adresleri(ozetler: list[str], sure_sn: int = 3600) -> dict[str, str]:
    if _disk_mi():
        return _disk().indirme_adresleri(ozetler, sure_sn)
    sonuc = {}
    for i in range(0, len(ozetler), 200):
        grup = ozetler[i:i + 200]
        durum, icerik = _istek("POST", f"/object/sign/{_kova()}",
                               {"expiresIn": sure_sn, "paths": [parca_yolu(o) for o in grup]})
        if durum != 200 or not isinstance(icerik, list):
            raise DepoHatasi(f"İndirme adresi alınamadı ({durum}): {icerik}")
        yola_gore = {k.get("path"): k for k in icerik if isinstance(k, dict)}   # sıraya değil yola göre eşlenir
        for o in grup:
            kayit = yola_gore.get(parca_yolu(o)) or {}
            adres = kayit.get("signedURL") or kayit.get("signedUrl")
            if not adres:
                raise DepoHatasi(f"Parça depoda yok: {o[:12]}… ({kayit.get('error')})")
            sonuc[o] = _mutlak(adres)
    return sonuc


def yukleme_adresi(sha256: str) -> str:
    if _disk_mi():
        return _disk().yukleme_adresi(sha256)
    # x-upsert imza anında verilir: yükleme zaman aşımına uğrayıp tekrar denenirse "zaten var" hatası olmasın
    durum, icerik = _istek("POST", f"/object/upload/sign/{_kova()}/{parca_yolu(sha256)}", {}, ek_baslik={"x-upsert": "true"})
    adres = (icerik or {}).get("url") or (icerik or {}).get("signedURL")
    if durum != 200 or not adres:
        raise DepoHatasi(f"Yükleme adresi alınamadı ({durum}): {icerik}")
    return _mutlak(adres)


def parcalari_sil(ozetler: list[str]) -> int:
    if _disk_mi():
        return _disk().parcalari_sil(ozetler)
    for i in range(0, len(ozetler), 500):
        grup = [parca_yolu(o) for o in ozetler[i:i + 500]]
        durum, icerik = _istek("DELETE", f"/object/{_kova()}", {"prefixes": grup})
        if durum != 200:
            raise DepoHatasi(f"Eski parçalar silinemedi ({durum}): {icerik}")
    return len(ozetler)


def parca_bozuk_mu(sha256: str) -> bool:
    """Parçayı depodan okuyup içerik özetini denetler (adı içeriğiyle uyuşmuyorsa True). Bozuksa silinir; ilk gönderen
    bilgisayar bir sonraki gönderimde yeniden yükler."""
    if _disk_mi():
        return _disk().parca_bozuk_mu(sha256)
    import hashlib
    istek = urllib.request.Request(f"{_taban()}/object/{_kova()}/{parca_yolu(sha256)}", headers=_kimlik_basliklari())
    h = hashlib.sha256()
    try:
        with urllib.request.urlopen(istek, timeout=120) as y:
            while True:
                blok = y.read(1024 * 1024)
                if not blok:
                    break
                h.update(blok)
    except urllib.error.HTTPError as e:
        if e.code in (400, 404):
            return False   # zaten yok: yeniden yüklenebilir
        raise DepoHatasi(f"Parça okunamadı ({e.code}).")
    if h.hexdigest() == sha256:
        return False
    parcalari_sil([sha256])
    return True
