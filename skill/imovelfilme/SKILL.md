---
name: imovelfilme
description: "Link de anúncio de imóvel vira filme de divulgação: lê os dados verificáveis, separa até 10 fotos, faz versão profissional de cada uma e decoração virtual dos cômodos, monta o brief e renderiza o vídeo motion (HyperFrames) com trilha. Gatilho: 'faz o vídeo desse imóvel', 'filme do anúncio', link de anúncio + 'vídeo'."
---

# imovelfilme

Do link do anúncio ao filme do imóvel. Repositório: https://github.com/inematds/imovelfilme

## Antes de começar

1. Confirme que a pessoa tem direito de usar as fotos (é dona, corretora do imóvel ou tem autorização).
   Marca d'água só sai de foto que ela pode editar.
2. Pergunte o estilo da decoração virtual. Mostre a lista com `python3 imovelfilme.py estilos`
   (praia-contemporaneo, luxo-moderno, escandinavo, industrial, familia) ou aceite uma descrição livre.
3. Pergunte se há música própria; sem ela, o vídeo sai mudo.

## Passo a passo

```bash
cd ~/projetos/imovelfilme
python3 imovelfilme.py extrair "<link>" --projeto ~/imoveis/<nome>
#  → confira imovel/anuncio.json: só dados que estão no anúncio, cada um com a fonte em _fontes
python3 imovelfilme.py fotos --projeto ~/imoveis/<nome> --estilo praia-contemporaneo
#  → fotos/profissional/ e fotos/decorada/ (Codex image_gen pela assinatura; refaz só o que falta)
python3 imovelfilme.py brief --projeto ~/imoveis/<nome>
#  → imovel/brief.md para a pessoa revisar; edite imovel/brief.json se precisar
python3 imovelfilme.py video --projeto ~/imoveis/<nome> --trilha musica.mp3 [--formato 9x16]
#  → output/filme-16x9.mp4
```

`tudo` faz as quatro etapas de uma vez.

## Regras que não mudam

- **Nada inventado.** Campo que não está no anúncio não entra no vídeo.
- **A casa é a mesma.** Foto profissional e decoração virtual não mexem em parede, janela, porta,
  piso, bancada, sacada nem na vista. Ao revisar, compare lado a lado com a original e descarte o que mudou a arquitetura.
- **Aviso no fecho.** Quando há cômodo decorado, o último quadro diz "Imagens tratadas por IA · cômodos com decoração virtual".
- Nunca use API paga sem pedido explícito: as imagens saem do Codex logado (assinatura).

## Conferência antes de entregar

```bash
ffmpeg -v error -ss 0 -i output/filme-16x9.mp4 -frames:v 1 quadro0.jpg   # quadro 0 já cheio
ffprobe -v error -show_entries format=duration -of csv=p=0 output/filme-16x9.mp4
```

Olhe o quadro 0, uma cena de antes e depois e o fecho. Confira nome, preço e local escritos.
