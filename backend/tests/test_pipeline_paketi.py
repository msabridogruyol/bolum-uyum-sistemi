# -*- coding: utf-8 -*-
"""[2026-11-01] Pipeline'ın sistemden kurulması: kurulum dosyası → bilgisayar anahtarı → kod / canlı liste → veri gönderimi,
sayaç ve erişim kaldırma. Supabase Storage bellekteki sahte bir depoyla değiştirilir."""
import re
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from app.core import pipeline_depo as depo
from app.core import pipeline_paketi as pp
from tests.conftest import db_gerekli

API = "https://ornek-api.onrender.com"


def _goc(db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for ad in ("0087_veri_yonetimi_demo", "0088_pipeline_paketi"):
        for k in _komutlar(_sql_oku(ad)):
            db.execute(text(k))
    db.commit()


@pytest.fixture
def sahte_depo(monkeypatch):
    nesneler: set[str] = set()
    yeni: set[str] = set()      # bu kümedeki parçalar "az önce yüklendi" sayılır (budanmaz)
    eski_zaman = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
    monkeypatch.setattr(depo, "hazir_mi", lambda: True)
    monkeypatch.setattr(depo, "kova_hazirla", lambda: None)
    monkeypatch.setattr(depo, "mevcut_parcalar",
                        lambda: {o: (datetime.now(timezone.utc).isoformat() if o in yeni else eski_zaman) for o in nesneler})
    monkeypatch.setattr(depo, "parca_bozuk_mu", lambda o: o == "e" * 64)
    monkeypatch.setattr(depo, "yukleme_adresi", lambda o: f"https://depo/yukle/{o}")
    monkeypatch.setattr(depo, "indirme_adresleri", lambda ozetler, sure_sn=3600: {o: f"https://depo/indir/{o}" for o in ozetler})

    def sil(ozetler):
        nesneler.difference_update(ozetler)
        return len(ozetler)
    monkeypatch.setattr(depo, "parcalari_sil", sil)
    return nesneler, yeni


def _kur(istemci, kisiler, ad="Ofis PC"):
    r = istemci.post("/admin/pipeline-paketi/kurulum-dosyasi", headers=kisiler["super"], json={"cihaz_adi": ad, "api_adresi": API})
    assert r.status_code == 200, r.text
    icerik = r.content.decode("utf-8-sig")
    assert f'$Api = "{API}"' in icerik and "__KURULUM_ANAHTARI__" not in icerik
    return re.search(r'\$KurulumAnahtari = "([^"]+)"', icerik).group(1)


def test_kod_manifesti_ve_sablon():
    m = pp.kod_manifesti()
    yollar = {d["yol"] for d in m}
    assert {"pipeline_calistir.ps1", "requirements_kilit.txt", "src/s1_sistemden_al.py", "src/s2_sisteme_gonder.py",
            "src/b1_bolum_esitle.py", "src/b7_kontrol.py"} <= yollar
    assert not any(y.startswith("_") or "__pycache__" in y for y in yollar), "kurulum şablonu ve önbellek bilgisayara gitmez"
    assert pp.KURULUM_SABLONU.exists()
    with pytest.raises(pp.PaketHatasi):
        pp.kod_dosyasi("../app/core/config.py")


@db_gerekli
def test_kurulum_gonderim_sayac_ve_iptal(istemci, kisiler, db, sahte_depo):
    _goc(db)
    db.execute(text("DELETE FROM pipeline_surumleri"))
    db.commit()
    sahte_depo, yeni_parcalar = sahte_depo
    kurulum = _kur(istemci, kisiler)
    # yalnızca süper admin
    assert istemci.post("/admin/pipeline-paketi/kurulum-dosyasi", headers=kisiler["yetkili"],
                        json={"cihaz_adi": "x y", "api_adresi": API}).status_code in (401, 403)
    assert istemci.post("/admin/pipeline-paketi/kurulum-dosyasi", headers=kisiler["super"],
                        json={"cihaz_adi": "PC", "api_adresi": "javascript:alert(1)"}).status_code == 422
    # anahtarsız / yanlış anahtarla erişim yok
    assert istemci.get("/pipeline-istemci/manifest").status_code == 401
    assert istemci.get("/pipeline-istemci/manifest", headers={"X-Pipeline-Anahtari": "yanlis"}).status_code == 401

    r = istemci.post("/pipeline-istemci/etkinlestir", json={"kurulum_anahtari": kurulum})
    assert r.status_code == 200 and r.json()["cihaz_adi"] == "Ofis PC"
    bas = {"X-Pipeline-Anahtari": r.json()["cihaz_anahtari"]}
    assert istemci.post("/pipeline-istemci/etkinlestir", json={"kurulum_anahtari": kurulum}).status_code == 400, "tek kullanımlık"

    m = istemci.get("/pipeline-istemci/manifest", headers=bas).json()
    assert m["veri"] is None and m["kod"]
    d = next(x for x in m["kod"] if x["yol"] == "src/s1_sistemden_al.py")
    k = istemci.get("/pipeline-istemci/kod", params={"yol": d["yol"]}, headers=bas)
    assert k.status_code == 200 and pp._sha(k.content) == d["sha256"]
    assert istemci.get("/pipeline-istemci/kod", params={"yol": "../app/main.py"}, headers=bas).status_code == 404

    canli = istemci.get("/pipeline-istemci/canli", headers=bas).json()
    assert set(canli["ozet"]) == {"bolumler", "degiskenler", "k5"} and isinstance(canli["bolumler"], list)

    # gönderim: biri depoda olan iki parça
    a, b = "a" * 64, "b" * 64
    sahte_depo.add(a)
    r = istemci.post("/pipeline-istemci/gonderim/baslat", headers=bas, json={"parcalar": [{"sha256": a, "boyut": 10}, {"sha256": b, "boyut": 20}]})
    assert r.status_code == 200 and list(r.json()["eksik"]) == [b] and r.json()["var_olan"] == 1
    dosyalar = {"veri/x.csv": {"sha256": "c" * 64, "boyut": 30, "parcalar": [a, b]}}
    r = istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={"dosyalar": dosyalar, "girdi_ozeti": canli["ozet"]})
    assert r.status_code == 422, "yüklenmemiş parça varken sürüm kaydedilmez"
    sahte_depo.add(b)
    sahte_depo.add("d" * 64)   # hiçbir sürümün kullanmadığı eski artık parça → budanır
    sahte_depo.add("f" * 64); yeni_parcalar.add("f" * 64)   # az önce yüklenmiş (başka gönderime ait olabilir) → kalır
    r = istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={"dosyalar": dosyalar, "girdi_ozeti": canli["ozet"]})
    assert r.status_code == 200, r.text
    assert r.json()["silinen_parca"] == 1 and sahte_depo == {a, b, "f" * 64}
    ilk = r.json()["surum_id"]
    # bu çalıştırma eski bir sürümden başladıysa (başka bilgisayar arada gönderdi) üzerine yazılmaz; zorla ile yazılır
    r2 = istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={"dosyalar": dosyalar, "taban_surum_id": ilk - 1})
    assert r2.status_code == 409
    r2 = istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={"dosyalar": dosyalar, "taban_surum_id": ilk})
    assert r2.status_code == 200
    r = istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={"dosyalar": dosyalar, "taban_surum_id": ilk, "zorla": True})
    assert r.status_code == 200
    # veri klasörleri dışına (kod, ayar) yol kabul edilmez; özetler onaltılık olmalı
    for kotu in ("src/b1_bolum_esitle.py", "pipeline_calistir.ps1", "ayar.json", "veri/a:b", "veri/../src/x.py", "veri\\x"):
        assert istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={
            "dosyalar": {kotu: {"sha256": "c" * 64, "boyut": 1, "parcalar": [a]}}, "zorla": True}).status_code == 422, kotu
    assert istemci.post("/pipeline-istemci/parca-adresleri", headers=bas, json={"parcalar": ["Z" * 64]}).status_code == 422
    assert istemci.post("/pipeline-istemci/parca-bozuk", headers=bas, json={"sha256": "e" * 64}).json() == {"bozuktu": True}
    # kötü yol reddedilir
    assert istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={
        "dosyalar": {"../../x": {"sha256": "c" * 64, "boyut": 1, "parcalar": [a]}}}).status_code == 422
    m = istemci.get("/pipeline-istemci/manifest", headers=bas).json()
    assert m["veri"]["surum_id"] == r.json()["surum_id"] and m["veri"]["dosyalar"] == dosyalar
    assert set(istemci.post("/pipeline-istemci/parca-adresleri", headers=bas, json={"parcalar": [a, b]}).json()["adresler"]) == {a, b}

    # sayaç ve bilgisayar listesi
    v = istemci.get("/admin/pipeline-paketi/durum", headers=kisiler["super"]).json()
    assert v["depo_hazir"] and "Ofis PC" in [c["cihaz_adi"] for c in v["cihazlar"]] and v["surumler"][0]["dosya_sayisi"] == 1
    assert v["sayac"]["durum"] in ("canliya_al", "gerekli"), "çalıştırma sonrası çıktılar canlıya alınmadıysa"
    # erişim kaldırma
    cid = next(c["id"] for c in v["cihazlar"] if c["cihaz_adi"] == "Ofis PC")
    assert istemci.delete(f"/admin/pipeline-paketi/cihazlar/{cid}", headers=kisiler["super"]).status_code == 204
    assert istemci.get("/pipeline-istemci/manifest", headers=bas).status_code == 401
    assert db.execute(text("SELECT COUNT(*) FROM audit_log WHERE islem IN ('pipeline_kurulum_dosyasi', 'pipeline_cihaz_kaldirma')")).scalar() >= 2


