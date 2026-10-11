"""
[2026-10-11] Boş bir PostgreSQL veritabanına test/CI için şema kurar.

Neden `alembic upgrade head` değil? Göç zinciri boş bir veritabanında baştan sona çalışmıyor:
  - 0001_ilk_sema DDL'i ';' ile böler; yorum satırlarındaki ';' yüzünden bazı parçalar SQL değil, düz metin olur.
  - alembic_version.version_num varsayılan VARCHAR(32); 0006_gelisim_karsilastirma_yorumu 33 karakter.
  - Bazı tablolar (ör. guvenlik_olaylari) hiçbir göçte oluşturulmuyor, yalnızca ORM modellerinde var.
Canlı veritabanı yıllar içinde bu adımların karışımıyla oluştuğu için burada aynı karışım "hoşgörülü" biçimde
yeniden üretilir:
  1) 0001 DDL'i (yorumlar ayıklanarak) komut komut,
  2) ORM modelleri: Base.metadata.create_all (eksik tabloları tamamlar; sonda eksik kolonlar ALTER ile eklenir),
  3) 0002 → son göç: her göçün upgrade()'i, her op çağrısı ayrı ayrı ve hatası yutularak (AUTOCOMMIT),
  4) tekrar create_all ve uygulamanın kendi app.core.sema_guncelleme.semayi_guncelle'si.
Kullanım:  DATABASE_URL=postgresql://... python scripts/test_semasi_kur.py
Hata sayısı yazdırılır; kritik tablolar (ogrenciler, admin_kullanicilar, okullar, sistem_parametreleri,
hata_kayitlari) yoksa çıkış kodu 1 olur.
"""
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KOK))

from alembic.operations import Operations  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from sqlalchemy import inspect, text  # noqa: E402

from app import models  # noqa: E402,F401  — tüm modelleri metadata'ya kaydeder
from app.core.database import Base, engine  # noqa: E402

SURUMLER = KOK / "alembic" / "versions"
KRITIK = ["ogrenciler", "admin_kullanicilar", "okullar", "sistem_parametreleri", "hata_kayitlari", "bildirimler"]
hatalar: list[str] = []


def _modul(yol: Path):
    spec = importlib.util.spec_from_file_location(f"_goc_{yol.stem}", yol)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _yorumsuz(sql: str) -> str:
    return "\n".join(re.sub(r"--.*$", "", satir) for satir in sql.splitlines())


def _bol(sql: str) -> list[str]:
    """';' ile biten komutlara böler; $$ ... $$ blokları (DO / fonksiyon gövdesi) içinde bölmez."""
    parcalar, tampon = [], ""
    for parca in re.split(r"(;)", _yorumsuz(sql)):
        tampon += parca
        if parca == ";" and tampon.count("$$") % 2 == 0:
            if tampon.strip(" \n;"):
                parcalar.append(tampon)
            tampon = ""
    if tampon.strip(" \n;"):
        parcalar.append(tampon)
    return parcalar


def _eksik_kolonlari_ekle(b) -> int:
    """create_all var olan tabloya kolon eklemez: ORM'de olup veritabanında olmayan kolonları ALTER ile ekler."""
    ins = inspect(b)
    n = 0
    for tablo in Base.metadata.tables.values():
        if not ins.has_table(tablo.name):
            continue
        var = {c["name"] for c in ins.get_columns(tablo.name)}
        for kolon in tablo.columns:
            if kolon.name in var:
                continue
            tip = kolon.type.compile(dialect=b.dialect)
            varsayilan = ""
            if kolon.server_default is not None and hasattr(kolon.server_default, "arg"):
                arg = kolon.server_default.arg
                varsayilan = f" DEFAULT {arg.text if hasattr(arg, 'text') else repr(arg)}"
            try:
                b.execute(text(f'ALTER TABLE "{tablo.name}" ADD COLUMN IF NOT EXISTS "{kolon.name}" {tip}{varsayilan}'))
                n += 1
            except Exception as e:  # noqa: BLE001
                hatalar.append(f"kolon {tablo.name}.{kolon.name}: {str(e).splitlines()[0][:140]}")
    return n


