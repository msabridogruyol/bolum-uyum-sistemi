// [2026-10-10] Kulüplerim — okulun kulüpleri (katılma talebi, üyelik durumu), kulüp duyuruları ve ilgi testi.
// Talepleri okul yetkilisi (rehber öğretmen) onaylar; duyuru ve etkinlikleri de o yayınlar.
import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import IlgiKulupSekmesi from '../components/IlgiKulupSekmesi'

const DURUM = {
  bekliyor: { ad: 'Talebin bekliyor', renk: 'var(--am)', zemin: 'var(--aml)' },
  onaylandi: { ad: 'Üyesin ✓', renk: 'var(--gr)', zemin: 'var(--grl)' },
  reddedildi: { ad: 'Talep kabul edilmedi', renk: 'var(--re)', zemin: 'var(--rel)' },
  ayrildi: { ad: 'Ayrıldın', renk: 'var(--tx3)', zemin: 'var(--sur2)' },
}
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const tarihMetni = (t) => { const d = new Date(t); return `${d.getDate()} ${AY[d.getMonth()]}` }

function Duyurular({ liste }) {
  if (!liste.length) return null
  return (
    <div className="card">
      <div className="ct">📣 Kulüp duyuruları</div>
      <div className="kd-liste">
        {liste.map((d) => (
          <div key={d.id} className={`kd-satir ${d.tur}`}>
            {d.tur === 'etkinlik' ? (
              <div className="kd-tarih"><b>{new Date(d.tarih).getDate()}</b><span>{AY[new Date(d.tarih).getMonth()]}</span></div>
            ) : <div className="kd-tarih duyuru">📣</div>}
            <div style={{ minWidth: 0, flex: 1 }}>
              <div className="kd-ust"><span className="kd-kulup">{d.kulup}</span>{d.herkese && !d.uye && <span className="kd-herkese">Okula açık</span>}</div>
              <div className="kd-baslik">{d.baslik}</div>
              {d.tur === 'etkinlik' && <div className="yp-ince">{[d.saat && `⏰ ${d.saat}`, d.yer && `📍 ${d.yer}`].filter(Boolean).join(' · ')}</div>}
              {d.metin && <div className="kd-metin">{d.metin}</div>}
            </div>
            <span className="yp-ince">{tarihMetni(d.olusturulma_zamani)}</span>
          </div>
        ))}
      </div>
      <div className="yp-ince" style={{ marginTop: 8 }}>Etkinlikler Takvim'ine de eklenir.</div>
    </div>
  )
}

function KulupKarti({ k, onDegisti }) {
  const [form, setForm] = useState(false)
  const [mesaj, setMesaj] = useState('')
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const u = k.uyelik
  const d = u ? DURUM[u.durum] : null
  async function islem(f) { setBekle(true); setHata(null); try { onDegisti(await f()); setForm(false); setMesaj('') } catch (e) { setHata(e.detail || 'İşlem yapılamadı.') } finally { setBekle(false) } }
  return (
    <div className={`kk-kart${u?.durum === 'onaylandi' ? ' uye' : ''}`}>
      <div className="kk-ust">
        <b>{k.ad}</b>
        {k.uyum != null && <span className="ik-uyum" title="İlgi testine göre uyum">%{k.uyum}</span>}
      </div>
      {k.aciklama && <div className="kk-ac">{k.aciklama}</div>}
      <div className="yp-ince">{[k.sorumlu && `👤 ${k.sorumlu}`, k.bulusma && `🗓 ${k.bulusma}`, `👥 ${k.uye_sayisi} üye`].filter(Boolean).join(' · ')}</div>
      {d && <div className="kk-durum" style={{ color: d.renk, background: d.zemin }}>{d.ad}</div>}
      {u?.yanit && <div className="kk-yanit">💬 <i>Rehber öğretmenin:</i> {u.yanit}</div>}
      {hata && <div className="auth-error" style={{ margin: 0 }}>{hata}</div>}
      {form ? (
        <div className="kk-form">
          <textarea maxLength={300} rows={2} placeholder="Neden katılmak istiyorsun? (isteğe bağlı)" value={mesaj} onChange={(e) => setMesaj(e.target.value)} />
          <div style={{ display: 'flex', gap: 6 }}>
            <button className="btn" disabled={bekle} onClick={() => islem(() => api.kulupTalepEt(k.id, mesaj))}>Talebi gönder</button>
            <button className="btn sec" onClick={() => setForm(false)}>Vazgeç</button>
          </div>
        </div>
      ) : (
        <div className="kk-dugmeler">
          {(!u || ['reddedildi', 'ayrildi'].includes(u.durum)) && <button className="btn" onClick={() => setForm(true)}>{u ? 'Tekrar talep et' : 'Katılmak istiyorum'}</button>}
          {u?.durum === 'bekliyor' && <button className="btn sec" disabled={bekle} onClick={() => islem(() => api.kulupTalepGeriCek(k.id))}>Talebi geri çek</button>}
          {u?.durum === 'onaylandi' && <button className="hg-link" disabled={bekle} onClick={() => islem(() => api.kulupTalepGeriCek(k.id))}>Kulüpten ayrıl</button>}
        </div>
      )}
    </div>
  )
}

