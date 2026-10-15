"""[2026-10-12] Türkçe metin yardımcıları (bağımlılıksız; her modülden döngüsel import riski olmadan alınabilir)."""


def turkce_kucult(metin: str | None) -> str:
    """Türkçe küçük harf: Python'un str.lower()'ı 'İ' harfini 'i̇' (i + birleşik nokta, U+0307) yapar ve ekranda
    "i̇ş güvencesi" gibi bozuk görünür; 'I' harfini de 'ı' yerine 'i' yapar. Önce bu iki harf Türkçe kurala göre çevrilir."""
    return (metin or "").replace("İ", "i").replace("I", "ı").lower()


def turkce_buyut(metin: str | None) -> str:
    """[2026-10-14] Türkçe büyük harf: str.upper() 'i' harfini 'I' yapar ("FILIZYOL NEDIR"); önce i → İ, ı → I çevrilir."""
    return (metin or "").replace("i", "İ").replace("ı", "I").upper()
