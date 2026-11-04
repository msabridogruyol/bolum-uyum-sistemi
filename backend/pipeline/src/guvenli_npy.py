"""[2026-11-04] Güvenlik denetimi — önbellekteki ad / kod listeleri pickle'sız okunur.

onbellek/ klasörü sistem deposu üzerinden cihazlar arasında eşitlenir. Ad ve kod listeleri eskiden dtype=object (pickle)
olarak kaydedilip np.load(..., allow_pickle=True) ile okunuyordu: depoya pickle içeren bir .npy koyabilen biri, dosyayı
açan her bilgisayarda kod çalıştırabilirdi. Artık:
  * kayıt düz Unicode dizisi olarak yapılır (dtype='<U…', pickle yok);
  * okuma önce allow_pickle=False ile denenir; eski (object) dosyalar yalnızca numpy dizi yapısı ve düz metin
    nesnelerine izin veren kısıtlı bir çözücüyle okunur — başka hiçbir sınıf/fonksiyon yüklenmez.
"""
from __future__ import annotations

import io
import pickle
from pathlib import Path

import numpy as np

_IZINLI = {
    ("numpy.core.multiarray", "_reconstruct"), ("numpy._core.multiarray", "_reconstruct"),
    ("numpy", "ndarray"), ("numpy", "dtype"),
    ("numpy.core.multiarray", "scalar"), ("numpy._core.multiarray", "scalar"),
    ("builtins", "str"), ("builtins", "list"), ("builtins", "tuple"),
}


class _KisitliCozucu(pickle.Unpickler):
    def find_class(self, modul, ad):
        if (modul, ad) in _IZINLI:
            return super().find_class(modul, ad)
        raise pickle.UnpicklingError(f"Önbellek dosyasında izin verilmeyen nesne: {modul}.{ad}")


def metin_listesi_kaydet(yol: Path, ogeler) -> None:
    np.save(yol, np.array([str(x) for x in ogeler], dtype=str))


def metin_listesi_oku(yol: Path) -> list[str]:
    try:
        return [str(x) for x in np.load(yol, allow_pickle=False)]
    except ValueError:
        pass   # eski biçim: object dizisi (pickle)
    with open(yol, "rb") as f:
        ham = f.read()
    tampon = io.BytesIO(ham)
    surum = np.lib.format.read_magic(tampon)
    oku_baslik = {(1, 0): np.lib.format.read_array_header_1_0, (2, 0): np.lib.format.read_array_header_2_0}.get(surum)
    if oku_baslik is None:
        raise ValueError(f"{yol.name}: desteklenmeyen .npy sürümü {surum}")
    _sekil, _fortran, dtype = oku_baslik(tampon, max_header_size=10_000)
    if dtype != np.dtype(object):
        raise ValueError(f"{yol.name}: beklenmeyen veri türü {dtype}")
    dizi = _KisitliCozucu(tampon).load()
    if not all(isinstance(x, str) for x in np.asarray(dizi).ravel()):
        raise ValueError(f"{yol.name}: ad listesi yalnızca metin içermeli")
    return [str(x) for x in np.asarray(dizi).ravel()]
