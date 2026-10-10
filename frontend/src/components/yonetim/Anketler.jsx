// [2026-10-10] Anket ve envanterler: liste, şablondan / boş anket, soru düzenleyici, yayınla / kapat, sonuçlar.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { Pencere } from './ortak'

const SINIFLAR = ['9. Sınıf', '10. Sınıf', '11. Sınıf', '12. Sınıf', 'Mezun']
const AY = ['Oca', 'Şub', 'Mar', 'Nis', 'May', 'Haz', 'Tem', 'Ağu', 'Eyl', 'Eki', 'Kas', 'Ara']
const kisaTarih = (t) => { if (!t) return ''; const d = new Date(`${t}T12:00`); return `${d.getDate()} ${AY[d.getMonth()]}` }
// Likert dağılımı: iki uç (katılmıyorum ↔ katılıyorum) + gri orta
export const LIKERT_RENK = ['#c8553d', '#e7a58f', '#c9c3b8', '#93b6e3', '#2a78d6']
// Seviye rengi yöne göre: destek gerektiren uç kırmızı, orta amber, iyi uç yeşil
const seviyeRengi = (yon, kod) => kod === 'orta' ? 'var(--eu-orta, #b7791f)'
  : kod === (yon === 'yuksek_kotu' ? 'yuksek' : 'dusuk') ? 'var(--eu-yuksek, #c0392b)' : 'var(--gr)'
const SABLON_IKON = { sinav_kaygisi: '😰', calisma_aliskanliklari: '📚', okul_iklimi: '🏫', kariyer_kararliligi: '🧭', rehberlik_memnuniyet: '💬' }
const hedefMetni = (h) => {
  const s = [...(h?.siniflar || []), ...(h?.subeler || []).map((x) => x.replace('|', '-').replace('. Sınıf', ''))]
  return s.length ? s.join(', ') : 'Tüm okul'
}

