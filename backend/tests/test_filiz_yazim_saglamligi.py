"""[2026-11-02] 2.000 öğrencilik uçtan uca simülasyonda bulunan Filiz yazım hatası sorunlarının kalıcı testleri.

Kök nedenler (ayrıntı: filiz_bilgi._yazim, Dizin._hatali_cok_sozcuklu, anahtar_yakin):
  1. Çok sözcüklü bölüm adının bir sözcüğü hatalı yazılınca ad bulunamıyor, kalan sözcüklere uyan BAŞKA bir bölüm
     anlatılıyordu ("Siyaset İlimi ve Kamu Yönetimi" → Kamu Yönetimi, "Fizi Öğretmenliği" → başka öğretmenlik).
  2. Yazım düzeltmesi doğru yazılmış ekli sözcüğü bozuyordu ("puanları" → "planları") ve belirsiz durumda yanlış
     adaya düşüyordu ("bilişi" → "bilimi").
  3. Konu anahtarındaki tek harf hatası ("şifrei unuttum", "sistem nsıl çalışıyor") hiç tanınmıyordu.
  4. "Taban puanları nerede görürüm?" yer sorusu sözlük tanımıyla cevaplanıyordu.
Yapay dizinle çalışır (veritabanı gerekmez)."""
import pytest

from app.core import filiz_anlama as fa
from app.core import filiz_bilgi as fb
from app.core import filiz_rehber as fr

BOLUMLER = ["Siyaset Bilimi ve Kamu Yönetimi", "Kamu Yönetimi", "Fizik Öğretmenliği", "Bilgisayar ve Öğretim Teknolojileri Öğretmenliği",
            "Tarih Öğretmenliği", "Özel Eğitim Öğretmenliği", "Spor Öğretmenliği", "Dil Öğretmenliği", "Ekonomi ve Finans", "Ekonomi",
            "Finans ve Bankacılık", "Endüstriyel Tasarım Mühendisliği", "Endüstri Mühendisliği", "Maden Mühendisliği",
            "Bilişim Sistemleri Mühendisliği", "Siber Güvenlik Mühendisliği", "Türk Halk Oyunları", "Medya ve İletişim",
            "Dil ve Konuşma Terapisi", "Kurgu, Ses ve Görüntü Yönetimi", "Çizgi Film ve Animasyon", "Animasyon ve Oyun Tasarımı",
            "Modern Dans", "Fizik", "Tarım Ekonomisi", "Yiyecek ve İçecek İşletmeciliği", "İşletme"]


def _dizin():
    B = fb.Belge
    return fb.Dizin([B("bolum", f"{ad} bölümü", f"{ad} bölümünde dersler ve meslekler.", f"Bölümler › {ad} › Genel bakış", None,
                       fb.sade(ad).strip()) for ad in BOLUMLER]
                    + [B("sozluk", "Taban puan", "Bir bölüme o yıl yerleşen en düşük puanlı öğrencinin puanı.", "Sözlük", None, "",
                         ("taban puan",))])


def _bolum(d, soru):
    coz = d.varliklari_coz(soru)
    hedef = {h for _, hs in coz for h in hs if h in d.bolumler}
    return hedef


@pytest.mark.parametrize("soru,beklenen", [
    ("Siyaset ilimi ve Kamu Yönetimi mezunları nerelerde çalışır", "siyaset bilimi ve kamu yonetimi"),
    ("siyaset biimi ve kamu yönetimi hakkında bilgi verir misin?", "siyaset bilimi ve kamu yonetimi"),
    ("siyaset bilimi v kamu yönetimi zor mu", "siyaset bilimi ve kamu yonetimi"),
    ("Fizi Ogretmenligi okursam ne kadar maas alirim", "fizik ogretmenligi"),
    ("tari öğretmenliği mezunları nerelerde çalışır", "tarih ogretmenligi"),
    ("öze eğitim öğretmenliği zor mu?", "ozel egitim ogretmenligi"),
    ("spo öğretmenliği zor mu?", "spor ogretmenligi"),
    ("Ekonomi e Finans kaç yıl?", "ekonomi ve finans"),
    ("endustriyel asarim muhendisligi bolumunde hangi dersler var", "endustriyel tasarim muhendisligi"),
    ("made muhendisligi okumak istiyorum neler ogrenirim", "maden muhendisligi"),
    ("bilişi sistemleri mühendisliği hakkında bilgi verir misin?", "bilisim sistemleri muhendisligi"),
    ("Türk Hak Oyunları zor mu?", "turk halk oyunlari"),
    ("Medya e İletişim zor mu", "medya ve iletisim"),
    ("dil ve konuma terapisi kaç yıl?", "dil ve konusma terapisi"),
    ("kuru, ses ve goruntu yonetimi hangi puan turuyle ogrenci aliyor", "kurgu  ses ve goruntu yonetimi"),
    ("cizgi flm ve animasyon okursam ne kadar maas alirim", "cizgi film ve animasyon"),
    ("modern das bölümünde hangi dersler var?", "modern dans"),
    ("yiyecek vei̇çecek i̇şletmeciliği zor mu", "yiyecek ve icecek isletmeciligi"),
])
def test_hatali_yazilan_cok_sozcuklu_bolum_dogru_bulunur(soru, beklenen):
    assert _bolum(_dizin(), soru) == {beklenen}, soru


