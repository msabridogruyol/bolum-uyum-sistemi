# İş Hayatı modülü (`is_hayati`)

Amaç: öğrencinin seçtiği bölüm/mesleğin iş hayatındaki gerçeklerini resmî verilerle, gerçekçi ama umut veren bir dille göstermek
("pembe rüyadan uyanmak"). Bu belge altyapı + veri katmanının sözleşmesidir; içerik sekmelerini ekleyen ajanlar buna uyar.

## Paket / modül

- `app/core/paketler.py` → `MODULLER["is_hayati"]` ("İş Hayatı", 💼). Bağımlılık yok.
- Göç 0054, modülü **yalnızca `tam` paketine** bir kez ekler (`tek_seferlik_gocler` işareti `0054_is_hayati_paket`). Gerekçe: Tam paket
  kariyer odaklı modülleri (tercih, mezun takibi) zaten içeriyor; Temel/Gelişim'e okul bazında `modul_ekle` ile açılabilir. Süper admin
  modülü paketten çıkarırsa açılışta geri gelmez.
- Öğrenci uçları `ogrenci_modulu("is_hayati")` ile korunur (kapalıysa 403). Frontend: `YOL_MODULU['/is-hayati']`, `MODUL_ADI.is_hayati`;
  menüde "Keşfet" grubunda "💼 İş Hayatı" (`acik('is_hayati')`).

## Göç numaraları

| Göç | Sahibi |
|---|---|
| `0054_is_hayati` | altyapı (bu belge) — tablolar, ISCO tohumu, asgari ücret tohumu, paket |
| `0055`, `0056`, `0057` | içerik bileşenleri (diğer ajanlar) — `down_revision` zincirini sırayla sürdürün |

Her yeni göç `app/core/sema_guncelleme.py` → `OTOMATIK` listesine eklenir ve **her açılışta yeniden çalışır**: SQL idempotent olmalı
(`IF NOT EXISTS`, `ON CONFLICT DO NOTHING`), komutlar `;\n` ile ayrılır, SQL içinde `:ad` biçiminde iki nokta kullanmayın (SQLAlchemy bağ
parametresi sanır). Tek seferlik veri/UPDATE için 0052/0054'teki `tek_seferlik_gocler` CTE kalıbını kullanın.

## Tablolar (0054)

| Tablo | İçerik | Not |
|---|---|---|
| `istihdam_gostergeleri` | TÜİK Yükseköğretim İstihdam Göstergeleri: `bolum_id` (null olabilir), `program_adi_kaynak`, `duzey` (`lisans`/`onlisans`), `istihdam_orani`, `is_bulma_suresi_ay`, `alan_uyum_orani`, `kazanc_grubu` (`cok_yuksek`…`cok_dusuk`), `kazanc_tl`, `veri_yili`, `kaynak`, `yukleme_id` | yükleme silinince satırları da silinir (CASCADE) |
| `kazanc_meslek_gruplari` | TÜİK Kazanç Yapısı: `isco_kodu` (1–2 hane), `ad`, `brut_aylik_ortalama_tl`, `veri_yili`, `asgari_brut_o_yil`, `kaynak` | `UNIQUE(isco_kodu, veri_yili)` |
| `meslek_isco` | `meslek_adi` (bölüm detayındaki meslek adı, Türkçe küçük harf) → `isco_kodu`, `guven` (`yuksek`/`orta`/null), `kaynak` (`otomatik`/`elle`) | tohum: `app/data/meslek_isco.json` |
| `kamu_maaslari` | `kadro_adi`, `anahtar_kelimeler` (jsonb), `net_min`, `net_max`, `donem` (ör. `2026-1`), `kaynak`, `aciklama` | yalnızca elle |
| `asgari_ucret` | `donem` (unique), `brut`, `net`, `kaynak`, `yururluk_tarihi` | tohum: 2022-1, 2022-2, 2025, 2026 |
| `yasam_giderleri` | `il` (null = Türkiye geneli), `kalem_kodu`, `ad`, `aylik_tutar`, `kaynak`, `tarih` | `UNIQUE(COALESCE(il,''), kalem_kodu)`; boş başlar |
| `veri_yuklemeleri` | `tur`, `dosya_adi`, `satir`, `eslesen`, `eslesmeyen` (jsonb), `veri_yili`, `kaynak`, `yukleyen`, `zaman` | yükleme geçmişi |

Kural: **hiçbir sayı uydurulmaz.** Kaynak + yıl/tarih her kayıtta zorunlu; veri yoksa uç `null` döner ve `eksik` listesine yazar.
Tohumlanan tek sayılar asgari ücretlerdir (ÇSGB Çalışma Genel Müdürlüğü tablosu; 2026 için Resmî Gazete 26.12.2025/33119).

