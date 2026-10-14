"""Etapa 6: o filme do imóvel em HyperFrames (HTML + GSAP → MP4) e a trilha mixada pelo FFmpeg.

Roteiro fixo, preenchido com o brief e as fotos do projeto:
  abertura (fachada + nome, cheio já no quadro 0) → preço → um cômodo por cena
  (cômodo interno: a foto profissional vazia e, por cortina, a versão decorada) →
  números contando → fecho com nome, preço, local e o aviso de decoração virtual.
Zoom lento (≤ 1,10), troca por dissolve, sem sons de movimento.
"""
from __future__ import annotations

import html
import json
import shutil
import subprocess
from pathlib import Path

from .extrair import COMODOS

RAIZ = Path(__file__).resolve().parent.parent
FORMATOS = {"16x9": (1920, 1080), "9x16": (1080, 1920)}
NOMES_COMODO = {"fachada": "Fachada", "sala": "Sala", "cozinha": "Cozinha", "suite": "Suíte",
                "banheiro": "Banheiro", "sacada": "Sacada", "vista": "Vista", "lazer": "Lazer", "outro": ""}
XF = 0.5  # dissolve entre cenas (s)


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""), quote=True)


def nome_html(nome) -> str:
    """Nome do imóvel sem deixar o separador começar uma linha."""
    return esc(nome).replace(" · ", "&nbsp;· ")


def _foto(projeto: Path, f: dict, tipo: str) -> Path | None:
    base = Path(f["arquivo"]).stem
    p = projeto / "fotos" / tipo / f"{base}.jpg"
    return p if p.exists() else None


def plano(projeto: Path, com_decorada: bool = True) -> dict:
    """Decide as cenas a partir do brief e das fotos. Puro (sem render), testável."""
    an = json.loads((projeto / "imovel" / "anuncio.json").read_text())
    b = json.loads((projeto / "imovel" / "brief.json").read_text())
    fotos = []
    for f in an["fotos"]:
        pro = _foto(projeto, f, "profissional") or (projeto / f["arquivo"])
        deco = _foto(projeto, f, "decorada") if com_decorada and f.get("interno") else None
        fotos.append({"comodo": f["comodo"], "pro": pro, "deco": deco})
    if not fotos:
        raise SystemExit("sem fotos no projeto: rode extrair antes")
    abertura = next((x for x in fotos if x["comodo"] == "fachada"), fotos[0])
    vista = next((x for x in fotos if x["comodo"] in ("sacada", "vista") and x is not abertura), None)
    resto = [x for x in fotos if x is not abertura and x is not vista]
    textos = [f["texto"] for f in b["fatos"] if f["rotulo"] in ("Destaque", "Lazer")]

    def frase(comodo: str) -> str:
        """Destaque que cita este cômodo; se não houver, um destaque que não cita cômodo nenhum."""
        chaves = dict(COMODOS).get(comodo, [])
        for t in textos:
            if any(k in t.lower() for k in chaves):
                textos.remove(t)
                return t
        for t in textos:
            if not any(k in t.lower() for _, ks in COMODOS for k in ks if len(k) > 3):
                textos.remove(t)
                return t
        return ""
    stats = [f for f in b["fatos"] if isinstance(f.get("valor"), (int, float))][:4]

    cenas = [{"tipo": "abertura", "dur": 3.6, "foto": abertura["pro"]}]
    if b.get("preco"):
        cenas.append({"tipo": "preco", "dur": 3.0, "foto": (vista or abertura)["pro"]})
    elif vista:
        cenas.append({"tipo": "foto", "dur": 2.8, "foto": vista["pro"], "comodo": vista["comodo"],
                      "texto": frase(vista["comodo"])})
    for x in resto:
        if x["deco"]:
            cenas.append({"tipo": "antes-depois", "dur": 4.2, "foto": x["pro"], "deco": x["deco"],
                          "comodo": x["comodo"], "texto": frase(x["comodo"])})
        else:
            cenas.append({"tipo": "foto", "dur": 2.8, "foto": x["pro"], "comodo": x["comodo"],
                          "texto": frase(x["comodo"])})
    if stats:
        cenas.append({"tipo": "numeros", "dur": 3.6, "foto": (vista or abertura)["pro"], "stats": stats})
    if vista and b.get("preco"):
        cenas.append({"tipo": "foto", "dur": 2.8, "foto": vista["pro"], "comodo": vista["comodo"],
                      "texto": frase(vista["comodo"])})
    cenas.append({"tipo": "fecho", "dur": 4.4, "foto": abertura["pro"],
                  "aviso": any(x["deco"] for x in fotos)})
    for c in cenas:  # destaque que sobrou vai para a primeira cena de cômodo sem frase
        if c["tipo"] in ("foto", "antes-depois") and not c.get("texto") and textos:
            c["texto"] = textos.pop(0)
    t = 0.0
    for i, c in enumerate(cenas):
        c["ini"] = round(t, 3)
        t += c["dur"] - (XF if i < len(cenas) - 1 else 0)
    return {"brief": b, "cenas": cenas, "total": round(t, 3)}


