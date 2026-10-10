// [2026-10-10] Uzman koçlar — okulun anlaşmalı eğitim koçları ve görüşme talepleri.
// Talep önce rehber öğretmene gider; koçun iletişim bilgisi öğrenciye gösterilmez.
import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { Pencere } from '../components/yonetim/ortak'

const DURUM_RENK = { beklemede: 'am', onaylandi: 'gr', tamamlandi: 'pu', reddedildi: 'tx3', iptal: 'tx3' }
const basHarf = (ad) => ad.split(/\s+/).filter((x) => !/\.$/.test(x)).slice(0, 2).map((x) => x[0]).join('').toLocaleUpperCase('tr-TR')
const tarihSaat = (t) => t ? new Date(t).toLocaleString('tr-TR', { day: 'numeric', month: 'long', weekday: 'long', hour: '2-digit', minute: '2-digit' }) : ''

function TalepFormu({ koc, konular, onKapat, onGonderildi }) {
  const [f, setF] = useState({ konu: koc.konular[0] || konular[0], tercih_zamani: '', mesaj: '', talep_eden: 'ogrenci', veli_ad: '', iletisim: '' })
  const [bekle, setBekle] = useState(false)
  const [hata, setHata] = useState(null)
  const alan = (k) => (e) => setF({ ...f, [k]: e.target.value })
  const gonder = async (e) => {
    e.preventDefault(); setBekle(true); setHata(null)
    try { await api.kocTalebi(koc.id, f); onGonderildi() } catch (er) { setHata(er.detail || 'Gönderilemedi.') }
    setBekle(false)
  }
  return (
    <Pencere baslik={`${koc.ad_soyad} ile görüşme talebi`} altBaslik="Talebin önce rehber öğretmenine iletilir; uygun zamanı birlikte planlarlar." onKapat={onKapat}>
      <form onSubmit={gonder} className="kc-form">
        <label className="auth-label">Talebi kim yapıyor?</label>
        <div className="kc-secim">
          <button type="button" className={f.talep_eden === 'ogrenci' ? 'secili' : ''} onClick={() => setF({ ...f, talep_eden: 'ogrenci' })}>🎓 Ben</button>
          <button type="button" className={f.talep_eden === 'veli' ? 'secili' : ''} onClick={() => setF({ ...f, talep_eden: 'veli' })}>👪 Velim adına</button>
        </div>
        {f.talep_eden === 'veli' && (
          <div className="kl-form">
            <input className="auth-input" required maxLength={80} value={f.veli_ad} onChange={alan('veli_ad')} placeholder="Veli adı soyadı" />
            <input className="auth-input" required maxLength={120} value={f.iletisim} onChange={alan('iletisim')} placeholder="Veli telefonu veya e-postası" />
          </div>
        )}
        <label className="auth-label">Konu</label>
        <select className="auth-input" value={f.konu} onChange={alan('konu')}>{konular.map((k) => <option key={k}>{k}</option>)}</select>
        <label className="auth-label">Sana uygun zaman (isteğe bağlı)</label>
        <input className="auth-input" maxLength={120} value={f.tercih_zamani} onChange={alan('tercih_zamani')} placeholder="ör. Hafta içi 16:00 sonrası, Cumartesi sabah" />
        <label className="auth-label">Konuşmak istediklerin (isteğe bağlı)</label>
        <textarea className="auth-input" rows={4} maxLength={800} value={f.mesaj} onChange={alan('mesaj')} placeholder="ör. Tıp ile biyomühendislik arasında kararsızım…" />
        {hata && <div className="auth-error">{hata}</div>}
        <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
          <button className="btn" type="submit" disabled={bekle}>{bekle ? <span className="spin" /> : 'Talebi gönder'}</button>
          <button className="btn sec" type="button" onClick={onKapat}>Vazgeç</button>
        </div>
      </form>
    </Pencere>
  )
}

function KocKarti({ k, acikTalep, onTalep }) {
  const [acik, setAcik] = useState(false)
  return (
    <div className={`kc-kart${k.uygun ? ' uygun' : ''}`}>
      <div className="kc-ust">
        <div className="kc-avatar" aria-hidden="true">{basHarf(k.ad_soyad)}</div>
        <div style={{ minWidth: 0 }}>
          <div className="kc-ad">{k.ad_soyad}</div>
          {k.unvan && <div className="kc-unvan">{k.unvan}</div>}
        </div>
      </div>
      {k.uygun && <div className="kc-uygun">✓ İlgilendiğin alanda: {k.uygun_alanlar.join(', ')}</div>}
      <div>{k.alan_adlari.map((a) => <span key={a} className="ak-cip">{a}</span>)}</div>
      <div className="kc-bilgi">
        {k.deneyim_yil != null && <span>⏳ {k.deneyim_yil} yıl deneyim</span>}
        <span>💬 {k.gorusme_metni}</span>
        {k.ucret_bilgisi && <span>🏷 {k.ucret_bilgisi}</span>}
      </div>
      {k.konular.length > 0 && <div className="kc-konular">{k.konular.map((x) => <span key={x}>• {x}</span>)}</div>}
      {k.hakkinda && (
        <div className={`kc-hakkinda${acik ? ' acik' : ''}`}>{k.hakkinda}{k.hakkinda.length > 140 && <button onClick={() => setAcik(!acik)}>{acik ? 'Daha az' : 'Devamı'}</button>}</div>
      )}
      <div style={{ marginTop: 'auto' }}>
        {acikTalep ? <div className="kc-talep-var">Talebin var: {acikTalep.durum_metni}</div>
          : <button className="btn" style={{ width: '100%', justifyContent: 'center' }} onClick={onTalep}>Görüşme talep et</button>}
      </div>
    </div>
  )
}