### Meslek → ISCO eşleştirmesi

Bölüm detayındaki meslekler (`bolumler.detay.meslekler[].ad`) ESCO/ISCO kodu taşımıyor (yerel `meslekler` tablosu boş ve ad kümesi farklı).
Bu yüzden 1.034 benzersiz meslek adı ISCO-08 2 haneli alt ana gruplara ad + bölüm bağlamıyla sınıflandırıldı:
`app/data/meslek_isco.json` (`eslesme`, ayrıca `isco08_alt_ana_gruplar` / `isco08_ana_gruplar` Türkçe adlar). 0054 bu dosyayı
`ON CONFLICT DO NOTHING` ile yükler: elle düzeltmeler ezilmez, JSON'a eklenen yeni adlar bir sonraki açılışta gelir. Düzeltme ekranı:
Süper admin → İş Hayatı Verileri → Meslek – ISCO.

## Öğrenci uçları (`app/api/is_hayati.py`, prefix `/ogrenci/is-hayati`)

- `GET /ozet` → `{hedef, oneriler[≤5] {id, ad, uyum, sira}, varsayilan_bolum_id, bolumler[{id, ad}], kisa{bolum_id: {istihdam_orani, is_bulma_suresi_ay, alan_uyum_orani, kazanc_grubu, kazanc_grubu_ad, veri_yili}}, asgari, veri_kaynaklari}`
- `GET /bolum/{bolum_id}` → 
  ```
  { bolum: {id, ad, ogrenim_suresi, meslek_sayisi},
    istihdam: {program_adi_kaynak, duzey, istihdam_orani, is_bulma_suresi_ay, alan_uyum_orani, kazanc_grubu, kazanc_grubu_ad, kazanc_tl,
               kaynak, veri_yili, programlar:[aynı yılın tüm eşleşen programları], onceki_yillar:[], tahmin:false} | null,
    kazanc: { meslekler: [{meslek, isco_kodu, isco_guven, grup_adi, grup_duzeyi ('alt_ana_grup'|'ana_grup'|null), brut_veri_yili_tl, veri_yili,
                           asgari_kat, guncel_tahmin_brut_tl, guncel_tahmin_net_tl, guncel_donem, kaynak, veri_grup_kodu, veri_grup_adi, tahmin:true}],
              aciklama },
    kamu: [{id, kadro_adi, net_min, net_max, donem, kaynak, aciklama, tahmin:false}],
    asgari: {donem, brut, net, kaynak, yururluk_tarihi} | null,
    eksik: ['istihdam'|'kazanc'|'kamu'|'asgari'],
    veri_kaynaklari: [{veri, ad, kaynak, yil, kayit}] }
  ```
  Kazanç tahmini: `asgari_kat = brut_veri_yili / asgari_brut_o_yil`; `guncel_tahmin_brut = kat × güncel asgari brüt`;
  `guncel_tahmin_net ≈ tahmin_brut × (güncel net / güncel brüt)` (oransal yaklaşım, vergi dilimi hesaplanmaz). Meslek önce 2 haneli
  grupta, yoksa 1 haneli ana grupta aranır. Tüm meslekler listelenir; verisi olmayanlarda değerler `null`.
- `GET /giderler?il=` → `{il, iller[], kalemler[{kalem_kodu, ad, aylik_tutar, il, turkiye_geneli, kaynak, tarih, tahmin:false}], toplam, asgari}`
  (il satırı varsa Türkiye geneli yerine o kullanılır).

Yardımcılar `app/core/is_hayati_servisi.py`: `bolum_verisi`, `guncel_asgari`, `kazanc_meslekleri`, `istihdam_bolum`, `veri_kaynaklari`,
`tr_kucuk`, `tr_baslik`, `sayi`, `kazanc_grubu_coz`, `program_eslestir` …

### Diğer ajanlar uç noktalarını nereye ekler? — **ayrı dosya, otomatik bağlanır**

Her içerik bileşeni kendi dosyasını açar: `backend/app/api/is_hayati_<konu>.py` (ör. `is_hayati_cv.py`, `is_hayati_mulakat.py`).
`is_hayati.py` açılışta `app/api/is_hayati_*.py` modüllerini bulur:

- `ogrenci_router = APIRouter()` (**prefix vermeyin**) → yolları `/ogrenci/is-hayati/...` altına eklenir; modül kapısı
  `ogrenci_modulu("is_hayati")` otomatik uygulanır. Öğrenci için `Depends(get_mevcut_ogrenci)` yine kendi ucunuzda olmalı.
