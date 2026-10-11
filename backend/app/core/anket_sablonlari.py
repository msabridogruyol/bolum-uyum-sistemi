# -*- coding: utf-8 -*-
"""
[2026-10-10] Hazır anket / tarama şablonları.

Maddeler Filizyol için yazıldı; yayımlanmış ölçeklerden alınmadı (telif yok). Bunlar **tarama** amaçlıdır,
tanı koymaz: yüksek puan "rehber öğretmenle konuşmak iyi olabilir" demektir. Geçerlik / güvenirlik çalışması
yapılmamıştır; okul kendi ihtiyacına göre maddeleri değiştirebilir.

Likert: 1 Hiç katılmıyorum … 5 Tamamen katılıyorum. "ters": True olan maddeler puanlamada 6 − cevap alınır.
puanlama.yon: "yuksek_kotu" (yüksek puan = destek ihtiyacı) | "yuksek_iyi" (düşük puan = destek ihtiyacı)
"""

LIKERT = ["Hiç katılmıyorum", "Katılmıyorum", "Kararsızım", "Katılıyorum", "Tamamen katılıyorum"]


def _l(no: int, metin: str, ters: bool = False) -> dict:
    return {"id": f"s{no}", "metin": metin, "tur": "likert", "zorunlu": True, "ters": ters}


