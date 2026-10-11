# -*- coding: utf-8 -*-
"""
[2026-10-10] Okul paneli → Rapor Merkezi → "Tek Bakışta" (yönetici özeti).

GET /yonetim/okul/{okul_id}/tek-bakista?sinif=&sube=      — bulgular, KPI, kritik öğrenciler, akademik sıralama,
                                                          şube karşılaştırma, grafik verileri, hedef–uyum (tek istek)
GET /yonetim/okul/{okul_id}/tek-bakista/pdf?sinif=&sube=  — aynı veriler "Yönetici özeti" PDF'i (isimli, okul içi)

Kapsam / yetki: okul_yonetimi._okul_kapsami (okul yetkilisi yalnızca kendi okulu). Test hesapları sayılmaz.
Öğrenci kümesi ve koçluk etkinliği okul_istatistik.py'deki ortak yardımcılardan; kritik öğrenciler rehberlik.uyarilari_hesapla
(erken uyarı motoru) ile. Rehberlik modülü kapalıysa liste yalnızca katılım kurallarından (hiç giriş yok, test yarıda,
doğrulanamayan tur) oluşur. Paket modülü kapalı bölümler (akademik, koçluk) hesaplanmaz ve dönmez.

Etik: kişilik / değer / ilgi puanlarına göre sıralama YAPILMAZ (profil performans değildir). Sıralamalar yalnızca net,
net değişimi, katılım ve hedef uyumu ölçütleriyle. Okul kendi öğrencilerini isimle gördüğü için küçük grup gizleme yoktur.
"Okul ortalaması" her zaman tüm okuldur (filtre yalnızca gösterilen öğrencileri / şubeleri daraltır).
Performans: sabit sayıda toplu SQL; öğrenci başına sorgu yok.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_istatistik import _baslik, _ort, _sinif_sira, _yuzde, kocluk_etkinligi, ogrenci_kumesi
from app.api.okul_yonetimi import _durum, _ilerleme, _okul_kapsami, _sinif_metni, sube_etiketi
from app.core.database import get_db
from app.core.hesap_yonetimi import denetim_yaz
from app.core.paketler import okul_modulleri
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim", tags=["Okul istatistikleri"])
TR = ZoneInfo("Europe/Istanbul")

BELIRGIN_FARK = 15          # bulgu: okul ortalamasından en az bu kadar puan (yüzde puanı) ayrışma "belirgin" sayılır
HAFIF_FARK = 5              # şube tablosu renklendirme: bunun altı nötr
UYUM_DUSUK = 40             # hedef bölüm uyumu: sistem istatistiklerindeki "yetmiyor" bandı (< 40)
KOCLUK_GUN = 30             # "koçlukta aktif": son 30 günde adım ya da görev tamamlayan
OKUL_DENEME_GUNCEL_GUN = 180  # okul denemesi bundan eskiyse ve Net Takibi açıksa öğrencilerin kendi son denemeleri kullanılır
KATILIM_KURALLARI = {"giris_yok", "yarim_test"}   # rehberlik modülü kapalıyken kullanılan erken uyarı kuralları
SEVIYE_AD = {"yuksek": "Yüksek", "orta": "Orta", "dusuk": "Düşük"}


def _tr_sayi(x, kesir=1) -> str:
    if x is None:
        return "—"
    s = f"{x:.{kesir}f}".rstrip("0").rstrip(".") if kesir else f"{x:.0f}"
    return s.replace(".", ",")


def _isaretli(x) -> str:
    return ("+" if x > 0 else "−" if x < 0 else "") + _tr_sayi(abs(x))


def _gun_iso(z) -> str | None:
    if not z:
        return None
    if z.tzinfo is None:
        z = z.replace(tzinfo=timezone.utc)
    return z.astimezone(TR).isoformat()


# ============================================================================= kritik öğrenciler
def _kritik_liste(db: Session, okul_id: int, tum: list, gecersiz: set, rehberlik_acik: bool) -> tuple[list, list]:
    """(gösterilecek liste, ham erken uyarı listesi). Ham liste bulgular için (yarıda kalan / hiç giriş yok sayıları)."""
    from app.api.rehberlik import SEVIYE_PUAN, uyarilari_hesapla
    ham = uyarilari_hesapla(db, okul_id)
    if rehberlik_acik:
        return ham, ham
    ogr = {str(o.id): o for o in tum}
    liste = {}
    for s in ham:
        u = [x for x in s["uyarilar"] if x["kural"] in KATILIM_KURALLARI]
        if u:
            liste[s["ogrenci_id"]] = {**s, "uyarilar": u, "son_gorusme": None, "yaklasan_gorusme": None}
    for oid in gecersiz:
        k = str(oid)
        if k not in ogr:
            continue
        x = {"kural": "dogrulanamadi", "ad": "Değerlendirme doğrulanamadı", "seviye": "orta",
             "metin": "Son değerlendirmenin güvenilirlik kontrolü düşük; yeniden değerlendirme önerilir."}
        if k in liste:
            liste[k]["uyarilar"].append(x)
        else:
            o = ogr[k]
            liste[k] = {"ogrenci_id": k, "ad_soyad": o.ad_soyad, "sinif_metni": _sinif_metni(o), "sinif": o.sinif,
                        "uyarilar": [x], "son_gorusme": None, "yaklasan_gorusme": None}
    sonuc = []
    for s in liste.values():
        s["puan"] = sum(SEVIYE_PUAN[u["seviye"]] for u in s["uyarilar"])
        s["seviye"] = max(s["uyarilar"], key=lambda u: SEVIYE_PUAN[u["seviye"]])["seviye"]
        sonuc.append(s)
    sonuc.sort(key=lambda s: (-SEVIYE_PUAN[s["seviye"]], -s["puan"], s["ad_soyad"].lower()))
    return sonuc, ham


# ============================================================================= akademik
def _akademik(db: Session, okul_id: int, tum: list, secili: set, moduller: set) -> dict | None:
    """Oturum başına (TYT, AYT): kaynak, sıralamalar, değişim, trend. Kaynak seçimi:
    - Okul Denemeleri açık ve son okul denemesi güncelse (≤180 gün) → son okul denemesi (herkes aynı sınava girdi; en adil kıyas)
    - değilse Net Takibi açıksa → her öğrencinin kendi girdiği son deneme
    Değişim: son iki okul denemesi (her ikisine giren öğrenciler); tek okul denemesi varsa ve Net Takibi açıksa öğrencinin son iki denemesi."""
    okul_acik, net_acik = "okul_denemeleri" in moduller, "net_takibi" in moduller
    if not (okul_acik or net_acik) or not tum:
        return None
    ids = [o.id for o in tum]
    ogr = {o.id: o for o in tum}
    bugun = datetime.now(TR).date()

    od_rows = db.execute(text("""
        SELECT od.id, od.ad, od.tarih, od.oturum, d.ogrenci_id, d.toplam_net
          FROM okul_denemeleri od JOIN ogrenci_denemeleri d ON d.okul_deneme_id = od.id
         WHERE od.okul_id = :ok AND d.ogrenci_id = ANY(:ids) ORDER BY od.tarih, od.id"""),
        {"ok": okul_id, "ids": ids}).all() if okul_acik and okul_id else []
    okul_den = defaultdict(dict)    # oturum → {deneme_id: {ad, tarih, netler{ogr: net}}}
    for r in od_rows:
        d = okul_den[r.oturum].setdefault(r.id, {"id": r.id, "ad": r.ad, "tarih": r.tarih, "netler": {}})
        d["netler"][r.ogrenci_id] = float(r.toplam_net)

    son2 = defaultdict(lambda: defaultdict(list))   # oturum → ogr → [(tarih, net), ...] (yeniden eskiye, en çok 2)
    aylik = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))   # oturum → ay → ogr → [net]
    if net_acik:
        for r in db.execute(text("""
            SELECT ogrenci_id, oturum, tarih, toplam_net FROM (
                SELECT ogrenci_id, oturum, tarih, toplam_net,
                       row_number() OVER (PARTITION BY ogrenci_id, oturum ORDER BY tarih DESC, id DESC) AS sira
                  FROM ogrenci_denemeleri WHERE ogrenci_id = ANY(:ids)) x WHERE sira <= 2
             ORDER BY ogrenci_id, oturum, sira"""), {"ids": ids}).all():
            son2[r.oturum][r.ogrenci_id].append((r.tarih, float(r.toplam_net)))
        for r in db.execute(text("""
            SELECT oturum, to_char(tarih, 'YYYY-MM') AS ay, ogrenci_id, avg(toplam_net) AS net FROM ogrenci_denemeleri
             WHERE ogrenci_id = ANY(:ids) AND tarih >= :bas GROUP BY 1, 2, 3"""),
                {"ids": ids, "bas": (bugun.replace(day=1) - timedelta(days=150)).replace(day=1)}).all():
            aylik[r.oturum][r.ay][r.ogrenci_id].append(float(r.net))

    def satir(oid, net, okul_ort):
        o = ogr[oid]
        return {"ogrenci_id": str(oid), "ad_soyad": o.ad_soyad, "sube": _sinif_metni(o) or "—", "net": round(net, 2),
                "fark": round(net - okul_ort, 2) if okul_ort is not None else None}

    oturumlar = {}
    for ot in ("TYT", "AYT"):
        dl = list(okul_den[ot].values())
        son_okul = dl[-1] if dl else None
        okul_guncel = son_okul is not None and (bugun - son_okul["tarih"]).days <= OKUL_DENEME_GUNCEL_GUN
        kaynak = "okul" if son_okul is not None and (okul_guncel or not net_acik) else ("ogrenci" if son2[ot] else None)
        if kaynak is None:
            continue
        x: dict = {"oturum": ot, "kaynak": kaynak}
        if kaynak == "okul":
            netler = son_okul["netler"]
            x["kaynak_metni"] = f"Son okul denemesi: {son_okul['ad']} ({son_okul['tarih'].strftime('%d.%m.%Y')}) · {len(netler)} öğrenci katıldı"
            x["deneme"] = {"ad": son_okul["ad"], "tarih": son_okul["tarih"].isoformat()}
        else:
            netler = {i: l[0][1] for i, l in son2[ot].items()}
            x["kaynak_metni"] = "Her öğrencinin Net Takibi'ne girdiği son deneme (deneme tarihleri öğrenciye göre değişebilir)"
        okul_ort = _ort(netler.values())
        sec = {i: n for i, n in netler.items() if i in secili}
        x["okul_ort"] = okul_ort
        x["kapsam_ort"] = _ort(sec.values())
        x["katilim"] = len(sec)
        x["ogr_net"] = sec   # (iç kullanım: şube tablosu / KPI) — yanıtta çıkarılır
        sirali = sorted(sec.items(), key=lambda kv: (-kv[1], ogr[kv[0]].ad_soyad))
        x["en_yuksek"] = [satir(i, n, okul_ort) for i, n in sirali[:10]]
        kalan = sirali[10:]
        x["en_dusuk"] = [satir(i, n, okul_ort) for i, n in sorted(kalan, key=lambda kv: (kv[1], ogr[kv[0]].ad_soyad))[:10]]

        # değişim
        deg, deg_metni, onceki_ort = {}, None, None
        if kaynak == "okul" and len(dl) >= 2:
            onceki = dl[-2]
            deg = {i: (onceki["netler"][i], n) for i, n in sec.items() if i in onceki["netler"]}
            deg_metni = f"{onceki['ad']} → {son_okul['ad']} (iki denemeye de giren öğrenciler)"
            onceki_ort = _ort(n for i, n in onceki["netler"].items() if i in secili)
        elif net_acik:
            deg = {i: (l[1][1], l[0][1]) for i, l in son2[ot].items() if i in secili and len(l) >= 2}
            if deg:
                deg_metni = "Öğrencinin Net Takibi'ndeki son iki denemesi"
        d_sirali = sorted(((i, a, b, b - a) for i, (a, b) in deg.items()), key=lambda t: -t[3])
        dsat = lambda i, a, b, f: {"ogrenci_id": str(i), "ad_soyad": ogr[i].ad_soyad, "sube": _sinif_metni(ogr[i]) or "—",  # noqa: E731
                                   "onceki": round(a, 2), "son": round(b, 2), "fark": round(f, 2)}
        x["degisim_metni"] = deg_metni
        x["degisim_sayisi"] = {"artan": sum(1 for t in d_sirali if t[3] > 0), "azalan": sum(1 for t in d_sirali if t[3] < 0),
                               "toplam": len(d_sirali)}
        x["yukselen"] = [dsat(*t) for t in d_sirali if t[3] > 0][:5]
        x["dusen"] = [dsat(*t) for t in reversed(d_sirali) if t[3] < 0][:5]
        x["onceki_kapsam_ort"] = onceki_ort

        # trend (okul geneli + seçili kapsam)
        if kaynak == "okul" and (len(dl) >= 2 or len(aylik[ot]) < 2):
            x["trend"] = [{"ad": d["ad"], "etiket": d["tarih"].strftime("%d.%m"), "tarih": d["tarih"].isoformat(),
                           "okul": _ort(d["netler"].values()),
                           "kapsam": _ort(n for i, n in d["netler"].items() if i in secili)} for d in dl[-8:]]
            x["trend_metni"] = "Okul denemeleri (son 8)"
        else:   # tek okul denemesi varsa ve Net Takibi açıksa eğilim aylık ortalamadan (tek nokta eğilim göstermez)
            AY = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"]
            x["trend"] = [{"ad": ay, "etiket": f"{AY[int(ay[5:7]) - 1]} {ay[2:4]}", "tarih": f"{ay}-01",
                           "okul": _ort(sum(l) / len(l) for l in aylik[ot][ay].values()),
                           "kapsam": _ort(sum(l) / len(l) for i, l in aylik[ot][ay].items() if i in secili)}
                          for ay in sorted(aylik[ot])]
            x["trend_metni"] = "Aylık ortalama (son 6 ay, öğrencilerin girdiği tüm denemeler)"
        oturumlar[ot] = x
    return {"oturumlar": oturumlar}


# ============================================================================= şube tablosu
def _ton(fark: float | None, iyi_yon: int) -> str:
    """fark: okul ortalamasına göre (yüzde puanı ya da % göreli). iyi_yon: +1 yüksek iyi, −1 düşük iyi."""
    if fark is None:
        return "notr"
    f = fark * iyi_yon
    if f >= BELIRGIN_FARK:
        return "iyi"
    if f >= HAFIF_FARK:
        return "iyi_hafif"
    if f <= -BELIRGIN_FARK:
        return "kotu"
    if f <= -HAFIF_FARK:
        return "uyari"
    return "notr"


SUBE_SUTUNLARI = [   # anahtar, ad, iyi yön, birim
    ("tamamlama", "Tamamlama", 1, "%"),
    ("aktif7", "Son 7 gün aktif", 1, "%"),
    ("tyt", "Ort. TYT neti", 1, "net"),
    ("hedef", "Hedef seçen", 1, "%"),
    ("kritik", "Kritik öğrenci", -1, "sayı"),
]


def _grup_olcu(ogrler: list, durum: dict, aktif7: set, hedef: dict, tyt: dict | None, kritik: set) -> dict:
    n = len(ogrler)
    ids = [o.id for o in ogrler]
    tn = [tyt[i] for i in ids if tyt and i in tyt]
    return {
        "ogrenci": n,
        "tamamlama": _yuzde(sum(1 for i in ids if durum.get(i) == "tamamlandi"), n),
        "aktif7": _yuzde(sum(1 for i in ids if i in aktif7), n),
        "tyt": _ort(tn) if tn else None, "tyt_n": len(tn),
        "hedef": _yuzde(sum(1 for i in ids if hedef.get(i)), n),
        "kritik": sum(1 for i in ids if i in kritik),
        "kritik_oran": _yuzde(sum(1 for i in ids if i in kritik), n),
    }


def _sube_tablosu(ogr: list, okul: dict, durum, aktif7, hedef, tyt, kritik) -> list:
    gruplar = defaultdict(list)
    for o in ogr:
        gruplar[(o.sinif or "Belirtilmedi", o.sube or "")].append(o)
    satirlar = []
    for (s, b), l in sorted(gruplar.items(), key=lambda kv: (_sinif_sira(kv[0][0]), kv[0][1])):
        m = _grup_olcu(l, durum, aktif7, hedef, tyt, kritik)
        m.update({"etiket": sube_etiketi(s, b) if b else s, "sinif": s, "sube": b, "tonlar": {}, "vurgu": {}})
        for k, _, yon, _b in SUBE_SUTUNLARI:
            if k == "kritik":
                fark = None if m["kritik_oran"] is None or okul["kritik_oran"] is None else m["kritik_oran"] - okul["kritik_oran"]
            elif k == "tyt":
                fark = None if m["tyt"] is None or not okul["tyt"] else 100 * (m["tyt"] - okul["tyt"]) / okul["tyt"]
            else:
                fark = None if m[k] is None or okul[k] is None else m[k] - okul[k]
            m["tonlar"][k] = _ton(fark, yon)
        satirlar.append(m)
    # her sütunda en iyi / en geride hücre: yalnızca gerçek şubeler arasında (Aday / Mezun / şubesiz gruplar hariç)
    # ve değer tekse (eşitlikte vurgu yok)
    for k, _, yon, _b in SUBE_SUTUNLARI:
        alan = "kritik_oran" if k == "kritik" else k
        dolu = [m for m in satirlar if m["sube"] and m.get(alan) is not None]
        if len(dolu) < 2:
            continue
        degerler = [m[alan] * yon for m in dolu]
        for hedef_deger, ad in ((max(degerler), "en_iyi"), (min(degerler), "en_kotu")):
            esit = [m for m in dolu if m[alan] * yon == hedef_deger]
            # [2026-10-10] yalnızca okul ortalamasından belirgin farklıysa (aynı ton kuralı): 66'ya 65 gibi
            # anlamsız farklar "en iyi / en geride" diye işaretlenmez
            gerekli_ton = "iyi" if ad == "en_iyi" else "kotu"
            if len(esit) == 1 and max(degerler) != min(degerler) and esit[0]["tonlar"].get(k) == gerekli_ton:
                esit[0]["vurgu"][k] = ad
    return satirlar


# ============================================================================= bulgular
def _bulgular(v: dict, ham_uyari: list, secili_str: set, gecersiz_n: int, rehberlik_acik: bool) -> list:
    dikkat, olumlu, bilgi = [], [], []
    okul = v["okul_ort"]
    kapsam = v["filtre"]["etiket"]
    subeler = [s for s in v["subeler"] if s["sube"] and s["tamamlama"] is not None]
    if okul["tamamlama"] is not None and subeler and (len(subeler) >= 2 or v["filtre"]["sinif"]):
        en_kotu = min(subeler, key=lambda s: s["tamamlama"])
        if okul["tamamlama"] - en_kotu["tamamlama"] >= BELIRGIN_FARK:
            dikkat.append(f"{en_kotu['etiket']}'de tamamlama %{_tr_sayi(en_kotu['tamamlama'], 0)} — okul ortalaması "
                          f"%{_tr_sayi(okul['tamamlama'], 0)}'ün belirgin altında.")
        en_iyi = max(subeler, key=lambda s: s["tamamlama"])
        if en_iyi["tamamlama"] - okul["tamamlama"] >= BELIRGIN_FARK:
            olumlu.append(f"{en_iyi['etiket']}'de tamamlama %{_tr_sayi(en_iyi['tamamlama'], 0)} — okul ortalamasının "
                          f"(%{_tr_sayi(okul['tamamlama'], 0)}) belirgin üstünde.")
        aktif_kotu = min((s for s in subeler if s["aktif7"] is not None), key=lambda s: s["aktif7"], default=None)
        if aktif_kotu and okul["aktif7"] is not None and okul["aktif7"] - aktif_kotu["aktif7"] >= BELIRGIN_FARK and aktif_kotu is not en_kotu:
            dikkat.append(f"{aktif_kotu['etiket']}'de son 7 günde giriş yapan öğrenci %{_tr_sayi(aktif_kotu['aktif7'], 0)} — "
                          f"okul ortalaması %{_tr_sayi(okul['aktif7'], 0)}.")

    if rehberlik_acik:
        yuksek = [s for s in ham_uyari if s["ogrenci_id"] in secili_str and s["seviye"] == "yuksek"]
        gorusmesiz = [s for s in yuksek if not s["son_gorusme"] and not s["yaklasan_gorusme"]]
        if gorusmesiz:
            dikkat.insert(0, f"{len(gorusmesiz)} öğrenci yüksek seviyede uyarıda ve henüz görüşme yapılmadı ya da planlanmadı.")
        elif yuksek:
            olumlu.append(f"Yüksek seviyede uyarıdaki {len(yuksek)} öğrencinin tamamıyla görüşme yapıldı ya da planlandı.")

    for ot in ("TYT", "AYT"):
        a = ((v.get("akademik") or {}).get("oturumlar") or {}).get(ot)
        if not a:
            continue
        if a["kaynak"] == "okul" and a.get("onceki_kapsam_ort") is not None and a.get("kapsam_ort") is not None:
            f = round(a["kapsam_ort"] - a["onceki_kapsam_ort"], 1)
            m = f"Son okul denemesinde {ot} ortalaması önceki denemeye göre {_isaretli(f)} net ({_tr_sayi(a['kapsam_ort'])})."
            (olumlu if f > 0 else dikkat if f < 0 else bilgi).append(m)
        elif a["degisim_sayisi"]["toplam"] >= 2:
            ds = a["degisim_sayisi"]
            m = (f"Son iki denemesine göre {ds['artan']} öğrencinin {ot} neti arttı, "
                 + (f"{ds['azalan']} öğrencinin düştü." if ds["azalan"] else "düşen öğrenci yok."))
            (olumlu if ds["artan"] > ds["azalan"] else dikkat if ds["azalan"] > ds["artan"] else bilgi).append(m)
        break   # tek oturum yeterli (TYT öncelikli)

    kural = Counter(u["kural"] for s in ham_uyari if s["ogrenci_id"] in secili_str for u in s["uyarilar"])
    if kural.get("yarim_test"):
        dikkat.append(f"{kural['yarim_test']} öğrenci değerlendirmeyi yarıda bıraktı (bir haftadır devam etmiyor).")
    if kural.get("giris_yok"):
        dikkat.append(f"{kural['giris_yok']} öğrenci hesabı açıldığı hâlde henüz hiç giriş yapmadı.")
    if gecersiz_n:
        dikkat.append(f"{gecersiz_n} öğrencinin son değerlendirmesi doğrulanamadı; yeniden değerlendirme önerilir.")
    k = v["kpi"]
    if (v["filtre"]["sinif"] and k["tamamlama"] is not None and okul["tamamlama"] is not None
            and k["tamamlama"] >= okul["tamamlama"] + BELIRGIN_FARK):
        olumlu.append(f"{kapsam} genelinde tamamlama %{_tr_sayi(k['tamamlama'], 0)} — okul ortalamasının belirgin üstünde.")
    hu = v.get("hedef_uyum")
    if hu and hu["sayi"]:
        bilgi.append(f"{hu['sayi']} öğrencinin seçtiği hedef bölümle uyumu %{UYUM_DUSUK}'ın altında — koçlukta birlikte değerlendirme fırsatı.")
    if k["kocluk_aktif"] == 0 and k["ogrenci"]:
        bilgi.append(f"Son {KOCLUK_GUN} günde koçlukta adım ya da görev tamamlayan öğrenci yok.")
    elif k["kocluk_aktif"] and k["ogrenci"]:
        bilgi.append(f"Son {KOCLUK_GUN} günde {k['kocluk_aktif']} öğrenci (%{_tr_sayi(_yuzde(k['kocluk_aktif'], k['ogrenci']), 0)}) "
                     "koçlukta adım ya da görev tamamladı.")

    secim = [("dikkat", m) for m in dikkat[:4]] + [("olumlu", m) for m in olumlu[:2]]
    kalan = [("dikkat", m) for m in dikkat[4:]] + [("olumlu", m) for m in olumlu[2:]] + [("bilgi", m) for m in bilgi]
    secim += kalan[: max(0, 6 - len(secim))]
    sira = {"dikkat": 0, "olumlu": 1, "bilgi": 2}
    return [{"tur": t, "metin": m} for t, m in sorted(secim, key=lambda x: sira[x[0]])]


# ============================================================================= veri
def tek_bakista_verisi(db: Session, okul_id: int, sinif: str | None = None, sube: str | None = None) -> dict:
    moduller = set(okul_modulleri(db, okul_id or None))
    kume = ogrenci_kumesi(db, okul_id, sinif, sube)
    tum, ogr = kume["tum"], kume["ogr"]
    secili = {o.id for o in ogr}
    secili_str = {str(i) for i in secili}
    simdi = datetime.now(timezone.utc)
    rehberlik_acik = "rehberlik" in moduller

    il = _ilerleme(db, okul_id)
    durum = {o.id: _durum(o, il.get(o.id))[0] for o in tum}
    hedef = {o.id: (il.get(o.id) or {}).get("hedef") for o in tum}
    aktif7 = {o.id for o in tum if o.son_giris_zamani and o.son_giris_zamani >= simdi - timedelta(days=7)}
    son_tur = {i: x["tur_id"] for i, x in il.items() if x.get("tur_id") and i in durum}
    gecersiz = {r.ogrenci_id for r in db.execute(text("""
        SELECT ogrenci_id FROM ogrenci_degerlendirme_turu
         WHERE id = ANY(:t) AND durum = 'tamamlandi' AND sonuc_gecerli_mi IS FALSE"""), {"t": list(son_tur.values())}).all()} if son_tur else set()

    # ---------------------------------------------------------------- kritik öğrenciler
    liste, ham = _kritik_liste(db, okul_id, tum, gecersiz, rehberlik_acik)
    ogr_map = {str(o.id): o for o in tum}
    kritik_tum = {ogr_map[s["ogrenci_id"]].id for s in liste if s["seviye"] == "yuksek" and s["ogrenci_id"] in ogr_map}
    kapsam_liste = [s for s in liste if s["ogrenci_id"] in secili_str]
    kritik_satirlar = [{
        "ogrenci_id": s["ogrenci_id"], "ad_soyad": s["ad_soyad"], "sube": s["sinif_metni"] or "—", "seviye": s["seviye"],
        "seviye_ad": SEVIYE_AD[s["seviye"]], "puan": s["puan"],
        "nedenler": [{"ad": u["ad"], "metin": u["metin"], "seviye": u["seviye"]} for u in s["uyarilar"]],
        "son_giris": _gun_iso(ogr_map[s["ogrenci_id"]].son_giris_zamani) if s["ogrenci_id"] in ogr_map else None,
        "son_gorusme": s.get("son_gorusme"), "yaklasan_gorusme": s.get("yaklasan_gorusme"),
    } for s in kapsam_liste]

    # ---------------------------------------------------------------- akademik
    ak = _akademik(db, okul_id, tum, secili, moduller)
    tyt = (ak or {}).get("oturumlar", {}).get("TYT")
    tyt_kapsam = tyt["ogr_net"] if tyt else None   # kapsamdaki öğrencilerin TYT neti (akademik bölümle aynı kaynak)

    # ---------------------------------------------------------------- KPI + şube tablosu
    kocluk_acik = "kocluk" in moduller
    kocluk_aktif = None
    if kocluk_acik:
        bugun = datetime.now(TR).date()
        _, aktif = kocluk_etkinligi(db, [o.id for o in ogr], bugun - timedelta(days=KOCLUK_GUN - 1), bugun)
        kocluk_aktif = len(aktif)
    okul_olcu = _grup_olcu(tum, durum, aktif7, hedef, None, kritik_tum)
    okul_olcu["tyt"] = tyt["okul_ort"] if tyt else None   # tüm okulun ortalaması
    kapsam_olcu = _grup_olcu(ogr, durum, aktif7, hedef, tyt_kapsam, kritik_tum)
    seviye_say = Counter(s["seviye"] for s in kapsam_liste)

    v: dict = {
        "moduller": sorted(moduller),
        "rehberlik": rehberlik_acik,
        "filtre": {"sinif": kume["sinif"], "sube": kume["sube"], "etiket": kume["etiket"], "secenekler": kume["secenekler"]},
        "tarih": simdi.astimezone(TR).isoformat(),
        "kpi": {
            "ogrenci": len(ogr), "tamamlama": kapsam_olcu["tamamlama"],
            "tamamlayan": sum(1 for o in ogr if durum[o.id] == "tamamlandi"),
            "tyt": tyt["kapsam_ort"] if tyt else None, "tyt_n": tyt["katilim"] if tyt else 0,
            "tyt_onceki": tyt.get("onceki_kapsam_ort") if tyt else None,
            "tyt_kaynak": tyt["kaynak"] if tyt else None,
            "kritik": seviye_say.get("yuksek", 0), "takip": len(kapsam_liste),
            "kocluk_aktif": kocluk_aktif,
            "hedef": kapsam_olcu["hedef"], "hedef_secen": sum(1 for o in ogr if hedef.get(o.id)),
            "aktif7": kapsam_olcu["aktif7"],
        },
        "okul_ort": okul_olcu,
        "kritik": {"baslik": "Kritik ve dikkat gerektiren öğrenciler" if rehberlik_acik else "Takip edilmesi gereken öğrenciler",
                   "toplam": len(kritik_satirlar), "ogrenciler": kritik_satirlar[:10],
                   "seviyeler": [{"kod": k, "ad": a, "deger": seviye_say.get(k, 0)} for k, a in SEVIYE_AD.items()]},
        "akademik": None,
    }
    v["subeler"] = _sube_tablosu(ogr, okul_olcu, durum, aktif7, hedef, tyt_kapsam, kritik_tum)
    if ak is not None:
        v["akademik"] = {"oturumlar": {ot: {k: x for k, x in a.items() if k != "ogr_net"} for ot, a in ak["oturumlar"].items()},
                         "okul_denemeleri": "okul_denemeleri" in moduller, "net_takibi": "net_takibi" in moduller}

    # ---------------------------------------------------------------- hedef–uyum (< 40)
    hedefli = {o.id: (son_tur[o.id], hedef[o.id]) for o in ogr if hedef.get(o.id) and durum[o.id] == "tamamlandi" and o.id in son_tur}
    dusuk = []
    if hedefli:
        uy = {(r.tur_id, r.bolum_id): float(r.toplam_uyum) for r in db.execute(text("""
            SELECT tur_id, bolum_id, toplam_uyum FROM ogrenci_bolum_uyum_skorlari WHERE tur_id = ANY(:t) AND bolum_id = ANY(:b)"""),
            {"t": [t for t, _ in hedefli.values()], "b": list({b for _, b in hedefli.values()})}).all()}
        adlar = {r.id: _baslik(r.ad) for r in db.execute(text("SELECT id, ad FROM bolumler WHERE id = ANY(:b)"),
                                                         {"b": list({b for _, b in hedefli.values()})}).all()}
        for oid, (t, b) in hedefli.items():
            u = uy.get((t, b))
            if u is not None and u < UYUM_DUSUK:
                o = ogr_map[str(oid)]
                dusuk.append({"ogrenci_id": str(oid), "ad_soyad": o.ad_soyad, "sube": _sinif_metni(o) or "—",
                              "bolum": adlar.get(b, "—"), "uyum": round(u)})
    dusuk.sort(key=lambda x: (x["uyum"], x["ad_soyad"]))
    v["hedef_uyum"] = {"sayi": len(dusuk), "hedefli": len(hedefli), "ogrenciler": dusuk[:10], "esik": UYUM_DUSUK}

    v["bulgular"] = _bulgular(v, ham, secili_str, sum(1 for i in gecersiz if i in secili), rehberlik_acik)
    return v


# ============================================================================= uç noktalar
@router.get("/okul/{okul_id}/tek-bakista")
def okul_tek_bakista(okul_id: int, sinif: str | None = None, sube: str | None = None,
                     db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    return tek_bakista_verisi(db, okul_id, sinif, sube)


@router.get("/okul/{okul_id}/tek-bakista/pdf")
def okul_tek_bakista_pdf(okul_id: int, sinif: str | None = None, sube: str | None = None,
                         db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    from app.api.raporlar import _cevap, _dosya_adi
    from app.core.rapor.pdf import yonetici_ozeti_pdf
    from app.core.rapor.veri import okul_bilgisi
    okul = _okul_kapsami(db, yon, okul_id)
    v = tek_bakista_verisi(db, okul_id, sinif, sube)
    icerik = yonetici_ozeti_pdf(v, okul_bilgisi(db, okul_id or None))
    f = v["filtre"]
    denetim_yaz(db, yon, "rapor_indir", "okullar", okul_id, f"Yönetici özeti PDF ({f['etiket']})", okul_id or None)
    db.commit()
    return _cevap(icerik, "pdf", _dosya_adi("Yonetici_Ozeti", okul.ad if okul else "Okul_harici",
                                            f["etiket"] if f["sinif"] else None, datetime.now(TR).strftime("%Y%m%d")))
