"""
[2026-11-05] Gelişim listesi (haftalık görevlerin yerine): tarihli "ne yaptım" kayıtları, durumlar, isteğe bağlı keşif,
Filiz seviyesi, okul özeti ve rehberlik erken uyarısı.

Plan hesabı (gap analizi + gelişim planı) değerlendirme verisi ister; burada `_plan` sabit bir planla değiştirilir.
Böylece test yalnızca gelişim listesinin kendi kurallarını sınar.
"""
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli

pytestmark = db_gerekli

KOD = "I6-G-1"        # Eleştiriye açıklık — gelişim adımı
KOD2 = "I6-G-2"


def _plan(kodlar=(KOD, KOD2)):
    adimlar = [{"kod": k, "degisken_kod": "I6", "baslik": f"Adım {k}", "aciklama": "Açıklama", "olcut": "Ölçüt",
                "asama": "simdi", "tur_etiket": "Okuma", "durum": None} for k in kodlar]
    return {"odak_alanlari": [{"degisken_kod": "I6", "degisken_adi": "Eleştiriye açıklık", "oncelik_sirasi": 1, "neden_onemli": "Önemli"}],
            "asamalar": [{"kod": "simdi", "ad": "1. Aşama · Başlangıç", "adimlar": adimlar}],
            "guclu_yonler": []}


@pytest.fixture
def ortam(db, kisiler, monkeypatch):
    """Okul A öğrencisi + hedef bölüm; plan sabit (durumlar veritabanından okunur)."""
    from app.core import gelisim_listesi as gl
    from app.models import Ogrenci, OgrenciGelisimAdimDurumu, OgrenciHedefBolum

    ek = uuid.uuid4().hex[:8]
    bid = db.execute(text("INSERT INTO bolumler (ad, durum) VALUES (:a, 'yayinda') RETURNING id"), {"a": f"Test Bölüm {ek}"}).scalar()
    ogr = db.execute(text("SELECT id FROM ogrenciler WHERE okul_id = :o"), {"o": kisiler["okul_a"]}).scalar()
    db.execute(text("""INSERT INTO ogrenci_hedef_bolum (ogrenci_id, bolum_id, aktif_mi, secim_zamani)
                       VALUES (:o, :b, TRUE, now())"""), {"o": ogr, "b": bid})
    db.commit()

    def sahte_plan(dbs, ogrenci):
        hedef = dbs.query(OgrenciHedefBolum).filter(OgrenciHedefBolum.ogrenci_id == ogrenci.id, OgrenciHedefBolum.aktif_mi.is_(True)).first()
        if hedef is None:
            return None, None
        p = _plan()
        durum = {r.adim_kodu: r.durum for r in dbs.query(OgrenciGelisimAdimDurumu).filter(
            OgrenciGelisimAdimDurumu.ogrenci_id == ogrenci.id, OgrenciGelisimAdimDurumu.hedef_bolum_id == hedef.bolum_id)}
        for s in p["asamalar"]:
            for a in s["adimlar"]:
                a["durum"] = durum.get(a["kod"])
        return hedef, p

    monkeypatch.setattr(gl, "_plan", sahte_plan)
    monkeypatch.setattr(gl, "on_adim", lambda dbs, o: None)
    monkeypatch.setattr(gl, "kesif_onerisi", lambda dbs, o, h: None)
    return {"db": db, "ogrenci": db.get(Ogrenci, ogr), "bolum": bid, "baslik": kisiler["ogrenci"], "kisiler": kisiler, "gl": gl}


def _bugun():
    return datetime.now(timezone.utc).astimezone(timezone(timedelta(hours=3))).date()


# ----------------------------------------------------------------------------- kayıt kuralları
def test_kayit_ekle_maddeyi_yapiyoruma_gecirir(ortam):
    gl, db, o = ortam["gl"], ortam["db"], ortam["ogrenci"]
    gl.kayit_ekle(db, o, KOD, _bugun(), "Bir otobiyografi okudum ve yazarın zorlandığı anı not ettim.")
    v = gl.liste(db, o)
    m = v["alanlar"][0]["adimlar"][0]
    assert m["durum"] == "devam_ediyor"
    assert len(m["kayitlar"]) == 1 and m["kayitlar"][0]["tarih"] == _bugun().isoformat()
    assert v["ozet"]["devam_eden"] == 1 and v["ozet"]["tamamlanan"] == 0


@pytest.mark.parametrize("tarih,metin,parca", [
    (lambda: _bugun() + timedelta(days=1), "Yarın yapacağım bir şey burada", "İleri bir tarih"),
    (lambda: _bugun() - timedelta(days=401), "Çok eski bir kayıt denemesi", "bir yıldan"),
    (lambda: _bugun(), "kısa", "en az 10"),
])
def test_kayit_kurallari(ortam, tarih, metin, parca):
    from app.core.katman_servisi import IsKuraliHatasi
    with pytest.raises(IsKuraliHatasi, match=parca):
        ortam["gl"].kayit_ekle(ortam["db"], ortam["ogrenci"], KOD, tarih(), metin)


