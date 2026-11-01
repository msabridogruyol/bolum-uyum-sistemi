// [2026-10-31] Filiz (backend) ana sözlüğü Sözlük sayfasıyla aynı kaynaktan okusun: frontend/src/yardimci/sozluk.js
// içindeki SOZLUK ve GRUPLAR → backend/app/data/sozluk_temel.json. sozluk.js değişince bu betik çalıştırılır;
// backend/tests/test_coklu_dil.py iki kopyanın aynı olduğunu denetler.
import { writeFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { SOZLUK, GRUPLAR } from '../frontend/src/yardimci/sozluk.js'

const hedef = fileURLToPath(new URL('../backend/app/data/sozluk_temel.json', import.meta.url))
const terimler = SOZLUK.map(({ k, ad, g, t, o, es }) => ({ k, ad, g, t, ...(o ? { o } : {}), es: es || [] }))
writeFileSync(hedef, JSON.stringify({ gruplar: GRUPLAR, terimler }, null, 1) + '\n')
console.log(`${terimler.length} terim → ${hedef}`)
