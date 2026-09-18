import { useState, useEffect, useCallback } from 'react'
import { api } from '../../api/client'

const KATMANLAR = ['K1', 'K2', 'K3', 'K4']
const KATMAN_ADI = { K1: 'Değerler', K2: 'Kişilik', K3: 'İş Ortamı', K4: 'Alan Eğilimi' }
const ARALIK_ADI = {
  belirgin_ustun: 'Belirgin Üstün', ustun: 'Üstün', beklenti: 'Beklenti',
  altinda: 'Altında', belirgin_altinda: 'Belirgin Altında',
}
const TIP_ADI = { kitap: '📖 Kitap', film: '🎬 Film', rol_model: '🌟 Rol Model', psikolojik_yaklasim: '🧠 Psikolojik Yaklaşım', aktivite: '🏃 Aktivite' }
const TIP_RENK = { kitap: 'var(--pu)', film: 'var(--am)', rol_model: 'var(--gr)', psikolojik_yaklasim: 'var(--tl, var(--pu))', aktivite: 'var(--re, #e05252)' }

function DuzenlenebilirMetin({ deger, coklu, onKaydet, stil = {} }) {
  const [duzenleniyor, setDuzenleniyor] = useState(false)
  const [taslak, setTaslak] = useState(deger)
  const [kaydediliyor, setKaydediliyor] = useState(false)

  useEffect(() => { setTaslak(deger) }, [deger])

  async function kaydet() {
    if (taslak.trim() === deger.trim()) { setDuzenleniyor(false); return }
    setKaydediliyor(true)
    try {
      await onKaydet(taslak.trim())
      setDuzenleniyor(false)
    } catch (err) {
      alert(err.detail || 'Kaydedilemedi.')
    } finally {
      setKaydediliyor(false)
    }
  }

  if (!duzenleniyor) {
    return (
      <div
        onClick={() => setDuzenleniyor(true)}
        style={{ cursor: 'text', padding: '2px 4px', borderRadius: 6, ...stil }}
        onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--sur2)')}
        onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
      >
        {deger}
      </div>
    )
  }

  const ortak = {
    value: taslak, autoFocus: true, disabled: kaydediliyor,
    onChange: (e) => setTaslak(e.target.value),
    onBlur: kaydet,
    onKeyDown: (e) => {
      if (e.key === 'Enter' && !coklu) kaydet()
      if (e.key === 'Escape') { setTaslak(deger); setDuzenleniyor(false) }
    },
    style: { width: '100%', fontFamily: 'inherit', fontSize: 'inherit', padding: '4px 6px', border: '1.5px solid var(--pu)', borderRadius: 6, ...stil },
  }
  return coklu ? <textarea rows={2} {...ortak} /> : <input type="text" {...ortak} />
}

function KaynakKarti({ kaynak, onGuncelle, onSil }) {
  return (
    <div className="card" style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 8, alignItems: 'center' }}>
        <span className="bdg bdg-prog">{kaynak.katman_kod}</span>
        <span className="bdg bdg-lock">{kaynak.degisken_adi}</span>
        <span className="bdg bdg-lock">{ARALIK_ADI[kaynak.aralik]}</span>
        <span className="bdg" style={{ background: 'var(--sur2)', color: TIP_RENK[kaynak.kaynak_tipi] }}>{TIP_ADI[kaynak.kaynak_tipi]}</span>
        <div style={{ flex: 1 }} />
        <button
          onClick={() => { if (confirm('Bu kaynağı silmek istiyor musunuz?')) onSil(kaynak.id) }}
          style={{ background: 'none', border: 'none', color: 'var(--tx3)', cursor: 'pointer', fontSize: 13 }}
        >
          🗑
        </button>
      </div>
      <DuzenlenebilirMetin
        deger={kaynak.baslik}
        stil={{ fontSize: 14, fontWeight: 700, marginBottom: 4 }}
        onKaydet={(v) => onGuncelle(kaynak.id, { baslik: v })}
      />
      <DuzenlenebilirMetin
        deger={kaynak.aciklama}
        coklu
        stil={{ fontSize: 13, color: 'var(--tx2)' }}
        onKaydet={(v) => onGuncelle(kaynak.id, { aciklama: v })}
      />
    </div>
  )
}

