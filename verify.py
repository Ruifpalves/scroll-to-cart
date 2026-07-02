#!/usr/bin/env python3
"""Verificacao real do repo scroll-to-cart. Output binario: PASS/FAIL por check."""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
fails = []

def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name}" + (f" -> {detail}" if detail else ""))
    if not ok:
        fails.append(name)

# 1. Estrutura obrigatoria
required = ["SKILL.md", "README.md", "LICENSE",
            "templates/01-contexto-produto.md", "templates/02-referencias.md"]
for f in required:
    check(f"existe {f}", os.path.isfile(os.path.join(ROOT, f)))

# 2. Frontmatter YAML do SKILL.md
skill = open(os.path.join(ROOT, "SKILL.md"), encoding="utf-8").read()
m = re.match(r"^---\n(.*?)\n---\n", skill, re.DOTALL)
check("SKILL.md tem frontmatter", bool(m))
if m:
    fm = m.group(1)
    try:
        import yaml
        data = yaml.safe_load(fm)
        check("frontmatter YAML parseia", isinstance(data, dict))
        check("campo name presente", bool(data.get("name")))
        check("name em formato slug", bool(re.fullmatch(r"[a-z0-9-]+", str(data.get("name","")))),
              str(data.get("name")))
        check("campo description presente", bool(data.get("description")))
        check("description >= 40 chars", len(str(data.get("description",""))) >= 40)
        check("name == nome da pasta", data.get("name") == os.path.basename(ROOT), os.path.basename(ROOT))
    except ImportError:
        # parser minimo sem pyyaml
        keys = dict(re.findall(r"^(\w+):", fm, re.MULTILINE) and
                    [(k, True) for k in re.findall(r"^(\w+):", fm, re.MULTILINE)])
        check("campo name presente", "name" in keys)
        check("campo description presente", "description" in keys)

# 3. Links internos relativos resolvem
md_files = []
for dp, _, fns in os.walk(ROOT):
    for fn in fns:
        if fn.endswith(".md"):
            md_files.append(os.path.join(dp, fn))
link_re = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
broken = []
for mf in md_files:
    base = os.path.dirname(mf)
    for link in link_re.findall(open(mf, encoding="utf-8").read()):
        if link.startswith(("http://", "https://", "#", "mailto:")):
            continue
        target = os.path.normpath(os.path.join(base, link.split("#")[0]))
        if not os.path.exists(target):
            broken.append(f"{os.path.relpath(mf,ROOT)} -> {link}")
check("links internos resolvem", not broken, "; ".join(broken))

# 4. Sem residuos da marca antiga
leftovers = []
for mf in md_files:
    if re.search(r"helpai", open(mf, encoding="utf-8").read(), re.IGNORECASE):
        leftovers.append(os.path.relpath(mf, ROOT))
check("sem residuos 'helpai'", not leftovers, "; ".join(leftovers))

# 5. Marca datascript.ch presente no README e SKILL
for f in ["README.md", "SKILL.md"]:
    txt = open(os.path.join(ROOT, f), encoding="utf-8").read()
    check(f"datascript.ch referida em {f}", "datascript.ch" in txt)

# 6. Sem em-dash (regra de estilo do cliente)
emdash = [os.path.relpath(mf,ROOT) for mf in md_files if "\u2014" in open(mf,encoding="utf-8").read()]
check("sem em-dashes (\u2014)", not emdash, "; ".join(emdash))

print("\n" + ("VERIFICACAO PASSOU LIMPA" if not fails else f"FALHAS: {fails}"))
sys.exit(1 if fails else 0)