- `yonetim_router = APIRouter(prefix="/admin/is-hayati-<konu>" ya da "/yonetim/...")` → olduğu gibi eklenir; yetki bağımlılığı
  (`get_mevcut_super_admin` vb.) sizde.
- `main.py`'ye dokunmayın. Yol çakışmasını önlemek için yollarınızı kendi konu adınızla başlatın (`/cv/...`, `/mulakat/...`).
- Modül içe aktarılırken hata verirse loglanır ve atlanır (site açılır) — `python3 -c "import app.main"` ile kontrol edin.

## Frontend

- Sayfa: `src/pages/IsHayatiSayfasi.jsx`, rota `/is-hayati` (`?bolum=ID&sekme=kod`). Bölüm seçici (hedef + ilk 5 öneri çipleri + tüm
  bölümlerde arama), kısa veri şeridi (istihdam, iş bulma süresi, alan uyumu, kazanç düzeyi), sekmeler, en altta "Veriler hakkında".
- Sekme sözleşmesi: `src/components/isHayati/sekmeler.js` — her sekme ayrı dosyada varsayılan dışa aktarılan bileşen,
  **props `{ bolum, veri, ogrenci }`** (`veri` = `/bolum/{id}` yanıtı, `ogrenci` = profil ya da null). Şu an hepsi `Yakinda` yer tutucusu.

| kod | ad | dosya |
|---|---|---|
| `gercek` | Beklenti ve Gerçek | `components/isHayati/BeklentiGercek.jsx` |
| `maas` | İlk Maaşla Bir Ay | `components/isHayati/IlkMaas.jsx` |
| `yol` | Mesleğe Giden Yol | `components/isHayati/MeslegeYol.jsx` |
| `zorgun` | Zor Günler | `components/isHayati/ZorGunler.jsx` |
| `cv` | CV Atölyesi | `components/isHayati/CvAtolyesi.jsx` |
| `mulakat` | Mülakat Pratiği | `components/isHayati/MulakatPratigi.jsx` |
| `dersler` | Okulda Öğretilmeyenler | `components/isHayati/OkuldaOgretilmeyenler.jsx` |
| `mezun` | Mezunlardan | `components/isHayati/MezunHikayeleri.jsx` |

- Ortak: `components/isHayati/ortak.jsx` (`tl`, `yuzde`, `ay`, `KAZANC_GRUBU_RENK`, `<TahminEtiketi/>` — `tahmin:true` olan her değerin
  yanında gösterilmeli), `VerilerHakkinda.jsx`, `Yakinda.jsx`. API: `api.isHayatiOzet()`, `api.isHayatiBolum(id)`, `api.isHayatiGiderler(il)`;
  kendi uçlarınız için `api/client.js`'e `isHayati<Konu>...` adıyla ekleyin. Grafik gerekirse `components/istatistik/` (README.md).

## Veri yükleme akışı (süper admin → İçerik → "İş Hayatı Verileri", `/admin/is-hayati-verileri`)

Uçlar `app/api/admin_is_hayati.py` (`/admin/is-hayati/*`, yalnız süper admin; her değişiklik `denetim_yaz`).

1. **TÜİK İstihdam Göstergeleri**: `.xlsx`/`.csv` seç → `POST /dosya/oku` (başlık satırı + sütunlar otomatik tahmin; elle değiştirilebilir)
   → sütun eşleştirme (program adı*, düzey, istihdam %, iş bulma süresi, alan uyumu %, kazanç grubu ya da TL) → `POST /istihdam/onizle`:
   oranlar 0–1 ise %'ye çevrilir, kazanç grubu metni normalize edilir (tanınmazsa uyarı, değer boş), program adı Türkçe-normalize edilip
   parantez içi ("(İngilizce)", "(Burslu)", "(İÖ)") atılarak bölüm adı + elle girilmiş YÖK Atlas gruplarıyla eşleştirilir
   (`otomatik` = birebir/aynı kelimeler; `oneri` = benzerlik ≥ %85; değilse aday listesi) → eşleşmeyenleri seç → veri yılı + kaynak (zorunlu)
   → `POST /istihdam/kaydet` (varsayılan: aynı yılın eski satırları silinip yerine yazılır). Geri alma: yükleme geçmişinde "Geri al".
2. **Kazanç Yapısı**: aynı akış; ISCO kodu sütunu yoksa adın başındaki rakamdan ("2 Profesyonel …") ya da ISCO grup adından bulunur;
   yıllık tutarlar 12'ye bölünür; **o yılın asgari brüt ücreti zorunlu** (ekran, asgari ücret tablosundan ay ağırlıklı ortalamayı önerir;
   2022 için (5.004×6 + 6.471×6)/12 = 5.737,50 TL). Tablo ayrıca elle düzenlenebilir.