@db_gerekli
def test_kurulum_anahtari_suresi_dolar(istemci, kisiler, db):
    _goc(db)
    kurulum = _kur(istemci, kisiler, "Eski PC")
    db.execute(text("UPDATE pipeline_anahtarlari SET son_gecerlilik = now() - interval '1 hour' WHERE tur = 'kurulum' AND cihaz_adi = 'Eski PC'"))
    db.commit()
    r = istemci.post("/pipeline-istemci/etkinlestir", json={"kurulum_anahtari": kurulum})
    assert r.status_code == 400 and "süresi dolmuş" in r.json()["detail"]


@db_gerekli
def test_sayac_kurallari(db):
    _goc(db)
    db.execute(text("DELETE FROM pipeline_surumleri"))
    db.commit()
    bugun = datetime.now(timezone.utc)
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = :z"), {"z": bugun - timedelta(days=10)})
    db.commit()
    s = pp.sayac_durumu(db)
    if s["son_guncelleme"] is None:
        pytest.skip("test veritabanında bölüm profili yok")
    assert 354 <= s["kalan_gun"] <= 356
    assert any("ilk çalıştırmadan" in n for n in s["notlar"])
    # 340 gün önce → son 30 gün uyarısı (yayındaki her bölümün profili varsa 'yaklasiyor', yoksa 'gerekli')
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = :z"), {"z": bugun - timedelta(days=340)})
    db.commit()
    s = pp.sayac_durumu(db)
    assert s["durum"] in ("yaklasiyor", "gerekli") and 24 <= s["kalan_gun"] <= 26
    # 400 gün önce → süre doldu
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = :z"), {"z": bugun - timedelta(days=400)})
    db.commit()
    s = pp.sayac_durumu(db)
    assert s["durum"] == "gerekli" and "süresi doldu" in s["nedenler"][0]
    # son çalıştırmadan sonra K5 cümlesi değişirse 'gerekli' der; özellik tanımı değişince yalnızca not
    ozet = pp.canli_listeler(db)["ozet"]
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = :z"), {"z": bugun - timedelta(days=5)})
    db.execute(text("INSERT INTO pipeline_surumleri (dosyalar, girdi_ozeti, zaman) VALUES ('{}'::jsonb, CAST(:g AS JSONB), :z)"),
               {"g": __import__("json").dumps({**ozet, "k5": "eski", "degiskenler": "eski"}), "z": bugun - timedelta(days=6)})
    db.commit()
    s = pp.sayac_durumu(db)
    assert any("K5" in n for n in s["nedenler"]) and any("kutup" in n for n in s["notlar"])
    assert not any("bölüm listesi" in n for n in s["nedenler"])
    # aynı özetle yapılmış ve canlıya alınmamış bir çalıştırma: yapılacak iş "canlıya al"
    db.execute(text("DELETE FROM pipeline_surumleri"))
    db.execute(text("INSERT INTO pipeline_surumleri (dosyalar, girdi_ozeti, zaman) VALUES ('{}'::jsonb, CAST(:g AS JSONB), :z)"),
               {"g": __import__("json").dumps(ozet), "z": bugun - timedelta(days=1)})
    db.commit()
    s = pp.sayac_durumu(db)
    eksik_var = any("yok:" in n for n in s["nedenler"])
    assert s["durum"] == ("gerekli" if eksik_var else "canliya_al") and any("canlıya alınmadı" in n for n in s["nedenler"])


