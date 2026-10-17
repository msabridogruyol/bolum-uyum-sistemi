"""
[2026-10-17] Bölüm uyumu — sonradan müdahale yok:
  * uyum puanı = 10 ÇKKV yönteminin ortalaması (alan cezası puana yazılıp 0'a kırpılmaz);
  * öneri sırası yalnızca gösterilen puana göredir (alan gruplaması / kota yok).
"""
from app.core import skor_motoru as sm
from tests.conftest import db_gerekli


def _satir(b, u):
    return sm.SiralamaSatiri(bolum_id=b, toplam_uyum=u)


def test_sira_yalnizca_puana_gore():
    # farklı alanlardan karışık puanlar: alan, sıra üzerinde hiçbir etki yapmamalı
    alan_of = {0: "Turizm & Hizmet", 1: "Spor Bilimleri", 2: "Tarım, Hayvancılık, Gıda & Çevre",
               3: "Tarım, Hayvancılık, Gıda & Çevre", 4: "İşletme, Ekonomi & Finans", 5: "Mimarlık & Planlama"}
    puan = {0: 90.0, 1: 71.0, 2: 90.0, 3: 88.0, 4: 54.0, 5: 85.0}
    satirlar = [_satir(b, u) for b, u in puan.items()]
    sira = sm._satirlari_sirala(list(satirlar), alan_of, {2: 1.0, 0: 2.0}, {}, {})
    assert [s.toplam_uyum for s in sira] == sorted(puan.values(), reverse=True)
    assert [s.bolum_id for s in sira[:2]] == [2, 0]                 # eşitlikte ağırlıklı varyansı düşük olan önde
    assert {s.bolum_id: s.toplam_uyum for s in sira} == puan        # puan değişmez
    assert all(s.alan == alan_of[s.bolum_id] for s in sira)          # alan yalnızca bilgi
    ilk3 = sm._satirlari_sirala(list(satirlar), alan_of, {2: 1.0, 0: 2.0}, {}, {}, ilk_n=3)
    assert [s.bolum_id for s in ilk3] == [s.bolum_id for s in sira[:3]]


@db_gerekli
def test_gercek_siralama_puanla_tutarli(db):
    """Veritabanındaki her tamamlanmış tur: öğrencinin gördüğü sıra puana göre azalan."""
    from app.models import Ogrenci, OgrenciBolumUyumSkoru, OgrenciDegerlendirmeTuru
    for o_id, t_id in db.query(OgrenciBolumUyumSkoru.ogrenci_id, OgrenciBolumUyumSkoru.tur_id).distinct().limit(10):
        sira = sm.siralama_getir(db, db.get(Ogrenci, o_id), db.get(OgrenciDegerlendirmeTuru, t_id), ilk_n=301)
        puanlar = [s.toplam_uyum for s in sira]
        assert puanlar == sorted(puanlar, reverse=True)


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
