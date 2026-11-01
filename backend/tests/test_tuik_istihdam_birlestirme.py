"""[2026-11-01] TÜİK aynı yılın verisini ayrı tablolarda yayımlar (istihdam oranı / ilk iş bulma süresi / kazanç grubu, lisans ve
ön lisans ayrı). Sırayla yüklenince aynı programın tek satırında birleşmeli; önceki yükleme silinmemeli."""
import uuid

from sqlalchemy import text

from tests.conftest import db_gerekli


@db_gerekli
def test_ayri_tuik_tablolari_ayni_satirda_birlesir(istemci, kisiler, db):
    ad = f"DENEME BÖLÜMÜ {uuid.uuid4().hex[:5].upper()}"
    bid = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": ad}).scalar()
    db.commit()
    yil = 2091
    h = kisiler["super"]

    def yukle(satir, kaynak):
        r = istemci.post("/admin/is-hayati/istihdam/kaydet", headers=h, json={
            "veri_yili": yil, "kaynak": kaynak, "satirlar": [{"program_adi_kaynak": ad, "duzey": "lisans", "bolum_id": bid, **satir}]})
        assert r.status_code == 200, r.text
        return r.json()

    assert yukle({"istihdam_orani": 81.5}, "TÜİK, 2091, istihdam oranı")["eklenen"] == 1
    assert yukle({"is_bulma_suresi_ay": 4.2}, "TÜİK, 2091, ilk iş bulma süresi")["guncellenen"] == 1
    assert yukle({"kazanc_grubu": "yuksek"}, "TÜİK, 2091, kazanç grupları")["guncellenen"] == 1
    rows = db.execute(text("SELECT istihdam_orani, is_bulma_suresi_ay, kazanc_grubu, kaynak FROM istihdam_gostergeleri "
                           "WHERE veri_yili = :y AND bolum_id = :b"), {"y": yil, "b": bid}).all()
    assert len(rows) == 1
    r = rows[0]
    assert float(r.istihdam_orani) == 81.5 and float(r.is_bulma_suresi_ay) == 4.2 and r.kazanc_grubu == "yuksek"
    assert "istihdam oranı" in r.kaynak and "kazanç grupları" in r.kaynak
    # Ön lisans aynı adla ayrı satırdır
    r2 = istemci.post("/admin/is-hayati/istihdam/kaydet", headers=h, json={
        "veri_yili": yil, "kaynak": "TÜİK ön lisans", "satirlar": [{"program_adi_kaynak": ad, "duzey": "onlisans", "istihdam_orani": 60}]}).json()
    assert r2["eklenen"] == 1
    # Açıkça istenirse yıl baştan yüklenir
    r3 = istemci.post("/admin/is-hayati/istihdam/kaydet", headers=h, json={
        "veri_yili": yil, "kaynak": "TÜİK yeniden", "ayni_yili_degistir": True,
        "satirlar": [{"program_adi_kaynak": ad, "duzey": "lisans", "istihdam_orani": 70}]}).json()
    assert r3["silinen"] == 2 and r3["eklenen"] == 1
    db.execute(text("DELETE FROM istihdam_gostergeleri WHERE veri_yili = :y"), {"y": yil})
    db.commit()


def test_tuik_hucreleri_iki_dilli_ve_eksik_isaret():
    from app.api.admin_is_hayati import _hucre
    assert _hucre(["Tıp\r\nMedicine"], 0) == "Tıp"
    assert _hucre(["Çok yüksek\r\nVery high"], 0) == "Çok yüksek"
    assert _hucre(["."], 0) is None and _hucre(["  "], 0) is None and _hucre([95.4], 0) == 95.4