@db_gerekli
def test_disk_deposu(istemci, kisiler, db, tmp_path, monkeypatch):
    """Kendi sunucu: PIPELINE_DEPO=disk. Parçalar sunucu klasörüne backend üzerinden, imzalı adresle gider / gelir."""
    import hashlib
    from app.core.config import settings
    _goc(db)
    db.execute(text("DELETE FROM pipeline_surumleri"))
    db.commit()
    monkeypatch.setattr(settings, "PIPELINE_DEPO", "disk")
    monkeypatch.setattr(settings, "PIPELINE_DEPO_DIZINI", str(tmp_path / "depo"))
    assert depo.tur() == "disk" and depo.hazir_mi()
    v = istemci.get("/admin/pipeline-paketi/durum", headers=kisiler["super"]).json()
    assert v["depo_turu"] == "disk" and v["depo_hazir"] and v["depo_eksik"] is None
    bas = {"X-Pipeline-Anahtari": istemci.post("/pipeline-istemci/etkinlestir",
                                               json={"kurulum_anahtari": _kur(istemci, kisiler, "Sunucu PC")}).json()["cihaz_anahtari"]}
    veri = b"merhaba pipeline" * 1000
    o = hashlib.sha256(veri).hexdigest()
    eksik = istemci.post("/pipeline-istemci/gonderim/baslat", headers=bas, json={"parcalar": [{"sha256": o, "boyut": len(veri)}]}).json()["eksik"]
    adres = eksik[o]
    assert adres.startswith("/pipeline-istemci/depo/"), "göreli adres: bilgisayar kendi sistem adresine ekler"
    assert istemci.put(adres, content=b"bozuk").status_code == 400, "içerik özeti adıyla uyuşmazsa kabul edilmez"
    assert istemci.put(adres[:-1] + ("0" if adres[-1] != "0" else "1"), content=veri).status_code == 403
    assert istemci.put(adres.replace("islem=yukle", "islem=indir"), content=veri).status_code == 403
    assert istemci.put(adres, content=veri).status_code == 200
    r = istemci.post("/pipeline-istemci/gonderim/tamamla", headers=bas, json={
        "dosyalar": {"veri/x.bin": {"sha256": o, "boyut": len(veri), "parcalar": [o]}}})
    assert r.status_code == 200, r.text
    indir = istemci.post("/pipeline-istemci/parca-adresleri", headers=bas, json={"parcalar": [o]}).json()["adresler"][o]
    g = istemci.get(indir)
    assert g.status_code == 200 and g.content == veri
    assert istemci.get(indir.replace("islem=indir", "islem=yukle")).status_code == 403
    # bozulmuş parça: denetimde silinir
    (tmp_path / "depo" / "parca" / o).write_bytes(b"x")
    assert istemci.post("/pipeline-istemci/parca-bozuk", headers=bas, json={"sha256": o}).json() == {"bozuktu": True}
    assert not (tmp_path / "depo" / "parca" / o).exists()
    # supabase türünde bu uçlar kapalı
    monkeypatch.setattr(settings, "PIPELINE_DEPO", "supabase")
    assert istemci.get(indir).status_code == 404


