# 🏠 imovelfilme

[![Tu anuncio se vuelve película](guia/assets/banner-es.jpg)](https://inematds.github.io/imovelfilme/guia/es/)

**🇧🇷 [Português](README.md) · 🇺🇸 [English](README.en.md) · 🇪🇸 [Español](README.es.md)**

## Qué es

imovelfilme es una herramienta gratuita que convierte el anuncio de un inmueble en un video corto de promoción. Sirve para corredores, inmobiliarias o dueños que quieren publicar el inmueble en redes sin contratar fotógrafo ni editor. Tú indicas el enlace; la herramienta lee los datos que están en el anuncio, mejora las fotos, crea versiones decoradas de los ambientes y arma una película de 30 segundos con música. Necesita una computadora con Python, Node.js, FFmpeg y Codex con la sesión iniciada en tu suscripción.

## 📖 Guía de uso

Guía completa (landing + paso a paso + video): **https://inematds.github.io/imovelfilme/guia/es/**

## Cómo funciona

```
enlace del anuncio → datos verificados → hasta 10 fotos → foto profesional → decoración virtual → brief → película MP4
```

1. **Leer el anuncio** (`engine/extrair.py`): JSON-LD, `og:`, marcado `data-imovel` y texto de la página. Cada campo guarda la fuente; lo que no está en el anuncio queda fuera.
2. **Fotos** (`engine/fotos.py`): hasta 10, una por ambiente antes de repetir. Codex (`image_gen`, con la suscripción) hace la versión profesional de cada foto y la decoración virtual de sala, cocina y dormitorios. El color se neutraliza (el generador tira hacia el amarillo).
3. **Brief** (`engine/brief.py`): de 4 a 8 datos fuertes (dormitorios, superficie, baños, cocheras, destacados).
4. **Película** (`engine/video.py`): composición HyperFrames (HTML + GSAP) → MP4 16:9 o 9:16; música mezclada a −14 LUFS.

## Uso

```bash
git clone https://github.com/inematds/imovelfilme && cd imovelfilme
npm i
python3 imovelfilme.py estilos
python3 imovelfilme.py tudo "https://seusite.com.br/imoveis/apto-1202" --projeto ~/imoveis/apto1202 \
  --estilo praia-contemporaneo --trilha assets/trilhas/elegante.mp3
```

Etapas sueltas: `extrair`, `fotos`, `brief`, `video` (mismos parámetros). La carpeta del inmueble queda así:

```
apto1202/
  imovel/anuncio.json  brief.json  brief.md
  fotos/original/  profissional/  decorada/
  video/16x9/        (composición HyperFrames)
  output/filme-16x9.mp4
```

## Demo

`samples/anuncio-demo/` es un anuncio **ficticio** (fotos generadas por IA) para probar sin depender de un sitio de terceros:

```bash
python3 -m http.server 8941 --directory samples/anuncio-demo &
python3 imovelfilme.py tudo http://127.0.0.1:8941/ --projeto projetos/demo --trilha assets/trilhas/elegante.mp3
```

El video de presentación (`promo/promo.py`) se hace con el propio motor a partir del resultado del demo.

## Reglas

- Nada inventado: un campo ausente en el anuncio no aparece en el video.
- La foto profesional y la decoración virtual no cambian pared, ventana, puerta, piso, mesada, balcón ni vista.
- Cuando hay un ambiente decorado, el cierre del video avisa: "Imágenes tratadas por IA · ambientes con decoración virtual".
- Usa fotos que puedas publicar. La marca de agua solo se quita de fotos tuyas o autorizadas.
- Portales que cargan las fotos por script: guarda la página y pasa el `.html`.

## Pruebas

```bash
python3 -m unittest discover -s tests
```

## Licencia

MIT. Fuentes Sora e Inter: SIL OFL 1.1. Pistas en `assets/trilhas/`: generadas localmente con MusicGen-small (modelo CC-BY-NC; uso no comercial).

---

[INEMA.CLUB](https://inema.club)