def _img(src: str, cls: str = "ph") -> str:
    return f'<img class="{cls}" src="{esc(src)}" alt="">'


def _cena_html(c: dict, i: int, b: dict, assets: dict) -> tuple[str, str]:
    """Devolve (html, js). js recebe tl (timeline da cena), q (seletor dentro da cena) e D (duração)."""
    foto = assets[str(c["foto"])]
    tipo = c["tipo"]
    kb = "tl.fromTo(q('.ph'),{scale:1.0},{scale:1.08,duration:D,ease:'none'},0);"
    if tipo == "abertura":
        h = (_img(foto) + '<div class="scrim baixo"></div><div class="bloco abre">'
             f'<div class="chip">À VENDA</div><h1 class="nome">{nome_html(b.get("nome"))}</h1>'
             f'<p class="local">{esc(b.get("local"))}</p><div class="barra"></div></div>')
        js = kb + "tl.fromTo(q('.barra'),{scaleX:0.35},{scaleX:1,duration:1.2,ease:'power2.out'},0.1);"
        return h, js
    if tipo == "preco":
        h = (_img(foto) + '<div class="scrim esq"></div><div class="bloco preco">'
             f'<div class="rot">PREÇO</div><div class="valor">{esc(b["preco"])}</div>'
             f'<p class="local">{esc(b.get("local"))}</p></div>')
        js = kb + ("tl.from(q('.rot'),{opacity:0,y:20,duration:.5,ease:'power2.out'},.35);"
                   "tl.from(q('.valor'),{opacity:0,y:30,duration:.7,ease:'power3.out'},.5);"
                   "tl.from(q('.preco .local'),{opacity:0,duration:.6},.9);")
        return h, js
    if tipo in ("foto", "antes-depois"):
        nome = NOMES_COMODO.get(c.get("comodo"), "")
        deco = ""
        js = kb
        if tipo == "antes-depois":
            deco = (f'<div class="deco">{_img(assets[str(c["deco"])], "ph2")}</div><div class="linha"></div>'
                    '<div class="etq antes">COMO ESTÁ</div><div class="etq depois">DECORAÇÃO VIRTUAL</div>')
            js += ("tl.fromTo(q('.ph2'),{scale:1.0},{scale:1.08,duration:D,ease:'none'},0);"
                   "tl.fromTo(q('.deco'),{clipPath:'inset(0 0 0 100%)'},{clipPath:'inset(0 0 0 0%)',duration:1.3,ease:'power2.inOut'},1.3);"
                   "tl.fromTo(q('.linha'),{left:'100%',opacity:1},{left:'0%',duration:1.3,ease:'power2.inOut'},1.3);"
                   "tl.to(q('.linha'),{opacity:0,duration:.2},2.6);"
                   "tl.to(q('.antes'),{opacity:0,duration:.3},1.3);"
                   "tl.from(q('.depois'),{opacity:0,duration:.4},2.4);")
        txt = c.get("texto") or ""
        h = (_img(foto) + deco + '<div class="scrim baixo"></div><div class="bloco legenda">'
             + (f'<div class="rot">{esc(nome.upper())}</div>' if nome else "")
             + (f'<div class="frase">{esc(txt)}</div>' if txt else "") + "</div>")
        js += ("tl.from(q('.legenda'),{opacity:0,y:24,duration:.6,ease:'power2.out'},.45);")
        return h, js
    if tipo == "numeros":
        itens = "".join(
            f'<div class="st"><div class="n" data-v="{s["valor"]}">{s["valor"]}</div>'
            f'<div class="u">{esc(s.get("unidade") or s["rotulo"])}</div></div>' for s in c["stats"])
        h = _img(foto, "ph borrada") + f'<div class="veu"></div><div class="grade n{len(c["stats"])}">{itens}</div>'
        js = (kb + "qa('.st').forEach(function(el,k){tl.from(el,{opacity:0,y:30,duration:.5,ease:'power2.out'},.3+k*.18);});"
              "qa('.n').forEach(function(el,k){var v=+el.getAttribute('data-v');var o={x:0};"
              "tl.to(o,{x:v,duration:1.1,ease:'power2.out',onUpdate:function(){el.textContent=Math.round(o.x).toLocaleString('pt-BR');}},.3+k*.18);});")
        return h, js
    # fecho
    aviso = '<p class="aviso">Imagens tratadas por IA · cômodos com decoração virtual</p>' if c.get("aviso") else ""
    contato = f'<p class="contato">{esc(b["contato"])}</p>' if b.get("contato") else ""
    h = (_img(foto, "ph borrada") + '<div class="veu"></div><div class="bloco fim">'
         f'<h2 class="nome">{nome_html(b.get("nome"))}</h2><p class="local">{esc(b.get("local"))}</p>'
         + (f'<div class="valor">{esc(b["preco"])}</div>' if b.get("preco") else "")
         + contato + aviso + "</div>")
    js = kb + ("tl.from(q('.fim .nome'),{opacity:0,y:24,duration:.7,ease:'power2.out'},.35);"
               "tl.from(q('.fim .local'),{opacity:0,duration:.6},.7);"
               "tl.from(q('.fim .valor'),{opacity:0,y:20,duration:.6,ease:'power2.out'},.95);"
               "tl.from(q('.fim .contato, .fim .aviso'),{opacity:0,duration:.6},1.3);")
    return h, js