SABLONLAR = {
    "sinav_kaygisi": {
        "baslik": "Sınav kaygısı tarama formu",
        "aciklama": "Sınavlara hazırlanırken ve sınav sırasında neler hissettiğini anlamamıza yardım eder. Doğru ya da yanlış cevap yok; "
                    "sonuçlar rehber öğretmeninin sana daha iyi destek olması içindir.",
        "anonim": False,
        "sorular": [
            _l(1, "Sınavdan önceki gece uyumakta zorlanırım."),
            _l(2, "Sınav sırasında bildiğim şeyleri unuttuğumu hissederim."),
            _l(3, "Sınav yaklaştıkça midem bulanır ya da kalbim hızlı atar."),
            _l(4, "Sınavda başarısız olursam herkesin beni yargılayacağını düşünürüm."),
            _l(5, "Sınav sırasında dikkatimi soruya vermekte zorlanırım."),
            _l(6, "Sınav sonuçlarını düşünmek beni günlerce meşgul eder."),
            _l(7, "Sınav günü kendimi sakin ve hazır hissederim.", ters=True),
            _l(8, "Deneme sınavlarının ilk dakikalarında panik yaşarım."),
            _l(9, "Sınavı düşündüğümde ders çalışmaya başlamayı ertelerim."),
            _l(10, "Bir soruda hata yaptığımda kendimi çok sert eleştiririm."),
        ],
        "puanlama": {"yon": "yuksek_kotu", "esikler": [2.5, 3.5], "seviyeler": [
            {"kod": "dusuk", "ad": "Düşük", "metin": "Sınavlara karşı kaygın düşük görünüyor. Bu dengeyi korumak için düzenli çalışma ve uyku düzenine devam et."},
            {"kod": "orta", "ad": "Orta", "metin": "Biraz sınav kaygısı yaşaman çok doğal ve seni harekete de geçirebilir. Nefes egzersizleri, deneme sınavlarını gerçek sınav gibi çözmek ve küçük hedefler koymak işe yarar."},
            {"kod": "yuksek", "ad": "Yüksek", "metin": "Sınavlar seni epey zorluyor gibi görünüyor; bu yalnız olduğun anlamına gelmiyor. Rehber öğretmeninle konuşmak, kaygıyla baş etme yollarını birlikte bulmanı sağlar."},
        ]},
    },
    "calisma_aliskanliklari": {
        "baslik": "Çalışma alışkanlıkları formu",
        "aciklama": "Nasıl çalıştığını anlamak için. Cevapların, sana uygun çalışma önerileri hazırlamamıza yardım eder.",
        "anonim": False,
        "sorular": [
            _l(1, "Haftalık bir çalışma planım var ve çoğunlukla ona uyarım."),
            _l(2, "Çalışmaya başlamadan önce ne çalışacağımı belirlerim."),
            _l(3, "Çalışırken telefonumu uzakta tutarım."),
            _l(4, "Yanlış yaptığım soruları daha sonra yeniden çözerim."),
            _l(5, "Öğrendiğim bir konuyu birkaç gün sonra tekrar ederim."),
            _l(6, "Uzun çalışırken düzenli kısa molalar veririm."),
            _l(7, "Anlamadığım konuyu öğretmenime ya da arkadaşıma sorarım."),
            _l(8, "Çalışmayı genellikle son ana bırakırım.", ters=True),
            _l(9, "Deneme sonuçlarımı inceleyip eksik konularımı belirlerim."),
            _l(10, "Uyku düzenime dikkat ederim."),
        ],
        "puanlama": {"yon": "yuksek_iyi", "esikler": [2.8, 3.8], "seviyeler": [
            {"kod": "dusuk", "ad": "Desteğe ihtiyaç var", "metin": "Çalışma alışkanlıklarını güçlendirmek için küçük bir adımla başla: bu hafta için gerçekçi bir program yap ve her akşam 10 dakikada yanlışlarını tekrar et. Rehber öğretmenin planı birlikte kurmana yardım edebilir."},
            {"kod": "orta", "ad": "Gelişmekte", "metin": "İyi alışkanlıkların var; birkaç tanesini düzenli hale getirmek fark yaratır. Özellikle tekrar ve yanlış analizi netlerini hızla artırır."},
            {"kod": "yuksek", "ad": "Güçlü", "metin": "Çalışma alışkanlıkların güçlü. Planını korurken dinlenmeyi ve uyku düzenini ihmal etme."},
        ]},
    },
    "okul_iklimi": {
        "baslik": "Okul iklimi ve aidiyet anketi",
        "aciklama": "Okulumuzda kendini nasıl hissettiğini merak ediyoruz. Anket anonimdir; cevapların kimliğinle eşleştirilmez.",
        "anonim": True,
        "sorular": [
            _l(1, "Okulda kendimi güvende hissederim."),
            _l(2, "Okulda bana değer veren en az bir yetişkin var."),
            _l(3, "Sınıfımda kendimi kabul görmüş hissederim."),
            _l(4, "Öğretmenlerim başarabileceğime inanır."),
            _l(5, "Okulda zorbalığa ya da dışlanmaya maruz kaldığımı hissediyorum.", ters=True),
            _l(6, "Okuldaki etkinliklere katılmak isterim."),
            _l(7, "Bir sorun yaşadığımda kime başvuracağımı biliyorum."),
            _l(8, "Okuluma gelmekten genellikle memnunum."),
            {"id": "s9", "metin": "Okulumuzu daha iyi bir yer yapmak için bir önerin var mı?", "tur": "acik", "zorunlu": False},
        ],
        "puanlama": {"yon": "yuksek_iyi", "esikler": [2.8, 3.8], "seviyeler": [
            {"kod": "dusuk", "ad": "Zayıf", "metin": "Cevapların için teşekkürler."},
            {"kod": "orta", "ad": "Orta", "metin": "Cevapların için teşekkürler."},
            {"kod": "yuksek", "ad": "Güçlü", "metin": "Cevapların için teşekkürler."},
        ]},
    },
    "kariyer_kararliligi": {
        "baslik": "Kariyer kararlılığı formu",
        "aciklama": "Bölüm ve meslek seçimi konusunda ne kadar hazır hissettiğini anlamak için.",
        "anonim": False,
        "sorular": [
            _l(1, "Hangi alanda okumak istediğime büyük ölçüde karar verdim."),
            _l(2, "İlgilendiğim mesleklerde günlük işin nasıl geçtiğini biliyorum."),
            _l(3, "Hedefim için hangi puan türüne çalışmam gerektiğini biliyorum."),
            _l(4, "Bölüm seçimimde kendi isteğim ailemin beklentisinden daha belirleyici."),
            _l(5, "Kararsız olduğum için kaygı duyuyorum.", ters=True),
            _l(6, "Hedef bölümümün iş olanaklarını araştırdım."),
            _l(7, "Bir meslek sahibiyle görüşme ya da kampüs gezisi fırsatı aradım."),
            _l(8, "Seçeneklerimi karşılaştırmak için yeterli bilgiye sahibim."),
        ],
        "puanlama": {"yon": "yuksek_iyi", "esikler": [2.8, 3.8], "seviyeler": [
            {"kod": "dusuk", "ad": "Kararsız", "metin": "Henüz kararsız olman çok normal. Filizyol'daki bölüm önerilerinden 3 tanesini seç ve her biri için bir meslek sahibinin videosunu izle; rehber öğretmeninle de konuş."},
            {"kod": "orta", "ad": "Keşfediyor", "metin": "Seçeneklerin şekilleniyor. Hedef bölümünün iş olanaklarını ve gereken puan türünü netleştirmek kararını güçlendirir."},
            {"kod": "yuksek", "ad": "Kararlı", "metin": "Kariyer hedefin net görünüyor. Yol haritandaki adımlarla bu kararı somut başarılara çevirebilirsin."},
        ]},
    },
    "rehberlik_memnuniyet": {
        "baslik": "Rehberlik servisi memnuniyet anketi",
        "aciklama": "Rehberlik servisinin sana nasıl destek olduğunu öğrenmek istiyoruz. Anket anonimdir.",
        "anonim": True,
        "sorular": [
            _l(1, "Rehberlik servisine ihtiyaç duyduğumda kolayca ulaşabiliyorum."),
            _l(2, "Görüşmelerde dinlendiğimi ve anlaşıldığımı hissediyorum."),
            _l(3, "Aldığım öneriler işime yaradı."),
            _l(4, "Rehberlik etkinlikleri (seminer, tanıtım günleri) faydalı."),
            {"id": "s5", "metin": "Rehberlik servisinden başka neler beklersin?", "tur": "acik", "zorunlu": False},
        ],
        "puanlama": None,
    },
}

