// [2026-11-11] Yayındaki bölüm adları (yazarken öneri listesi). Oturum boyunca bir kez yüklenir; hata olursa sonraki çağrıda yeniden denenir.
import { useEffect, useState } from 'react'
import { api } from '../api/client'

let bekleyen = null
export function bolumAdlariGetir() {
  if (!bekleyen) bekleyen = api.bolumAdlari().catch((e) => { bekleyen = null; throw e })
  return bekleyen
}

/** [{ id, ad }] ya da yüklenene kadar [] */
export function useBolumAdlari() {
  const [l, setL] = useState([])
  useEffect(() => { let iptal = false; bolumAdlariGetir().then((x) => { if (!iptal) setL(x || []) }).catch(() => {}); return () => { iptal = true } }, [])
  return l
}