3. **Meslek – ISCO**: aranabilir liste (boş / orta / yüksek / elle / tabloda olmayan), açılır listeden düzelt; "JSON'daki eksikleri ekle".
4. **Kamu maaşları**, 5. **Asgari ücret ve yaşam giderleri**: genel CRUD (`/kayit/{tablo}`), kaynak + tarih/dönem zorunlu.

## CV Atölyesi ('cv') ve Mezunlardan ('mezun') — göç 0057

- Tablolar: `is_hayati_cv` (ogrenci_id PK, `icerik` jsonb, `paylas` bool, `paylasim_zamani`, `guncelleme`) ve `mezun_hikayeleri`
  (okul_id, mezun_ad, `ad_bicimi` tam|bas_harf, mezuniyet_yili, bolum_id/bolum_ad, universite, su_anki_is, `cevaplar` jsonb,
  `riza_alindi` CHECK TRUE, `riza_tarihi`, `riza_kaydeden`, `durum` taslak|yayinda).
- `app/api/is_hayati_cv.py`: öğrenci `GET|PUT|DELETE /cv`, `GET /cv/pdf` (tek sayfa, ATS dostu, "OKUL ONAYLI" sunucuda portfolyo
  doğrulamasından hesaplanır), `GET /cv/ilanlar?bolum_id=` (kurgusal örnek ilanlar: `app/data/ornek_ilanlar.json`); okul
  `GET /yonetim/ogrenci/{id}/is-hayati-cv` (+`/pdf`) yalnızca `paylas` ise, `okul_modulu("is_hayati")`. Kontrol listesi (15 madde, /100) sunucuda.
- `app/api/is_hayati_mezun.py`: okul `GET|POST /yonetim/okul/{okul_id}/mezun-hikayeleri`, `PUT|DELETE …/{hikaye_id}`
  (`okul_modulu("mezun_takibi")`; yazma YALNIZCA kendi okulunun `okul_yetkilisi` — süper admin ekleyemez/düzenleyemez, yalnızca kaldırabilir);
  öğrenci `GET /mezun/hikayeler?bolum_id=` (kendi okulu, yayında; bölüm → aynı dal (`bolum_dal_eslesme`) → diğerleri).
- Frontend: `components/isHayati/CvAtolyesi.jsx` + `cv/` (CvDuzenleyici, CvKontrol, OnYazi, IlanOkuma, CvOnizleme), `MezunHikayeleri.jsx`;
  okul paneli `components/yonetim/MezunHikayeleriYonetim.jsx` (Mezunlar → "Mezun hikâyeleri" alt sekmesi), `OgrenciCv.jsx` (öğrenci detayı → Portfolyo).

## Zor Günler / Okulda Öğretilmeyenler / Mülakat Pratiği (göç 0056)

- Uçlar: `app/api/is_hayati_zor_gun.py` (`GET /zor-gun/{bolum_id}`, `GET /zor-gun/{bolum_id}/tur?meslek=`, `POST /zor-gun`),
  `is_hayati_dersler.py` (`GET /dersler`, `POST /dersler/{kod}/sinav`), `is_hayati_mulakat.py` (`GET /mulakat?bolum_id=`,
  `POST /mulakat/pratik`, `POST /mulakat/pratik/{id}/geri-bildirim`, `GET /mulakat/gecmis`, `DELETE /mulakat/pratik/{id}`).
  Ortak yardımcı: `app/core/is_hayati_pratik.py` (JSON yükleme, bölümün K5 üst alanı `U..`).
- Tablolar (0056): `is_hayati_zor_gun`, `is_hayati_ders_ilerleme`, `is_hayati_mulakat` (cevaplar yalnızca öğrencinin kendi uçlarından okunur).
- İçerik: `app/data/zor_gunler.json` (17 alan × 5 + 300 meslek × 2; anahtar = simülasyondaki gibi `ad.strip().lower()`),
  `is_hayati_dersler.json` (12 ders, kaynak + `son_kontrol`), `is_hayati_mulakat.json` (genel/davranışsal/staj + 17 alan × 6).
- Bordro örneği tutar uydurmaz: güncel `asgari_ucret` satırından %14 SGK + %1 işsizlik ile hesaplanır, yalnızca tablodaki netle tutarlıysa gösterilir.
- Filiz geri bildirimi: `ai_koc._ai` kapısı (anahtar + `filiz_ai`), koçla ortak günlük hak, kriz ifadesinde model çağrılmaz, modele gitmeden e-posta/telefon maskelenir.
