"""
[2026-10-11] Hata izleme.

  * HataYakalamaAraKatmani (saf ASGI): her isteğe istek kimliği verir (gelen geçerli X-Istek-Kimligi korunur) ve tüm
    yanıtlara X-Istek-Kimligi başlığını ekler. Yakalanmamış istisnada kullanıcıya genel Türkçe 500 mesajı + istek kimliği
    döner; istisna hata_kayitlari tablosuna (parmak izine göre gruplu, sayaçlı) yazılır.
  * maskele(): e-posta, telefon, TC kimlik no, JWT/Bearer, şifre/token alanları, base64 blokları ve SQLAlchemy
    "[parameters: ...]" bölümü kayda girmeden ayıklanır.
  * Yeni (ya da çözüldükten sonra yeniden görülen) hata grubunda süper adminlere günde EN ÇOK BİR bildirim
    (tek_seferlik_gocler'de 'hata_bildirimi_YYYY-MM-DD' işareti; app.core.bildirim.bildir, alici_tipi 'yonetim').
  * İsteğe bağlı Sentry: SENTRY_DSN ortam değişkeni varsa ve sentry-sdk kuruluysa başlatılır (yoksa sessizce atlanır).
  * Aynı parmak izi kısa sürede tekrar tekrar gelirse (döngüdeki hata) veritabanına en çok 2 sn'de bir yazılır;
    aradaki tekrarlar sayaca eklenir.
Kayıt yazma başarısız olursa asıl yanıt ASLA bozulmaz.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import threading
import time
import traceback
import uuid

log = logging.getLogger("hata_izleme")

# ----------------------------------------------------------------------------- maskeleme
_DESENLER = [
    (re.compile(r"\[parameters: .*?\](?=\s*(\(|\[|$))", re.S), "[parameters: <ayıklandı>]"),
    (re.compile(r"data:[\w/+.-]+;base64,[A-Za-z0-9+/=]+"), "<base64>"),
    (re.compile(r"\beyJ[\w-]{5,}\.[\w-]{5,}\.[\w-]{5,}"), "<token>"),
    (re.compile(r"(?i)\bbearer\s+[\w.\-~+/=]+"), "Bearer <token>"),
    (re.compile(r"(?i)((?<!\w)[\"']?(?:sifre|şifre|parola|password|passwd|yeni_sifre|eski_sifre|token|erisim_tokeni|yenileme_tokeni|"
                r"gecici_token|cihaz_tokeni|access_token|refresh_token|secret|api[_-]?key|authorization|kod|dogrulama_kodu)"
                r"[\"']?\s*[:=]\s*)(\"[^\"]*\"|'[^']*'|[^\s,&;)}\]]+)"), r"\1<gizli>"),
    (re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+"), "<e-posta>"),
    (re.compile(r"(?<!\d)(?:\+?90[\s-]?)?0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}(?!\d)"), "<telefon>"),
    (re.compile(r"(?<!\d)[1-9]\d{10}(?!\d)"), "<tc>"),
    (re.compile(r"[A-Za-z0-9+/]{200,}={0,2}"), "<uzun-veri>"),
]


def maskele(metin: str | None, en_fazla: int | None = None) -> str:
    if not metin:
        return ""
    s = str(metin)
    for desen, yerine in _DESENLER:
        s = desen.sub(yerine, s)
    if en_fazla and len(s) > en_fazla:
        s = s[:en_fazla] + "…"
    return s


def yigin_kisalt(metin: str, en_fazla_satir: int = 60, en_fazla_karakter: int = 8000) -> str:
    """Yığın izinin SON kısmı (asıl hatanın olduğu yer) korunur."""
    satirlar = (metin or "").splitlines()
    if len(satirlar) > en_fazla_satir:
        satirlar = ["… (" + str(len(satirlar) - en_fazla_satir) + " satır kısaltıldı)"] + satirlar[-en_fazla_satir:]
    s = "\n".join(satirlar)
    if len(s) > en_fazla_karakter:
        s = "…" + s[-en_fazla_karakter:]
    return maskele(s)


# ----------------------------------------------------------------------------- parmak izi
_KIMLIK_PARCASI = re.compile(r"/(\d+|[0-9a-fA-F]{8}-[0-9a-fA-F-]{27,}|[0-9a-fA-F]{24,})(?=/|$)")
_DERLEME_HASH = re.compile(r"-[A-Za-z0-9_-]{8}\.(js|css)")


def yol_kalibi(yol: str) -> str:
    return _KIMLIK_PARCASI.sub("/{id}", (yol or "").split("?")[0])[:300]


def parmak_izi(kaynak: str, istisna_turu: str, yol: str, konum: str) -> str:
    ham = "|".join([kaynak, istisna_turu or "", yol_kalibi(yol), konum or ""])
    return hashlib.sha1(ham.encode("utf-8", "replace")).hexdigest()


def _sunucu_konumu(exc: BaseException) -> str:
    """En içteki uygulama (app/) çerçevesi: dosya:fonksiyon — satır numarası kod kaydıkça grubu bölmesin diye yok."""
    tb = traceback.extract_tb(exc.__traceback__)
    uygulama = [f for f in tb if "/app/" in f.filename.replace("\\", "/")]
    f = (uygulama or tb or [None])[-1]
    if f is None:
        return ""
    return f"{f.filename.replace(chr(92), '/').split('/app/')[-1]}:{f.name}"


def istemci_konumu(yigin: str, mesaj: str) -> str:
    ilk = next((s.strip() for s in (yigin or "").splitlines() if re.search(r"(at |@).*\.(js|jsx|ts|tsx)", s)), "")
    ilk = _DERLEME_HASH.sub(r".\1", re.sub(r"https?://[^/\s]+", "", ilk))
    ilk = re.sub(r":\d+:\d+\)?$", "", ilk)
    duz_mesaj = re.sub(r"\d+", "#", (mesaj or ""))[:160]
    return f"{duz_mesaj}|{ilk[:200]}"


# ----------------------------------------------------------------------------- kayıt
_son_yazim: dict[str, list] = {}   # parmak izi → [son_yazım_zamanı, bekleyen_tekrar]
_yazim_kilidi = threading.Lock()
YAZIM_ARALIGI_SN = 2.0


def _kullanici_tipi_tokendan(yetki: str | None) -> str:
    if not yetki or not yetki.startswith("Bearer "):
        return "anonim"
    try:
        from app.core.security import token_coz
        p = token_coz(yetki[7:].strip()) or {}
    except Exception:
        return "anonim"
    rol = p.get("rol")
    return {"super_admin": "super_admin", "okul_yetkilisi": "okul_yetkilisi", "ogrenci": "ogrenci"}.get(rol, "anonim")


def kaydet(*, kaynak: str, yol: str, metod: str | None, durum_kodu: int | None, istisna_turu: str, mesaj: str,
           yigin: str, kullanici_tipi: str, istek_kimligi: str | None, konum: str, tarayici: str | None = None,
           db_fabrikasi=None) -> dict | None:
    """Gruplu kayıt (upsert). Dönen: {'id', 'yeni'} ya da yazım ertelendiyse / başarısızsa None."""
    pi = parmak_izi(kaynak, istisna_turu, yol, konum)
    simdi = time.monotonic()
    with _yazim_kilidi:
        d = _son_yazim.get(pi)
        if d and simdi - d[0] < YAZIM_ARALIGI_SN:
            d[1] += 1
            return None
        ek = d[1] if d else 0
        _son_yazim[pi] = [simdi, 0]
        if len(_son_yazim) > 5000:
            _son_yazim.clear()
    try:
        from sqlalchemy import text
        if db_fabrikasi is None:
            from app.core.database import SessionLocal as db_fabrikasi
        db = db_fabrikasi()
        try:
            onceki = db.execute(text("SELECT id, cozuldu_mu FROM hata_kayitlari WHERE parmak_izi = :p"), {"p": pi}).first()
            iz = json.dumps({"k": istek_kimligi, "y": maskele(yol, 300), "z": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())})
            r = db.execute(text("""
                INSERT INTO hata_kayitlari (parmak_izi, kaynak, yol, yol_kalibi, metod, durum_kodu, istisna_turu, mesaj, yigin_izi,
                                            kullanici_tipi, istek_kimligi, tarayici, sayi, son_istekler)
                VALUES (:p, :ka, :y, :yk, :m, :d, :t, :me, :yi, :ku, :ik, :tr, :s, jsonb_build_array(CAST(:iz AS jsonb)))
                ON CONFLICT (parmak_izi) DO UPDATE SET
                    sayi = hata_kayitlari.sayi + EXCLUDED.sayi, son_gorulme = now(),
                    yol = EXCLUDED.yol, metod = EXCLUDED.metod, durum_kodu = EXCLUDED.durum_kodu, mesaj = EXCLUDED.mesaj,
                    yigin_izi = EXCLUDED.yigin_izi, kullanici_tipi = EXCLUDED.kullanici_tipi,
                    istek_kimligi = EXCLUDED.istek_kimligi, tarayici = EXCLUDED.tarayici,
                    son_istekler = jsonb_path_query_array(EXCLUDED.son_istekler || hata_kayitlari.son_istekler, '$[0 to 19]'),
                    cozuldu_mu = FALSE, cozulme_zamani = NULL, cozen = NULL
                RETURNING id
            """), {"p": pi, "ka": kaynak, "y": maskele(yol, 500), "yk": yol_kalibi(maskele(yol)), "m": (metod or "")[:10] or None,
                   "d": durum_kodu, "t": (istisna_turu or "")[:200], "me": maskele(mesaj, 2000), "yi": yigin_kisalt(yigin),
                   "ku": kullanici_tipi, "ik": istek_kimligi, "tr": maskele(tarayici, 300) or None, "s": 1 + ek, "iz": iz}).first()
            yeni = onceki is None or bool(onceki.cozuldu_mu)
            db.commit()
            if yeni:
                _gunluk_bildirim(db, istisna_turu, yol_kalibi(yol), kaynak)
            return {"id": r[0], "yeni": yeni}
        finally:
            db.close()
    except Exception as e:  # tablo yoksa vb. — asıl isteği etkilemesin
        log.warning("Hata kaydı yazılamadı: %s", str(e).splitlines()[0][:200] if str(e) else type(e).__name__)
        return None


def _gunluk_bildirim(db, istisna_turu: str, yol: str, kaynak: str) -> bool:
    try:
        from sqlalchemy import text
        from app.core.bildirim import bildir
        isaret = "hata_bildirimi_" + time.strftime("%Y-%m-%d", time.gmtime())
        eklendi = db.execute(text("INSERT INTO tek_seferlik_gocler (ad) VALUES (:a) ON CONFLICT (ad) DO NOTHING RETURNING ad"),
                             {"a": isaret}).first()
        if not eklendi:
            db.rollback()
            return False
        idler = [r[0] for r in db.execute(text(
            "SELECT id FROM admin_kullanicilar WHERE rol = 'super_admin' AND COALESCE(aktif_mi, TRUE)")).all()]
        bildir(db, "yonetim", idler, "sistem", "Yeni hata kaydı",
               f"{'Tarayıcıda' if kaynak == 'istemci' else 'Sunucuda'} yeni bir hata türü görüldü: {istisna_turu[:80]} · {yol[:120]}. "
               "Ayrıntılar Hata Kayıtları sayfasında (bugün başka bildirim gönderilmeyecek).",
               link="/admin/hata-kayitlari", eposta=True)
        db.commit()
        return True
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        return False


# ----------------------------------------------------------------------------- Sentry (isteğe bağlı)
_sentry = None


def sentry_baslat() -> bool:
    """SENTRY_DSN varsa ve sentry-sdk kuruluysa başlatır. Paket yoksa sessizce atlar."""
    global _sentry
    dsn = os.environ.get("SENTRY_DSN", "").strip()
    if not dsn:
        return False
    try:
        import sentry_sdk  # type: ignore
    except Exception:
        log.info("SENTRY_DSN tanımlı ama sentry-sdk kurulu değil; Sentry atlandı.")
        return False

    def _ayikla(olay, _ipucu):
        try:
            for ex in (olay.get("exception") or {}).get("values") or []:
                ex["value"] = maskele(ex.get("value"))
            if "request" in olay:
                olay["request"].pop("cookies", None)
                olay["request"].pop("data", None)
                h = olay["request"].get("headers") or {}
                for k in list(h):
                    if k.lower() in ("authorization", "cookie"):
                        h[k] = "<gizli>"
        except Exception:
            pass
        return olay

    try:
        sentry_sdk.init(dsn=dsn, send_default_pii=False, before_send=_ayikla,
                        traces_sample_rate=float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0") or 0),
                        environment=os.environ.get("SENTRY_ENVIRONMENT", "production"))
        _sentry = sentry_sdk
        return True
    except Exception:
        return False


def _sentry_bildir(exc: BaseException, istek_kimligi: str) -> None:
    if _sentry is None:
        return
    try:
        with _sentry.push_scope() as kapsam:
            kapsam.set_tag("istek_kimligi", istek_kimligi)
            _sentry.capture_exception(exc)
    except Exception:
        pass


# ----------------------------------------------------------------------------- ara katman
_GECERLI_KIMLIK = re.compile(r"^[A-Za-z0-9_-]{8,64}$")


def genel_500_govdesi(istek_kimligi: str) -> bytes:
    return json.dumps({
        "detail": f"Beklenmeyen bir hata oluştu; sorun kaydedildi. Tekrar dener misiniz? Sürerse destek ekibine şu kodu iletin: {istek_kimligi}",
        "istek_kimligi": istek_kimligi,
    }, ensure_ascii=False).encode("utf-8")


class HataYakalamaAraKatmani:
    def __init__(self, app, db_fabrikasi=None):
        self.app = app
        self.db_fabrikasi = db_fabrikasi

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        basliklar = {k.decode("latin-1"): v.decode("latin-1") for k, v in scope.get("headers") or []}
        gelen = basliklar.get("x-istek-kimligi", "")
        kimlik = gelen if _GECERLI_KIMLIK.match(gelen) else uuid.uuid4().hex[:20]
        scope.setdefault("state", {})["istek_kimligi"] = kimlik
        basladi = False

        async def ekle_send(mesaj):
            nonlocal basladi
            if mesaj["type"] == "http.response.start":
                basladi = True
                mesaj = dict(mesaj)
                mesaj["headers"] = list(mesaj.get("headers") or []) + [(b"x-istek-kimligi", kimlik.encode())]
            await send(mesaj)

        try:
            await self.app(scope, receive, ekle_send)
        except Exception as exc:  # noqa: BLE001
            yol = scope.get("path", "")
            log.exception("Yakalanmamış hata [%s] %s %s", kimlik, scope.get("method"), yol)
            _sentry_bildir(exc, kimlik)
            try:
                import anyio
                yigin = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
                await anyio.to_thread.run_sync(lambda: kaydet(
                    kaynak="sunucu", yol=yol, metod=scope.get("method"), durum_kodu=500,
                    istisna_turu=f"{type(exc).__module__}.{type(exc).__name__}".removeprefix("builtins."),
                    mesaj=str(exc), yigin=yigin, kullanici_tipi=_kullanici_tipi_tokendan(basliklar.get("authorization")),
                    istek_kimligi=kimlik, konum=_sunucu_konumu(exc), tarayici=basliklar.get("user-agent"),
                    db_fabrikasi=self.db_fabrikasi))
            except Exception:
                pass
            if basladi:   # yanıt yarıda kaldı — yapılacak bir şey yok
                return
            govde = genel_500_govdesi(kimlik)
            await send({"type": "http.response.start", "status": 500, "headers": [
                (b"content-type", b"application/json; charset=utf-8"), (b"content-length", str(len(govde)).encode()),
                (b"x-istek-kimligi", kimlik.encode())]})
            await send({"type": "http.response.body", "body": govde})