function YeniKaynakFormu({ aktifKatman, degiskenler, onEklendi, onKapat }) {
  const [degiskenKod, setDegiskenKod] = useState(degiskenler[0]?.kod || '')
  const [aralik, setAralik] = useState('altinda')
  const [kaynakTipi, setKaynakTipi] = useState('kitap')
  const [baslik, setBaslik] = useState('')
  const [aciklama, setAciklama] = useState('')
  const [gonderiliyor, setGonderiliyor] = useState(false)
  const [hata, setHata] = useState(null)

  async function gonder(e) {
    e.preventDefault()
    if (!degiskenKod || !baslik.trim() || !aciklama.trim()) return
    setGonderiliyor(true)
    setHata(null)
    try {
      await api.gelisimKaynagiEkle({ degisken_kod: degiskenKod, aralik, kaynak_tipi: kaynakTipi, baslik: baslik.trim(), aciklama: aciklama.trim() })
      setBaslik(''); setAciklama('')
      onEklendi()
    } catch (err) {
      setHata(err.detail || 'Eklenemedi.')
    } finally {
      setGonderiliyor(false)
    }
  }

  return (
    <form onSubmit={gonder} className="card" style={{ borderColor: 'var(--pu)', marginBottom: 16 }}>
      <div className="ct">Yeni Kaynak Ekle — {aktifKatman}</div>
      {hata && <div className="auth-error">{hata}</div>}
      <div style={{ display: 'flex', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
        <select className="auth-input" style={{ flex: '1 1 160px' }} value={degiskenKod} onChange={(e) => setDegiskenKod(e.target.value)}>
          {degiskenler.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}
        </select>
        <select className="auth-input" style={{ flex: '1 1 160px' }} value={aralik} onChange={(e) => setAralik(e.target.value)}>
          {Object.entries(ARALIK_ADI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="auth-input" style={{ flex: '1 1 160px' }} value={kaynakTipi} onChange={(e) => setKaynakTipi(e.target.value)}>
          {Object.entries(TIP_ADI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
      </div>
      <input className="auth-input" style={{ marginBottom: 10 }} placeholder="Başlık (kitap/film/kişi/yaklaşım adı)" value={baslik} onChange={(e) => setBaslik(e.target.value)} />
      <textarea className="auth-input" rows={2} style={{ marginBottom: 10 }} placeholder="Açıklama — neden bu değişkenle ilgili" value={aciklama} onChange={(e) => setAciklama(e.target.value)} />
      <div style={{ display: 'flex', gap: 8 }}>
        <button className="btn" type="submit" disabled={gonderiliyor}>{gonderiliyor ? <span className="spin" /> : 'Ekle'}</button>
        <button className="btn sec" type="button" onClick={onKapat}>Kapat</button>
      </div>
    </form>
  )
}

export default function GelisimKaynakSayfasi() {
  const [aktifKatman, setAktifKatman] = useState('K1')
  const [degiskenler, setDegiskenler] = useState([])
  const [degiskenFiltre, setDegiskenFiltre] = useState('')
  const [aralikFiltre, setAralikFiltre] = useState('')
  const [tipFiltre, setTipFiltre] = useState('')
  const [arama, setArama] = useState('')
  const [aramaGecikmeli, setAramaGecikmeli] = useState('')
  const [kaynaklar, setKaynaklar] = useState(null)
  const [yeniFormuAcik, setYeniFormuAcik] = useState(false)
  const [hata, setHata] = useState(null)

  useEffect(() => {
    const t = setTimeout(() => setAramaGecikmeli(arama), 400)
    return () => clearTimeout(t)
  }, [arama])

  useEffect(() => {
    setDegiskenFiltre(''); setAralikFiltre(''); setTipFiltre(''); setArama('')
    api.gelisimKaynakDegiskenleriGetir(aktifKatman).then(setDegiskenler).catch(() => setDegiskenler([]))
  }, [aktifKatman])

  const yukle = useCallback(() => {
    api.gelisimKaynaklariListele({
      katman_kod: aktifKatman, degisken_kod: degiskenFiltre, aralik: aralikFiltre,
      kaynak_tipi: tipFiltre, arama: aramaGecikmeli,
    }).then(setKaynaklar).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  }, [aktifKatman, degiskenFiltre, aralikFiltre, tipFiltre, aramaGecikmeli])

  useEffect(() => { yukle() }, [yukle])

  async function guncelle(id, veri) {
    await api.gelisimKaynagiGuncelle(id, veri)
    yukle()
  }
  async function sil(id) {
    await api.gelisimKaynagiSil(id)
    yukle()
  }

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Gelişim Kaynak Havuzu</div>
        <div className="ps">Filiz'in (AI koç) öğrenciye önerdiği kitap, film, rol model, psikolojik yaklaşım ve aktivite önerileri — bölümden bağımsız, genel bir havuz.</div>
      </div>
      {hata && <div className="auth-error">{hata}</div>}

      <div style={{ display: 'flex', gap: 6, marginBottom: 18, borderBottom: '1.5px solid var(--bor)' }}>
        {KATMANLAR.map((k) => (
          <button
            key={k}
            onClick={() => setAktifKatman(k)}
            style={{
              padding: '10px 20px', border: 'none', background: 'none', cursor: 'pointer',
              fontFamily: 'var(--fd)', fontSize: 13.5, fontWeight: 700,
              color: aktifKatman === k ? 'var(--pu)' : 'var(--tx3)',
              borderBottom: aktifKatman === k ? '2.5px solid var(--pu)' : '2.5px solid transparent',
              marginBottom: -1.5,
            }}
          >
            {k} — {KATMAN_ADI[k]}
          </button>
        ))}
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <input className="auth-input" style={{ width: 220 }} placeholder="🔍 Başlıkta ara..." value={arama} onChange={(e) => setArama(e.target.value)} />
        <select className="auth-input" style={{ width: 200 }} value={degiskenFiltre} onChange={(e) => setDegiskenFiltre(e.target.value)}>
          <option value="">Tüm değişkenler</option>
          {degiskenler.map((d) => <option key={d.kod} value={d.kod}>{d.ad}</option>)}
        </select>
        <select className="auth-input" style={{ width: 170 }} value={aralikFiltre} onChange={(e) => setAralikFiltre(e.target.value)}>
          <option value="">Tüm aralıklar</option>
          {Object.entries(ARALIK_ADI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <select className="auth-input" style={{ width: 190 }} value={tipFiltre} onChange={(e) => setTipFiltre(e.target.value)}>
          <option value="">Tüm tipler</option>
          {Object.entries(TIP_ADI).map(([k, v]) => <option key={k} value={k}>{v}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn" onClick={() => setYeniFormuAcik((a) => !a)}>{yeniFormuAcik ? 'Kapat' : '+ Yeni Kaynak'}</button>
      </div>

      {yeniFormuAcik && (
        <YeniKaynakFormu aktifKatman={aktifKatman} degiskenler={degiskenler} onEklendi={() => { yukle(); setYeniFormuAcik(false) }} onKapat={() => setYeniFormuAcik(false)} />
      )}

      {!kaynaklar ? (
        <div className="bos-durum">Yükleniyor…</div>
      ) : kaynaklar.length === 0 ? (
        <div className="bos-durum">Bu filtreye uyan kaynak yok.</div>
      ) : (
        <>
          <div style={{ fontSize: 12, color: 'var(--tx3)', fontWeight: 600, marginBottom: 10 }}>{kaynaklar.length} kaynak bulundu</div>
          {kaynaklar.map((k) => <KaynakKarti key={k.id} kaynak={k} onGuncelle={guncelle} onSil={sil} />)}
        </>
      )}
    </div>
  )
}
