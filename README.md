# 🏠 imovelfilme

[![Seu anúncio vira filme](guia/assets/banner.jpg)](https://inematds.github.io/imovelfilme/guia/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## O que é

O imovelfilme é uma ferramenta gratuita que transforma o anúncio de um imóvel num vídeo curto de divulgação. Serve para corretor, imobiliária ou dono que quer postar o imóvel nas redes sem contratar fotógrafo nem editor. Você informa o link; ele lê os dados que estão no anúncio, melhora as fotos, cria versões decoradas dos cômodos e monta um filme de 30 segundos com trilha. Precisa de um computador com Python, Node.js, FFmpeg e o Codex logado na sua assinatura.

## 📖 Guia de uso

Guia completo (landing + passo a passo + vídeo): **https://inematds.github.io/imovelfilme/guia/**

## Como funciona

```
link do anúncio → dados verificados → até 10 fotos → foto profissional → decoração virtual → brief → filme MP4
```

1. **Ler o anúncio** (`engine/extrair.py`): JSON-LD, `og:`, marcações `data-imovel` e texto da página. Cada campo guarda a fonte; o que não está no anúncio fica de fora.
2. **Fotos** (`engine/fotos.py`): até 10, uma por cômodo antes de repetir. O Codex (`image_gen`, pela assinatura) faz a versão profissional de cada foto e a decoração virtual de sala, cozinha e quartos. A cor é neutralizada (o gerador puxa para o amarelo).
3. **Brief** (`engine/brief.py`): 4 a 8 fatos fortes (quartos, área, banheiros, vagas, destaques).
4. **Filme** (`engine/video.py`): composição HyperFrames (HTML + GSAP) → MP4 16:9 ou 9:16; trilha mixada a −14 LUFS.

## Uso

```bash
git clone https://github.com/inematds/imovelfilme && cd imovelfilme
npm i
python3 imovelfilme.py estilos
python3 imovelfilme.py tudo "https://seusite.com.br/imoveis/apto-1202" --projeto ~/imoveis/apto1202 \
  --estilo praia-contemporaneo --trilha assets/trilhas/elegante.mp3
```

Etapas soltas: `extrair`, `fotos`, `brief`, `video` (mesmos parâmetros). A pasta do imóvel fica assim:

```
apto1202/
  imovel/anuncio.json  brief.json  brief.md
  fotos/original/  profissional/  decorada/
  video/16x9/        (composição HyperFrames)
  output/filme-16x9.mp4
```

## Demo

`samples/anuncio-demo/` é um anúncio **fictício** (fotos geradas por IA) para testar sem depender de site de terceiros:

```bash
python3 -m http.server 8941 --directory samples/anuncio-demo &
python3 imovelfilme.py tudo http://127.0.0.1:8941/ --projeto projetos/demo --trilha assets/trilhas/elegante.mp3
```

O vídeo de apresentação (`promo/promo.py`) é feito com o próprio motor a partir do resultado do demo.

## Regras

- Nada inventado: campo ausente no anúncio não aparece no vídeo.
- Foto profissional e decoração virtual não mudam parede, janela, porta, piso, bancada, sacada nem vista.
- Quando há cômodo decorado, o fecho do vídeo avisa: "Imagens tratadas por IA · cômodos com decoração virtual".
- Use fotos que você pode publicar. Marca d'água só sai de foto sua ou autorizada.
- Portais que carregam as fotos por script: salve a página e passe o `.html`.

## Testes

```bash
python3 -m unittest discover -s tests
```

## Licença

MIT. Fontes Sora e Inter: SIL OFL 1.1. Trilhas em `assets/trilhas/`: geradas localmente com o MusicGen-small (modelo CC-BY-NC; uso não comercial).

---

[INEMA.CLUB](https://inema.club)
