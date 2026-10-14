"""Etapas 3 e 4: foto profissional e decoração virtual, pelo Codex image_gen (assinatura).

Cada foto vira uma chamada `codex exec -i <original>` pedindo para EDITAR a imagem:
  - profissional: mesma casa, foto melhor (luz, enquadramento, perspectiva, nitidez);
  - decorada: só cômodos internos, móveis e decoração no estilo escolhido, arquitetura intacta.

Sem chave de API: usa o Codex logado no terminal. Arquivo que já existe não é refeito (retomável).
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ESTILOS = {
    "praia-contemporaneo": "contemporâneo de praia: madeira clara, linho cru, tons de areia e branco, fibras naturais, plantas, luz natural",
    "luxo-moderno": "luxo moderno: pedra natural, madeira quente, tecidos neutros, iluminação de design, detalhes metálicos discretos, estilo cobertura de alto padrão",
    "escandinavo": "escandinavo: madeira clara, branco e cinza suave, linhas simples, tecidos aconchegantes, pouca decoração",
    "industrial": "industrial: couro, metal preto, madeira de demolição, luminárias pendentes, tons terrosos",
    "familia": "aconchegante para família: sofá grande, tapete macio, cores claras e quentes, móveis práticos",
}

NAO_MUDAR = ("paredes, janelas, portas, teto, piso, proporções do cômodo, bancadas e armários fixos, "
             "revestimentos, sacada, guarda-corpo, fachada e a vista real pela janela")

PROMPT_PRO = """Use sua ferramenta de geração de imagem (image_gen) para EDITAR a foto anexada e salve o resultado como {saida} neste diretório. Não crie nem edite nenhum outro arquivo.

Objetivo: a MESMA propriedade, fotografada por um fotógrafo profissional de imóveis.
Melhore só a apresentação: enquadramento, perspectiva corrigida (linhas verticais retas), correção de lente, exposição equilibrada, luz natural agradável, faixa dinâmica natural, nitidez e limpeza da imagem. Horizontal 3:2.
NÃO mude: {nao_mudar}, nem o tamanho aparente do espaço. Não acrescente nem remova móveis. Não acrescente pessoas, texto, logotipo ou marca d'água.
O resultado precisa representar o imóvel real com honestidade. Responda só OK ao terminar."""

PROMPT_DECO = """Use sua ferramenta de geração de imagem (image_gen) para EDITAR a foto anexada e salve o resultado como {saida} neste diretório. Não crie nem edite nenhum outro arquivo.

Objetivo: decoração virtual (home staging) deste cômodo, no estilo {estilo}.
Pode mudar SOMENTE móveis soltos, tapetes, cortinas, quadros, luminárias de mesa/piso, plantas e objetos de decoração.
NÃO mude: {nao_mudar}. Não aumente o cômodo, não mova janelas, não troque a vista. Foto profissional de imóvel, luz natural, horizontal 3:2.
Sem pessoas, sem texto, sem logotipo, sem marca d'água. Responda só OK ao terminar."""


def _codex_editar(original: Path, destino: Path, prompt: str, timeout: int = 900) -> str:
    if destino.exists():
        return "já existe"
    with tempfile.TemporaryDirectory(prefix="imovelfilme-") as d:
        alvo = "saida.png"
        r = subprocess.run(
            ["codex", "exec", "--skip-git-repo-check", "--dangerously-bypass-approvals-and-sandbox",
             "-i", str(original.resolve()), "-"],
            input=prompt,
            cwd=d, capture_output=True, text=True, timeout=timeout)
        png = Path(d) / alvo
        if not png.exists():
            achados = sorted(Path(d).glob("*.png"))
            png = achados[0] if achados else png
        if not png.exists():
            return "FALHOU " + (r.stderr or r.stdout)[-300:].replace("\n", " ")
        destino.parent.mkdir(parents=True, exist_ok=True)
        _para_jpg(png, destino)
    return "ok"


def amarelo(im) -> float:
    """(R+G)/2 - B da imagem inteira. Foto neutra fica em 0-10; o gerador costuma entregar 25-55."""
    from PIL import ImageStat
    r, g, b = ImageStat.Stat(im.convert("RGB").resize((256, 256))).mean
    return (r + g) / 2 - b


def cor_neutra(im, limite: float = 18.0, alvo: float = 12.0):
    """Tira o amarelado que o gerador de imagem põe: puxa os canais para o cinza até `alvo`."""
    from PIL import Image, ImageStat
    im = im.convert("RGB")
    if amarelo(im) <= limite:
        return im
    r, g, b = ImageStat.Stat(im.resize((256, 256))).mean
    cinza = (r + g + b) / 3
    out = im
    for k in range(1, 21):
        gs = [(cinza / c) ** (k / 20) for c in (r, g, b)]
        out = Image.merge("RGB", [ch.point(lambda v, m=m: min(255, int(v * m + .5))) for ch, m in zip(im.split(), gs)])
        if amarelo(out) <= alvo:
            break
    return out


def _para_jpg(png: Path, destino: Path):
    try:
        from PIL import Image
        cor_neutra(Image.open(png)).save(destino, quality=92)
    except ImportError:
        shutil.copy(png, destino.with_suffix(".png"))


def preparar(projeto: Path, estilo: str, paralelo: int = 3, log=print) -> dict:
    anuncio = json.loads((projeto / "imovel" / "anuncio.json").read_text())
    desc_estilo = ESTILOS.get(estilo, estilo)  # aceita nome da lista ou texto livre
    tarefas = []
    for f in anuncio["fotos"]:
        orig = projeto / f["arquivo"]
        base = Path(f["arquivo"]).stem
        tarefas.append(("profissional", orig, projeto / "fotos" / "profissional" / f"{base}.jpg",
                        PROMPT_PRO.format(saida="saida.png", nao_mudar=NAO_MUDAR)))
        if f.get("interno"):
            tarefas.append(("decorada", orig, projeto / "fotos" / "decorada" / f"{base}.jpg",
                            PROMPT_DECO.format(saida="saida.png", nao_mudar=NAO_MUDAR, estilo=desc_estilo)))

    def roda(t):
        tipo, orig, dest, prompt = t
        return tipo, dest, _codex_editar(orig, dest, prompt)

    resultado = {"ok": 0, "falhas": []}
    with ThreadPoolExecutor(paralelo) as ex:
        for tipo, dest, st in ex.map(roda, tarefas):
            log(f"  {tipo:12} {dest.name}: {st}")
            if st.startswith("FALHOU"):
                resultado["falhas"].append(str(dest))
            else:
                resultado["ok"] += 1
    (projeto / "imovel" / "estilo.txt").write_text(desc_estilo + "\n")
    return resultado
