"""Etapa 5: brief do vídeo — os 4 a 8 fatos mais fortes do anúncio, prontos para virar texto animado.

Determinístico: lê imovel/anuncio.json e escolhe por prioridade. Campo ausente não entra.
Saída: imovel/brief.json (lido pelo vídeo) e imovel/brief.md (para a pessoa revisar e editar).
"""
from __future__ import annotations

import json
from pathlib import Path

MOEDAS = {"BRL": "R$", "USD": "US$", "EUR": "€", "AED": "AED", "GBP": "£"}


def _int(v):
    return int(v) if isinstance(v, (int, float)) and float(v).is_integer() else v


def _milhar(n: float, sep=".") -> str:
    return f"{int(round(n)):,}".replace(",", sep)


def formatar_preco(dados: dict) -> str | None:
    if dados.get("preco"):
        simbolo = MOEDAS.get(str(dados.get("moeda") or "BRL").upper(), dados.get("moeda") or "R$")
        return f"{simbolo} {_milhar(dados['preco'])}"
    return dados.get("preco_texto")


def montar(dados: dict, maximo: int = 8) -> dict:
    fatos = []
    if dados.get("quartos"):
        q = _int(dados["quartos"])
        s = _int(dados.get("suites") or 0)
        fatos.append({"rotulo": "Quartos", "valor": q, "texto": f"{q} quartos" + (f" · {s} suíte{'s' if s > 1 else ''}" if s else "")})
    if dados.get("area_m2"):
        fatos.append({"rotulo": "Área", "valor": _int(dados["area_m2"]), "unidade": "m²", "texto": f"{_milhar(dados['area_m2'])} m²"})
    elif dados.get("area_sqft"):
        fatos.append({"rotulo": "Área", "valor": _int(dados["area_sqft"]), "unidade": "sq ft", "texto": f"{_milhar(dados['area_sqft'], ',')} sq ft"})
    if dados.get("banheiros"):
        b = _int(dados["banheiros"])
        fatos.append({"rotulo": "Banheiros", "valor": b, "texto": f"{b} banheiro{'s' if b != 1 else ''}"})
    if dados.get("vagas"):
        v = _int(dados["vagas"])
        fatos.append({"rotulo": "Vagas", "valor": v, "texto": f"{v} vaga{'s' if v != 1 else ''}"})
    for d in (dados.get("destaques") or [])[:4]:
        fatos.append({"rotulo": "Destaque", "texto": d})
    for c in (dados.get("comodidades") or [])[:2]:
        fatos.append({"rotulo": "Lazer", "texto": c})
    return {
        "nome": dados.get("nome"),
        "local": dados.get("local"),
        "preco": formatar_preco(dados),
        "contato": dados.get("contato"),
        "fatos": fatos[:maximo],
    }


def salvar(projeto: Path) -> dict:
    anuncio = json.loads((projeto / "imovel" / "anuncio.json").read_text())
    b = montar(anuncio["dados"])
    (projeto / "imovel" / "brief.json").write_text(json.dumps(b, ensure_ascii=False, indent=1) + "\n")
    linhas = [f"# Brief do vídeo", "", f"IMÓVEL\n{b['nome'] or '(sem nome no anúncio)'}", ""]
    if b["local"]:
        linhas += [f"LOCAL\n{b['local']}", ""]
    if b["preco"]:
        linhas += [f"PREÇO\n{b['preco']}", ""]
    linhas += ["FATOS"] + [f"- {f['texto']}" for f in b["fatos"]]
    linhas += ["", "Edite imovel/brief.json para mudar o que aparece no vídeo. Só entram dados que estão no anúncio."]
    (projeto / "imovel" / "brief.md").write_text("\n".join(linhas) + "\n")
    return b