@db_gerekli
def test_kontrol_paneli_sayac_maddesi(db):
    """Sayaç güncel değilse Kontrol Paneli 'dikkat' listesinde görünür (Pipeline Sonuçları ile aynı hesap)."""
    from app.api.sistem_istatistik import _pipeline_sayac_maddesi
    _goc(db)
    db.execute(text("DELETE FROM pipeline_surumleri"))
    db.commit()
    if pp.sayac_durumu(db)["son_guncelleme"] is None:
        pytest.skip("test veritabanında bölüm profili yok")
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = now() - interval '400 days'"))
    db.commit()
    m = _pipeline_sayac_maddesi(db)
    assert len(m) == 1 and m[0]["k"] == "pipeline_sayac" and m[0]["seviye"] == "uyari" and "süresi doldu" in m[0]["aciklama"]
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = now() - interval '340 days'"))
    db.commit()
    m = _pipeline_sayac_maddesi(db)
    s = pp.sayac_durumu(db)
    if s["durum"] == "yaklasiyor":
        assert m[0]["sayi"] == s["kalan_gun"] and m[0]["seviye"] == "bilgi"
    db.execute(text("UPDATE bolum_agirliklari SET olusturulma_zamani = now() - interval '5 days'"))
    db.commit()
    assert pp.sayac_durumu(db)["durum"] != "guncel" or _pipeline_sayac_maddesi(db) == []


def test_supabase_anahtar_turleri_ve_adres(monkeypatch):
    """Yeni gizli anahtar (sb_secret_) yalnızca apikey başlığında; eski service_role (JWT) Bearer ile de. Proje adresine
    yapıştırılmış ekler (/rest/v1, /) yok sayılır."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_KEY", "sb_secret_abc")
    assert depo._kimlik_basliklari() == {"apikey": "sb_secret_abc"}
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_KEY", "eyJhbGciOi.x.y")
    assert depo._kimlik_basliklari() == {"Authorization": "Bearer eyJhbGciOi.x.y", "apikey": "eyJhbGciOi.x.y"}
    for adres in ("https://abcd.supabase.co", "https://abcd.supabase.co/", "https://abcd.supabase.co/rest/v1/", " abcd.supabase.co "):
        monkeypatch.setattr(settings, "SUPABASE_URL", adres)
        assert depo._taban() == "https://abcd.supabase.co/storage/v1", adres
