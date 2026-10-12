// Frontend Türkçe arayüz metinlerini çıkarır → JSON {metin: [dosya,...]}
import fs from 'node:fs'
import path from 'node:path'
import { parse } from '@babel/parser'
import traverseMod from '@babel/traverse'
const traverse = traverseMod.default

const KOK = process.argv[2]
const CIKTI = process.argv[3]
const HARF = /\p{L}/u
const TR = /[çğıöşüÇĞİÖŞÜ]/
const BUYUK = /^[A-ZÇĞİÖŞÜ]/
const ATTR_RED = new Set(['className', 'class', 'id', 'key', 'href', 'to', 'src', 'type', 'name', 'role', 'style', 'htmlFor', 'value', 'method', 'target', 'rel', 'autoComplete', 'inputMode', 'pattern', 'd', 'viewBox', 'fill', 'stroke', 'kapsam', 'variant', 'mode', 'size', 'accept', 'lang', 'dir', 'xmlns', 'points', 'transform', 'textAnchor', 'strokeLinecap', 'strokeLinejoin', 'path', 'element', 'sekme', 'tip', 'tur', 'kod', 'renk', 'ikon', 'width', 'height', 'loading', 'download', 'enterKeyHint', 'capture', 'form', 'sandbox', 'allow', 'referrerPolicy', 'encType', 'wrap', 'spellCheck', 'dateTime'])
const CAGRI_RED = /^(localStorage|sessionStorage|document\.(querySelector|querySelectorAll|getElementById|createElement|addEventListener|removeEventListener)|window\.(addEventListener|removeEventListener|dispatchEvent|open)|console\.|.*\.classList\.|.*\.(setItem|getItem|removeItem|setAttribute|getAttribute|addEventListener|removeEventListener|querySelector|querySelectorAll|closest|matches|startsWith|endsWith|includes|split|replace|replaceAll|padStart|toLocaleDateString|toLocaleString|toLocaleTimeString|localeCompare)$|fetch|navigate|new Date|.*\.get$|.*\.post$|.*\.put$|.*\.patch$|.*\.delete$|istek|indir|dosyaIndir|.*\.append$|.*\.has$|.*\.set$|matchMedia|CustomEvent|Event|RegExp|Intl\..*|require)$/

