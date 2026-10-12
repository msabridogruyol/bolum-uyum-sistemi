"""Backend kullanıcıya görünen Türkçe metinleri çıkarır (HTTPException detail, yanıt sözlükleri, f-string kalıpları)."""
import ast, json, re, sys, pathlib

KOK = pathlib.Path(sys.argv[1])
CIKTI = sys.argv[2]
TR = re.compile(r"[çğıöşüÇĞİÖŞÜ]")
HARF = re.compile(r"[^\W\d_]")
ATLA_DOSYA = {"ai_koc_servisi.py", "filiz_yonetim_ai.py", "sema_guncelleme.py", "canli_denetim.py"}
ATLA_CAGRI = re.compile(r"(logger|log|logging)\.|text$|execute$|getenv|environ|re\.|compile|startswith|endswith|split|replace|strftime|strptime|encode|decode|join$|Column|ForeignKey|relationship|Index|index|alias|label|filter|order_by|setdefault|get$|pop$|open$|__import__|import_module|Path|uuid|hashlib|hmac")
sonuc = {}

def ekle(m, dosya):
    m = re.sub(r"\s+", " ", m).strip()
    if not m or len(m) > 600 or not HARF.search(re.sub(r"\{\d+\}", "", m)):
        return
    if not (TR.search(m) or " " in m or m[:1].isupper()):
        return
    if re.fullmatch(r"[a-z0-9_\-./:#%?=&@{}]+", m, re.I) and not TR.search(m):
        return
    if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|WHERE|CREATE|ALTER|JOIN)\b", m):
        return
    sonuc.setdefault(m, set()).add(dosya)

def cagri_ad(n):
    if isinstance(n, ast.Name): return n.id
    if isinstance(n, ast.Attribute): return f"{cagri_ad(n.value)}.{n.attr}"
    if isinstance(n, ast.Call): return cagri_ad(n.func) + "()"
    return ""

for f in sorted(KOK.rglob("*.py")):
    if f.name in ATLA_DOSYA or "/models/" in str(f) or "__pycache__" in str(f):
        continue
    kod = f.read_text("utf8")
    agac = ast.parse(kod)
    ebeveyn = {}
    for d in ast.walk(agac):
        for c in ast.iter_child_nodes(d):
            ebeveyn[c] = d
    rel = str(f.relative_to(KOK))
    for d in ast.walk(agac):
        if isinstance(d, ast.JoinedStr):
            par = ebeveyn.get(d)
            if isinstance(par, ast.Call) and ATLA_CAGRI.search(cagri_ad(par.func)):
                continue
            s, i = "", 0
            for v in d.values:
                if isinstance(v, ast.Constant): s += str(v.value)
                else: s += "{%d}" % i; i += 1
            sabit = "".join(str(v.value) for v in d.values if isinstance(v, ast.Constant))
            if TR.search(sabit) or (" " in sabit.strip() and re.search(r"[^\W\d_]{3,}", sabit)):
                ekle(s, rel)
        elif isinstance(d, ast.Constant) and isinstance(d.value, str):
            par = ebeveyn.get(d)
            if isinstance(par, ast.JoinedStr):
                continue
            if isinstance(par, ast.Expr):  # docstring
                continue
            if isinstance(par, ast.Call) and ATLA_CAGRI.search(cagri_ad(par.func)):
                continue
            if isinstance(par, ast.Dict) and d in par.keys:
                continue
            if isinstance(par, ast.Compare) or isinstance(par, ast.Subscript):
                continue
            if isinstance(par, ast.keyword) and par.arg in ("primary_key", "server_default", "name", "default", "tags", "prefix", "media_type", "pattern", "regex", "alias"):
                continue
            ekle(d.value, rel)

cikti = {m: sorted(s) for m, s in sorted(sonuc.items())}
json.dump(cikti, open(CIKTI, "w"), ensure_ascii=False)
print("metin", len(cikti), "karakter", sum(len(m) for m in cikti))
