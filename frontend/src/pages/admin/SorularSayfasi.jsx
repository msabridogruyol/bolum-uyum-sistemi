import { useEffect, useState, useCallback } from 'react'
import { api } from '../../api/client'

const KATMAN_ID = { K1: 1, K2: 2, K3: 3, K4: 4, K5: 5 }

const DEGISKENLER = [
  { id: 1, kod: 'D1' }, { id: 2, kod: 'D2' }, { id: 3, kod: 'D3' }, { id: 4, kod: 'D4' },
  { id: 5, kod: 'D5' }, { id: 6, kod: 'D6' }, { id: 7, kod: 'D7' },
  { id: 8, kod: 'P1' }, { id: 9, kod: 'P2' }, { id: 10, kod: 'P3' }, { id: 11, kod: 'P4' },
  { id: 12, kod: 'P5' }, { id: 13, kod: 'P6' }, { id: 14, kod: 'P7' }, { id: 15, kod: 'P8' },
  { id: 16, kod: 'A1' }, { id: 17, kod: 'A2' }, { id: 18, kod: 'A3' }, { id: 19, kod: 'A4' },
  { id: 20, kod: 'A5' }, { id: 21, kod: 'A6' }, { id: 22, kod: 'A7' }, { id: 23, kod: 'A8' }, { id: 24, kod: 'A9' },
  { id: 25, kod: 'I1' }, { id: 26, kod: 'I2' }, { id: 27, kod: 'I3' }, { id: 28, kod: 'I4' },
  { id: 29, kod: 'I5' }, { id: 30, kod: 'I6' }, { id: 31, kod: 'I7' },
]

const BOS_LIKERT_SECENEK = ['Kesinlikle Katılmıyorum', 'Katılmıyorum', 'Kararsızım', 'Katılıyorum', 'Kesinlikle Katılıyorum']

function YeniSoruFormu({ onEklendi }) {
  const [katmanKod, setKatmanKod] = useState('K1')
  const [soruTipi, setSoruTipi] = useState('likert')
  const [degiskenId, setDegiskenId] = useState(DEGISKENLER[0].id)
  const [soruMetni, setSoruMetni] = useState('')
  const [tersKodlanmisMi, setTersKodlanmisMi] = useState(false)
  const [secenekler, setSecenekler] = useState([...BOS_LIKERT_SECENEK])
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)
  const [basari, setBasari] = useState(false)

  function tipDegistir(yeniTip) {
    setSoruTipi(yeniTip)
    setSecenekler(yeniTip === 'likert' ? [...BOS_LIKERT_SECENEK] : ['', ''])
  }

  function secenekMetniGuncelle(i, deger) {
    setSecenekler((onceki) => onceki.map((s, idx) => (idx === i ? deger : s)))
  }

  function secenekEkle() {
    setSecenekler((onceki) => [...onceki, ''])
  }

  function secenekSil(i) {
    setSecenekler((onceki) => onceki.filter((_, idx) => idx !== i))
  }

  async function gonder(e) {
    e.preventDefault()
    setHata(null)
    setBasari(false)

    if (soruMetni.trim().length < 5) {
      setHata('Soru metni en az 5 karakter olmalı.')
      return
    }
    const temizSecenekler = secenekler.map((s) => s.trim())
    if (temizSecenekler.some((s) => s.length === 0)) {
      setHata('Tüm seçenek alanları doldurulmalı (boş seçenek olamaz).')
      return
    }
    if (temizSecenekler.length < 2) {
      setHata('En az 2 seçenek gerekli.')
      return
    }

    setGonderiliyor(true)
    try {
      await api.soruEkle({
        katman_id: KATMAN_ID[katmanKod],
        degisken_id: soruTipi === 'likert' ? degiskenId : null,
        soru_tipi: soruTipi,
        soru_metni: soruMetni.trim(),
        ters_kodlanmis_mi: soruTipi === 'likert' ? tersKodlanmisMi : false,
        secenekler: temizSecenekler,
      })
      setBasari(true)
      setSoruMetni('')
      setSecenekler(soruTipi === 'likert' ? [...BOS_LIKERT_SECENEK] : ['', ''])
      setTersKodlanmisMi(false)
      onEklendi()
    } catch (err) {
      setHata(err.detail || 'Soru eklenemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <div className="card">
      <div className="ct">Yeni Soru Ekle</div>

      {soruTipi === 'sjt' && (
        <div className="auth-error" style={{ background: 'var(--aml)', color: 'var(--am)' }}>
          Not: SJT sorularında seçenek başına değişken ağırlığı bu formdan girilemiyor — yalnızca soru ve
          seçenek metinleri kaydedilir. Ağırlıklandırma ayrıca yapılmalı.
        </div>
      )}
      {hata && <div className="auth-error">{hata}</div>}
      {basari && <div style={{ background: 'var(--grl)', color: 'var(--gr)', fontSize: 12.5, fontWeight: 600, padding: '10px 13px', borderRadius: 8, marginBottom: 14 }}>Soru eklendi ✓</div>}

      <form onSubmit={gonder}>
        <div style={{ display: 'flex', gap: 10, marginBottom: 14 }}>
          <div style={{ flex: 1 }}>
            <label className="auth-label">Katman</label>
            <select className="auth-input" value={katmanKod} onChange={(e) => setKatmanKod(e.target.value)}>
              {Object.keys(KATMAN_ID).map((k) => <option key={k} value={k}>{k}</option>)}
            </select>
          </div>
          <div style={{ flex: 1 }}>
            <label className="auth-label">Soru Tipi</label>
            <select className="auth-input" value={soruTipi} onChange={(e) => tipDegistir(e.target.value)}>
              <option value="likert">Likert (5'li ölçek)</option>
              <option value="sjt">SJT (durumsal yargı)</option>
            </select>
          </div>
        </div>

        {soruTipi === 'likert' && (
          <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'flex-end' }}>
            <div style={{ flex: 1 }}>
              <label className="auth-label">Ölçtüğü Değişken</label>
              <select className="auth-input" value={degiskenId} onChange={(e) => setDegiskenId(Number(e.target.value))}>
                {DEGISKENLER.map((d) => <option key={d.id} value={d.id}>{d.kod}</option>)}
              </select>
            </div>
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, color: 'var(--tx2)', paddingBottom: 11 }}>
              <input type="checkbox" checked={tersKodlanmisMi} onChange={(e) => setTersKodlanmisMi(e.target.checked)} />
              Ters kodlanmış (puan = 100 − puan)
            </label>
          </div>
        )}

        <div className="auth-field">
          <label className="auth-label">Soru Metni</label>
          <textarea
            className="auth-input"
            style={{ minHeight: 70, resize: 'vertical', fontFamily: 'var(--fn)' }}
            value={soruMetni}
            onChange={(e) => setSoruMetni(e.target.value)}
            placeholder="Örn: İşimde en çok değer verdiğim şey..."
          />
        </div>

        <label className="auth-label">Seçenekler</label>
        {secenekler.map((s, i) => (
          <div key={i} style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <input
              className="auth-input"
              style={{ flex: 1 }}
              value={s}
              onChange={(e) => secenekMetniGuncelle(i, e.target.value)}
              placeholder={`Seçenek ${i + 1}`}
              disabled={soruTipi === 'likert'}
            />
            {soruTipi === 'sjt' && secenekler.length > 2 && (
              <button type="button" className="btn sec" onClick={() => secenekSil(i)}>Sil</button>
            )}
          </div>
        ))}
        {soruTipi === 'sjt' && (
          <button type="button" className="btn sec" style={{ marginBottom: 14 }} onClick={secenekEkle}>+ Seçenek Ekle</button>
        )}

        <button className="btn full" type="submit" disabled={gonderiliyor} style={{ marginTop: 6 }}>
          {gonderiliyor ? <span className="spin" /> : 'Soruyu Kaydet'}
        </button>
      </form>
    </div>
  )
}