function KuluplerSekmesi({ v, setV, testeGit }) {
  if (!v.kulupler.length) {
    return <div className="card bos-durum">Okulun henüz kulüp listesini girmedi. Bu arada <button className="hg-link" onClick={testeGit}>ilgi testini çözerek</button> sana uygun kulüp türlerini görebilirsin.</div>
  }
  const uyeler = v.kulupler.filter((k) => k.uyelik?.durum === 'onaylandi')
  const digerleri = [...v.kulupler.filter((k) => k.uyelik?.durum !== 'onaylandi')].sort((a, b) => (b.uyum ?? -1) - (a.uyum ?? -1))
  const testYok = v.kulupler.every((k) => k.uyum == null)
  return (
    <>
      <Duyurular liste={v.duyurular} />
      {uyeler.length > 0 && (
        <div className="card">
          <div className="ct">✅ Üye olduğun kulüpler</div>
          <div className="kk-izgara">{uyeler.map((k) => <KulupKarti key={k.id} k={k} onDegisti={setV} />)}</div>
        </div>
      )}
      <div className="card">
        <div className="ct">🏫 Okulundaki kulüpler</div>
        {testYok && <div className="yp-uyari" style={{ marginBottom: 10 }}>İlgi testini çözersen kulüpler sana uygunluğuna göre sıralanır. <button className="hg-link" onClick={testeGit}>Teste git →</button></div>}
        <div className="yp-ince" style={{ marginBottom: 10 }}>Katılmak istediğin kulübe talep gönder; rehber öğretmenin onaylayınca üye olursun ve kulübün duyurularını görürsün. Aynı anda en fazla {v.maks_aktif} kulüp.</div>
        <div className="kk-izgara">{digerleri.map((k) => <KulupKarti key={k.id} k={k} onDegisti={setV} />)}</div>
      </div>
    </>
  )
}

export default function KuluplerimSayfasi() {
  const [params, setParams] = useSearchParams()
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const sekme = params.get('sekme') || 'kulupler'
  // kulüpler sekmesine her dönüşte tazelenir (ilgi testi sonrası uyum sıralaması güncellensin)
  useEffect(() => { if (sekme === 'kulupler') api.kulupDurumu().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [sekme])
  const git = (k) => setParams(k === 'kulupler' ? {} : { sekme: k }, { replace: true })
  const bekleyen = v?.kulupler.filter((k) => k.uyelik?.durum === 'bekliyor').length || 0
  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Kulüplerim</div>
        <div className="ps">Okulundaki kulüplere katılma talebi gönder, kulüp duyurularını ve etkinliklerini takip et; ilgi testinle sana uygun olanları bul.</div>
      </div>
      <div className="koc-sekmeler" role="tablist">
        <button role="tab" aria-selected={sekme === 'kulupler'} className={sekme === 'kulupler' ? 'aktif' : ''} onClick={() => git('kulupler')}>
          🎭 Kulüpler{bekleyen > 0 && <span className="koc-cip-sayi">{bekleyen} bekliyor</span>}
        </button>
        <button role="tab" aria-selected={sekme === 'test'} className={sekme === 'test' ? 'aktif' : ''} onClick={() => git('test')}>🎯 İlgi testi</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {sekme === 'kulupler' && (v ? <KuluplerSekmesi v={v} setV={setV} testeGit={() => git('test')} /> : !hata && <div className="bos-durum">Yükleniyor…</div>)}
      {sekme === 'test' && <IlgiKulupSekmesi />}
    </div>
  )
}
