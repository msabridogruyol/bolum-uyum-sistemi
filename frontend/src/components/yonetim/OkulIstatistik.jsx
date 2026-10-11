// [2026-10-10] Okul paneli → İstatistikler: okulun tüm istatistikleri tek istekte (GET /yonetim/okul/{id}/istatistik).
// Filtreler (tek satır): sınıf düzeyi, şube, tarih aralığı. Paket modülü kapalı bölümler gösterilmez (sunucu da döndürmez).
// Okul kendi öğrencilerini isimle gördüğü için bu ekranda küçük grup gizleme yoktur (toplu PDF/Excel raporlarında vardır).
import { useEffect, useMemo, useState } from 'react'
import { api } from '../../api/client'
import {
  CizgiGrafik, GrafikKarti, Halka, Histogram, Huni, IsiHaritasi, KATEGORIK, KpiKarti, KpiSatiri, SutunGrafik,
  YatayCubuk, YiginSutun, bicim, histogramTablosu, sayi,
} from '../istatistik'
import { BANTLAR } from '../../yardimci/seviye'
import { katmanAdi } from '../../yardimci/katmanAdlari'
import { useOkulModulleri } from '../../yardimci/moduller'

const OKUL = 'var(--okul-c, var(--ist-k1))'
const BOLUMLER = [
  ['katilim', 'Katılım'], ['profil', 'Profil'], ['bolum', 'Bölüm ve Meslek'], ['kocluk', 'Koçluk'], ['akademik', 'Akademik'], ['rehberlik', 'Rehberlik'],
]
const ARALIKLAR = [[30, 'Son 30 gün'], [90, 'Son 90 gün'], [180, 'Son 6 ay'], [365, 'Son 1 yıl'], ['ozel', 'Özel aralık']]

const gunStr = (d) => d.toLocaleDateString('sv-SE')   // YYYY-AA-GG (yerel)
const geri = (gun) => { const d = new Date(); d.setDate(d.getDate() - gun + 1); return gunStr(d) }
const hafta = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit' })
const tarihTR = (iso) => new Date(`${iso}T00:00:00`).toLocaleDateString('tr-TR')
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const ayAdi = (ym) => `${AY[Number(ym.slice(5, 7)) - 1]} ${ym.slice(2, 4)}`
const yuzde = (v) => (v == null ? '—' : bicim(v, '%'))
const tabloYap = (sutunlar, satirlar) => ({ sutunlar, satirlar })
const cubukTablosu = (bas, birim, l) => tabloYap([bas, birim], l.map((x) => [x.ad, x.deger]))

function Bolum({ id, baslik, aciklama, children }) {
  return (
    <section id={`ist-${id}`} className="ois-bolum" aria-labelledby={`ist-${id}-b`}>
      <h2 id={`ist-${id}-b`} className="ois-bolum-baslik">{baslik}</h2>
      {aciklama && <p className="ois-bolum-aciklama">{aciklama}</p>}
      {children}
    </section>
  )
}

