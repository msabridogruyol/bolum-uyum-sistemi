"""[2026-10-30] Bitmiş katman aynı turda yeniden açılmaz, cevabı değiştirilmez, ikinci kez puanlanmaz.

Önceden katman_oturumu_baslat donmuş soru setini "tamamlandı" kontrolünden ÖNCE döndürüyordu: öğrenci bitirdiği
bölüme dönüp soruları ve kendi cevaplarını görebiliyor, cevap değiştirip bölümü yeniden puanlatabiliyordu.
Güven sorunu nedeniyle tekrar çözme (katmani_tekrara_ac) oturumu sildiği için çalışmaya devam etmeli.
"""
import uuid

import pytest
from sqlalchemy import text

from tests.conftest import db_gerekli


def _kur(db):
    from app.models import Katman, Ogrenci
    ek = uuid.uuid4().hex[:6]
    # Test şemasında 0001'den kalan eski CHECK (yalnızca likert/sjt) olabilir; ORM'deki güncel kural kontrolü de içerir.
    db.execute(text("ALTER TABLE sorular DROP CONSTRAINT IF EXISTS sorular_soru_tipi_check"))
    kid = db.execute(text("INSERT INTO katmanlar (kod, ad, sira, kosullu_mu) VALUES (:k, 'Test katmanı', 90, FALSE) RETURNING id"),
                     {"k": f"T{ek}"}).scalar()
    soru_secenek = []
    for i in range(2):
        sid = db.execute(text("""INSERT INTO sorular (katman_id, soru_tipi, soru_metni, ters_kodlanmis_mi, aktif_mi,
                                  olusturulma_zamani, beklenen_secenek_sira, cevap_bicimi)
                                  VALUES (:k, 'kontrol', :m, FALSE, TRUE, now(), 1, 'tek') RETURNING id"""),
                         {"k": kid, "m": f"Test sorusu {i} {ek}"}).scalar()
        secs = [db.execute(text("INSERT INTO soru_secenekleri (soru_id, secenek_sirasi, secenek_metni) VALUES (:s, :n, :t) RETURNING id"),
                           {"s": sid, "n": n, "t": f"Şık {n}"}).scalar() for n in (1, 2)]
        soru_secenek.append((sid, secs))
    oid = uuid.uuid4()
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Test Öğrenci', :e, 'x', now(), now())"""), {"i": oid, "e": f"kilit.{ek}@test.invalid"})
    db.flush()
    return db.get(Katman, kid), db.get(Ogrenci, oid), soru_secenek


@db_gerekli
def test_bitmis_katman_yeniden_acilmaz_ve_cevap_degismez(db):
    from app.core.katman_servisi import (IsKuraliHatasi, aktif_veya_yeni_tur_getir, cevabi_kaydet, katman_oturumu_baslat,
                                         katmani_tamamla, katmani_tekrara_ac)
    katman, ogrenci, ss = _kur(db)
    tur = aktif_veya_yeni_tur_getir(db, ogrenci)

    oturum, sorular = katman_oturumu_baslat(db, ogrenci, katman, tur)
    assert len(sorular) == 2
    # Bitmeden geri dönmek serbest: aynı donmuş set gelir
    assert [s.id for s in katman_oturumu_baslat(db, ogrenci, katman, tur)[1]] == [s.id for s in sorular]
    for sid, secs in ss:
        cevabi_kaydet(db, ogrenci, tur, sid, secs[0])
    cevabi_kaydet(db, ogrenci, tur, ss[0][0], ss[0][1][1])        # bitmeden cevap değiştirmek serbest
    katmani_tamamla(db, ogrenci, katman, tur, oturum)
    assert oturum.durum == "tamamlandi"

    with pytest.raises(IsKuraliHatasi):                            # sorular ve cevaplar yeniden açılmaz
        katman_oturumu_baslat(db, ogrenci, katman, tur)
    with pytest.raises(IsKuraliHatasi):                            # cevap değiştirilemez
        cevabi_kaydet(db, ogrenci, tur, ss[0][0], ss[0][1][0])
    with pytest.raises(IsKuraliHatasi):                            # ikinci kez puanlanmaz
        katmani_tamamla(db, ogrenci, katman, tur, oturum)
    kayitli = db.execute(text("SELECT secenek_id FROM ogrenci_cevaplar WHERE tur_id = :t AND soru_id = :s"),
                         {"t": tur.id, "s": ss[0][0]}).scalar()
    assert kayitli == ss[0][1][1], "reddedilen istek kayıtlı cevabı değiştirmemeli"

    # Güven sorunu / yönetim isteğiyle tekrar açma çalışmaya devam eder
    katmani_tekrara_ac(db, ogrenci, tur, katman)
    db.flush()
    yeni, sorular2 = katman_oturumu_baslat(db, ogrenci, katman, tur)
    assert yeni.durum != "tamamlandi" and len(sorular2) == 2
    cevabi_kaydet(db, ogrenci, tur, ss[0][0], ss[0][1][0])
