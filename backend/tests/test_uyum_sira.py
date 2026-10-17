"""
[2026-10-17] Bölüm uyumu:
  * alan cezası PUANI değiştirmez (eskiden ~200/301 bölüm 0'a kırpılıyordu), yalnızca sırayı etkiler;
  * ilk 10'da tek bir üst alandan en fazla ILK10_ALAN_UST_SINIRI bölüm olur, fazlası 11. sıradan itibaren gelir.
"""
from app.core import skor_motoru as sm
from tests.conftest import db_gerekli


def _satir(b, u):
    return sm.SiralamaSatiri(bolum_id=b, toplam_uyum=u)


def test_ilk10_alan_ust_siniri_ve_puan_korunur():
    # 12 mühendislik bölümü (95→84), 4 bilişim (80→77), 4 temel bilim (70→67): mühendislik komşularıyla aynı grupta
    alan_of = {}
    satirlar = []
    for i in range(12):
        alan_of[i] = "Mühendislik"; satirlar.append(_satir(i, 95 - i))
    for i in range(12, 16):
        alan_of[i] = "Bilişim & Yazılım"; satirlar.append(_satir(i, 80 - (i - 12)))
    for i in range(16, 20):
        alan_of[i] = "Temel Bilimler"; satirlar.append(_satir(i, 70 - (i - 16)))
    puan_once = {s.bolum_id: s.toplam_uyum for s in satirlar}
    sira = sm._satirlari_sirala(list(satirlar), alan_of, {}, {}, {})
    ilk10 = sira[:10]
    assert sum(1 for s in ilk10 if s.alan == "Mühendislik") == sm.ILK10_ALAN_UST_SINIRI
    assert {s.alan for s in ilk10} >= {"Mühendislik", "Bilişim & Yazılım", "Temel Bilimler"}
    assert [s.bolum_id for s in ilk10[:5]] == [0, 1, 2, 3, 4]       # en yüksek puanlılar başta
    assert sira[10].alan == "Mühendislik"                             # ertelenen mühendislik 11. sıradan gelir
    assert {s.bolum_id: s.toplam_uyum for s in sira} == puan_once     # gösterilen puan değişmez
    assert len(sira) == 20 and len({s.bolum_id for s in sira}) == 20
    assert [s.bolum_id for s in sm._satirlari_sirala(list(satirlar), alan_of, {}, {}, {}, ilk_n=7)] == [s.bolum_id for s in sira[:7]]


@db_gerekli
def test_kayitli_uyum_ceza_iceremez(db):
    """Yeniden hesaplanan TOPLAM_UYUM = 10 yöntemin ortalaması; alan cezasıyla 0'a kırpılmış toplu kayıt yok."""
    import numpy as np

    from app.models import Ogrenci, OgrenciBolumUyumSkoru, OgrenciDegerlendirmeTuru
    kayit = db.query(OgrenciBolumUyumSkoru.ogrenci_id, OgrenciBolumUyumSkoru.tur_id).distinct().first()
    if kayit is None:
        return
    o, t = db.get(Ogrenci, kayit[0]), db.get(OgrenciDegerlendirmeTuru, kayit[1])
    assert sm.toplam_uyum_hesapla(db, o, t) > 0
    g = sm.girdi_hazirla(db, o, t)
    beklenen = np.mean([sm._min_max_0_100(f(g.performans, g.agirliklar)) for f in sm.YONTEMLER.values()], axis=0)
    kayitli = {s.bolum_id: float(s.toplam_uyum) for s in db.query(OgrenciBolumUyumSkoru).filter_by(tur_id=t.id)}
    for i, b in enumerate(g.bolum_idler):
        assert abs(kayitli[b] - round(float(beklenen[i]), 2)) < 0.011
    assert sum(1 for v in kayitli.values() if v == 0) <= 1
    db.rollback()