CSS = """
@font-face{font-family:'Sora';src:url(assets/fonts/Sora-800.woff2) format('woff2');font-weight:800}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-400.woff2) format('woff2');font-weight:400}
@font-face{font-family:'Inter';src:url(assets/fonts/Inter-700.woff2) format('woff2');font-weight:700}
html,body{margin:0;width:100%;height:100%;background:#0c0c10}
#root{position:relative;width:100%;height:100%;overflow:hidden;background:#0c0c10;color:#fff;font-family:Inter,sans-serif;
  --u:calc(min(var(--W),var(--H))/1080)}
.cena{position:absolute;inset:0;overflow:hidden;background:#0c0c10}
.ph,.ph2{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;transform-origin:50% 50%}
.borrada{filter:blur(18px) brightness(.55);transform:scale(1.1)}
.deco{position:absolute;inset:0;overflow:hidden}
.linha{position:absolute;top:0;bottom:0;width:calc(6*var(--u));background:#FACC15;transform:translateX(-50%)}
.scrim{position:absolute;inset:0}
.scrim.baixo{background:linear-gradient(to top,rgba(8,8,12,.86) 0%,rgba(8,8,12,.35) 34%,rgba(8,8,12,0) 58%)}
.scrim.esq{background:linear-gradient(to right,rgba(8,8,12,.85) 0%,rgba(8,8,12,.4) 45%,rgba(8,8,12,0) 70%)}
.veu{position:absolute;inset:0;background:rgba(8,8,12,.35)}
.bloco{position:absolute;left:calc(96*var(--u));right:calc(96*var(--u))}
.abre{bottom:calc(110*var(--u))}
.chip{display:inline-block;font:700 calc(26*var(--u))/1 Inter,sans-serif;letter-spacing:.18em;background:#FACC15;color:#1a1206;padding:calc(12*var(--u)) calc(20*var(--u));border-radius:999px}
.nome{font:800 calc(92*var(--u))/1.04 Sora,sans-serif;margin:calc(26*var(--u)) 0 calc(14*var(--u));letter-spacing:-.01em;max-width:16ch;text-wrap:balance}
.local{font:400 calc(40*var(--u))/1.2 Inter,sans-serif;margin:0;color:#e8e8ee}
.barra{width:calc(220*var(--u));height:calc(8*var(--u));background:#FACC15;margin-top:calc(30*var(--u));transform-origin:0 50%}
.preco{top:50%;transform:translateY(-50%)}
.rot{font:700 calc(30*var(--u))/1 Inter,sans-serif;letter-spacing:.22em;color:#FACC15}
.valor{font:800 calc(124*var(--u))/1.05 Sora,sans-serif;margin:calc(18*var(--u)) 0 calc(16*var(--u));white-space:nowrap}
.legenda{bottom:calc(96*var(--u))}
.frase{font:800 calc(70*var(--u))/1.1 Sora,sans-serif;margin-top:calc(16*var(--u));max-width:18ch;text-wrap:balance}
.etq{position:absolute;top:calc(64*var(--u));font:700 calc(26*var(--u))/1 Inter,sans-serif;letter-spacing:.16em;padding:calc(12*var(--u)) calc(18*var(--u));border-radius:999px;background:rgba(8,8,12,.7)}
.etq.antes{left:calc(64*var(--u))}
.etq.depois{right:calc(64*var(--u));background:#FACC15;color:#1a1206}
.grade{position:absolute;inset:0;display:grid;align-content:center;justify-content:center;gap:calc(40*var(--u)) calc(90*var(--u));grid-template-columns:repeat(var(--cols),auto)}
.grade.n1{--cols:1}.grade.n2{--cols:2}.grade.n3{--cols:3}.grade.n4{--cols:2}
.st{text-align:center;min-width:calc(300*var(--u))}
.st .n{font:800 calc(170*var(--u))/1 Sora,sans-serif}
.st .u{font:700 calc(32*var(--u))/1 Inter,sans-serif;letter-spacing:.2em;color:#FACC15;text-transform:uppercase;margin-top:calc(12*var(--u))}
.fim{top:50%;transform:translateY(-50%);text-align:center}
.fim .nome{max-width:none;margin:0 auto calc(16*var(--u))}
.fim .valor{margin-top:calc(34*var(--u))}
.contato{font:700 calc(40*var(--u))/1.2 Inter,sans-serif;margin:calc(20*var(--u)) 0 0}
.aviso{font:400 calc(24*var(--u))/1.3 Inter,sans-serif;color:#c9c9d2;margin-top:calc(46*var(--u))}
"""


