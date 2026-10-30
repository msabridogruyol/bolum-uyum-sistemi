"""[2026-10-31] Katmanlı Filiz: bilgi katmanı (sistem içeriğinden kaynaklı cevap), yapay zekâya içerik bağlamı, ölçüm kaydı.
Paket kuralı: kapalı modülün içeriği (ör. İş Hayatı) aramaya hiç girmez."""
import json
import uuid

from sqlalchemy import text

from app.core import filiz_bilgi as fb
from tests.conftest import db_gerekli


def _dizin():
    B = fb.Belge
    return fb.Dizin([
        B("bolum_ders", "Hukuk: neler öğrenilir, hangi dersler var", "Anayasa hukuku, ceza hukuku ve medeni hukuk dersleri.", "Bölümler › Hukuk", None, "hukuk"),
        B("bolum", "Hukuk bölümü", "Hukuk, toplumu düzenleyen kuralları inceler.", "Bölümler › Hukuk", None, "hukuk"),
        B("bolum_ders", "Mimarlık: neler öğrenilir, hangi dersler var", "Mimari tasarım stüdyosu ve yapı bilgisi dersleri.", "Bölümler › Mimarlık", None, "mimarlik"),
        B("ders", "Brüt, net ve bordro okuma", "Brüt ücret kesintilerden önceki, net ücret kesintilerden sonraki tutardır.", "İş Hayatı › Okulda Öğretilmeyenler", "is_hayati"),
        B("sozluk", "Taban suyu", "Toprağın altındaki su.", "Sözlük", None, "", ("taban suyu",)),
        B("sozluk", "Taban puan", "Bir programa yerleşen son kişinin puanı.", "Sözlük", None, "", ("taban puan",)),
    ])


def test_varlik_ve_niyet_dogru_belgeyi_one_alir():
    d = _dizin()
    r = d.ara("Hukuk bölümünde hangi dersler var?", set())
    assert r[0].belge.baslik.startswith("Hukuk: neler") and d.soru_varliklari("Hukuk bölümünde hangi dersler var?") == ["hukuk"]
    assert d.ara("Mimarlık bölümünde hangi dersler okutuluyor?", set())[0].belge.varlik == "mimarlik"


def test_sozluk_yalnizca_terim_aynen_gecerse():
    d = _dizin()
    basliklar = [s.belge.baslik for s in d.ara("taban puan ne demek", set())]
    assert "Taban puan" in basliklar and "Taban suyu" not in basliklar


def test_paket_kurali_kapali_modul_icerigi_gelmez():
    d = _dizin()
    assert not [s for s in d.ara("brüt ve net ücret farkı", set()) if s.belge.modul == "is_hayati"]
    assert d.ara("brüt ve net ücret farkı", {"is_hayati"})[0].belge.tur == "ders"


def test_kisisel_soru_bilgi_sorusu_sayilmaz():
    assert fb.kisisel_mi("Hedefim hukuk, bana uygun mu?") and not fb.kisisel_mi("Hukuk bölümünde hangi dersler var?")


def test_dosya_icerikleri_dizine_girer():
    tur = {b.tur for b in fb._dosya_belgeleri()}
    assert {"gun", "sozluk", "ders", "yol", "zorgun", "dusunme", "cv", "mulakat"} <= tur
    assert all(b.modul == "is_hayati" for b in fb._dosya_belgeleri() if b.tur in {"ders", "yol", "zorgun", "dusunme", "cv", "mulakat"})


def test_cevap_kaynak_gosterir_ve_uydurmaz():
    r = _dizin().ara("Hukuk bölümünde hangi dersler var?", set())
    c = fb.bilgi_cevabi(r)
    assert "Kaynak: Bölümler › Hukuk" in c and "ceza hukuku" in c


# ---------------------------------------------------------------------------------------------------- uçtan uca
def _bolum_ekle(db):
    ad = f"TESTBOLUMU{uuid.uuid4().hex[:5].upper()}"
    detay = {"ozet": "Deneme bölümü özeti.", "neler_ogrenilir": ["Kuramsal temeller öğrenilir."],
             "ornek_dersler": ["Zeytinyağı kimyası", "Kalite denetimi"], "calisma_alanlari": ["Gıda fabrikaları"],
             "meslekler": [{"ad": "Tadım uzmanı", "aciklama": "Ürünlerin kalitesini tadarak değerlendirir."}]}
    db.execute(text("INSERT INTO bolumler (ad, kisa_aciklama, detay, durum) VALUES (:a, 'Kısa', CAST(:d AS jsonb), 'yayinda')"),
               {"a": ad, "d": json.dumps(detay, ensure_ascii=False)})
    db.commit()
    fb.dizini_sifirla()
    return ad


