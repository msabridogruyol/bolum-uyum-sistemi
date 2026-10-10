# İstatistik bileşenleri (`components/istatistik/`)

Süper admin ve okul yetkilisi panelleri için ortak, bağımlılıksız (saf React + inline SVG/CSS) grafik kütüphanesi.
Stiller `src/index.css` sonunda **"/* [2026-10-10] İstatistik bileşenleri */"** bölümünde, tüm sınıflar `ist-` önekli.

```jsx
import { GrafikKarti, KpiKarti, KpiSatiri, YatayCubuk, SutunGrafik, YiginSutun, CizgiGrafik,
         Huni, Histogram, IsiHaritasi, Halka, histogramTablosu, KATEGORIK } from '../components/istatistik'
```

## Her bileşende ortak olanlar

- **Erişilebilir:** çizim `role="img"` + otomatik `aria-label` özeti (ör. "8 kategori, en yüksek Tıp 151 öğrenci").
  Kendi metnin için `ariaEtiket` prop'u. Asıl ekran okuyucu yolu `GrafikKarti`'nın **tablo görünümüdür** — veri varsa `tablo` verin.
- **Boş veri:** veri yoksa / hepsi geçersizse "Henüz veri yok" kutusu.
- **Araç ipucu:** fareyle/dokunarak ve **klavyeyle** (grafiğe Tab → ← → ↑ ↓, Home/End, Esc). Değer önde, ad ikincil.
  Çubuk/hücre/dilim: işaretin kendisi hedef; çizgi: dikey çizgi (crosshair) en yakın x'e oturur, o x'teki tüm seriler listelenir.
- **Koyu tema:** `[data-theme="dark"]` ile renkler kendi koyu adımlarına geçer (otomatik ters çevirme değil).
- **Telefon:** SVG'ler kapsayıcının gerçek piksel genişliğinde çizilir (`ResizeObserver`), yazılar küçülmez; sayfa yatay taşmaz
  (ısı haritası ve tablo kendi içinde kayar).
- **Sayılar** Türkçe: `1.250`, `%45`, `68,4`. Eksende 10.000 ve üstü kısaltılır (`12,9 B`).
- `baslik` prop'u (isteğe bağlı) grafiğin üstüne küçük başlık yazar ve aria-label'a girer. **`GrafikKarti` içinde vermeyin** (çift başlık olur).
- `birim`: `'%'` → `%45`; başka metin → `45 öğrenci`. `kesir`: en çok ondalık (vars. 1).

## Hangi grafik? (önce biçim, sonra renk)

| Veri / iş | Kullan | Kullanma |
|---|---|---|
| Tek güncel sayı (+değişim) | `KpiKarti` | tek çubuklu grafik, 2 dilimli halka |
| Birkaç başlık sayı | `KpiSatiri` içinde `KpiKarti`'lar | gruplu sütun |
| Kategorileri büyüklüğe göre sıralamak (bölüm, okul, özellik); uzun adlar | `YatayCubuk` | halka |
| Tek ölçünün dönem/kategori karşılaştırması (az sayıda, kısa adlı) | `SutunGrafik` | — |
| Parça-bütün, kategori başına (şube başına durum dağılımı) | `YiginSutun` (`oransal` ile %100) | çok sayıda halka |
| Zaman içindeki eğilim | `CizgiGrafik` | çift eksen (yasak) |
| Adım adım dönüşüm (davet → kayıt → tamamlama) | `Huni` | sütun |
| 0–100 puanların dağılımı | `Histogram` (+ `BANTLAR`) | ortalama tek başına |
| İki boyutlu büyüklük ızgarası (şube × katman) | `IsiHaritasi` | gruplu sütun |
| Bir bakışta 2–5 parçalı oran | `Halka` | 6+ parça ya da yakın değerler → `YatayCubuk` |
| "Bizim okul" vs diğerleri | `YatayCubuk vurgu="Bizim okul"` (diğerleri gri) | 8 renk |

Farklı ölçekli iki ölçü (ör. kullanıcı sayısı ve oturum sayısı) → **iki ayrı grafik** ya da ortak tabana endeksleme (t0 = 100). Asla iki y ekseni.

---

## 1. `KpiKarti` / `KpiSatiri`

```jsx
<KpiSatiri min={170}>
  <KpiKarti etiket="Aktif öğrenci" deger={12873} ikon="🎓" ton="okul"
    degisim={{ deger: 4.2, birim: '%', donem: 'geçen aya göre' }} seyir={[3,4,5,7,9,12]} />
  <KpiKarti etiket="Ortalama süre" deger={23} birim="dk" degisim={{ deger: 3, birim: 'dk', iyiYon: 'asagi' }} alt="K1–K4 toplamı" />
</KpiSatiri>
```

