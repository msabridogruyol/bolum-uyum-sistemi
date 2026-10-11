"""
[2026-10-11] Ortak test düzeneği.

Karar: testlerin çoğu VERİTABANSIZ birim testidir (hız sınırlayıcı, boyut sınırı, maskeleme, ara katmanlar küçük bir
Starlette uygulamasıyla). Gerçek uygulama + yetki testleri (`db` / `istemci` fikstürleri) PostgreSQL ister:
  * DATABASE_URL ortam değişkeni bir PostgreSQL'i göstermeli (CI'da servis konteyneri, şema scripts/test_semasi_kur.py ile).
  * Her test TEK bir bağlantı üzerinde açılan dış işlemde çalışır; uygulamanın get_db'si bu bağlantıya
    "create_savepoint" kipinde bağlanır (uygulamadaki commit'ler SAVEPOINT olur) ve test sonunda her şey GERİ ALINIR.
  * DATABASE_URL yoksa ya da bağlanılamıyorsa bu testler atlanır (skip), birim testleri yine çalışır.
"""
import os
import sys
import uuid
from pathlib import Path

import pytest

KOK = Path(__file__).resolve().parents[1]
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

_DB_URL = os.environ.get("DATABASE_URL", "")


def _db_var_mi() -> bool:
    if not _DB_URL.startswith("postgresql"):
        return False
    try:
        from sqlalchemy import text
        from app.core.database import engine
        with engine.connect() as b:
            b.execute(text("SELECT 1 FROM ogrenciler LIMIT 1"))
        return True
    except Exception:
        return False


DB_VAR = _db_var_mi()
db_gerekli = pytest.mark.skipif(not DB_VAR, reason="DATABASE_URL ile erişilebilir, şeması kurulmuş bir PostgreSQL gerekli")


@pytest.fixture
def baglanti():
    from app.core.database import engine
    b = engine.connect()
    dis = b.begin()
    try:
        yield b
    finally:
        dis.rollback()
        b.close()


@pytest.fixture
def db_fabrikasi(baglanti):
    from sqlalchemy.orm import sessionmaker
    return sessionmaker(bind=baglanti, autoflush=False, join_transaction_mode="create_savepoint")


@pytest.fixture
def db(db_fabrikasi):
    s = db_fabrikasi()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def istemci(db_fabrikasi):
    """Gerçek app.main uygulaması; get_db test işlemine bağlı. Başlangıç olayları (şema güncelleme, arka plan iş
    parçacıkları) çalışmasın diye TestClient bağlam yöneticisi olmadan kullanılır. Hız sınırı sayaçları her testte sıfırlanır."""
    from fastapi.testclient import TestClient
    from app.core.database import get_db
    from app.main import app

    def _get_db():
        s = db_fabrikasi()
        try:
            yield s
        finally:
            s.close()

    app.dependency_overrides[get_db] = _get_db
    _hiz_sayaclarini_sifirla(app)
    try:
        yield TestClient(app, raise_server_exceptions=False)
    finally:
        app.dependency_overrides.pop(get_db, None)


def _hiz_sayaclarini_sifirla(app):
    from app.core.hiz_siniri import HizSiniriAraKatmani
    yigin = app.middleware_stack
    while yigin is not None:
        if isinstance(yigin, HizSiniriAraKatmani):
            yigin.sinirlayici.sifirla()
            return
        yigin = getattr(yigin, "app", None)


@pytest.fixture
def kisiler(db):
    """İki okul; A okulunun yetkilisi, A okulunda bir öğrenci ve bir süper admin + erişim tokenleri."""
    from sqlalchemy import text
    from app.core.security import erisim_tokeni_uret
    ek = uuid.uuid4().hex[:8]
    okul_a = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"Test A {ek}"}).scalar()
    okul_b = db.execute(text("INSERT INTO okullar (ad, aktif_mi) VALUES (:a, TRUE) RETURNING id"), {"a": f"Test B {ek}"}).scalar()
    yetkili, ogrenci, sa = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    for kid, rol, okul in ((yetkili, "okul_yetkilisi", okul_a), (sa, "super_admin", None)):
        db.execute(text("""INSERT INTO admin_kullanicilar (id, ad_soyad, email, sifre_hash, rol, okul_id, aktif_mi, olusturulma_zamani)
                           VALUES (:i, :ad, :e, 'x', :r, :o, TRUE, now())"""),
                   {"i": kid, "ad": f"Test {rol}", "e": f"{rol}.{ek}@test.invalid", "r": rol, "o": okul})
    db.execute(text("""INSERT INTO ogrenciler (id, ad_soyad, email, sifre_hash, okul_id, olusturulma_zamani, guncelleme_zamani)
                       VALUES (:i, 'Test Öğrenci', :e, 'x', :o, now(), now())"""),
               {"i": ogrenci, "e": f"ogr.{ek}@test.invalid", "o": okul_a})
    db.commit()
    return {
        "okul_a": okul_a, "okul_b": okul_b,
        "yetkili": {"Authorization": f"Bearer {erisim_tokeni_uret(yetkili, 'okul_yetkilisi')}"},
        "ogrenci": {"Authorization": f"Bearer {erisim_tokeni_uret(ogrenci, 'ogrenci')}"},
        "super": {"Authorization": f"Bearer {erisim_tokeni_uret(sa, 'super_admin')}"},
    }