def _goc(db):
    from app.core.sema_guncelleme import _komutlar, _sql_oku
    for g in ("0083_filiz_her_pakette", "0084_filiz_olcum"):
        for k in _komutlar(_sql_oku(g)):
            db.execute(text(k))
    db.commit()


@db_gerekli
def test_rehber_modunda_icerikten_kaynakli_cevap(istemci, kisiler, db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    ad = _bolum_ekle(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: False)
    h = kisiler["ogrenci"]
    ot = istemci.post("/koclugu/asistan/oturum/baslat", headers=h).json()["oturum_id"]
    r = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": f"{ad} bölümünde hangi dersler var?"}).json()
    assert r["kaynak"] == "icerik" and "Zeytinyağı kimyası" in r["asistan_yaniti"] and "Kaynak:" in r["asistan_yaniti"]
    satir = db.execute(text("SELECT kaynak, sure_ms, yapay_zeka FROM ogrenci_koclugu_mesajlari WHERE oturum_id = :o AND rol = 'asistan'"),
                       {"o": ot}).first()
    assert satir.kaynak == "icerik" and satir.sure_ms is not None and satir.yapay_zeka is False
    fb.dizini_sifirla()


@db_gerekli
def test_yapay_zeka_acikken_bilgi_sorusu_yz_ye_gitmez_diger_soruya_baglam_eklenir(istemci, kisiler, db, monkeypatch):
    from app.api import ai_koc
    _goc(db)
    ad = _bolum_ekle(db)
    monkeypatch.setattr(ai_koc, "_ai", lambda db_, o: True)
    istemler = []

    def sahte(sistem, mesajlar):
        istemler.append(sistem)
        return "yapay zekâ cevabı"
    monkeypatch.setattr(ai_koc, "openai_ile_konus", sahte)
    h = kisiler["ogrenci"]
    ot = istemci.post("/koclugu/asistan/oturum/baslat", headers=h).json()["oturum_id"]
    r1 = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h, json={"mesaj": f"{ad} bölümünde hangi dersler var?"}).json()
    assert r1["kaynak"] == "icerik" and istemler == [], "bilgi sorusu yapay zekâya gitmemeli"
    r2 = istemci.post(f"/koclugu/asistan/oturum/{ot}/mesaj", headers=h,
                      json={"mesaj": "Tadım uzmanı olmak bana göre mi, zeytinyağı kimyası kalite denetimi ilgimi çekiyor"}).json()
    assert r2["kaynak"] == "yz" and len(istemler) == 1 and "SİSTEMDEKİ İLGİLİ İÇERİK" in istemler[0]
    assert db.execute(text("SELECT count(*) FROM ogrenci_koclugu_mesajlari WHERE oturum_id = :o AND yapay_zeka"),
                      {"o": ot}).scalar() == 1, "yalnızca yapay zekâ cevabı hakkından düşer"
    fb.dizini_sifirla()


@db_gerekli
def test_admin_kullanim_ozeti(istemci, kisiler, db):
    _goc(db)
    r = istemci.get("/admin/filiz/kullanim?gun=7", headers=kisiler["super"])
    assert r.status_code == 200 and set(r.json()) == {"gun", "kaynaklar", "okullar"}
    assert istemci.get("/admin/filiz/kullanim", headers=kisiler["yetkili"]).status_code in (401, 403)


# ---------------------------------------------------------------------------------- [2026-10-31] bağımsız inceleme
def test_ders_calisma_sorusu_bolum_tanitimina_gitmez(monkeypatch):
    B = fb.Belge
    d = fb.Dizin([B("bolum_is", "Matematik mezunları nerelerde çalışır", "Bankalar, yazılım şirketleri.", "Bölümler › Matematik", None, "matematik"),
                  B("bolum", "Tarih bölümü", "Geçmişi kaynaklarla inceler.", "Bölümler › Tarih", None, "tarih")])
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    for q in ("Matematik netimi nasıl artırırım", "tarih dersine nasıl çalışayım", "biyoloji için kaynak önerir misin",
              "matematik konularını nasıl çalışmalıyım"):
        assert not fb.bilgi_sorusu_mu(None, q), q
    for q in ("Matematik mezunları nerelerde çalışır?", "Tarih bölümü hakkında bilgi verir misin?"):
        assert fb.bilgi_sorusu_mu(None, q), q