def test_plan_disi_madde_reddedilir(ortam):
    from app.core.katman_servisi import IsKuraliHatasi
    with pytest.raises(IsKuraliHatasi, match="listesinde yok"):
        ortam["gl"].kayit_ekle(ortam["db"], ortam["ogrenci"], "P1-G-1", _bugun(), "Plan dışı bir madde için kayıt")


def test_yaptim_kayit_ister_yapmadim_kayitlari_korur(ortam):
    from app.core.katman_servisi import IsKuraliHatasi
    from app.models import OgrenciGelisimAdimDurumu
    gl, db, o = ortam["gl"], ortam["db"], ortam["ogrenci"]
    with pytest.raises(IsKuraliHatasi, match="Yaptım"):
        gl.durum_degistir(db, o, KOD, "tamamlandi")
    gl.kayit_ekle(db, o, KOD, _bugun(), "Hedef meslekten birinin röportajını izledim.")
    gl.durum_degistir(db, o, KOD, "tamamlandi")
    assert gl.liste(db, o)["ozet"]["tamamlanan"] == 1
    gl.durum_degistir(db, o, KOD, "bekliyor")
    r = db.query(OgrenciGelisimAdimDurumu).filter_by(ogrenci_id=o.id, adim_kodu=KOD).one()
    assert r.durum == "planlandi"                      # silinmez; kayıtlar yerinde
    m = gl.liste(db, o)["alanlar"][0]["adimlar"][0]
    assert m["durum"] == "bekliyor" and len(m["kayitlar"]) == 1


def test_kayit_yalniz_sahibince_silinir(ortam, db):
    from app.core.katman_servisi import IsKuraliHatasi
    from app.models import Ogrenci
    gl, o = ortam["gl"], ortam["ogrenci"]
    kid = gl.kayit_ekle(db, o, KOD, _bugun(), "Silinecek bir deneme kaydı yazdım.")["id"]
    baska = Ogrenci(id=uuid.uuid4())
    with pytest.raises(IsKuraliHatasi):
        gl.kayit_sil(db, baska, kid)
    gl.kayit_sil(db, o, kid)
    assert gl.adim_kayitlari(db, o, ortam["bolum"]) == {}


def test_plan_hatasi_ayni_islemdeki_kaydi_geri_almaz(ortam, monkeypatch):
    """Plan hesaplanamazsa yalnızca o deneme geri alınır (kayıt noktası); az önce yazılan kayıt kaybolmaz."""
    gl, db, o = ortam["gl"], ortam["db"], ortam["ogrenci"]
    gl.kayit_ekle(db, o, KOD, _bugun(), "Kaybolmaması gereken bir kayıt yazdım.")
    monkeypatch.undo()
    import app.core.koclugu_servisi as ks
    monkeypatch.setattr(ks, "gelisim_plani_olustur", lambda *a, **k: (_ for _ in ()).throw(RuntimeError("profil yok")))
    monkeypatch.setattr(gl, "_son_tur", lambda dbs, og: type("T", (), {"durum": "tamamlandi"})())
    monkeypatch.setattr(ks, "gap_analizi_hesapla", lambda *a, **k: {})
    hedef, plan = gl._plan(db, o)
    assert hedef is not None and plan is None
    n = db.execute(text("SELECT count(*) FROM ogrenci_gelisim_kayitlari WHERE ogrenci_id = :o"), {"o": o.id}).scalar()
    assert n == 1


# ----------------------------------------------------------------------------- isteğe bağlı maddeler ve seviye
def test_kesif_tek_kez_sayilir_ve_seviye_puani(ortam):
    gl, db, o = ortam["gl"], ortam["db"], ortam["ogrenci"]
    p0 = gl.seviye_hesapla(db, o)["puan"]
    assert gl.kesif_kaydet(db, o, ortam["bolum"]) is True
    assert gl.kesif_kaydet(db, o, ortam["bolum"]) is False
    gl.oz_degerlendirme_kaydet(db, o, {"iyi": "Planımı uyguladım", "zor": "Zaman ayırmak", "hedef": "Bir biyografi bitirmek"})
    assert gl.seviye_hesapla(db, o)["puan"] == p0 + 2 * gl.PUAN_ISTEGE_BAGLI
    gl.kayit_ekle(db, o, KOD, _bugun(), "Bir biyografinin ilk bölümünü okudum.")
    gl.durum_degistir(db, o, KOD, "tamamlandi")
    assert gl.seviye_hesapla(db, o)["puan"] == p0 + 2 * gl.PUAN_ISTEGE_BAGLI + gl.PUAN_ADIM