| prop | tür | açıklama |
|---|---|---|
| `etiket` | metin | Cümle düzeninde, sonda iki nokta yok |
| `deger` | sayı \| metin | Sayı Türkçe biçimlenir; metin aynen (`'—'`, `'4,2 / 5'`) |
| `birim` | metin | `'%'` önek olur, diğerleri küçük sonek |
| `alt` | metin/düğüm | Alt bilgi satırı |
| `degisim` | sayı \| `{deger, birim?, donem?, iyiYon?: 'yukari'\|'asagi'\|'yok'}` | ▲/▼ + işaretli değer; renk = yön × iyi mi (vars. artış iyi). Renk tek başına anlam taşımaz |
| `ikon` | emoji/düğüm | Sol üstte tonlu kutu içinde |
| `ton` | `'notr'\|'okul'\|'iyi'\|'uyari'\|'kotu'\|'bilgi'` | İkon zemini; `okul` sol kenara okul rengi çizgisi ekler |
| `seyir` | sayı[] | İsteğe bağlı küçük seyir çizgisi (gri, son nokta vurgulu) |
| `onClick` | fn | Verilirse kart düğme olur |

`KpiSatiri({ children, min=170 })` — `auto-fit` ızgara, dar ekranda kendiliğinden alt satıra geçer.

## 2. `YatayCubuk`

```jsx
<YatayCubuk veri={[{ ad: 'Bilgisayar Mühendisliği', deger: 182, alt: '43 okul' }, ...]} birim="öğrenci" enFazla={10} />
```

| prop | açıklama |
|---|---|
| `veri` | `[{ ad, deger, alt? }]` — `alt` adın altında küçük yazı |
| `birim` | değer birimi |
| `maks` | ölçek üst sınırı (vars. en büyük değer; yüzdelerde `100` verin) |
| `renk` | tek seri rengi (vars. `KATEGORIK[0]`; `'var(--okul-c)'` de olur) |
| `enFazla` | gösterilecek en çok satır; kalan "+N kategori daha" notu (tamamı tabloda) |
| `vurgu` | ad ya da ad dizisi: yalnızca bunlar renkli, diğerleri gri |
| `sirala` | vars. `true` (büyükten küçüğe) |
| `onTik(oge)` | satır tıklanınca |

Uzun adlar "…" ile kesilir, tam ad `title` ve ipucunda. Değer çubuğun ucunda.

## 3. `SutunGrafik` / `YiginSutun`

```jsx
<SutunGrafik veri={[{ ad: 'Oca', deger: 325 }, ...]} birim="kayıt" />
<YiginSutun kategoriler={['9-A','9-B']} seriler={[
  { ad: 'Tamamladı', degerler: [18, 22] },
  { ad: 'Devam ediyor', degerler: [8, 5] },
  { ad: 'Başlamadı', degerler: [4, 3] },
]} />
```

**SutunGrafik:** `veri, birim, renk, maks, yukseklik=200, kesir, degerEtiketi=true`. Tek seri, lejant yok (başlık neyin çizildiğini söyler).
Değer sütun başında **yalnızca sığarsa**; dar ekranda ipucu + tabloya kalır. Çok kategoride x etiketleri seyreltilir.

**YiginSutun:** `kategoriler, seriler:[{ad, degerler, renk?}], birim, oransal=false, maks, yukseklik=220, segmentEtiketi=true`.
- **Lejant her zaman** (2+ seri).
- **Doğrudan etiket kuralı:** segment değeri segmentin içine yalnızca yazı rahatça sığarsa yazılır (yükseklik ≥16px ve genişlik yeterli);
  sığmayan segmentin değeri ipucunda ve tabloda. Toplam sütun başında. Kendi `renk`'inizi verdiğiniz serilerde segment içi
  etiket yazılmaz (yazı rengi kontrastı bilinmez) — palet renklerini kullanın.
- `oransal`: her sütun %100'e ölçeklenir; ipucunda yüzde + ham değer.
- Seri rengi verilmezse **dizin sırasıyla** kategorik palet. Filtreyle seri sayısı değişebiliyorsa rengi varlığa sabitleyin
  (`renk: KATEGORIK[2]`) — yoksa kalan seriler yeniden boyanır.

## 4. `CizgiGrafik`