SORU_TURLERI = {"likert": "Katılım (1–5)", "tek": "Tek seçim", "coklu": "Çoklu seçim", "puan": "Puan (1–10)", "acik": "Açık uçlu"}


def puanla(sorular: list[dict], cevaplar: dict, puanlama: dict | None) -> tuple[float | None, str | None]:
    """Likert maddelerin ortalaması (ters maddeler çevrilir) ve seviye kodu."""
    if not puanlama:
        return None, None
    degerler = []
    for s in sorular:
        if s.get("tur") != "likert":
            continue
        v = cevaplar.get(s["id"])
        if isinstance(v, int) and 1 <= v <= 5:
            degerler.append(6 - v if s.get("ters") else v)
    if not degerler:
        return None, None
    ort = round(sum(degerler) / len(degerler), 2)
    a, b = puanlama["esikler"]
    kod = "dusuk" if ort < a else ("orta" if ort <= b else "yuksek")
    return ort, kod


def seviye_bilgisi(puanlama: dict | None, kod: str | None) -> dict | None:
    if not puanlama or not kod:
        return None
    return next((s for s in puanlama["seviyeler"] if s["kod"] == kod), None)


def destek_gerekiyor_mu(puanlama: dict | None, kod: str | None) -> bool:
    """Erken uyarı için: yüksek kaygı / düşük alışkanlık-kararlılık."""
    if not puanlama or not kod:
        return False
    return (puanlama["yon"] == "yuksek_kotu" and kod == "yuksek") or (puanlama["yon"] == "yuksek_iyi" and kod == "dusuk")