// ----------------------------------------------------------------------------- düzenleyici
function Duzenleyici({ okulId, kaynak, mevcut, turler, onKapat, onKaydet }) {
  const [f, setF] = useState(() => mevcut
    ? { baslik: mevcut.baslik, aciklama: mevcut.aciklama || '', anonim: mevcut.anonim, siniflar: mevcut.hedef?.siniflar || [], bitis: mevcut.bitis || '', sorular: mevcut.sorular, sablon: mevcut.sablon }
    : kaynak
      ? { baslik: kaynak.baslik, aciklama: kaynak.aciklama, anonim: kaynak.anonim, siniflar: [], bitis: '', sorular: kaynak.sorular.map((s) => ({ ...s, secenekler: s.secenekler || [] })), sablon: kaynak.kod }
      : { baslik: '', aciklama: '', anonim: true, siniflar: [], bitis: '', sorular: [{ metin: '', tur: 'likert', secenekler: [], zorunlu: true }], sablon: null })
  const [hata, setHata] = useState(null)
  const [bekle, setBekle] = useState(false)
  const kilitli = mevcut && mevcut.katilim > 0
  const soru = (i, ek) => setF({ ...f, sorular: f.sorular.map((s, j) => (j === i ? { ...s, ...ek } : s)) })
  const tasi = (i, d) => { const l = [...f.sorular]; const [x] = l.splice(i, 1); l.splice(i + d, 0, x); setF({ ...f, sorular: l }) }
  async function kaydet() {
    setBekle(true); setHata(null)
    const veri = { baslik: f.baslik, aciklama: f.aciklama || null, sablon: f.sablon, anonim: f.anonim, hedef: { siniflar: f.siniflar }, bitis: f.bitis || null,
      sorular: f.sorular.map((s) => ({ id: s.id, metin: s.metin, tur: s.tur, secenekler: s.secenekler || [], zorunlu: s.zorunlu, ters: !!s.ters })) }
    try { if (mevcut) await api.anketDuzenle(mevcut.id, veri); else await api.anketOlustur(okulId, veri); onKaydet() } catch (e) { setHata(e.detail || 'Kaydedilemedi.') } finally { setBekle(false) }
  }
  return (
    <Pencere genis baslik={mevcut ? 'Anketi düzenle' : 'Yeni anket'} altBaslik={f.sablon ? 'Hazır şablondan — maddeleri okulunuza göre değiştirebilirsiniz' : null} onKapat={onKapat}
      alt={<><button className="btn sec" onClick={onKapat}>Vazgeç</button><button className="btn" disabled={bekle || f.baslik.trim().length < 3} onClick={kaydet}>{bekle ? <span className="spin" /> : 'Taslak olarak kaydet'}</button></>}>
      {kilitli && <div className="yp-uyari" style={{ marginBottom: 10 }}>Bu ankete yanıt geldi; sorular ve anonimlik artık değiştirilemez. Başlık, açıklama, hedef ve bitiş tarihini değiştirebilirsiniz.</div>}
      <div className="an-alanlar">
        <label className="genis"><span>Başlık</span><input className="auth-input" maxLength={120} value={f.baslik} onChange={(e) => setF({ ...f, baslik: e.target.value })} /></label>
        <label className="genis"><span>Öğrenciye açıklama</span><textarea className="auth-input" rows={2} maxLength={1000} value={f.aciklama} onChange={(e) => setF({ ...f, aciklama: e.target.value })} /></label>
        <div className="genis">
          <span className="an-etiket">Kimler yanıtlasın?</span>
          <div className="an-siniflar">
            <label className={!f.siniflar.length ? 'secili' : ''}><input type="checkbox" checked={!f.siniflar.length} onChange={() => setF({ ...f, siniflar: [] })} />Tüm okul</label>
            {SINIFLAR.map((s) => (
              <label key={s} className={f.siniflar.includes(s) ? 'secili' : ''}>
                <input type="checkbox" checked={f.siniflar.includes(s)} onChange={() => setF({ ...f, siniflar: f.siniflar.includes(s) ? f.siniflar.filter((x) => x !== s) : [...f.siniflar, s] })} />{s}
              </label>
            ))}
          </div>
        </div>
        <label><span>Son yanıt tarihi <small>(isteğe bağlı)</small></span><input className="auth-input" type="date" value={f.bitis} onChange={(e) => setF({ ...f, bitis: e.target.value })} /></label>
        <label className="an-anonim">
          <input type="checkbox" checked={f.anonim} disabled={kilitli} onChange={(e) => setF({ ...f, anonim: e.target.checked })} />
          <span><b>Anonim</b><small>{f.anonim ? 'Yanıtlar öğrenci adıyla eşleştirilmez; sonuçlar en az 5 yanıt gelince ve 5 kişiden küçük sınıflar birleştirilerek görünür.' : 'Yanıtlar öğrenci adıyla görünür; tarama formlarında öğrenci kendi sonucunu görür ve destek gerekenler Erken uyarı listesine düşer.'}</small></span>
        </label>
      </div>
      <div className="an-etiket" style={{ marginTop: 14 }}>Sorular ({f.sorular.length})</div>
      {f.sorular.map((s, i) => (
        <div key={i} className="an-soru">
          <span className="an-no">{i + 1}</span>
          <div style={{ flex: 1, minWidth: 0, display: 'grid', gap: 6 }}>
            <input className="auth-input" maxLength={300} disabled={kilitli} placeholder="Soru metni" value={s.metin} onChange={(e) => soru(i, { metin: e.target.value })} />
            <div className="an-soru-alt">
              <select className="auth-input" disabled={kilitli} value={s.tur} onChange={(e) => soru(i, { tur: e.target.value })}>{Object.entries(turler).map(([k, ad]) => <option key={k} value={k}>{ad}</option>)}</select>
              {s.tur !== 'acik' && <label><input type="checkbox" disabled={kilitli} checked={s.zorunlu} onChange={(e) => soru(i, { zorunlu: e.target.checked })} /> Zorunlu</label>}
              {s.tur === 'likert' && f.sablon && <label title="Olumlu ifadeli madde: puanlamada ters çevrilir"><input type="checkbox" disabled={kilitli} checked={!!s.ters} onChange={(e) => soru(i, { ters: e.target.checked })} /> Ters puanlanır</label>}
            </div>
            {['tek', 'coklu'].includes(s.tur) && (
              <textarea className="auth-input" rows={3} disabled={kilitli} placeholder="Her satıra bir seçenek" value={(s.secenekler || []).join('\n')} onChange={(e) => soru(i, { secenekler: e.target.value.split('\n') })} />
            )}
          </div>
          {!kilitli && (
            <div className="an-soru-islem">
              <button className="yp-mini" disabled={i === 0} onClick={() => tasi(i, -1)} aria-label="Yukarı">↑</button>
              <button className="yp-mini" disabled={i === f.sorular.length - 1} onClick={() => tasi(i, 1)} aria-label="Aşağı">↓</button>
              <button className="yp-mini" onClick={() => setF({ ...f, sorular: f.sorular.filter((_, j) => j !== i) })} aria-label="Sil">×</button>
            </div>
          )}
        </div>
      ))}
      {!kilitli && <button className="hg-link" onClick={() => setF({ ...f, sorular: [...f.sorular, { metin: '', tur: 'likert', secenekler: [], zorunlu: true }] })}>+ Soru ekle</button>}
      {hata && <div className="auth-error" style={{ marginTop: 10 }}>{hata}</div>}
    </Pencere>
  )
}