```jsx
<CizgiGrafik x={['1. hf', '2. hf', ...]} seriler={[{ ad: 'Anadolu lisesi', degerler: [...] }, { ad: 'Fen lisesi', degerler: [...] }]} birim="kişi" />
```

| prop | açıklama |
|---|---|
| `x` | x etiketleri (zaman sırasıyla) |
| `seriler` | `[{ ad, degerler: (sayı\|null)[], renk? }]` — `null` çizgide boşluk |
| `birim` | y birimi |
| `yMin`, `yMaks` | eksen sınırları (vars. veri ≥0 ise 0'dan başlar; 0–100 puanlarda `yMin={0} yMaks={100}`) |
| `yukseklik` | çizim yüksekliği (vars. 220) |
| `alan` | tek seride %10 alan dolgusu (vars. `true`) |

Tek eksen. 2+ seride lejant (çizgi anahtarlı). ≤4 seride uç noktalar birbirine çarpmıyorsa seri adı ucuna yazılır; tek seride son değer.
4'ten fazla iç içe seri → küçük çoklu grafikler (her seri ayrı `CizgiGrafik`) daha iyidir. En çok 8 seri.

## 5. `Huni`

```jsx
<Huni adimlar={[{ ad: 'Davet edildi', deger: 1200 }, { ad: 'Kayıt oldu', deger: 930 }, { ad: 'K1 tamamladı', deger: 702 }]} birim="öğrenci" />
```

`adimlar, birim`. Adımlar arasında "↓ %77,5 devam etti" (bir önceki adıma göre); satır sonunda ilk adıma göre oran.
Renk sıralı tek ton (ilk adım en belirgin); 5'ten fazla adımda tek renk.

## 6. `Histogram`

```jsx
import { BANTLAR } from '../yardimci/seviye'
<GrafikKarti baslik="Puan dağılımı" tablo={histogramTablosu(puanlar)}>
  <Histogram degerler={puanlar} aralik={[0, 100]} kova={10} bantlar={BANTLAR} />
</GrafikKarti>
```

| prop | açıklama |
|---|---|
| `degerler` | `number[]` (ham puanlar) |
| `aralik` | `[min, maks]` (vars. `[0, 100]`); dışındaki değerler sayılmaz, not düşülür |
| `kova` | **kova sayısı** (vars. 10 → 0–9, 10–19, …, 90–100) |
| `bantlar` | isteğe bağlı arka plan bantları: `[{ alt, ust?, ad, zemin }]`. `seviye.js` `BANTLAR`'ı doğrudan kabul eder (`ust` bir sonraki bandın `alt`'ından türetilir). Bant adı sığarsa üstte yazılır, ipucunda her zaman |
| `birim` | sayım birimi (vars. `'öğrenci'`) |
| `ortalama` | ortalama çizgisi (vars. `true`) |
| `renk`, `yukseklik` | |

`histogramTablosu(degerler, { aralik, kova, birim })` → `GrafikKarti` için hazır `tablo`.

## 7. `IsiHaritasi`

```jsx
<IsiHaritasi satirBasligi="Şube" satirlar={['9-A', '9-B']} sutunlar={['K1','K2','K3','K4','K5']}
  degerler={[[62, 55, 71, 48, null], [58, 60, 66, 52, 40]]} aralik={[0, 100]} />
```

| prop | açıklama |
|---|---|
| `satirlar`, `sutunlar` | ad dizileri |
| `degerler` | `[satır][sütun]`; `null` → "—" |
| `bicim` | birim metni (`'%'`, `'puan'`) **ya da** `(v) => metin` |
| `aralik` | renk ölçeği `[min, maks]`; vars. verinin min–maks'ı. Okullar/dönemler arası tutarlılık için 0–100 puanlarda `[0, 100]` verin |
| `satirBasligi` | sol üst köşe başlığı |

Sıralı tek ton (az = açık, çok = koyu; koyu temada tersi), 7 adım, altında ölçek şeridi. Hücre değeri her zaman yazılı.
Çok sütunlu tablolarda telefonda kendi içinde yatay kayar. Klavyede ↑/↓ satır değiştirir.

## 8. `Halka`

```jsx
<Halka veri={[{ ad: 'Kız', deger: 642 }, { ad: 'Erkek', deger: 598 }, { ad: 'Belirtmedi', deger: 31 }]} birim="öğrenci" />
```