def composicao(pl: dict, assets: dict, formato: str = "16x9") -> str:
    w, h = FORMATOS[formato]
    b = pl["brief"]
    blocos_html, blocos_js = [], []
    for i, c in enumerate(pl["cenas"]):
        corpo, js = _cena_html(c, i, b, assets)
        cid = f"c{i}"
        blocos_html.append(
            f'<section id="{cid}" class="clip cena" data-start="{c["ini"]:.3f}" data-duration="{c["dur"]:.3f}" '
            f'data-track-index="{1 + i % 2}" style="z-index:{i + 1}">{corpo}</section>')
        entrada = "" if i == 0 else f"tl.fromTo(el,{{opacity:0}},{{opacity:1,duration:{XF},ease:'none'}},0);"
        blocos_js.append(
            f"(function(){{var el=document.getElementById('{cid}');var q=function(s){{return el.querySelectorAll(s)}};"
            f"var qa=q;var D={c['dur']};var tl=gsap.timeline();{entrada}{js}main.add(tl,{c['ini']:.3f});}})();")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width={w}, height={h}" />
<title>{esc(b.get('nome'))} · imovelfilme</title>
<script src="assets/gsap.min.js"></script>
<style>{CSS}</style>
</head>
<body>
<div id="root" data-composition-id="main" data-start="0" data-width="{w}" data-height="{h}" data-duration="{pl['total']:.3f}" data-fps="30" style="--W:{w}px;--H:{h}px">
{chr(10).join(blocos_html)}
</div>
<script>
var main = gsap.timeline({{ paused: true }});
{chr(10).join(blocos_js)}
window.__timelines = window.__timelines || {{}};
window.__timelines["main"] = main;
</script>
</body>
</html>
"""


def _rodar(cmd: list, cwd: Path) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"{Path(cmd[0]).name} falhou ({r.returncode}): {(r.stderr or r.stdout)[-800:]}")
    return r.stdout


def mixar(video_mudo: Path, trilha: Path | None, destino: Path, total: float):
    """Trilha em loop até o fim, entrada e saída suaves, −14 LUFS / pico −1 dBTP."""
    video_mudo, destino = Path(video_mudo).resolve(), Path(destino).resolve()
    if not trilha:
        shutil.copy(video_mudo, destino)
        return
    trilha = Path(trilha).resolve()
    fim = max(0.0, total - 2.5)
    base = (f"[1:a]atrim=0:{total:.3f},asetpts=PTS-STARTPTS,afade=t=in:d=0.6,"
            f"afade=t=out:st={fim:.3f}:d=2.5,loudnorm=I=-14:TP=-1:LRA=11")
    # 1ª passada mede; 2ª aplica linear (uma passada só fica ~1 LU abaixo do alvo)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video_mudo), "-stream_loop", "-1", "-i", str(trilha),
                        "-filter_complex", base + ":print_format=json[a]", "-map", "[a]", "-f", "null", "-"],
                       capture_output=True, text=True)
    m = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    medido = (f":measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}"
              f":measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    _rodar(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_mudo), "-stream_loop", "-1", "-i", str(trilha),
            "-filter_complex", base + medido + "[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest",
            str(destino)], destino.parent)


def renderizar(projeto: Path, trilha: Path | None = None, formato: str = "16x9", com_decorada: bool = True,
               qualidade: str = "looks") -> Path:
    pl = plano(projeto, com_decorada)
    pasta = projeto / "video" / formato
    if pasta.exists():
        shutil.rmtree(pasta)
    (pasta / "assets" / "fotos").mkdir(parents=True)
    shutil.copytree(RAIZ / "assets" / "fonts", pasta / "assets" / "fonts")
    shutil.copy(RAIZ / "node_modules" / "gsap" / "dist" / "gsap.min.js", pasta / "assets" / "gsap.min.js")
    assets = {}
    for c in pl["cenas"]:
        for k in ("foto", "deco"):
            p = c.get(k)
            if p and str(p) not in assets:
                destino = pasta / "assets" / "fotos" / f"{len(assets):02d}-{Path(p).parent.name}-{Path(p).name}"
                shutil.copy(p, destino)
                assets[str(p)] = f"assets/fotos/{destino.name}"
    (pasta / "index.html").write_text(composicao(pl, assets, formato))
    (pasta / "plano.json").write_text(json.dumps(
        {"total": pl["total"], "cenas": [{k: (str(v) if isinstance(v, Path) else v) for k, v in c.items()} for c in pl["cenas"]]},
        ensure_ascii=False, indent=1) + "\n")
    hf = str(RAIZ / "node_modules" / ".bin" / "hyperframes")
    _rodar([hf, "lint"], pasta)
    saida = projeto / "output"
    saida.mkdir(exist_ok=True)
    mudo = pasta / "mudo.mp4"
    _rodar([hf, "render", "--quality", qualidade, "-o", str(mudo), "--quiet"], pasta)
    final = saida / f"filme-{formato}.mp4"
    mixar(mudo, trilha.resolve() if trilha else None, final, pl["total"])
    return final
