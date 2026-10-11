// [2026-10-10] İş Hayatı bileşenlerinin ortak biçimlendirme yardımcıları.
export const tl = (v) => (v == null ? '—' : `${Math.round(Number(v)).toLocaleString('tr-TR')} TL`)
export const yuzde = (v) => (v == null ? '—' : `%${Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 1 })}`)
export const ay = (v) => (v == null ? '—' : `${Number(v).toLocaleString('tr-TR', { maximumFractionDigits: 1 })} ay`)
export const KAZANC_GRUBU_RENK = { cok_yuksek: 'var(--gr)', yuksek: 'var(--gr)', orta: 'var(--pu)', dusuk: 'var(--am)', cok_dusuk: 'var(--re)' }
// Tahmin olan değerin yanına konacak etiket (veride tahmin: true olan her değer için zorunlu)
export function TahminEtiketi({ baslik = 'Tahmin: TÜİK ortalamasının güncel asgari ücrete oranlanmasıyla hesaplandı' }) {
  return <span title={baslik} style={{ fontSize: 10, fontWeight: 800, color: 'var(--am)', background: 'var(--aml)', padding: '1px 6px', borderRadius: 999, marginLeft: 4, whiteSpace: 'nowrap' }}>tahmini</span>
}