def test_oz_degerlendirme_uc_soru_ister(ortam):
    from app.core.katman_servisi import IsKuraliHatasi
    with pytest.raises(IsKuraliHatasi):
        ortam["gl"].oz_degerlendirme_kaydet(ortam["db"], ortam["ogrenci"], {"iyi": "Bir şey"})


def test_seviye_eski_haftalik_puandan_dusmez(ortam):
    """Eski haftalık görevlerden kazanılan seviye, yeni puanlamaya geçince düşmemeli (max kuralı)."""
    gl, db, o = ortam["gl"], ortam["db"], ortam["ogrenci"]
    pzt = date.today() - timedelta(days=date.today().weekday())
    for i in range(6):
        db.execute(text("""INSERT INTO ogrenci_haftalik_gorev (ogrenci_id, hafta_baslangic, sira, tur, baslik, durum, tamamlanma_zamani)
                           VALUES (:o, :h, :s, 'plan_adimi', 'Eski görev', 'tamamlandi', now())"""),
                   {"o": o.id, "h": pzt - timedelta(weeks=i // 3), "s": i % 3 + 1})
    s = gl.seviye_hesapla(db, o)
    assert s["puan"] >= 6 * gl._ESKI_PUAN_GOREV


# ----------------------------------------------------------------------------- okul özeti ve erken uyarı
def test_okul_ozeti_ve_rehberlik_ayni_durgunluk_tanimi(ortam):
    from app.api.rehberlik import _gelisim_durgunlari
    gl, db, o = ortam["gl"], ortam["db"], ortam["ogrenci"]
    eski = datetime.now(timezone.utc) - timedelta(days=gl.DURGUN_GUN + 3)
    db.execute(text("UPDATE ogrenci_hedef_bolum SET secim_zamani = :z WHERE ogrenci_id = :o"), {"z": eski, "o": o.id})
    oz = gl.okul_ozeti(db, [o.id])
    assert oz["hedefli"] == 1 and oz["durgun"] == 1 and oz["dagilim"][0]["deger"] == 1
    assert _gelisim_durgunlari(db, [o.id]).get(o.id, 0) >= gl.DURGUN_GUN
    # Bir kayıt girmek (henüz "yaptım" demeden) de harekettir
    gl.kayit_ekle(db, o, KOD, _bugun(), "Bugün bir otobiyografiye başladım.")
    assert gl.okul_ozeti(db, [o.id])["durgun"] == 0
    assert o.id not in _gelisim_durgunlari(db, [o.id])


# ----------------------------------------------------------------------------- uçlar
def test_api_akisi(ortam, istemci):
    h = ortam["baslik"]
    r = istemci.get("/gelisim-listesi", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["alanlar"][0]["toplam"] == 2
    r = istemci.post(f"/gelisim-listesi/adim/{KOD}/durum", json={"durum": "tamamlandi"}, headers=h)
    assert r.status_code == 400
    r = istemci.post(f"/gelisim-listesi/adim/{KOD}/kayit", json={"tarih": _bugun().isoformat(), "aciklama": "Ünlü bir mühendisin hayatını okudum."}, headers=h)
    assert r.status_code == 200, r.text
    r = istemci.post(f"/gelisim-listesi/adim/{KOD}/durum", json={"durum": "tamamlandi"}, headers=h)
    assert r.status_code == 200 and r.json()["ozet"]["tamamlanan"] == 1
    r = istemci.post(f"/gelisim-listesi/adim/{KOD}/kayit", json={"tarih": (_bugun() + timedelta(days=2)).isoformat(), "aciklama": "Gelecek tarihli kayıt denemesi"}, headers=h)
    assert r.status_code == 400
    # Eski haftalık uç kaldırıldı
    assert istemci.get("/haftalik", headers=h).status_code == 404


def test_koclugu_yaptim_ne_yaptim_ister(ortam, istemci):
    """Koçluk sayfasındaki eski "tamamlandı" yolu da kayıtsız "yaptım"a izin vermez; ne_yaptim verilirse bugünün kaydı olur."""
    h = ortam["baslik"]
    r = istemci.post(f"/koclugu/hedef/adim/{KOD}", json={"durum": "tamamlandi"}, headers=h)
    assert r.status_code == 400, r.text
    r = istemci.post(f"/koclugu/hedef/adim/{KOD}", json={"durum": "tamamlandi", "ne_yaptim": "Bir biyografi okuyup not aldım."}, headers=h)
    assert r.status_code in (200, 204), r.text
    k = ortam["gl"].adim_kayitlari(ortam["db"], ortam["ogrenci"], ortam["bolum"])
    assert k[KOD][0]["tarih"] == _bugun().isoformat()