export default function KoclarSayfasi() {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  const [form, setForm] = useState(null)
  const [mesaj, setMesaj] = useState(null)
  const [filtre, setFiltre] = useState('hepsi')
  const yukle = () => api.koclar().then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.'))
  useEffect(() => { yukle() }, [])
  const iptal = async (t) => {
    if (!window.confirm('Bu görüşme talebini iptal etmek istiyor musun?')) return
    try { await api.kocTalebiIptal(t.id); yukle() } catch (e) { setMesaj({ hata: true, metin: e.detail || 'İptal edilemedi.' }) }
  }
  if (hata) return <div className="pg"><div className="auth-error">{hata}</div></div>
  if (!v) return <div className="pg"><div className="bos-durum">Yükleniyor…</div></div>
  const acikTalepler = Object.fromEntries(v.talepler.filter((t) => ['beklemede', 'onaylandi'].includes(t.durum)).map((t) => [t.koc_id, t]))
  const koclar = filtre === 'uygun' ? v.koclar.filter((k) => k.uygun) : v.koclar

  return (
    <div className="pg pg-genis">
      <div className="ph">
        <div className="pt">Uzman Koçlar</div>
        <div className="ps">Okulunun anlaşmalı eğitim koçlarıyla bölüm seçimi, çalışma planı ya da motivasyon üzerine birebir görüşebilirsin. Talebin önce rehber öğretmenine gider, görüşmeyi birlikte planlarlar.</div>
      </div>
      {mesaj && <div className={mesaj.hata ? 'auth-error' : 'yp-basari'} style={{ marginBottom: 12 }}>{mesaj.metin}</div>}

      {v.talepler.length > 0 && (
        <div className="card">
          <div className="ct">Görüşme taleplerim</div>
          <div className="kc-talepler">
            {v.talepler.map((t) => (
              <div key={t.id} className="kc-talep">
                <span className={`kc-durum kc-durum-${DURUM_RENK[t.durum] || 'tx3'}`}>{t.durum_metni}</span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <b>{t.koc_ad}</b> · {t.konu}{t.talep_eden === 'veli' && <span className="yp-ince"> (veli adına)</span>}
                  {t.randevu_zamani && t.durum === 'onaylandi' && <div className="kc-randevu">📅 {tarihSaat(t.randevu_zamani)}</div>}
                  {t.ogrenciye_not && <div className="yp-ince">Rehber öğretmenin notu: {t.ogrenciye_not}</div>}
                  <div className="yp-ince">Gönderildi: {new Date(t.olusturulma_zamani).toLocaleDateString('tr-TR')}</div>
                </div>
                {['beklemede', 'onaylandi'].includes(t.durum) && <button className="yp-mini" onClick={() => iptal(t)}>İptal et</button>}
              </div>
            ))}
          </div>
        </div>
      )}

      {v.koclar.length === 0 ? (
        <div className="card"><div className="bos-durum">Okulunun henüz anlaşmalı bir koçu yok. Rehber öğretmenine danışabilirsin.</div></div>
      ) : (
        <>
          <div className="kc-filtre">
            <button className={filtre === 'hepsi' ? 'aktif' : ''} onClick={() => setFiltre('hepsi')}>Tüm koçlar ({v.koclar.length})</button>
            <button className={filtre === 'uygun' ? 'aktif' : ''} onClick={() => setFiltre('uygun')} disabled={!v.ilgili_alanlar.length}
              title={v.ilgili_alanlar.length ? '' : 'Hedef bölüm seçtiğinde ya da Listem\'e bölüm eklediğinde açılır'}>
              İlgilendiğim alanlar ({v.koclar.filter((k) => k.uygun).length})
            </button>
            {v.ilgili_alanlar.length > 0 && <span className="yp-ince">Hedefin ve Listem'e göre: {v.ilgili_alanlar.slice(0, 4).join(', ')}</span>}
          </div>
          <div className="kc-grid">
            {koclar.map((k) => <KocKarti key={k.id} k={k} acikTalep={acikTalepler[k.id]} onTalep={() => setForm(k)} />)}
          </div>
        </>
      )}
      {!v.okul_var && <div className="yp-uyari" style={{ marginTop: 12 }}>Hesabın bir okula bağlı olmadığı için görüşme talebi gönderemezsin.</div>}
      {form && <TalepFormu koc={form} konular={v.konular} onKapat={() => setForm(null)}
        onGonderildi={() => { setForm(null); setMesaj({ metin: 'Talebin rehber öğretmenine iletildi. Durumunu bu sayfadan takip edebilirsin.' }); yukle() }} />}
    </div>
  )
}