@pytest.mark.parametrize("soru,beklenen", [
    ("Kamu Yönetimi zor mu", {"kamu yonetimi"}),                    # doğru yazılmış kısa ad uzun ada çekilmez
    ("Fizik okumak istiyorum", {"fizik"}),
    ("Ekonomi ile Finans ve Bankacılık arasındaki fark", {"ekonomi", "finans ve bankacilik"}),
    ("Endüstri Mühendisliği hangi puan türüyle alıyor", {"endustri muhendisligi"}),
    ("tarım ekonomisi mezunları", {"tarim ekonomisi"}),
])
def test_dogru_yazilan_ad_degismez(soru, beklenen):
    assert _bolum(_dizin(), soru) == beklenen, soru


def test_yazim_duzeltmesi_dogru_ekli_sozcuge_dokunmaz():
    _dizin()
    fb.capa_ekle(["planlari", "taban puan", "bilisim", "bilgisi", "postasi"])
    assert fb._yazim("puanlari") == "puanlari", "puan + lari geçerli; planlari'na çevrilmez"
    assert fb._yazim("bilisi") == "bilisi", "bilişim de bilgisi de olabilir: belirsizse dokunulmaz"
    assert fb.ek_mi("puan", "lari") and fb.ek_mi("posta", "si")
    assert not fb.ek_mi("sifre", "i"), "ünlüyle biten köke ünlüyle başlayan ek doğrudan gelmez"
    fb.capa_ekle(["muhendisi"])
    fb._BILINEN.discard("muhendis")
    assert fb._yazim("muhendis") == "muhendis", "çapanın eksiz kökü düzeltilmez"


def test_bir_harf_ve_yakin_ekli():
    assert fb.bir_harf("asarim", "tasarim") and fb.bir_harf("flm", "film") and fb.bir_harf("kitpa", "kitap")
    assert not fb.bir_harf("geldi", "gelmedi")
    assert fb.yakin_ekli("fizi", "fizik") and fb.yakin_ekli("kulanabilir", "kullan", 7)
    assert not fb.yakin_ekli("kulanabilir", "kullan", 0)


@pytest.mark.parametrize("soru,konu", [
    ("şifrei unuttum", "k_sifre"),
    ("sonuç e-posası gelmedi", "k_eposta"),
    ("sonu maili gelmedi", "k_eposta"),
    ("sistem nsıl çalışıyor?", "k_sistem"),
    ("uygulamayı ingilizce kulanabilir miyim", "k_dil"),
    ("matematik odevimi yaar misin", "k_odev"),
    ("Taban puanları nerede görürüm?", "k_universite"),
    ("Bölümlerin taban puanlarını nereden bulurum?", "k_universite"),
])
def test_konu_anahtari_tek_harf_hatasiyla_tanınır(monkeypatch, soru, konu):
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    monkeypatch.setattr(fa, "sonradan_netlestir", lambda db, m, mod: None)
    tur, f = fr._rota(None, soru, set())
    assert tur == "konu" and f.__name__ == konu, (soru, tur, f)


@pytest.mark.parametrize("soru", ["takım çalışması nasıl olur", "okulda geldi mi", "hafa sonu ne yapsam"])
def test_gecerli_sozcuk_konuya_benzetilmez(monkeypatch, soru):
    """Tanınan sözcük tek sözcüklü anahtara benzetilmez ("takım" ≠ "takvim"); 4 harften kısa anahtarlar bulanık aranmaz."""
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    monkeypatch.setattr(fa, "sonradan_netlestir", lambda db, m, mod: None)
    fb._BILINEN.update({"takim", "calismasi", "geldi"})
    tur, f = fr._rota(None, soru, set())
    assert not (tur == "konu" and f.__name__ in ("k_takvim", "k_eposta")), (soru, f)


def test_taban_puan_tanimi_hala_sozlukten(monkeypatch):
    d = _dizin()
    monkeypatch.setattr(fb, "dizin", lambda db: d)
    c = fa.onceden_anla(None, "Taban puan ne demek?", set())
    assert c and c.kaynak == "icerik" and "Taban puan" in c.yanit