def _varsayilanlari_tamamla(b) -> int:
    """ORM'in oluşturduğu tablolarda varsayılanlar yalnızca Python tarafındadır (default=datetime.utcnow vb.); göçlerin ham
    SQL INSERT'leri ve testler için veritabanı varsayılanı ekler: tarih → now(), uuid4 → gen_random_uuid(), sabit → değeri."""
    import uuid as _uuid
    from sqlalchemy import Date, DateTime
    ins = inspect(b)
    n = 0
    for tablo in Base.metadata.tables.values():
        if not ins.has_table(tablo.name):
            continue
        db_kolon = {c["name"]: c for c in ins.get_columns(tablo.name)}
        for kolon in tablo.columns:
            d = kolon.default
            if d is None or kolon.name not in db_kolon or db_kolon[kolon.name].get("default") is not None:
                continue
            ifade = None
            if getattr(d, "is_callable", False):
                fn = getattr(d.arg, "__wrapped__", d.arg)
                ad = getattr(fn, "__name__", "")
                if isinstance(kolon.type, (DateTime, Date)) or ad in ("utcnow", "now", "simdi", "_simdi"):
                    ifade = "now()"
                elif fn is _uuid.uuid4 or ad == "uuid4":
                    ifade = "gen_random_uuid()"
                elif fn in (list, dict) or ad in ("list", "dict", "<lambda>") and "json" in str(kolon.type).lower():
                    try:
                        ifade = "'" + json.dumps(fn() if fn in (list, dict) else d.arg(None)) + "'"
                    except Exception:  # noqa: BLE001
                        ifade = "'[]'"
            elif getattr(d, "is_scalar", False):
                v = d.arg
                if isinstance(v, bool):
                    ifade = "TRUE" if v else "FALSE"
                elif isinstance(v, (int, float)):
                    ifade = str(v)
                elif isinstance(v, str):
                    ifade = "'" + v.replace("'", "''") + "'"
                elif isinstance(v, (list, dict)):
                    ifade = "'" + json.dumps(v).replace("'", "''") + "'"
            if ifade is None:
                continue
            try:
                b.execute(text(f'ALTER TABLE "{tablo.name}" ALTER COLUMN "{kolon.name}" SET DEFAULT {ifade}'))
                n += 1
            except Exception as e:  # noqa: BLE001
                hatalar.append(f"varsayılan {tablo.name}.{kolon.name}: {str(e).splitlines()[0][:140]}")
    return n


class _HosgoruluOp:
    """alembic `op` yerine geçer: her çağrı ayrı denenir, hata kaydedilip geçilir."""

    def __init__(self, gercek: Operations, ad: str):
        self._g, self._ad = gercek, ad

    def __getattr__(self, isim):
        hedef = getattr(self._g, isim)
        if not callable(hedef):
            return hedef

        def _sar(*a, **k):
            try:
                return hedef(*a, **k)
            except Exception as e:  # noqa: BLE001
                # çok komutlu bir execute ise komutları tek tek dene (biri bozuksa diğerleri yine uygulansın)
                if isim == "execute" and a and isinstance(a[0], str) and ";" in a[0]:
                    for komut in _bol(a[0]):
                        if komut.strip():
                            try:
                                hedef(komut, *a[1:], **k)
                            except Exception as e2:  # noqa: BLE001
                                hatalar.append(f"{self._ad}.execute: {str(e2).splitlines()[0][:140]}")
                    return None
                hatalar.append(f"{self._ad}.{isim}: {str(e).splitlines()[0][:140]}")
                return None
        return _sar


def kur() -> int:
    with engine.connect() as b:
        b = b.execution_options(isolation_level="AUTOCOMMIT")
        # 1) 0001
        ddl = _modul(SURUMLER / "0001_ilk_sema.py")._DDL
        for komut in _bol(ddl):
            if komut.strip():
                try:
                    b.execute(text(komut))
                except Exception as e:  # noqa: BLE001
                    hatalar.append(f"0001: {str(e).splitlines()[0][:140]}")
        # 2) ORM
        Base.metadata.create_all(b)
        _eksik_kolonlari_ekle(b)
        _varsayilanlari_tamamla(b)
        # 3) diğer göçler
        ops = Operations(MigrationContext.configure(b))
        for yol in sorted(SURUMLER.glob("[0-9][0-9][0-9][0-9]_*.py")):
            if yol.stem.startswith("0001"):
                continue
            m = _modul(yol)
            if hasattr(m, "op"):
                m.op = _HosgoruluOp(ops, yol.stem)
            try:
                m.upgrade()
            except Exception as e:  # noqa: BLE001
                hatalar.append(f"{yol.stem}.upgrade: {str(e).splitlines()[0][:140]}")
        # 4) ORM (eksik tablo + eksik kolon) + uygulamanın kendi şema güncellemesi
        Base.metadata.create_all(b)
        _eksik_kolonlari_ekle(b)
        _varsayilanlari_tamamla(b)
    from app.core.sema_guncelleme import semayi_guncelle
    s = semayi_guncelle(engine)
    tablolar = set(inspect(engine).get_table_names())
    eksik = [t for t in KRITIK if t not in tablolar]
    print(f"Şema kuruldu: {len(tablolar)} tablo · hoşgörülen hata: {len(hatalar)} · sema_guncelleme: "
          f"{s.get('uygulanan', 0)} komut, {len(s.get('hata', []))} hata")
    if os.environ.get("AYRINTI"):
        print("\n".join(hatalar))
    if eksik:
        print("EKSİK KRİTİK TABLOLAR:", ", ".join(eksik))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(kur())
