#!/usr/bin/env python3
"""Vídeo promocional do imovelfilme, feito com o próprio motor (HyperFrames) e o resultado do anúncio-demo.

  python3 promo/promo.py            → promo/output/promo-imovelfilme.mp4

Precisa do projeto-demo pronto em projetos/demo (extrair → fotos → brief → video).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
sys.path.insert(0, str(RAIZ))
from engine import video  # noqa: E402

DEMO = RAIZ / "projetos" / "demo"
XF = 0.5

CSS_EXTRA = """
.escuro{background:#0c0c10}
.kick{font:700 calc(28*var(--u))/1 Inter,sans-serif;letter-spacing:.22em;color:#FACC15}
.tit{font:800 calc(76*var(--u))/1.05 Sora,sans-serif;margin:calc(14*var(--u)) 0 0;max-width:20ch;text-wrap:balance}
.topo{position:absolute;left:calc(96*var(--u));top:calc(70*var(--u))}
.janela{position:absolute;left:calc(560*var(--u));right:calc(96*var(--u));top:calc(250*var(--u));bottom:0;border-radius:calc(16*var(--u)) calc(16*var(--u)) 0 0;overflow:hidden;background:#fff;border:1px solid #2a2a33}
.barra-nav{height:calc(64*var(--u));background:#1d1d24;display:flex;align-items:center;gap:calc(12*var(--u));padding:0 calc(22*var(--u))}
.ponto{width:calc(16*var(--u));height:calc(16*var(--u));border-radius:50%;background:#3a3a44}
.url{flex:1;margin-left:calc(18*var(--u));height:calc(40*var(--u));border-radius:999px;background:#0c0c10;color:#e8e8ee;font:400 calc(24*var(--u))/calc(40*var(--u)) Inter,sans-serif;padding:0 calc(22*var(--u));white-space:nowrap;overflow:hidden}
.pagina{position:absolute;left:0;right:0;top:calc(64*var(--u));width:100%}
.lado{position:absolute;left:calc(96*var(--u));top:calc(330*var(--u));width:calc(400*var(--u))}
.passo{font:400 calc(34*var(--u))/1.35 Inter,sans-serif;color:#d8d8e0}
.dados{position:absolute;left:calc(96*var(--u));top:calc(260*var(--u));width:calc(760*var(--u))}
.dado{display:flex;justify-content:space-between;gap:calc(40*var(--u));text-align:right;align-items:baseline;border-bottom:1px solid #2a2a33;padding:calc(18*var(--u)) 0;font:700 calc(38*var(--u))/1.2 Inter,sans-serif}
.dado span{flex:none;text-align:left;font:400 calc(22*var(--u))/1 Inter,sans-serif;letter-spacing:.14em;color:#9a9aa6;text-transform:uppercase}
.grade-fotos{position:absolute;right:calc(96*var(--u));top:calc(260*var(--u));width:calc(840*var(--u));display:grid;grid-template-columns:repeat(3,1fr);gap:calc(12*var(--u))}
.grade-fotos img{width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:calc(10*var(--u))}
.nota{position:absolute;left:calc(96*var(--u));bottom:calc(60*var(--u));font:400 calc(26*var(--u))/1.3 Inter,sans-serif;color:#e8e8ee;background:rgba(8,8,12,.7);padding:calc(12*var(--u)) calc(20*var(--u));border-radius:calc(10*var(--u))}
.tag{position:absolute;left:calc(64*var(--u));top:calc(56*var(--u));font:700 calc(26*var(--u))/1 Inter,sans-serif;letter-spacing:.16em;padding:calc(14*var(--u)) calc(22*var(--u));border-radius:999px;background:#FACC15;color:#1a1206}
#filme{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.marca{font:800 calc(150*var(--u))/1 Sora,sans-serif;letter-spacing:-.02em}
.marca b{color:#FACC15}
.fim2{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;gap:calc(22*var(--u))}
.sub{font:400 calc(52*var(--u))/1.25 Inter,sans-serif;color:#e8e8ee}
.repo{font:700 calc(42*var(--u))/1 Inter,sans-serif;color:#fff;border:1px solid #3a3a44;border-radius:999px;padding:calc(16*var(--u)) calc(28*var(--u))}
.pill{font:800 calc(40*var(--u))/1 Sora,sans-serif;background:#FACC15;color:#1a1206;border-radius:999px;padding:calc(16*var(--u)) calc(30*var(--u))}
"""


def cenas(a: dict, b: dict) -> list[dict]:
    """a = caminhos dos assets na pasta do render; b = brief."""
    fatos = [("imóvel", b["nome"]), ("local", b["local"]), ("preço", b["preco"])] + \
            [(f["rotulo"], f["texto"]) for f in b["fatos"] if f["rotulo"] in ("Quartos", "Área")]
    linhas = "".join(f'<div class="dado"><span>{video.esc(k)}</span>{video.esc(v)}</div>' for k, v in fatos)
    grade = "".join(f'<img src="{s}" alt="">' for s in a["originais"])
    kb = "tl.fromTo(q('.ph'),{scale:1.0},{scale:1.06,duration:D,ease:'none'},0);"
    wipe = ("tl.fromTo(q('.deco'),{clipPath:'inset(0 0 0 100%)'},{clipPath:'inset(0 0 0 0%)',duration:1.4,ease:'power2.inOut'},1.8);"
            "tl.fromTo(q('.linha'),{left:'100%',opacity:1},{left:'0%',duration:1.4,ease:'power2.inOut'},1.8);"
            "tl.to(q('.linha'),{opacity:0,duration:.2},3.2);tl.to(q('.antes'),{opacity:0,duration:.3},1.8);"
            "tl.from(q('.depois'),{opacity:0,duration:.4},3.0);"
            "tl.fromTo(q('.ph2'),{scale:1.0},{scale:1.06,duration:D,ease:'none'},0);")
    url = "https://seusite.com.br/imoveis/apto-1202"
    return [
        {"dur": 3.8, "html": f'<img class="ph" src="{a["capa"]}" alt="">', "js": kb},
        {"dur": 5.8, "cls": "escuro", "html":
            '<div class="topo"><div class="kick">PASSO 1</div><div class="tit">Cole o link do anúncio</div></div>'
            '<div class="lado"><p class="passo">Pode ser o site da imobiliária, o seu ou um portal.</p></div>'
            f'<div class="janela"><div class="barra-nav"><i class="ponto"></i><i class="ponto"></i><i class="ponto"></i>'
            f'<div class="url" data-url="{url}"></div></div><img class="pagina" src="{a["print"]}" alt=""></div>',
         "js": ("var u=q('.url')[0];var s=u.getAttribute('data-url');var o={n:0};"
                "tl.to(o,{n:s.length,duration:1.6,ease:'none',onUpdate:function(){u.textContent=s.slice(0,Math.round(o.n));}},.4);"
                "tl.fromTo(q('.pagina'),{y:0},{y:'-38%',duration:3.2,ease:'power1.inOut'},2.3);"
                "tl.from(q('.topo'),{opacity:0,y:20,duration:.5},.1);")},
        {"dur": 5.6, "cls": "escuro", "html":
            '<div class="topo"><div class="kick">PASSO 2</div><div class="tit">Lê os dados e separa as fotos</div></div>'
            f'<div class="dados">{linhas}</div><div class="grade-fotos">{grade}</div>'
            '<div class="nota">Só entra o que está escrito no anúncio. Nada inventado.</div>',
         "js": ("qa('.dado').forEach(function(el,k){tl.from(el,{opacity:0,x:-30,duration:.45,ease:'power2.out'},.4+k*.22);});"
                "qa('.grade-fotos img').forEach(function(el,k){tl.from(el,{opacity:0,scale:.9,duration:.45,ease:'power2.out'},.6+k*.15);});"
                "tl.from(q('.nota'),{opacity:0,duration:.5},2.4);")},
        {"dur": 6.0, "html":
            f'<img class="ph" src="{a["sala_orig"]}" alt=""><div class="deco"><img class="ph2" src="{a["sala_pro"]}" alt=""></div>'
            '<div class="linha"></div><div class="etq antes">FOTO DO CELULAR</div><div class="etq depois">FOTO PROFISSIONAL</div>'
            '<div class="scrim baixo"></div><div class="bloco legenda"><div class="rot">PASSO 3</div>'
            '<div class="frase">Luz, ângulo e nitidez de fotógrafo</div></div>',
         "js": kb + wipe + "tl.from(q('.legenda'),{opacity:0,y:24,duration:.6},.3);"},
        {"dur": 6.0, "html":
            f'<img class="ph" src="{a["suite_pro"]}" alt=""><div class="deco"><img class="ph2" src="{a["suite_deco"]}" alt=""></div>'
            '<div class="linha"></div><div class="etq antes">VAZIO</div><div class="etq depois">DECORAÇÃO VIRTUAL</div>'
            '<div class="scrim baixo"></div><div class="bloco legenda"><div class="rot">PASSO 4 · VOCÊ ESCOLHE O ESTILO</div>'
            '<div class="frase">Móveis mudam. Parede, janela e vista, não.</div></div>',
         "js": kb + wipe + "tl.from(q('.legenda'),{opacity:0,y:24,duration:.6},.3);"},
        {"dur": 12.0, "video": a["filme"], "html": '<div class="tag">PASSO 5 · O FILME SAI PRONTO</div>',
         "js": "tl.from(q('.tag'),{opacity:0,y:-16,duration:.5},.4);tl.to(q('.tag'),{opacity:0,duration:.4},4.2);"},
        {"dur": 6.2, "cls": "escuro", "html":
            '<div class="fim2"><div class="marca">imovel<b>filme</b></div>'
            '<div class="sub">Do link do anúncio ao filme do imóvel</div>'
            '<div class="sub" style="font-size:calc(38*var(--u));color:#b4b4be">grátis · código aberto · roda com a sua assinatura</div>'
            '<div class="repo">github.com/inematds/imovelfilme</div><div class="pill">INEMA.CLUB</div></div>',
         "js": "qa('.fim2 > *').forEach(function(el,k){tl.from(el,{opacity:0,y:24,duration:.55,ease:'power2.out'},.3+k*.25);});"},
    ]


def composicao(lista: list[dict]) -> tuple[str, float]:
    w, h = video.FORMATOS["16x9"]
    t, htmls, jss = 0.0, [], []
    for i, c in enumerate(lista):
        ini = round(t, 3)
        cid = f"p{i}"
        if c.get("video"):  # vídeo com tempo próprio, fora de qualquer seção temporizada
            htmls.append(f'<video id="filme" class="clip" src="{c["video"]}" muted playsinline data-start="{ini:.3f}" '
                         f'data-duration="{c["dur"]:.3f}" data-track-index="3" style="z-index:{i + 1}"></video>')
            jss.append(f"main.fromTo('#filme',{{opacity:0}},{{opacity:1,duration:{XF},ease:'none'}},{ini:.3f});")
        htmls.append(f'<section id="{cid}" class="clip cena {c.get("cls", "")}" data-start="{ini:.3f}" data-duration="{c["dur"]:.3f}" '
                     f'data-track-index="{4 if c.get("video") else 1 + i % 2}" style="z-index:{i + 1}{";background:transparent" if c.get("video") else ""}">{c["html"]}</section>')
        entrada = "" if i == 0 or c.get("video") else f"tl.fromTo(el,{{opacity:0}},{{opacity:1,duration:{XF},ease:'none'}},0);"
        jss.append(f"(function(){{var el=document.getElementById('{cid}');var q=function(s){{return el.querySelectorAll(s)}};var qa=q;"
                   f"var D={c['dur']};var tl=gsap.timeline();{entrada}{c['js']}main.add(tl,{ini:.3f});}})();")
        t += c["dur"] - (XF if i < len(lista) - 1 else 0)
    total = round(t, 3)
    html = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={w}, height={h}" />
<title>imovelfilme · promo</title>
<script src="assets/gsap.min.js"></script>
<style>{video.CSS}{CSS_EXTRA}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="{w}" data-height="{h}" data-duration="{total:.3f}" data-fps="30" style="--W:{w}px;--H:{h}px">
{chr(10).join(htmls)}
</div>
<script>
var main = gsap.timeline({{ paused: true }});
{chr(10).join(jss)}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = main;
</script>
</body>
</html>
"""
    return html, total


def main():
    b = json.loads((DEMO / "imovel" / "brief.json").read_text())
    pasta = AQUI / "build"
    if pasta.exists():
        shutil.rmtree(pasta)
    (pasta / "assets").mkdir(parents=True)
    shutil.copytree(RAIZ / "assets" / "fonts", pasta / "assets" / "fonts")
    shutil.copy(RAIZ / "node_modules" / "gsap" / "dist" / "gsap.min.js", pasta / "assets" / "gsap.min.js")
    origem = {
        "capa": AQUI / "assets" / "capa.jpg", "print": AQUI / "assets" / "anuncio.png",
        "sala_orig": DEMO / "fotos/original/02-sala.jpg", "sala_pro": DEMO / "fotos/profissional/02-sala.jpg",
        "suite_pro": DEMO / "fotos/profissional/04-suite.jpg", "suite_deco": DEMO / "fotos/decorada/04-suite.jpg",
        "filme": DEMO / "output/filme-16x9.mp4",
    }
    a = {}
    for k, p in origem.items():
        shutil.copy(p, pasta / "assets" / f"{k}{p.suffix}")
        a[k] = f"assets/{k}{p.suffix}"
    a["originais"] = []
    for p in sorted((DEMO / "fotos" / "original").glob("*.jpg")):
        shutil.copy(p, pasta / "assets" / f"orig-{p.name}")
        a["originais"].append(f"assets/orig-{p.name}")
    html, total = composicao(cenas(a, b))
    (pasta / "index.html").write_text(html)
    hf = str(RAIZ / "node_modules" / ".bin" / "hyperframes")
    subprocess.run([hf, "lint"], cwd=pasta, check=True, capture_output=True)
    mudo = pasta / "mudo.mp4"
    subprocess.run([hf, "render", "--quality", "looks", "-o", str(mudo), "--quiet"], cwd=pasta, check=True)
    (AQUI / "output").mkdir(exist_ok=True)
    final = AQUI / "output" / "promo-imovelfilme.mp4"
    video.mixar(mudo, RAIZ / "assets" / "trilhas" / "energia.mp3", final, total)
    print(final, total)


if __name__ == "__main__":
    main()