// ----------------------------------------------------------------------------- Katılım
function Katilim({ v }) {
  const k = v.katilim
  const ad = k.durum_adlari
  const kodlar = ['tamamlandi', 'devam', 'baslamadi', 'giris_yok']
  return (
    <Bolum id="katilim" baslik="Katılım" aciklama="Haftalık eğilim seçili tarih aralığındadır; huni ve şube dağılımı öğrencilerin bugünkü durumunu gösterir.">
      <div className="ist-kartlar">
        <GrafikKarti genis baslik="Haftalık giriş ve test tamamlama" aciklama="Haftada en az bir kez giriş yapan ve değerlendirmeyi o hafta bitiren öğrenci sayısı"
          tablo={tabloYap(['Hafta (pazartesi)', 'Giriş yapan', 'Testi tamamlayan'], k.haftalik.map((h) => [tarihTR(h.hafta), h.giris, h.tamamlama]))}>
          <CizgiGrafik x={k.haftalik.map((h) => hafta(h.hafta))} birim="öğrenci" seriler={[
            { ad: 'Giriş yapan', degerler: k.haftalik.map((h) => h.giris), renk: KATEGORIK[0] },
            { ad: 'Testi tamamlayan', degerler: k.haftalik.map((h) => h.tamamlama), renk: KATEGORIK[1] },
          ]} />
        </GrafikKarti>
        <GrafikKarti baslik="Değerlendirme hunisi" aciklama="Hesaptan koçluğa kadar her adıma ulaşan öğrenci (teste başlayan, giriş yapmış sayılır)"
          tablo={tabloYap(['Adım', 'Öğrenci'], k.huni.map((h) => [h.ad, h.deger]))}>
          <Huni adimlar={k.huni} birim="öğrenci" />
        </GrafikKarti>
        <GrafikKarti baslik="Şubelere göre durum" aciklama="Her şubede öğrencilerin değerlendirme durumu"
          tablo={tabloYap(['Şube', 'Öğrenci', ...kodlar.map((x) => ad[x]), 'Tamamlama %'],
            k.subeler.map((s) => [s.etiket, s.toplam, ...kodlar.map((x) => s[x]), s.toplam ? Math.round((1000 * s.tamamlandi) / s.toplam) / 10 : null]))}>
          <YiginSutun kategoriler={k.subeler.map((s) => s.etiket)} birim="öğrenci"
            seriler={kodlar.map((x, i) => ({ ad: ad[x], degerler: k.subeler.map((s) => s[x]), renk: KATEGORIK[[5, 0, 3, 7][i]] }))} />
        </GrafikKarti>
      </div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Profil
function Profil({ v }) {
  const p = v.profil
  const [hk, setHk] = useState('hepsi')
  const kodlar = p.katmanlar.map((k) => k.kod)
  const kAd = (kod) => `${kod} · ${katmanAdi(kod, p.katmanlar.find((k) => k.kod === kod)?.ad)}`
  const histDeger = useMemo(() => (hk === 'hepsi' ? kodlar.flatMap((k) => p.histogram[k] || []) : p.histogram[hk] || []), [hk, p])
  if (!p.tamamlayan) {
    return <Bolum id="profil" baslik="Profil"><div className="card bos-durum">Profil istatistikleri değerlendirmeyi tamamlayan öğrenciler oldukça oluşur.</div></Bolum>
  }
  const ozellikTablosu = (l) => tabloYap(['Özellik', 'Katman', 'Ortalama', 'Öğrenci'], l.map((x) => [x.ad, x.katman, x.ortalama, x.n]))
  return (
    <Bolum id="profil" baslik="Profil" aciklama={`Değerlendirmeyi tamamlayan ${p.tamamlayan} öğrencinin son sonuçları. Puanlar 0–100; 50 civarı ortadır.`}>
      <div className="ist-kartlar">
        <GrafikKarti genis baslik="Katman ortalamaları" aciklama={p.katman_ort.length > 1 ? 'Seçili kapsamın geneli ve sınıf düzeyleri' : 'Seçili kapsamın ortalaması'}
          tablo={tabloYap(['Kapsam', ...kodlar], p.katman_ort.map((g) => [g.ad, ...kodlar.map((k) => g.degerler[k])]))}>
          <div className="ois-mini-izgara">
            {kodlar.map((k) => (
              <div key={k} className="ois-mini">
                <div className="ois-mini-baslik">{kAd(k)}</div>
                <YatayCubuk veri={p.katman_ort.map((g) => ({ ad: g.ad, deger: g.degerler[k] }))} maks={100} birim="puan"
                  sirala={false} vurgu={p.katman_ort[0].ad} renk={OKUL} />
              </div>
            ))}
          </div>
        </GrafikKarti>
        <GrafikKarti baslik="En güçlü 8 özellik" aciklama="Öğrencilerin ortalamada en yüksek puan aldığı özellikler" tablo={ozellikTablosu(p.guclu)}>
          <YatayCubuk veri={p.guclu.map((x) => ({ ad: x.ad, deger: x.ortalama, alt: kAd(x.katman) }))} maks={100} birim="puan" renk={OKUL} />
        </GrafikKarti>
        <GrafikKarti baslik="En az öne çıkan 8 özellik" aciklama="Ortalaması en düşük özellikler — gelişim çalışmaları için ipucu" tablo={ozellikTablosu(p.zayif)}>
          <YatayCubuk veri={p.zayif.map((x) => ({ ad: x.ad, deger: x.ortalama, alt: kAd(x.katman) }))} maks={100} birim="puan" sirala={false} renk={KATEGORIK[1]} />
        </GrafikKarti>
        <GrafikKarti baslik="Şube × katman ortalaması" aciklama="Her hücre o şubenin katman ortalaması (0–100)"
          tablo={tabloYap(['Şube', ...kodlar], p.sube_katman.map((g) => [g.ad, ...kodlar.map((k) => g.degerler[k])]))}>
          <IsiHaritasi satirBasligi="Şube" satirlar={p.sube_katman.map((g) => g.ad)} sutunlar={kodlar}
            degerler={p.sube_katman.map((g) => kodlar.map((k) => g.degerler[k]))} aralik={[0, 100]} bicim={(x) => sayi(x)} />
        </GrafikKarti>
        <GrafikKarti baslik="Katman puanı dağılımı" aciklama="Öğrenci başına katman ortalaması; arka plan düzey bantlarıdır"
          sag={<select className="yp-sec" value={hk} onChange={(e) => setHk(e.target.value)} aria-label="Katman">
            <option value="hepsi">Tüm katmanlar</option>{kodlar.map((k) => <option key={k} value={k}>{kAd(k)}</option>)}
          </select>}
          tablo={histogramTablosu(histDeger)}>
          <Histogram degerler={histDeger} aralik={[0, 100]} kova={10} bantlar={BANTLAR} renk={OKUL} />
        </GrafikKarti>
      </div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Bölüm ve meslek
function BolumMeslek({ v }) {
  const b = v.bolum
  return (
    <Bolum id="bolum" baslik="Bölüm ve Meslek" aciklama="Öneriler son tamamlanan değerlendirmeden; simülasyonlar seçili tarih aralığındadır.">
      <KpiSatiri>
        <KpiKarti etiket="Hedefi ilk 10 önerisinde" deger={b.uyum.oran == null ? '—' : b.uyum.oran} birim={b.uyum.oran == null ? undefined : '%'} ikon="🎯" ton="okul"
          alt={`${b.uyum.ilk10} / ${b.uyum.hedefli_tamamlayan} hedef seçmiş ve testi tamamlamış öğrenci`} />
        <KpiKarti etiket="Hedef bölüm seçen" deger={v.kpi.hedef_secen} ikon="📌" alt={`${v.kpi.ogrenci} öğrenciden`} />
        <KpiKarti etiket="K5 alan derinleşmesini bitiren" deger={v.kpi.k5_tamamlayan} ikon="🌻" />
      </KpiSatiri>
      <div className="ist-kartlar">
        <GrafikKarti baslik="1. sırada önerilen bölümler" aciklama="Testi tamamlayanların en üst önerisi" tablo={cubukTablosu('Bölüm', 'Öğrenci', b.ilk_oneri)}>
          <YatayCubuk veri={b.ilk_oneri} birim="öğrenci" enFazla={10} renk={OKUL} />
        </GrafikKarti>
        <GrafikKarti baslik="Hedeflenen bölümler" aciklama="Öğrencilerin seçtiği hedef bölüm" tablo={cubukTablosu('Bölüm', 'Öğrenci', b.hedef)}>
          <YatayCubuk veri={b.hedef} birim="öğrenci" enFazla={10} />
        </GrafikKarti>
        <GrafikKarti baslik="K5 alan dağılımı" aciklama="Alan derinleşmesinde tamamlanan alanlar (bir öğrenci birden çok alanda olabilir)" tablo={cubukTablosu('Alan', 'Öğrenci', b.k5_alan)}>
          <YatayCubuk veri={b.k5_alan} birim="öğrenci" enFazla={10} renk={KATEGORIK[2]} />
        </GrafikKarti>
        {b.simulasyon && (
          <GrafikKarti baslik="En çok denenen meslek simülasyonları" aciklama="Simülasyon sayısı; altında ortalama keyif"
            tablo={tabloYap(['Meslek', 'Simülasyon', 'Öğrenci', 'Ortalama keyif %'], b.simulasyon.map((s) => [s.ad, s.deger, s.ogrenci, s.keyif]))}>
            <YatayCubuk veri={b.simulasyon.map((s) => ({ ad: s.ad, deger: s.deger, alt: `keyif ${yuzde(s.keyif)} · ${s.ogrenci} öğrenci` }))} birim="simülasyon" enFazla={10} />
          </GrafikKarti>
        )}
      </div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Koçluk ve çalışma
function Kocluk({ v }) {
  const kc = v.kocluk, f = v.filiz, c = v.calisma
  if (!kc && !f && !c) return null
  const gt = kc?.gorev_toplam
  return (
    <Bolum id="kocluk" baslik="Koçluk" aciklama="Seçili tarih aralığındaki gelişim adımları, haftalık görevler, Filiz ve çalışma kayıtları.">
      <KpiSatiri>
        {kc && <KpiKarti etiket="Tamamlanan gelişim adımı" deger={kc.adim.tamamlanan} ikon="🪜" ton="okul" alt={`${kc.adim.ogrenci} öğrenci`} />}
        {kc && <KpiKarti etiket="Haftalık görev tamamlama" deger={gt.toplam ? Math.round((1000 * gt.tamamlanan) / gt.toplam) / 10 : '—'} birim={gt.toplam ? '%' : undefined}
          ikon="✅" alt={`${gt.tamamlanan} / ${gt.toplam} görev`} />}
        {kc && <KpiKarti etiket="Görev serisi süren" deger={kc.seri.aktif_seri} ikon="🔥" alt={`ortalama ${kc.seri.ortalama ?? 0} hafta · en uzun ${kc.seri.en_uzun}`} />}
        {f && <KpiKarti etiket="Filiz'i kullanan" deger={f.ogrenci} ikon="💬" alt={`${f.oturum} sohbet · ${f.mesaj} mesaj · öğrencilerin ${yuzde(f.oran)}`} />}
        {c && <KpiKarti etiket="Kaydedilen çalışma" deger={c.saat} birim="saat" ikon="⏱️" alt={`${c.ogrenci} öğrenci · ${c.program_yapan} öğrencinin programı var`} />}
        {c && <KpiKarti etiket="Çözülen soru" deger={c.soru} ikon="✏️" alt={`isabet ${yuzde(c.isabet)}`} />}
      </KpiSatiri>
      <div className="ist-kartlar">
        {kc && (
          <GrafikKarti genis baslik="Haftalık görev tamamlama oranı" aciklama="O hafta verilen görevlerin tamamlanan yüzdesi"
            tablo={tabloYap(['Hafta (pazartesi)', 'Görev', 'Tamamlanan', 'Oran %', 'Öğrenci'], kc.gorev_haftalik.map((h) => [tarihTR(h.hafta), h.toplam, h.tamamlanan, h.oran, h.ogrenci]))}>
            <CizgiGrafik x={kc.gorev_haftalik.map((h) => hafta(h.hafta))} seriler={[{ ad: 'Tamamlama', degerler: kc.gorev_haftalik.map((h) => h.oran), renk: OKUL }]}
              birim="%" yMin={0} yMaks={100} />
          </GrafikKarti>
        )}
        {kc && (
          <GrafikKarti baslik="Görev serisi" aciklama="En az bir görev tamamlanan ardışık hafta (bu hafta ya da geçen haftadan geriye)" tablo={cubukTablosu('Seri', 'Öğrenci', kc.seri.dagilim)}>
            <SutunGrafik veri={kc.seri.dagilim} birim="öğrenci" renk={OKUL} />
          </GrafikKarti>
        )}
        {c && (
          <GrafikKarti baslik="Derslere göre çalışma" aciklama="Öğrencilerin kaydettiği çalışma süresi"
            tablo={tabloYap(['Ders', 'Saat', 'Soru'], c.dersler.map((d) => [d.ad, d.saat, d.soru]))}>
            <YatayCubuk veri={c.dersler.map((d) => ({ ad: d.ad, deger: d.saat, alt: `${d.soru.toLocaleString('tr-TR')} soru` }))} birim="saat" enFazla={10} />
          </GrafikKarti>
        )}
      </div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Akademik
function Akademik({ v }) {
  const a = v.akademik
  const [ot, setOt] = useState(a?.oturumlar?.[0] || 'TYT')
  if (!a) return null
  const secici = a.oturumlar.length > 1 && (
    <select className="yp-sec" value={ot} onChange={(e) => setOt(e.target.value)} aria-label="Oturum">{a.oturumlar.map((o) => <option key={o}>{o}</option>)}</select>
  )
  const subeler = a.subeler[ot] || [], dersler = a.dersler[ot] || []
  return (
    <Bolum id="akademik" baslik="Akademik" aciklama={`Okul denemeleri (seçili aralık ve öğrenciler).${v.net_kullanim != null ? ` Net Takibi'ne kendi denemesini giren öğrenci: ${v.net_kullanim}.` : ''}`}>
      {!a.denemeler.length ? <div className="card bos-durum">Bu aralıkta yüklenmiş okul denemesi yok.</div> : (
        <div className="ist-kartlar">
          {a.oturumlar.map((o) => {
            const l = a.denemeler.filter((d) => d.oturum === o)
            return (
              <GrafikKarti key={o} baslik={`${o} ortalama net`} aciklama={`${l.length} deneme`}
                tablo={tabloYap(['Deneme', 'Tarih', 'Katılım', 'Ortalama net'], l.map((d) => [d.ad, tarihTR(d.tarih), d.katilim, d.ortalama]))}>
                <CizgiGrafik x={l.map((d) => hafta(d.tarih))} seriler={[{ ad: `${o} ortalama`, degerler: l.map((d) => d.ortalama), renk: OKUL }]} birim="net" />
              </GrafikKarti>
            )
          })}
          <GrafikKarti baslik={`Şube ortalamaları · ${ot}`} aciklama="Aralıktaki tüm okul denemelerinde ortalama toplam net" sag={secici}
            tablo={tabloYap(['Şube', 'Ortalama net', 'Sonuç'], subeler.map((s) => [s.ad, s.deger, s.katilim]))}>
            <YatayCubuk veri={subeler.map((s) => ({ ad: s.ad, deger: s.deger, alt: `${s.katilim} sonuç` }))} birim="net" renk={OKUL} />
          </GrafikKarti>
          <GrafikKarti baslik={`Ders ortalamaları · ${ot}`} aciklama="Ders başına ortalama net (altında soru sayısı)" sag={secici}
            tablo={tabloYap(['Ders', 'Ortalama net', 'Soru'], dersler.map((d) => [d.ad, d.deger, d.soru]))}>
            <YatayCubuk veri={dersler.map((d) => ({ ad: d.ad, deger: d.deger, alt: d.soru ? `${d.soru} soru` : undefined }))} birim="net" sirala={false} />
          </GrafikKarti>
        </div>
      )}
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Rehberlik
function Rehberlik({ v }) {
  const r = v.rehberlik || {}
  if (!Object.keys(r).length) return null
  const e = r.erken_uyari, g = r.gorusmeler, t = r.tercih, k = r.kulupler
  return (
    <Bolum id="rehberlik" baslik="Rehberlik" aciklama="Erken uyarılar bugünkü durumdur; görüşmeler seçili tarih aralığındadır. Mezun özetleri tüm yılları kapsar.">
      {e && (
        <KpiSatiri>
          <KpiKarti etiket="Dikkat gerektiren öğrenci" deger={e.toplam} ikon="🧭" ton="okul" />
          {e.seviyeler.map((s) => <KpiKarti key={s.kod} etiket={`${s.ad} seviye`} deger={s.deger} ton={{ yuksek: 'kotu', orta: 'uyari', dusuk: 'bilgi' }[s.kod]}
            ikon={{ yuksek: '🔴', orta: '🟠', dusuk: '🔵' }[s.kod]} alt={s.kod === 'yuksek' ? `${e.gorusulmemis_yuksek} öğrenciyle görüşme yok / planlanmadı` : undefined} />)}
          {g && <KpiKarti etiket="Yapılan görüşme" deger={g.yapildi} ikon="🗣️" alt={`${g.planlandi} planlı · ${g.toplam} kayıt`} />}
        </KpiSatiri>
      )}
      <div className="ist-kartlar">
        {e && (
          <GrafikKarti baslik="Erken uyarı kuralları" aciklama="Her kurala göre uyarı alan öğrenci" tablo={cubukTablosu('Kural', 'Öğrenci', e.kurallar)}>
            <YatayCubuk veri={e.kurallar} birim="öğrenci" />
          </GrafikKarti>
        )}
        {g && (
          <GrafikKarti baslik="Aylık görüşme" aciklama="Yapılan görüşmeler" tablo={tabloYap(['Ay', 'Görüşme'], g.aylik.map((x) => [ayAdi(x.ay), x.deger]))}>
            <SutunGrafik veri={g.aylik.map((x) => ({ ad: ayAdi(x.ay), deger: x.deger }))} birim="görüşme" renk={OKUL} />
          </GrafikKarti>
        )}
        {g && (
          <GrafikKarti baslik="Görüşme türleri" tablo={cubukTablosu('Tür', 'Görüşme', g.turler)}>
            <YatayCubuk veri={g.turler} birim="görüşme" />
          </GrafikKarti>
        )}
        {g && (
          <GrafikKarti baslik="Görüşme konuları" tablo={cubukTablosu('Konu', 'Görüşme', g.konular)}>
            <YatayCubuk veri={g.konular.filter((x) => x.deger > 0)} birim="görüşme" enFazla={8} />
          </GrafikKarti>
        )}
        {r.anketler && (
          <GrafikKarti baslik="Anket katılımı" aciklama="Yayındaki / kapanmış anketlerde hedef öğrencilerin katılım oranı"
            tablo={tabloYap(['Anket', 'Hedef öğrenci', 'Katılan', 'Katılım %'], r.anketler.map((x) => [x.ad, x.hedef, x.katilim, x.oran]))}>
            <YatayCubuk veri={r.anketler.map((x) => ({ ad: x.ad, deger: x.oran ?? 0, alt: `${x.katilim} / ${x.hedef} öğrenci` }))} birim="%" maks={100} />
          </GrafikKarti>
        )}
        {t && (
          <GrafikKarti baslik="Tercih listeleri" aciklama={`12. sınıf ve mezun: ${t.hedef} öğrenci`} tablo={cubukTablosu('Durum', 'Öğrenci', t.durumlar)}>
            <Halka veri={t.durumlar.map((x, i) => ({ ...x, renk: KATEGORIK[i] }))} birim="öğrenci" />
          </GrafikKarti>
        )}
        {r.mezun && (
          <GrafikKarti baslik="Mezun yerleşmeleri" aciklama="Yıllara göre yerleşen mezun; hedef ve öneri uyumu tablo görünümünde"
            tablo={tabloYap(['Yıl', 'Kayıt', 'Yerleşti', 'Hedefiyle aynı', 'İlk 10 öneride'], r.mezun.map((y) => [String(y.yil), y.kayit, y.yerlesti, `${y.hedefle_ayni} / ${y.hedef_bilinen}`, `${y.ilk10} / ${y.oneri_bilinen}`]))}>
            <YatayCubuk veri={r.mezun.map((y) => ({ ad: String(y.yil), deger: y.yerlesti, alt: `${y.kayit} kayıt` }))}
              birim="yerleşen" sirala={false} renk={OKUL} />
          </GrafikKarti>
        )}
        {k && (
          <GrafikKarti baslik="Kulüp üyelikleri" aciklama={`Bir kulübe üye öğrenci: ${k.uye_ogrenci} (${yuzde(k.oran)})`}
            tablo={tabloYap(['Kulüp', 'Üye', 'Bekleyen talep'], k.kulupler.map((x) => [x.ad, x.deger, x.bekleyen]))}>
            <YatayCubuk veri={k.kulupler.map((x) => ({ ad: x.ad, deger: x.deger, alt: x.bekleyen ? `${x.bekleyen} bekleyen talep` : undefined }))} birim="üye" enFazla={10} />
          </GrafikKarti>
        )}
      </div>
    </Bolum>
  )
}

// ----------------------------------------------------------------------------- Sayfa
export default function OkulIstatistik({ okulId }) {
  const modulAcik = useOkulModulleri()
  const [sinif, setSinif] = useState('')
  const [sube, setSube] = useState('')
  const [aralik, setAralik] = useState(90)
  const [ozel, setOzel] = useState({ bas: geri(90), bit: gunStr(new Date()) })
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const [excel, setExcel] = useState(false)
  const [secenekler, setSecenekler] = useState([])

  const filtre = useMemo(() => ({
    sinif, sube,
    ...(aralik === 'ozel' ? ozel : { bas: geri(aralik), bit: gunStr(new Date()) }),
  }), [sinif, sube, aralik, ozel])

  useEffect(() => {
    if (aralik === 'ozel' && (!ozel.bas || !ozel.bit || ozel.bas > ozel.bit)) return
    let iptal = false
    setBekle(true); setHata(null)
    api.okulIstatistik(okulId, filtre)
      .then((d) => { if (!iptal) { setV(d); if (!sinif) setSecenekler(d.filtre.secenekler) } })
      .catch((e) => { if (!iptal) setHata(e.detail || 'İstatistikler yüklenemedi.') })
      .finally(() => { if (!iptal) setBekle(false) })
    return () => { iptal = true }
  }, [okulId, filtre])   // eslint-disable-line react-hooks/exhaustive-deps

  const subeler = secenekler.find((s) => s.sinif === sinif)?.subeler || []
  async function excelIndir() {
    setExcel(true); setHata(null)
    try { await api.okulIstatistikExcel(okulId, filtre) } catch (e) { setHata(e.detail || 'Excel indirilemedi.') } finally { setExcel(false) }
  }

  const k = v?.kpi
  const gorunen = BOLUMLER.filter(([id]) => {
    if (!v) return false
    if (id === 'kocluk') return v.kocluk || v.filiz || v.calisma
    if (id === 'akademik') return !!v.akademik
    if (id === 'rehberlik') return Object.keys(v.rehberlik || {}).length > 0
    return true
  })

  return (
    <div className="ois">
      <div className="yp-arac ois-filtre" role="group" aria-label="Filtreler">
        <select className="yp-sec" value={sinif} onChange={(e) => { setSinif(e.target.value); setSube('') }} aria-label="Sınıf düzeyi">
          <option value="">Tüm sınıf düzeyleri</option>
          {secenekler.map((s) => <option key={s.sinif} value={s.sinif}>{s.sinif}</option>)}
        </select>
        <select className="yp-sec" value={sube} onChange={(e) => setSube(e.target.value)} disabled={!sinif || !subeler.length} aria-label="Şube">
          <option value="">{sinif ? 'Tüm şubeler' : 'Şube (önce sınıf)'}</option>
          {subeler.map((s) => <option key={s} value={s}>{sinif.replace('. Sınıf', '')}-{s}</option>)}
        </select>
        <select className="yp-sec" value={aralik} onChange={(e) => setAralik(e.target.value === 'ozel' ? 'ozel' : Number(e.target.value))} aria-label="Tarih aralığı">
          {ARALIKLAR.map(([d, a]) => <option key={d} value={d}>{a}</option>)}
        </select>
        {aralik === 'ozel' && (
          <>
            <input type="date" className="yp-sec" value={ozel.bas} max={ozel.bit} onChange={(e) => setOzel({ ...ozel, bas: e.target.value })} aria-label="Başlangıç" />
            <input type="date" className="yp-sec" value={ozel.bit} min={ozel.bas} max={gunStr(new Date())} onChange={(e) => setOzel({ ...ozel, bit: e.target.value })} aria-label="Bitiş" />
          </>
        )}
        {bekle && v && <span className="spin" aria-label="Yükleniyor" />}
        <div style={{ flex: 1 }} />
        <button type="button" className="rd-dugme" disabled={!v || excel} onClick={excelIndir}
          title="Bu ekrandaki tüm istatistikler, seçili filtrelerle, sayfa sayfa Excel'de">📊 {excel ? 'Hazırlanıyor…' : 'Excel'}</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {!v ? <div className="bos-durum">{hata ? '' : 'Yükleniyor…'}</div> : (
        <div style={{ opacity: bekle ? 0.6 : 1, transition: 'opacity .2s' }}>
          <div className="yp-ince ois-kapsam">
            <b>{v.filtre.etiket}</b> · {tarihTR(v.filtre.bas)} – {tarihTR(v.filtre.bit)} · test hesapları hariç
            <nav className="ois-atla" aria-label="Bölümlere atla">
              {gorunen.map(([id, ad]) => <a key={id} href={`#ist-${id}`} onClick={(e) => { e.preventDefault(); document.getElementById(`ist-${id}`)?.scrollIntoView({ behavior: 'smooth' }) }}>{ad}</a>)}
            </nav>
          </div>
          <KpiSatiri min={160}>
            <KpiKarti etiket="Öğrenci" deger={k.ogrenci} ikon="🎓" ton="okul" />
            <KpiKarti etiket="Giriş yapan" deger={k.giris_yapan} ikon="🔑" alt={`${yuzde(k.ogrenci ? (100 * k.giris_yapan) / k.ogrenci : null)} · aralıkta ${k.aralikta_giris}`} />
            <KpiKarti etiket="Son 7 gün aktif" deger={k.aktif_7} ikon="⚡" />
            <KpiKarti etiket="Testi tamamlayan" deger={k.tamamlayan} ikon="✅" ton="iyi" alt={`${yuzde(k.tamamlama_orani)} · ${k.teste_baslayan} başladı`} />
            <KpiKarti etiket="K5 tamamlayan" deger={k.k5_tamamlayan} ikon="🌻" />
            <KpiKarti etiket="Hedef seçen" deger={k.hedef_secen} ikon="🎯" />
            <KpiKarti etiket="Ortalama güven puanı" deger={k.ort_guven ?? '—'} ikon="🛡️" alt="testi tamamlayanlarda (0–100)" />
            <KpiKarti etiket="Doğrulanamayan tur" deger={k.gecersiz_tur} ikon="⚠️" ton={k.gecersiz_tur ? 'uyari' : 'notr'} alt="güven puanı eşiğin altında kalan" />
            {k.kocluk_aktif != null && modulAcik('kocluk') && <KpiKarti etiket="Koçlukta aktif" deger={k.kocluk_aktif} ikon="🪜" alt="aralıkta adım ya da görev tamamlayan" />}
          </KpiSatiri>
          <Katilim v={v} />
          <Profil v={v} />
          <BolumMeslek v={v} />
          <Kocluk v={v} />
          <Akademik key={(v.akademik?.oturumlar || []).join()} v={v} />
          <Rehberlik v={v} />
        </div>
      )}
    </div>
  )
}