def test_eslestirme_genel_sozcuk_ve_cati_bolumler():
    from app.core import is_hayati_servisi as ihs
    ad = [{"id": 1, "ad": "Mekatronik Mühendisliği", "anahtarlar": ["mekatronik muhendisligi"]},
          {"id": 2, "ad": "Elektrik ve Elektronik Mühendisliği", "anahtarlar": ["elektrik ve elektronik muhendisligi"]},
          {"id": 3, "ad": "Dil ve Edebiyat", "anahtarlar": ["dil ve edebiyat"]},
          {"id": 4, "ad": "Dil Öğretmenliği", "anahtarlar": ["dil ogretmenligi"]},
          {"id": 5, "ad": "Veterinerlik", "anahtarlar": ["veterinerlik"]}]
    assert ihs.program_eslestir("Elektrik mühendisliği", ad)["bolum_id"] == 2, "genel sözcük (mühendisliği) yetmez"
    assert ihs.program_eslestir("Uzay mühendisliği", ad)["bolum_id"] is None
    assert ihs.program_eslestir("Kore dili ve edebiyatı", ad)["bolum_id"] == 3
    assert ihs.program_eslestir("Almanca öğretmenliği", ad)["bolum_id"] == 4
    assert ihs.program_eslestir("Türkçe öğretmenliği", ad)["bolum_id"] is None, "Türkçe yabancı dil öğretmenliği değil"
    assert ihs.program_eslestir("Veteriner", ad)["bolum_id"] == 5


@db_gerekli
def test_cok_programli_bolum_tek_program_degeri_gostermez(db):
    from app.core import is_hayati_servisi as ihs
    ad = f"DENEME ÇATI {uuid.uuid4().hex[:5].upper()}"
    bid = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": ad}).scalar()
    for p, o, k in (("A dili ve edebiyatı", 50, "dusuk"), ("B dili ve edebiyatı", 70, "orta")):
        db.execute(text("INSERT INTO istihdam_gostergeleri (bolum_id, program_adi_kaynak, duzey, istihdam_orani, kazanc_grubu, veri_yili, kaynak) "
                        "VALUES (:b, :p, 'lisans', :o, :k, 2092, 'TÜİK | ek')"), {"b": bid, "p": p, "o": o, "k": k})
    db.commit()
    v = ihs.istihdam_bolum(db, bid)
    assert v["istihdam_orani"] is None and v["aralik"]["istihdam_orani"] == [50.0, 70.0] and v["coklu_program"] == 2
    assert v["kazanc_grubu"] is None and v["kaynak"] == "TÜİK"
    db.execute(text("INSERT INTO istihdam_gostergeleri (bolum_id, program_adi_kaynak, duzey, istihdam_orani, veri_yili, kaynak) "
                    "VALUES (:b, :p, 'lisans', 61, 2092, 'TÜİK')"), {"b": bid, "p": ad.title()})
    db.commit()
    assert ihs.istihdam_bolum(db, bid)["istihdam_orani"] == 61.0, "adı bölümle aynı program varsa o gösterilir"
    db.execute(text("DELETE FROM istihdam_gostergeleri WHERE veri_yili = 2092"))
    db.commit()


def _tuik_xlsx(baslik: str, satirlar: list[tuple]) -> str:
    """TÜİK Veri Portalı tablosunun biçimi: iki dilli başlık, 'Bölüm\\nProgramme' + yıl sütunları (arada boş sütun), dipnot."""
    import base64
    import io
    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append([baslik])
    ws.append(["English title"])
    ws.append([])
    ws.append(["Bölüm\nProgramme", 2024, None, 2025])
    for ad, d24, d25 in satirlar:
        ws.append([ad, d24, None, d25])
    ws.append(["TÜİK, Yükseköğretim İstihdam Göstergeleri, 2025"])
    ws.append([". Medyan (ortanca) değerin altında mezunu olan bölümlere tablolarda yer verilmemiştir."])
    b = io.BytesIO()
    wb.save(b)
    return base64.b64encode(b.getvalue()).decode()