// ----------------------------------------------------------------------------- sonuçlar
function Sonuclar({ id, onKapat }) {
  const [v, setV] = useState(null)
  const [hata, setHata] = useState(null)
  useEffect(() => { api.anketSonuclari(id).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')) }, [id])
  if (!v) return <Pencere baslik="Sonuçlar" onKapat={onKapat}><div className="bos-durum">{hata || 'Yükleniyor…'}</div></Pencere>
  const a = v.anket
  const env = v.envanter
  const enCok = (l) => Math.max(1, ...l)
  return (
    <Pencere genis baslik={a.baslik} altBaslik={`${a.katilim} / ${a.hedef_sayisi} öğrenci yanıtladı · ${a.anonim ? 'Anonim' : 'İsimli'} · ${hedefMetni(a.hedef)}`} onKapat={onKapat}
      alt={<><button className="btn sec" style={{ marginRight: 'auto' }} disabled={v.gizli} onClick={() => api.anketExcel(id).catch((e) => setHata(e.detail || 'İndirilemedi.'))}>📊 Excel</button><button className="btn" onClick={onKapat}>Kapat</button></>}>
      {hata && <div className="auth-error">{hata}</div>}
      {v.toplam === 0 && <div className="bos-durum">Henüz yanıt yok.</div>}
      {v.gizli && v.toplam > 0 && <div className="bos-durum">🔒 Anonimliği korumak için sonuçlar en az {v.esik} yanıt gelince görünür. Şu an {v.toplam} yanıt var.</div>}
      {env && v.toplam > 0 && (
        <div className="yp-iki" style={{ marginBottom: 14 }}>
          <div className="yp-kutu">
            <div className="ct">Seviye dağılımı · ortalama {env.ortalama?.toLocaleString('tr-TR')} / 5</div>
            {env.seviyeler.map((s) => (
              <div key={s.kod} className="od-cubuk-satir">
                <span>{s.ad}</span>
                <div className="nt-cubuk"><div style={{ width: `${(100 * s.sayi) / Math.max(1, v.toplam)}%`, background: seviyeRengi(env.yon, s.kod) }} /></div>
                <b>{s.sayi}</b><span className="yp-ince">%{Math.round((100 * s.sayi) / Math.max(1, v.toplam))}</span>
              </div>
            ))}
            <div className="yp-ince" style={{ marginTop: 6 }}>{env.yon === 'yuksek_kotu' ? 'Yüksek puan destek ihtiyacını gösterir.' : 'Düşük puan destek ihtiyacını gösterir.'} Bu bir tarama sonucudur, tanı değildir.</div>
          </div>
          <div className="yp-kutu">
            <div className="ct">Sınıflara göre ortalama</div>
            {env.siniflar.map((s) => (
              <div key={s.sinif} className="od-cubuk-satir">
                <span>{s.sinif} <small className="yp-ince">({s.sayi})</small></span>
                <div className="nt-cubuk"><div style={{ width: `${(100 * (s.ortalama - 1)) / 4}%`, background: 'var(--kt-izleme, #2a78d6)' }} /></div>
                <b>{s.ortalama.toLocaleString('tr-TR')}</b><span />
              </div>
            ))}
          </div>
        </div>
      )}
      {v.ogrenciler && v.ogrenciler.length > 0 && (
        <div className="yp-kutu" style={{ marginBottom: 14 }}>
          <div className="ct">Öğrenciler {v.ogrenciler.some((o) => o.destek) && <span className="eu-cip yuksek" style={{ marginLeft: 6 }}>▲ {v.ogrenciler.filter((o) => o.destek).length} öğrenci destek gerektirebilir</span>}</div>
          <div className="an-ogrenciler">
            {v.ogrenciler.map((o, i) => (
              <div key={i} className={`an-ogr${o.destek ? ' destek' : ''}`}>
                <span>{o.ad_soyad} <small className="yp-ince">{o.sinif}</small></span>
                <span className="eu-cip" style={{ color: seviyeRengi(env?.yon, o.seviye), background: 'var(--sur2)' }}>{o.destek ? '▲ ' : ''}{(env?.seviyeler.find((s) => s.kod === o.seviye) || {}).ad || '—'} · {o.puan?.toLocaleString('tr-TR')}</span>
              </div>
            ))}
          </div>
          <div className="yp-ince" style={{ marginTop: 6 }}>Destek gerektiren sonuçlar Rehberlik → Erken uyarı listesinde de görünür.</div>
        </div>
      )}
      {v.toplam > 0 && v.sorular.some((s) => s.tur === 'likert') && (
        <div className="an-lejant">{['Hiç katılmıyorum', 'Katılmıyorum', 'Kararsızım', 'Katılıyorum', 'Tamamen katılıyorum'].map((e, i) => <span key={e}><i style={{ background: LIKERT_RENK[i] }} />{e}</span>)}</div>
      )}
      {v.toplam > 0 && v.sorular.map((s, i) => (
        <div key={s.id} className="an-sonuc">
          <div className="an-sonuc-ust"><b>{i + 1}. {s.metin}</b><span className="yp-ince">{s.yanit} yanıt{s.ortalama != null ? ` · ort. ${s.ortalama.toLocaleString('tr-TR')}` : ''}{s.ters ? ' · ters madde' : ''}</span></div>
          {s.tur === 'likert' && (
            <div className="an-yigin" role="img" aria-label={s.dagilim.map((n, k) => `${s.etiketler[k]}: ${n}`).join(', ')}>
              {s.dagilim.map((n, k) => n > 0 && <div key={k} style={{ flex: n, background: LIKERT_RENK[k] }} title={`${s.etiketler[k]}: ${n} (%${Math.round((100 * n) / Math.max(1, s.yanit))})`}>{(100 * n) / Math.max(1, s.yanit) >= 9 ? `%${Math.round((100 * n) / s.yanit)}` : ''}</div>)}
            </div>
          )}
          {['tek', 'coklu', 'puan'].includes(s.tur) && s.dagilim.map((n, k) => (
            <div key={k} className="od-cubuk-satir">
              <span title={s.etiketler[k]}>{s.etiketler[k]}</span>
              <div className="nt-cubuk"><div style={{ width: `${(100 * n) / enCok(s.dagilim)}%`, background: 'var(--kt-izleme, #2a78d6)' }} /></div>
              <b>{n}</b><span />
            </div>
          ))}
          {s.tur === 'acik' && (s.metinler?.length ? <ul className="an-metinler">{s.metinler.map((m, k) => <li key={k}>{m}</li>)}</ul> : <div className="yp-ince">Yanıt yok.</div>)}
        </div>
      ))}
    </Pencere>
  )
}

// ----------------------------------------------------------------------------- bölüm
export default function Anketler({ okulId }) {
  const [v, setV] = useState(null)
  const [sablon, setSablon] = useState(null)
  const [secim, setSecim] = useState(false)
  const [duzen, setDuzen] = useState(null)   // { kaynak } | { mevcut }
  const [sonuc, setSonuc] = useState(null)
  const [silOnay, setSilOnay] = useState(null)
  const [hata, setHata] = useState(null)
  const yenile = useCallback(() => api.okulAnketleri(okulId).then(setV).catch((e) => setHata(e.detail || 'Yüklenemedi.')), [okulId])
  useEffect(() => { yenile(); api.anketSablonlari().then(setSablon).catch(() => {}) }, [yenile])
  async function islem(f) { setHata(null); try { await f(); yenile() } catch (e) { setHata(e.detail || 'İşlem yapılamadı.') } }
  async function duzenle(a) { try { setDuzen({ mevcut: await api.anket(a.id) }) } catch (e) { setHata(e.detail || 'Açılamadı.') } }
  if (!v || !sablon) return <div className="bos-durum">{hata || 'Yükleniyor…'}</div>
  return (
    <>
      <div className="rh-ust">
        <div className="yp-ince" style={{ maxWidth: 720, lineHeight: 1.6 }}>Öğrencilere anket gönderin ya da hazır tarama formlarını kullanın. Taslak olarak kaydedip <b>Yayınla</b> dediğinizde öğrencilere bildirim gider.</div>
        <button className="btn" onClick={() => setSecim(!secim)}>+ Yeni anket</button>
      </div>
      {hata && <div className="auth-error">{hata}</div>}
      {secim && (
        <div className="card">
          <div className="ct">Nereden başlayalım?</div>
          <div className="an-sablonlar">
            {sablon.sablonlar.map((s) => (
              <button key={s.kod} className="an-sablon" onClick={() => { setDuzen({ kaynak: s }); setSecim(false) }}>
                <span className="an-sablon-ikon" aria-hidden="true">{SABLON_IKON[s.kod] || '📋'}</span>
                <b>{s.baslik}</b>
                <small>{s.sorular.length} soru · {s.anonim ? 'anonim' : 'isimli'}{s.puanlama ? ' · puanlanır' : ''}</small>
              </button>
            ))}
            <button className="an-sablon bos" onClick={() => { setDuzen({}); setSecim(false) }}><span className="an-sablon-ikon">✏️</span><b>Boş anket</b><small>Kendi sorularınızı yazın</small></button>
          </div>
          <div className="yp-ince" style={{ marginTop: 10 }}>Tarama formlarının maddeleri Filizyol için yazılmıştır; tanı koymaz, rehberlik görüşmesine yön vermek içindir.</div>
        </div>
      )}
      {v.anketler.length === 0 && !secim ? <div className="card bos-durum">Henüz anket yok.</div> : (
        <div className="an-liste">
          {v.anketler.map((a) => (
            <div key={a.id} className="card an-kart">
              <div className="an-kart-ust">
                <b>{a.baslik}</b>
                <span className={`an-durum ${a.durum}`}>{a.durum === 'yayinda' && !a.acik ? 'Süresi doldu' : a.durum_adi}</span>
                {a.anonim ? <span className="gs-etiket">Anonim</span> : <span className="gs-etiket">İsimli</span>}
                {a.envanter && <span className="gs-etiket konu">Tarama</span>}
              </div>
              <div className="yp-ince">{hedefMetni(a.hedef)} · {a.soru_sayisi} soru{a.bitis ? ` · son gün ${kisaTarih(a.bitis)}` : ''} · {a.olusturan}</div>
              <div className="an-katilim">
                <div className="nt-cubuk" style={{ flex: 1 }}><div style={{ width: `${(100 * a.katilim) / Math.max(1, a.hedef_sayisi)}%`, background: 'var(--gr)' }} /></div>
                <span><b>{a.katilim}</b> / {a.hedef_sayisi} yanıt</span>
              </div>
              <div className="an-islem">
                {a.katilim > 0 && <button className="yp-mini" onClick={() => setSonuc(a.id)}>📊 Sonuçlar</button>}
                {a.durum === 'taslak' && a.hedef_sayisi < 5 && <span className="yp-ince" title="Anketler en az 5 öğrenciye gönderilir">Hedef 5 kişiden az</span>}
                {a.durum === 'taslak' && a.hedef_sayisi >= 5 && <button className="yp-mini pf-onayla" onClick={() => islem(() => api.anketDurum(a.id, 'yayinda'))}>▶ Yayınla</button>}
                {a.durum === 'yayinda' && <button className="yp-mini" onClick={() => islem(() => api.anketDurum(a.id, 'kapandi'))}>■ Kapat</button>}
                {a.durum === 'kapandi' && <button className="yp-mini" onClick={() => islem(() => api.anketDurum(a.id, 'yayinda'))}>Yeniden aç</button>}
                <button className="yp-mini" onClick={() => duzenle(a)}>✎ Düzenle</button>
                {silOnay === a.id
                  ? <><button className="yp-mini yp-tehlike" onClick={() => { setSilOnay(null); islem(() => api.anketSil(a.id)) }}>Yanıtlarıyla sil</button><button className="yp-mini" onClick={() => setSilOnay(null)}>×</button></>
                  : <button className="yp-mini" onClick={() => setSilOnay(a.id)}>🗑</button>}
              </div>
            </div>
          ))}
        </div>
      )}
      {duzen && <Duzenleyici okulId={okulId} {...duzen} turler={sablon.soru_turleri} onKapat={() => setDuzen(null)} onKaydet={() => { setDuzen(null); yenile() }} />}
      {sonuc && <Sonuclar id={sonuc} onKapat={() => setSonuc(null)} />}
    </>
  )
}
