"""[2026-10-12] Okul kayıtlarında (yönetim işlemleri ve öğrenci olayları) ham kod görünmesin: koddaki her
denetim_yaz / olay_yaz işlem kodunun okunur bir etiketi olmalı (etiketler 12 dile çevrilir)."""
import pathlib
import re

from app.api.okul_yonetimi import ISLEM_ETIKET, OLAY_ETIKET, islem_etiketi

KOK = pathlib.Path(__file__).resolve().parents[1] / "app"


def _kodlar(fonksiyon: str) -> set[str]:
    kodlar = set()
    for f in KOK.rglob("*.py"):
        kodlar |= set(re.findall(fonksiyon + r'\(\s*[^,]+,\s*[^,]+,\s*"([a-z_]+)"', f.read_text()))
    return kodlar


def test_her_denetim_kodunun_etiketi_var():
    eksik = sorted(_kodlar("denetim_yaz") - set(ISLEM_ETIKET))
    assert eksik == [], f"ISLEM_ETIKET'e eklenmeli: {eksik}"


def test_her_ogrenci_olayinin_etiketi_var():
    eksik = sorted(_kodlar("olay_yaz") - set(OLAY_ETIKET) - {"ogrenci"})
    assert eksik == [], f"OLAY_ETIKET'e eklenmeli: {eksik}"


def test_bilinmeyen_kod_okunur_gosterilir():
    assert islem_etiketi("yeni_bir_islem") == "Yeni bir islem"
    assert islem_etiketi("sinif_atlat") == "Sınıf atlatma yapıldı"
