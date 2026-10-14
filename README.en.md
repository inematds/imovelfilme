# 🏠 imovelfilme

[![Your listing becomes a film](guia/assets/banner-en.jpg)](https://inematds.github.io/imovelfilme/guia/en/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## What it is

imovelfilme is a free tool that turns a property listing into a short promo video. It is for agents, real estate agencies or owners who want to post the property on social media without hiring a photographer or an editor. You give it the link; it reads the data in the listing, improves the photos, creates furnished versions of the rooms and assembles a 30-second film with a soundtrack. It needs a computer with Python, Node.js, FFmpeg and Codex logged in to your subscription.

## 📖 User guide

Full guide (landing + step by step + video): **https://inematds.github.io/imovelfilme/guia/en/**

## How it works

```
listing link → verified data → up to 10 photos → professional photo → virtual staging → brief → MP4 film
```

1. **Read the listing** (`engine/extrair.py`): JSON-LD, `og:`, `data-imovel` markup and page text. Each field records its source; anything not in the listing is left out.
2. **Photos** (`engine/fotos.py`): up to 10, one per room before repeating. Codex (`image_gen`, through your subscription) makes the professional version of each photo and the virtual staging of living room, kitchen and bedrooms. The color is neutralized (the generator drifts toward yellow).
3. **Brief** (`engine/brief.py`): 4 to 8 strong facts (bedrooms, area, bathrooms, parking spots, highlights).
4. **Film** (`engine/video.py`): HyperFrames composition (HTML + GSAP) → 16:9 or 9:16 MP4; soundtrack mixed at −14 LUFS.

## Usage

```bash
git clone https://github.com/inematds/imovelfilme && cd imovelfilme
npm i
python3 imovelfilme.py estilos
python3 imovelfilme.py tudo "https://seusite.com.br/imoveis/apto-1202" --projeto ~/imoveis/apto1202 \
  --estilo praia-contemporaneo --trilha assets/trilhas/elegante.mp3
```

Individual steps: `extrair`, `fotos`, `brief`, `video` (same parameters). The property folder ends up like this:

```
apto1202/
  imovel/anuncio.json  brief.json  brief.md
  fotos/original/  profissional/  decorada/
  video/16x9/        (HyperFrames composition)
  output/filme-16x9.mp4
```

## Demo

`samples/anuncio-demo/` is a **fictional** listing (AI-generated photos) for testing without depending on third-party sites:

```bash
python3 -m http.server 8941 --directory samples/anuncio-demo &
python3 imovelfilme.py tudo http://127.0.0.1:8941/ --projeto projetos/demo --trilha assets/trilhas/elegante.mp3
```

The intro video (`promo/promo.py`) is made with the engine itself from the demo result.

## Rules

- Nothing invented: a field missing from the listing does not appear in the video.
- Professional photo and virtual staging do not change walls, windows, doors, floors, countertops, balconies or the view.
- When a room is furnished, the closing of the video states: "AI-processed images · rooms with virtual staging".
- Use photos you are allowed to publish. A watermark is only removed from your own or authorized photos.
- Portals that load photos by script: save the page and pass the `.html`.

## Tests

```bash
python3 -m unittest discover -s tests
```

## License

MIT. Sora and Inter fonts: SIL OFL 1.1. Tracks in `assets/trilhas/`: generated locally with MusicGen-small (CC-BY-NC model; non-commercial use).

---

[INEMA.CLUB](https://inema.club)
