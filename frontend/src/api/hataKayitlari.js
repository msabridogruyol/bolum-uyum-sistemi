// [2026-10-11] Hata Kayıtları (süper admin) — ortak client.js'e dokunmamak için ayrı küçük istemci.
import { api } from './client'

async function istek(yol, secenekler = {}) {
  const token = api.tokenAl('admin')
  const headers = { 'Content-Type': 'application/json', ...(token ? { Authorization: `Bearer ${token}` } : {}) }
  const yanit = await fetch(`/api${yol}`, { ...secenekler, headers })
  const metin = await yanit.text()
  let govde = null
  try { govde = metin ? JSON.parse(metin) : null } catch { govde = metin }
  if (!yanit.ok) throw new api.ApiHatasi(yanit.status, govde && typeof govde === 'object' ? govde.detail : govde)
  return govde
}

export const hataKayitlariApi = {
  listele: (f = {}) => istek(`/admin/hata-kayitlari?${new URLSearchParams(Object.entries(f).filter(([, v]) => v)).toString()}`),
  ayrinti: (id) => istek(`/admin/hata-kayitlari/${id}`),
  cozuldu: (id, cozuldu = true) => istek(`/admin/hata-kayitlari/${id}/cozuldu`, { method: 'POST', body: JSON.stringify({ cozuldu }) }),
  temizle: (kapsam) => istek(`/admin/hata-kayitlari?kapsam=${kapsam}`, { method: 'DELETE' }),
}