export default function SorularSayfasi() {
  const [sorular, setSorular] = useState(null)
  const [katmanFiltre, setKatmanFiltre] = useState('')
  const [formAcik, setFormAcik] = useState(false)
  const [hata, setHata] = useState(null)

  const yukle = useCallback((kod) => {
    api.sorulariListele(kod || undefined).then(setSorular).catch((e) => setHata(e.detail || 'Sorular yüklenemedi.'))
  }, [])

  useEffect(() => { yukle(katmanFiltre) }, [yukle, katmanFiltre])

  async function aktiflikDegistir(soruId, aktifMi) {
    try {
      await api.soruAktiflikGuncelle(soruId, !aktifMi)
      yukle(katmanFiltre)
    } catch (err) {
      setHata(err.detail || 'Güncellenemedi.')
    }
  }

  return (
    <div className="pg">
      <div className="ph">
        <div className="pt">Soru Bankası</div>
        <div className="ps">Sorular silinmez, yalnızca pasife alınır — geçmiş öğrenci oturumları bozulmasın diye.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ display: 'flex', gap: 10, marginBottom: 14, alignItems: 'center' }}>
        <select className="auth-input" style={{ width: 160 }} value={katmanFiltre} onChange={(e) => setKatmanFiltre(e.target.value)}>
          <option value="">Tüm katmanlar</option>
          {['K1', 'K2', 'K3', 'K4', 'K5'].map((k) => <option key={k} value={k}>{k}</option>)}
        </select>
        <button className="btn" onClick={() => setFormAcik((a) => !a)}>
          {formAcik ? 'Formu Kapat' : '+ Yeni Soru Ekle'}
        </button>
      </div>

      {formAcik && (
        <div style={{ marginBottom: 20 }}>
          <YeniSoruFormu onEklendi={() => yukle(katmanFiltre)} />
        </div>
      )}

      {!sorular ? <div className="bos-durum">Yükleniyor…</div> : (
        <div className="ll">
          {sorular.map((s) => (
            <div key={s.id} className="lc" style={{ cursor: 'default', opacity: s.aktif_mi ? 1 : 0.5 }}>
              <div className="lb-wrap">
                <div className="lt">{s.soru_metni}</div>
                <div className="ld">{s.katman_kod} · {s.soru_tipi}</div>
              </div>
              <span className={`bdg ${s.aktif_mi ? 'bdg-done' : 'bdg-lock'}`}>{s.aktif_mi ? 'Aktif' : 'Pasif'}</span>
              <button className="btn sec" onClick={() => aktiflikDegistir(s.id, s.aktif_mi)}>
                {s.aktif_mi ? 'Pasife Al' : 'Aktifleştir'}
              </button>
            </div>
          ))}
          {sorular.length === 0 && <div className="bos-durum">Bu katmanda soru yok.</div>}
        </div>
      )}
    </div>
  )
}
