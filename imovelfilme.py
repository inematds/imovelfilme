#!/usr/bin/env python3
"""imovelfilme — do link do anúncio ao filme do imóvel.

  python3 imovelfilme.py tudo <url> --projeto <pasta> [--estilo praia-contemporaneo] [--trilha musica.wav]
  python3 imovelfilme.py extrair <url> --projeto <pasta>      # dados + até 10 fotos
  python3 imovelfilme.py fotos --projeto <pasta> --estilo X    # foto profissional + decoração virtual (Codex)
  python3 imovelfilme.py brief --projeto <pasta>               # 4 a 8 fatos para o vídeo
  python3 imovelfilme.py video --projeto <pasta> [--trilha X] [--formato 16x9|9x16]
  python3 imovelfilme.py estilos                               # estilos de decoração prontos
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from engine import brief, extrair, fotos, video  # noqa: E402
from engine.version import VERSION  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(prog="imovelfilme", description="Do link do anúncio ao filme do imóvel.")
    ap.add_argument("--version", action="version", version=f"imovelfilme {VERSION}")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for nome in ("tudo", "extrair"):
        s = sub.add_parser(nome)
        s.add_argument("url", help="link do anúncio (ou caminho de um .html salvo)")
    for nome in ("fotos", "brief", "video"):
        sub.add_parser(nome)
    sub.add_parser("estilos")
    for s in sub.choices.values():
        if s.prog.endswith("estilos"):
            continue
        s.add_argument("--projeto", required=True, type=Path, help="pasta do projeto do imóvel")
        s.add_argument("--max-fotos", type=int, default=extrair.MAX_FOTOS)
        s.add_argument("--estilo", default="praia-contemporaneo", help="nome da lista (estilos) ou descrição livre")
        s.add_argument("--trilha", type=Path, help="música de fundo (wav/mp3)")
        s.add_argument("--formato", default="16x9", choices=list(video.FORMATOS))
        s.add_argument("--sem-decorada", action="store_true", help="vídeo só com as fotos profissionais")
    a = ap.parse_args(argv)

    if a.cmd == "estilos":
        for k, v in fotos.ESTILOS.items():
            print(f"{k:22} {v}")
        return 0
    p = a.projeto.resolve()
    if a.cmd in ("tudo", "extrair"):
        an = extrair.salvar(a.url, p, a.max_fotos)
        d = an["dados"]
        print(f"anúncio: {d.get('nome')} · {len(an['fotos'])} fotos de {d.get('fotos_encontradas')} encontradas")
        print("  campos:", ", ".join(k for k in d if not k.startswith("_") and k not in ("fonte", "fotos_encontradas")))
        if not an["fotos"]:
            print("nenhuma foto encontrada: confira o link ou salve a página e passe o .html", file=sys.stderr)
            return 2
    if a.cmd in ("tudo", "fotos"):
        r = fotos.preparar(p, a.estilo)
        print(f"fotos: {r['ok']} prontas, {len(r['falhas'])} falharam")
        if r["falhas"]:
            print("  rode de novo o mesmo comando para refazer só as que faltam", file=sys.stderr)
    if a.cmd in ("tudo", "brief"):
        b = brief.salvar(p)
        print(f"brief: {b['nome']} · {b['preco']} · {len(b['fatos'])} fatos → imovel/brief.md")
    if a.cmd in ("tudo", "video"):
        mp4 = video.renderizar(p, trilha=a.trilha, formato=a.formato, com_decorada=not a.sem_decorada)
        print(f"vídeo: {mp4}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