const sonuc = new Map()
const ekle = (m, dosya, jsx = false) => {
  m = m.replace(/\s+/g, ' ').trim()
  if (!m || !HARF.test(m)) return
  if (m.length > 1500) return
  const harfsiz = m.replace(/\{\d+\}/g, '')
  if (!HARF.test(harfsiz)) return
  if (!jsx && /^[a-z0-9_\-./:#%?=&@]+$/i.test(m) && !TR.test(m) && !BUYUK.test(m)) return
  if (/^(https?:|mailto:|tel:|\/)/.test(m) && !/\s/.test(m)) return
  if (/var\(--|\d+px|^[a-z-]+:\s/.test(m) && !TR.test(m)) return
  if (!sonuc.has(m)) sonuc.set(m, new Set())
  sonuc.get(m).add(dosya)
}
const uygunString = (s) => HARF.test(s) && (/\s/.test(s.trim()) || TR.test(s) || BUYUK.test(s))

const jsxMetin = (raw) => {
  // JSX boşluk kuralı: satırlar kırpılır, boş olmayan satırlar boşlukla birleşir
  const satirlar = raw.split(/\r?\n/)
  if (satirlar.length === 1) return raw
  return satirlar.map((s, i) => {
    let x = s
    if (i !== 0) x = x.replace(/^\s+/, '')
    if (i !== satirlar.length - 1) x = x.replace(/\s+$/, '')
    return x
  }).filter(Boolean).join(' ')
}

const calleeAd = (n) => {
  if (!n) return ''
  if (n.type === 'Identifier') return n.name
  if (n.type === 'MemberExpression') return `${calleeAd(n.object)}.${n.property.name || n.property.value || ''}`
  if (n.type === 'ThisExpression') return 'this'
  if (n.type === 'CallExpression') return calleeAd(n.callee) + '()'
  return ''
}

function sablon(q, exprs) {
  let s = '', i = 0
  q.forEach((qq, k) => { s += qq.value.cooked ?? qq.value.raw; if (k < exprs.length) s += `{${i++}}` })
  return s
}

function dosyaIsle(dosya) {
  const kod = fs.readFileSync(dosya, 'utf8')
  const rel = path.relative(KOK, dosya)
  let ast
  try { ast = parse(kod, { sourceType: 'module', plugins: ['jsx'] }) } catch (e) { console.error('PARSE', rel, e.message); return }
  traverse(ast, {
    JSXText(p) { const m = jsxMetin(p.node.value); if (m.trim()) ekle(m, rel, true) },
    JSXElement(p) {
      // Karışık çocuklar (metin + ifade, eleman yok) → kalıp
      const c = p.node.children
      if (c.length < 2) return
      if (!c.every((x) => x.type === 'JSXText' || (x.type === 'JSXExpressionContainer' && x.expression.type !== 'JSXEmptyExpression'))) return
      if (!c.some((x) => x.type === 'JSXText' && HARF.test(x.value))) return
      let s = '', i = 0
      for (const x of c) {
        if (x.type === 'JSXText') s += jsxMetin(x.value)
        else if (x.expression.type === 'StringLiteral') s += x.expression.value
        else s += `{${i++}}`
      }
      ekle(s, rel)
    },
    JSXAttribute(p) {
      const ad = p.node.name.name
      const v = p.node.value
      if (typeof ad !== 'string' || ATTR_RED.has(ad) || ad.startsWith('data-') || ad.startsWith('on')) { p.skip(); return }
      if (v && v.type === 'StringLiteral') { if (HARF.test(v.value)) ekle(v.value, rel) }
    },
    StringLiteral(p) {
      const par = p.parent
      if (par.type === 'ImportDeclaration' || par.type === 'ExportNamedDeclaration' || par.type === 'ExportAllDeclaration') return
      if (par.type === 'JSXAttribute') return
      if (par.type === 'ObjectProperty' && par.key === p.node && !par.computed) return
      if (par.type === 'CallExpression' && CAGRI_RED.test(calleeAd(par.callee))) return
      if (par.type === 'BinaryExpression' && ['===', '!==', '==', '!=', 'in'].includes(par.operator)) return
      if (par.type === 'SwitchCase') return
      if (par.type === 'MemberExpression') return
      // className={...'x'...}
      const jsxA = p.findParent((x) => x.isJSXAttribute())
      if (jsxA && (ATTR_RED.has(jsxA.node.name.name) || String(jsxA.node.name.name).startsWith('data-'))) return
      if (uygunString(p.node.value)) ekle(p.node.value, rel)
    },
    TemplateLiteral(p) {
      const par = p.parent
      if (par.type === 'TaggedTemplateExpression') return
      if (par.type === 'CallExpression' && CAGRI_RED.test(calleeAd(par.callee))) return
      const jsxA = p.findParent((x) => x.isJSXAttribute())
      if (jsxA && (ATTR_RED.has(jsxA.node.name.name) || String(jsxA.node.name.name).startsWith('data-'))) return
      const s = sablon(p.node.quasis, p.node.expressions)
      const sabit = p.node.quasis.map((q) => q.value.cooked ?? '').join(' ')
      if (uygunString(sabit) && /\p{L}{2,}/u.test(sabit)) ekle(s, rel)
    },
  })
}

function gez(d) {
  for (const f of fs.readdirSync(d)) {
    const t = path.join(d, f)
    if (fs.statSync(t).isDirectory()) gez(t)
    else if (/\.(jsx?|mjs)$/.test(f) && !/yardimci[\\/]dil\.js$/.test(t)) dosyaIsle(t)   // çeviri katmanının kendi kodu hariç
  }
}
gez(KOK)
const cikti = {}
for (const [m, s] of [...sonuc.entries()].sort()) cikti[m] = [...s]
fs.writeFileSync(CIKTI, JSON.stringify(cikti, null, 0))
const top = [...sonuc.keys()].reduce((a, b) => a + b.length, 0)
console.log('metin', sonuc.size, 'karakter', top)
