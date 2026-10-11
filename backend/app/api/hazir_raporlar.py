# -*- coding: utf-8 -*-
"""
[2026-10-11] Okul yetkilisi — hazır raporlar (indirmeden, doğrudan ekranda görülen öğrenci listeleri).

GET /yonetim/okul/{okul_id}/hazir-raporlar?gun=30&sinif=&sube=&adet=10

Listeler (her biri en fazla `adet` öğrenci; öğrenci adı, sınıf-şube, değer):
  en_aktif         — dönemde sistemi en çok gün açan     (ogrenci_aktif_gunler; ek bilgi: giriş sayısı)
  en_az_aktif      — dönemde en az gün açan / hiç açmayan (0 dahil; son aktif günü en eski olan önde)
  en_yuksek_net    — son TYT toplam neti en yüksek         (net_takibi modülü)
  en_cok_yukselen  — ilk ve son TYT denemesi arasındaki net artışı en yüksek (en az 2 TYT; net_takibi)
  en_cok_calisma   — dönemde en çok çalışma süresi kaydeden (calisma modülü)
  en_cok_kocluk    — dönemde en çok koçluk adımı + haftalık görev tamamlayan (kocluk modülü)

Kapsam / yetki: okul_yonetimi._okul_kapsami — okul yetkilisi yalnızca kendi okulu; süper admin herhangi bir okul.
Test hesapları sayılmaz (okul_istatistik.ogrenci_kumesi). Paket modülü kapalı listeler dönmez.
Etik: kişilik / değer / ilgi puanına göre sıralama YAPILMAZ; yalnızca katılım ve deneme neti.
[2026-10-11] Aktif gün: öğrencinin sistemi açtığı her gün bir kez sayılır ("beni hatırla" ile açık kalan oturumlar dahil).
Giriş: şifreyle yapılan başarılı oturum açma sayısı (ek bilgi).
Performans: liste başına tek toplu SQL.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_mevcut_yonetim
from app.api.okul_istatistik import ogrenci_kumesi
from app.api.okul_yonetimi import _okul_kapsami, _sinif_metni
from app.core.aktiflik import bugun_tr
from app.core.database import get_db
from app.core.paketler import okul_modulleri
from app.models import AdminKullanici

router = APIRouter(prefix="/yonetim", tags=["Okul istatistikleri"])

DONEMLER = (7, 30, 90, 365)


def _satir(o, deger, ek: str | None = None) -> dict:
    return {"id": str(o.id), "ad": o.ad_soyad, "sinif": _sinif_metni(o), "deger": deger, "ek": ek}


def _tarih(t) -> str | None:
    return t.astimezone(timezone(timedelta(hours=3))).strftime("%d.%m.%Y") if t else None


@router.get("/okul/{okul_id}/hazir-raporlar")
def hazir_raporlar(okul_id: int, gun: int = Query(30), sinif: str | None = None, sube: str | None = None,
                   adet: int = Query(10, ge=3, le=50),
                   db: Session = Depends(get_db), yon: AdminKullanici = Depends(get_mevcut_yonetim)):
    _okul_kapsami(db, yon, okul_id)
    gun = gun if gun in DONEMLER else 30
    k = ogrenci_kumesi(db, okul_id, sinif, sube)
    ogr = k["ogr"]
    harita = {str(o.id): o for o in ogr}
    ids = list(harita)
    moduller = set(okul_modulleri(db, okul_id or None))
    simdi = datetime.now(timezone.utc)
    bas = simdi - timedelta(days=gun)
    bugun = bugun_tr()
    p = {"ids": ids, "bas": bas, "gbas": bugun - timedelta(days=gun - 1)}
    listeler: list[dict] = []

    def say(sql: str) -> dict[str, float]:
        if not ids:
            return {}
        return {str(r[0]): r[1] for r in db.execute(text(sql), p).all()}

    # --- katılım: günlük aktiflik (öğrencinin sistemi açtığı günler) + giriş sayısı -------------------------------
    giris = say("SELECT ogrenci_id, count(*) FROM ogrenci_hesap_olaylari "
                "WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) AND olay = 'giris' AND zaman >= :bas GROUP BY 1")
    aktif = say("SELECT ogrenci_id, count(*) FROM ogrenci_aktif_gunler "
                "WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) AND gun >= CAST(:gbas AS date) GROUP BY 1") if ids else {}
    son_aktif = {str(r[0]): r[1] for r in db.execute(text(
        "SELECT ogrenci_id, max(gun) FROM ogrenci_aktif_gunler WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) GROUP BY 1"), p).all()} if ids else {}
    sa = lambda o: son_aktif.get(str(o.id))
    sa_metin = lambda o: f"son aktif {sa(o).strftime('%d.%m.%Y')}" if sa(o) else "kayıt yok"
    cok = sorted((o for o in ogr if aktif.get(str(o.id))),
                 key=lambda o: (-aktif[str(o.id)], -giris.get(str(o.id), 0), -(sa(o) or bugun).toordinal()))[:adet]
    listeler.append({"kod": "en_aktif", "ikon": "🔥", "baslik": "En aktif öğrenciler", "birim": "gün",
                     "aciklama": f"Son {gun} günde sistemi en çok gün açan öğrenciler (her gün bir kez sayılır)",
                     "satirlar": [_satir(o, aktif[str(o.id)], f"{sa_metin(o)} · {giris.get(str(o.id), 0)} giriş") for o in cok],
                     "bos": "Bu dönemde sistemi açan öğrenci yok."})
    az = sorted(ogr, key=lambda o: (aktif.get(str(o.id), 0), (sa(o) or date.min).toordinal()))[:adet]
    listeler.append({"kod": "en_az_aktif", "ikon": "💤", "baslik": "En az aktif öğrenciler", "birim": "gün",
                     "aciklama": f"Son {gun} günde sistemi en az gün açan ya da hiç açmayan öğrenciler (önce en uzun süredir açmayan)",
                     "satirlar": [_satir(o, aktif.get(str(o.id), 0), sa_metin(o)) for o in az],
                     "bos": "Öğrenci yok."})

    # --- [2026-10-11] değerlendirme ve hedef: rehber öğretmenin takip edeceği listeler ------------------------------
    from app.api.okul_yonetimi import _durum, _ilerleme
    il = _ilerleme(db, okul_id) if ids else {}
    yarim = sorted((o for o in ogr if _durum(o, il.get(o.id))[0] == "devam"),
                   key=lambda o: ((sa(o) or date.min).toordinal(), (il.get(o.id) or {}).get("biten", 0)))[:adet]
    listeler.append({"kod": "yarida_kalan", "ikon": "⏸️", "baslik": "Değerlendirmeyi yarıda bırakanlar", "birim": "bölüm",
                     "aciklama": "Değerlendirmeye başlayıp bitirmeyen öğrenciler (önce en uzun süredir açmayan)",
                     "satirlar": [_satir(o, f"{(il.get(o.id) or {}).get('biten', 0)}/{(il.get(o.id) or {}).get('toplam', 4)}", sa_metin(o)) for o in yarim],
                     "bos": "Yarıda bırakan öğrenci yok. 👏"})
    hedefsiz = [o for o in ogr if o.sinif in ("12. Sınıf", "Mezun") and _durum(o, il.get(o.id))[0] == "tamamlandi"
                and not (il.get(o.id) or {}).get("hedef")][:adet]
    listeler.append({"kod": "hedefsiz_son_sinif", "ikon": "🎯", "baslik": "Hedef bölümü olmayan son sınıflar", "birim": "",
                     "aciklama": "Değerlendirmeyi bitirmiş ama hedef bölüm seçmemiş 12. sınıf ve mezun öğrenciler (tercih öncesi görüşme için)",
                     "satirlar": [_satir(o, "—", sa_metin(o)) for o in hedefsiz],
                     "bos": "Son sınıfların hepsi hedef bölüm seçmiş."})

    # --- deneme neti (TYT) -------------------------------------------------------------------------------------------
    if "net_takibi" in moduller and ids:
        rows = db.execute(text(
            "SELECT ogrenci_id, toplam_net, tarih FROM ogrenci_denemeleri "
            "WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) AND oturum = 'TYT' ORDER BY ogrenci_id, tarih, id"), p).all()
        seri: dict[str, list] = {}
        for r in rows:
            seri.setdefault(str(r.ogrenci_id), []).append((float(r.toplam_net), r.tarih))
        son = sorted(((i, s[-1]) for i, s in seri.items()), key=lambda x: -x[1][0])[:adet]
        listeler.append({"kod": "en_yuksek_net", "ikon": "🏆", "baslik": "En yüksek TYT neti", "birim": "net",
                         "aciklama": "Son TYT denemesindeki toplam neti en yüksek öğrenciler",
                         "satirlar": [_satir(harita[i], round(n, 2), f"{t.strftime('%d.%m.%Y')} denemesi") for i, (n, t) in son],
                         "bos": "Henüz TYT denemesi girilmemiş."})
        artis = sorted(((i, round(s[-1][0] - s[0][0], 2), len(s)) for i, s in seri.items() if len(s) >= 2), key=lambda x: -x[1])
        artis = [a for a in artis if a[1] > 0][:adet]
        listeler.append({"kod": "en_cok_yukselen", "ikon": "📈", "baslik": "Netini en çok artıranlar", "birim": "net",
                         "aciklama": "İlk ve son TYT denemesi arasında toplam neti en çok artan öğrenciler (en az 2 deneme)",
                         "satirlar": [_satir(harita[i], f"+{d}", f"{n} deneme") for i, d, n in artis],
                         "bos": "Netini artıran öğrenci yok ya da en az 2 TYT denemesi girilmemiş."})

    # --- çalışma süresi --------------------------------------------------------------------------------------------
    if "calisma" in moduller:
        sure = say("SELECT ogrenci_id, sum(sure_dk) FROM calisma_kayitlari "
                   "WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) AND tarih >= CAST(:bas AS date) GROUP BY 1 HAVING sum(sure_dk) > 0")
        en = sorted(sure, key=lambda i: -sure[i])[:adet]
        listeler.append({"kod": "en_cok_calisma", "ikon": "⏱️", "baslik": "En çok çalışma kaydedenler", "birim": "saat",
                         "aciklama": f"Son {gun} günde Çalışmam sayfasına en çok çalışma süresi giren öğrenciler",
                         "satirlar": [_satir(harita[i], round(sure[i] / 60, 1)) for i in en],
                         "bos": "Bu dönemde çalışma kaydı yok."})

    # --- koçluk + haftalık görev -----------------------------------------------------------------------------------
    if "kocluk" in moduller:
        adim = say("SELECT ogrenci_id, count(*) FROM ogrenci_gelisim_adim_durumu WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) "
                   "AND durum = 'tamamlandi' AND guncelleme_zamani >= :bas GROUP BY 1")
        gorev = say("SELECT ogrenci_id, count(*) FROM ogrenci_haftalik_gorev WHERE ogrenci_id = ANY(CAST(:ids AS uuid[])) "
                    "AND durum = 'tamamlandi' AND tamamlanma_zamani >= :bas GROUP BY 1")
        top = {i: adim.get(i, 0) + gorev.get(i, 0) for i in set(adim) | set(gorev)}
        en = sorted(top, key=lambda i: -top[i])[:adet]
        listeler.append({"kod": "en_cok_kocluk", "ikon": "🎯", "baslik": "Koçluk ve görevlerde en aktifler", "birim": "adım",
                         "aciklama": f"Son {gun} günde en çok koçluk adımı ve haftalık görev tamamlayan öğrenciler",
                         "satirlar": [_satir(harita[i], top[i], f"{adim.get(i, 0)} adım · {gorev.get(i, 0)} görev") for i in en],
                         "bos": "Bu dönemde tamamlanan adım ya da görev yok."})

    # "hiç açmadı": özet sayfasındaki "Henüz giriş yapmadı" durumuyla aynı tanım (değerlendirmeye başlamışsa açmış demektir)
    hic = sum(1 for o in ogr if not sa(o) and not o.son_giris_zamani and _durum(o, il.get(o.id))[0] not in ("tamamlandi", "devam"))
    uzun = sum(1 for o in ogr if sa(o) and sa(o) < bugun - timedelta(days=14))
    bugun_aktif = sum(1 for o in ogr if sa(o) == bugun)
    return {"gun": gun, "donemler": list(DONEMLER), "kapsam": k["etiket"], "secenekler": k["secenekler"],
            "ogrenci_sayisi": len(ogr), "hic_girmeyen": hic, "girmeyen_14_gun": uzun, "bugun_aktif": bugun_aktif,
            "donemde_aktif": sum(1 for o in ogr if aktif.get(str(o.id))),
            "donemde_giris_yapan": sum(1 for o in ogr if giris.get(str(o.id))), "listeler": listeler}
