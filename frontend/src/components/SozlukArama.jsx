// [2026-10-11] Sistem sözlüğü — arama kutusu + sonuçlar. Filiz panelindeki "Sözlük" sekmesinde, Sözlük penceresinde
// ve /sozluk sayfasında aynı bileşen kullanılır. Kelime yazılınca anlamı, varsa örnekle birlikte görünür.
// [2026-10-11] Genişletilmiş sözlük: ~3.300 terim + 301 bölüm + meslekler + özellikler (ilk kullanımda yüklenir).
// Bölüm kartından bölüm bilgi penceresi, meslek kartından ilgili bölümler açılır.
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useBolumBilgi } from '../context/BolumBilgiContext'
import { sozlukAra, sozlukDinle, sozlukYukle, sozlukYuklendiMi, toplamTerim } from '../yardimci/sozluk'

const ONERILER = ['net', 'taban puan', 'başarı sırası', 'TYT', 'güçlü yön', 'KPSS', 'staj', 'brüt maaş']

/** Genişletilmiş sözlüğü yükler; yüklenince bileşeni yeniden çizer. */
export function useSozluk() {
  const [, setSurum] = useState(0)
  useEffect(() => {
    const kapat = sozlukDinle(() => setSurum((v) => v + 1))
    sozlukYukle()
    return kapat
  }, [])
  return { hazir: sozlukYuklendiMi(), toplam: toplamTerim() }
}

export function TerimKarti({ t, buyuk = false }) {
  const { ac } = useBolumBilgi()
  const [acik, setAcik] = useState(buyuk)
  const uzun = t.t.length > 260
  return (
    <div className={`sz-kart${buyuk ? ' buyuk' : ''}${t.tur ? ` ${t.tur}` : ''}`}>
      <div className="sz-ad">{t.tur === 'bolum' ? '🎓 ' : t.tur === 'meslek' ? '💼 ' : ''}{t.ad}</div>
      <div className="sz-grup">{t.tur === 'ozellik' ? `Değerlendirmede ölçülen özellik${t.katman ? ` · ${t.katman}` : ''}` : t.g}</div>
      <div className="sz-tanim">{uzun && !acik ? `${t.t.slice(0, 240).replace(/\s+\S*$/, '')}…` : t.t}
        {uzun && <button type="button" className="sz-devam" onClick={() => setAcik((v) => !v)}>{acik ? 'kısalt' : 'devamı'}</button>}
      </div>
      {t.o && <div className="sz-ornek"><b>Örnek:</b> {t.o}</div>}
      {t.tur === 'bolum' && <button type="button" className="sz-git" onClick={() => ac(t.bolumId, t.bolumAd)}>Bölümü incele →</button>}
      {t.tur === 'meslek' && t.bolumler?.length > 0 && (
        <div className="sz-bolumler"><span>İlgili bölümler:</span>
          {t.bolumler.slice(0, 6).map((b) => <button key={b.id} type="button" onClick={() => ac(b.id, b.hamAd)}>{b.ad}</button>)}
        </div>
      )}
    </div>
  )
}

export default function SozlukArama({ baslangic = '', otomatikOdak = true, kompakt = false, onSayfayaGit }) {
  const [ara, setAra] = useState(baslangic)
  const girdi = useRef(null)
  const { hazir, toplam } = useSozluk()
  useEffect(() => { if (otomatikOdak) window.setTimeout(() => girdi.current?.focus(), 60) }, [otomatikOdak])
  useEffect(() => { setAra(baslangic) }, [baslangic])
  const sonuc = useMemo(() => sozlukAra(ara, kompakt ? 8 : 40), [ara, kompakt, hazir])   // eslint-disable-line react-hooks/exhaustive-deps
  const q = ara.trim()

  return (
    <div className={`sz${kompakt ? ' kompakt' : ''}`}>
      <div className="sz-arama">
        <span aria-hidden="true">🔍</span>
        <input ref={girdi} value={ara} onChange={(e) => setAra(e.target.value)} placeholder="Anlamını merak ettiğin kelimeyi yaz…"
               aria-label="Sözlükte ara" enterKeyHint="search" />
        {ara && <button className="sz-temizle" onClick={() => { setAra(''); girdi.current?.focus() }} aria-label="Temizle">✕</button>}
      </div>

      {!q && (
        <div className="sz-oneri">
          <div className="sz-oneri-bas">Sık aranan kelimeler</div>
          <div className="sz-cipler">
            {ONERILER.map((o) => <button key={o} onClick={() => setAra(o)}>{o}</button>)}
          </div>
          <div className="sz-not">
            {hazir
              ? <>Sözlükte {toplam.toLocaleString('tr-TR')} kelime var: sistemde geçen terimler, tüm bölümler, meslekler, ders ve alan terimleri.</>
              : 'Sözlük hazırlanıyor…'}
          </div>
        </div>
      )}

      {q && sonuc.length === 0 && (
        <div className="sz-bos">
          {hazir ? <>“{q}” sözlükte yok. Başka bir yazılışla dene{kompakt ? ' ya da Filiz\'e sor' : ''}.</> : 'Sözlük hazırlanıyor…'}
        </div>
      )}
      {q && sonuc.length > 0 && (
        <div className="sz-sonuclar" aria-live="polite">
          {sonuc.map((t, i) => <TerimKarti key={t.k} t={t} buyuk={i === 0} />)}
        </div>
      )}

      {kompakt && (
        <Link to={q ? `/sozluk?q=${encodeURIComponent(q)}` : '/sozluk'} className="sz-tumu" onClick={onSayfayaGit}>📖 Sözlüğün tamamı →</Link>
      )}
    </div>
  )
}