@db_gerekli
def test_tuik_paketi_dosyalari_tanir_ve_birlestirir(istemci, kisiler, db):
    ad = f"PAKET BÖLÜMÜ {uuid.uuid4().hex[:5].upper()}"
    db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda')"), {"a": ad})
    db.commit()
    p = ad.capitalize()
    dosyalar = [
        {"dosya_adi": "a.xlsx", "icerik_base64": _tuik_xlsx("Lisans mezunlarının bölümlere göre kayıtlı istihdam oranı",
                                                            [("Toplam\nTotal", 75, 74), (f"{p}\r\nEnglish", 80.1, 81.2)])},
        {"dosya_adi": "b.xlsx", "icerik_base64": _tuik_xlsx("Lisans mezunlarının bölümlere göre ilk iş bulma süresi",
                                                            [(f"{p}\r\nEnglish", 5.0, "."), ("Başka bölüm\r\nOther", 6, 7)])},
        {"dosya_adi": "c.xlsx", "icerik_base64": _tuik_xlsx("Lisans mezunlarının bölümlere göre aylık ortalama kazanç grupları",
                                                            [(f"{p}\r\nEnglish", "Yüksek\r\nHigh", "Çok yüksek\r\nVery high")])},
        {"dosya_adi": "d.xlsx", "icerik_base64": _tuik_xlsx("Ön lisans mezunlarının bölümlere göre kayıtlı istihdam oranı",
                                                            [("Makine\r\nMachinery", 70, 71)])},
        {"dosya_adi": "e.xlsx", "icerik_base64": _tuik_xlsx(
            "Lisans mezunlarının eğitim ve öğretim alanları ile uyumlu bir meslek grubunda çalışma oranı", [("Eğitim\nEducation", 60, 61)])},
    ]
    r = istemci.post("/admin/is-hayati/istihdam/tuik-paket", headers=kisiler["super"], json={"dosyalar": dosyalar})
    assert r.status_code == 200, r.text
    v = r.json()
    durum = {d["dosya_adi"]: d["durum"] for d in v["dosyalar"]}
    assert durum == {"a.xlsx": "kullanilacak", "b.xlsx": "kullanilacak", "c.xlsx": "kullanilacak", "d.xlsx": "kullanilacak", "e.xlsx": "atlandi"}
    assert v["yil"] == 2025 and v["kaynak"] == "TÜİK, Yükseköğretim İstihdam Göstergeleri, 2025"
    assert len(v["satirlar"]) == 3, "Toplam satırı ve dipnotlar program değildir"
    on = next(x for x in v["satirlar"] if x["duzey"] == "onlisans")
    assert on["program_adi_kaynak"] == "Makine" and not on["bolum_id"], "ön lisans programı lisans bölümüne bağlanmaz"
    s = next(x for x in v["satirlar"] if x["program_adi_kaynak"] == p)
    assert s["istihdam_orani"] == 81.2 and s["is_bulma_suresi_ay"] is None and s["kazanc_grubu"] == "cok_yuksek"
    assert s["bolum_id"] and s["durum"] == "otomatik"


def test_bolum_duzeyleri_ve_duzeye_gore_eslestirme():
    from app.core import is_hayati_servisi as ihs
    assert ihs.bolum_duzeyleri("2 yıl") == {"onlisans"} and ihs.bolum_duzeyleri("4 yıl") == {"lisans"}
    assert ihs.bolum_duzeyleri("Programa göre 2 veya 4 yıl") == {"lisans", "onlisans"}
    ad = [{"id": 1, "ad": "İş Sağlığı ve Güvenliği", "anahtarlar": ["is sagligi ve guvenligi"], "duzeyler": {"lisans"}},
          {"id": 2, "ad": "Basım Teknolojileri", "anahtarlar": ["basim teknolojileri"], "duzeyler": {"lisans", "onlisans"}}]
    assert ihs.program_eslestir("İş sağlığı ve güvenliği", ad, duzey="onlisans")["bolum_id"] is None
    assert ihs.program_eslestir("İş sağlığı ve güvenliği", ad, duzey="lisans")["bolum_id"] == 1
    assert ihs.program_eslestir("Basım ve yayım teknolojileri", ad, duzey="onlisans")["bolum_id"] == 2