`veri:[{ad, deger, renk?}], birim, merkezEtiket='toplam', kesir`.
**Yalnızca 2–5 parça** ve bir bakışta oran için. 5'ten fazla parça gelirse ilk 4 tutulur, kalanı gri "Diğer (N)" olur.
Değerler yakınsa ya da parça çoksa **`YatayCubuk` kullanın**. Tek bir oran (ör. tamamlama %68) için halka değil `KpiKarti`.
Yanındaki listede her parçanın yüzdesi ve değeri yazılıdır.

## 9. `GrafikKarti`

```jsx
<div className="ist-kartlar">
  <GrafikKarti baslik="En çok uyum çıkan bölümler" aciklama="İlk 3'te yer alma sayısı"
    sag={<select>…</select>}
    tablo={{ sutunlar: ['Bölüm', 'Öğrenci'], satirlar: veri.map((v) => [v.ad, v.deger]) }}>
    <YatayCubuk veri={veri} birim="öğrenci" />
  </GrafikKarti>
  <GrafikKarti baslik="Haftalık aktif kullanıcı" genis>…</GrafikKarti>
</div>
```

| prop | açıklama |
|---|---|
| `baslik`, `aciklama` | kart başlığı (h3) ve alt açıklama |
| `sag` | sağ üst yuva (küçük seçici, bağlantı vb.). Filtreler normalde tüm grafiklerin **üstünde tek satırda** olmalı, kart içinde değil |
| `tablo` | `{ sutunlar: [...], satirlar: [[...], ...] }` — verilirse **"Tablo olarak gör"** geçişi çıkar. İlk sütun satır başlığıdır; sayılar sağa hizalanır ve Türkçe biçimlenir |
| `csv` | `true` (vars., tablo varsa) \| `false` \| `'dosya-adi'` — "CSV indir" (`;` ayraç, ondalık virgül, UTF-8 BOM: Türkçe Excel'de doğru açılır) |
| `genis` | `.ist-kartlar` ızgarasında tam satır kaplar |

Düzen: `.ist-kartlar` (auto-fit, en dar 360px) içinde kartlar; geniş grafikler `genis`. `.card` sınıfını kullanır.
Ayrıca dışa açık: `VeriTablosu({ tablo })`, `csvIndir(tablo, ad)`, `csvMetni(tablo)`.

## 10. Renk paleti — `palet.js`

| dışa aktarım | iş |
|---|---|
| `KATEGORIK` (8 × `var(--ist-kN)`), `kategorikRenk(i)` | **kimlik** (hangi seri). Sabit sırayla atanır; 8'i aşan dizin dönmez, gri `DIGER` döner |
| `DIGER` | "Diğer" kuyruğu ve vurgu dışı (gölgede) işaretler |
| `sirasalRenk(i, n)` (`--ist-o0..o4`) | **sıralı adımlar** (huni, kademeler) |
| `siraliAdim(oran)` (`--ist-s0..s6`, `.ist-s0..6`) | **büyüklük** (ısı haritası) |
| `DURUM.iyi/uyari/ciddi/kritik` | **durum** (sabit renk, temaya göre değişmez) — her zaman ikon + etiketle; seri rengi olarak kullanılmaz |
| `DEGISIM_METIN` | artış/azalış metin renkleri |

Kurallar: tek seri = tek renk (çubukları değere göre boyamayın); renk varlığı izler, sırasını değil; 8'den fazla seri
üretilmiş yeni renkle değil "Diğer"e katlanarak ya da küçük çoklu grafiklerle çözülür; yazı asla seri renginde olmaz
(renk yanındaki işaret/kutudadır). Palet `dataviz/scripts/validate_palette.js` ile uygulamanın açık (#FFFFFF) ve koyu (#2B261D)
kart yüzeylerinde doğrulandı — sonuçlar `palet.js` başındaki yorumda. Rengi değiştirirseniz `index.css` ve `palet.js`'yi birlikte
güncelleyip doğrulayıcıyı yeniden çalıştırın. Saçılım/harita gibi "her çift yan yana gelebilir" biçimlerde en çok 3 seri.

## Dosyalar

- `index.js` — tek giriş noktası
- `KpiKarti.jsx`, `YatayCubuk.jsx`, `SutunGrafik.jsx`, `CizgiGrafik.jsx`, `Huni.jsx`, `Histogram.jsx`, `IsiHaritasi.jsx`, `Halka.jsx`, `GrafikKarti.jsx`
- `ortak.jsx` — `Ipucu`, `Lejant`, `Bos`, `Cerceve`
- `yardimci.js` — `bicim`, `sayi`, eksen adımları, metin ölçümü, `useGenislik`, `useEtkilesim` (fare + klavye), CSV, `histogramTablosu`
- `palet.js` — renkler ve doğrulama kaydı
