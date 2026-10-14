"""Etapa 1 e 2: lê o anúncio (URL ou arquivo local) e separa os dados verificáveis e as fotos.

Sem API e sem IA: só HTML. Fontes, em ordem de confiança:
  1. JSON-LD (schema.org: Product, Offer, Residence, Apartment, House, RealEstateListing...)
  2. <meta property="og:*"> e <meta name="description">
  3. marcações data-imovel="<campo>" (o anúncio-demo usa; sites próprios podem usar)
  4. padrões no texto da página (quartos, banheiros, m², preço)

Campo que não aparece em nenhuma fonte fica de fora. Nada é inventado.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140 Safari/537.36"
MAX_FOTOS = 10

# palavras que indicam o tipo de cômodo no nome do arquivo, no alt ou na legenda
COMODOS = [
    ("fachada", ["fachada", "exterior", "facade", "building", "predio", "prédio", "frente"]),
    ("sala", ["sala", "living", "estar", "lounge"]),
    ("cozinha", ["cozinha", "kitchen", "gourmet"]),
    ("suite", ["suite", "suíte", "quarto", "dormitorio", "dormitório", "bedroom", "master"]),
    ("banheiro", ["banheiro", "bathroom", "lavabo", "wc", "bath"]),
    ("sacada", ["sacada", "varanda", "balcony", "terraco", "terraço", "terrace"]),
    ("vista", ["vista", "view", "panorama", "mar", "sea"]),
    ("lazer", ["piscina", "pool", "academia", "gym", "lazer", "salao", "salão", "amenit"]),
]
ORDEM = [c for c, _ in COMODOS]
INTERNOS = {"sala", "cozinha", "suite"}  # banheiro decorado quase não muda


class _Leitor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}
        self.jsonld: list[str] = []
        self.imgs: list[dict] = []
        self.marcados: dict[str, str] = {}
        self.titulo = ""
        self.texto: list[str] = []
        self._pilha: list[tuple[str, str | None]] = []
        self._em_jsonld = False
        self._em_title = False
        self._ignorar = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "meta":
            k = a.get("property") or a.get("name")
            if k and a.get("content"):
                self.meta[k.lower()] = a["content"].strip()
        elif tag == "script":
            self._em_jsonld = (a.get("type") or "").lower() == "application/ld+json"
            if not self._em_jsonld:
                self._ignorar += 1
        elif tag == "style":
            self._ignorar += 1
        elif tag == "title":
            self._em_title = True
        elif tag == "img":
            src = a.get("data-src") or a.get("src") or ""
            if a.get("srcset") and not src:
                src = a["srcset"].split(",")[-1].strip().split(" ")[0]
            if src and not src.startswith("data:"):
                self.imgs.append({"src": src, "alt": a.get("alt", ""),
                                  "comodo": a.get("data-comodo", ""),
                                  "w": a.get("width"), "h": a.get("height")})
        campo = a.get("data-imovel")
        self._pilha.append((tag, campo))

    def handle_endtag(self, tag):
        if tag == "script":
            if not self._em_jsonld:
                self._ignorar = max(0, self._ignorar - 1)
            self._em_jsonld = False
        elif tag == "style":
            self._ignorar = max(0, self._ignorar - 1)
        elif tag == "title":
            self._em_title = False
        while self._pilha:
            t, _ = self._pilha.pop()
            if t == tag:
                break

    def handle_data(self, data):
        if self._em_jsonld:
            self.jsonld.append(data)
            return
        if self._ignorar:
            return
        if self._em_title:
            self.titulo += data
        s = data.strip()
        if not s:
            return
        self.texto.append(s)
        for _, campo in reversed(self._pilha):
            if campo:
                self.marcados[campo] = (self.marcados.get(campo, "") + " " + s).strip()
                break


def baixar(url: str, timeout: int = 30) -> bytes:
    if re.match(r"^[a-z]+://", url) and not url.startswith("file://"):
        req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    caminho = url[7:] if url.startswith("file://") else url
    return Path(caminho).read_bytes()


def _jsonld_objetos(blocos: list[str]) -> list[dict]:
    out = []
    for b in blocos:
        try:
            d = json.loads(b)
        except json.JSONDecodeError:
            continue
        pilha = d if isinstance(d, list) else [d]
        while pilha:
            o = pilha.pop()
            if isinstance(o, dict):
                out.append(o)
                pilha.extend(o.get("@graph", []) if isinstance(o.get("@graph"), list) else [])
    return out


def _num(s) -> float | None:
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return float(s)
    m = re.search(r"\d[\d.,]*", str(s))
    if not m:
        return None
    t = m.group(0)
    if re.search(r",\d{1,2}$", t):  # 1.234,56
        t = t.replace(".", "").replace(",", ".")
    else:
        t = t.replace(".", "").replace(",", "")
    try:
        return float(t)
    except ValueError:
        return None


def _do_texto(texto: str) -> dict:
    """Padrões simples no texto corrido. Só pega o que está escrito com número explícito."""
    t = " " + texto.lower() + " "
    out = {}
    pad = {
        "quartos": r"(\d+)\s*(?:quartos?|dormit[óo]rios?|bedrooms?|beds?)\b",
        "suites": r"(\d+)\s*su[íi]tes?\b",
        "banheiros": r"(\d+)\s*(?:banheiros?|bathrooms?|baths?)\b",
        "vagas": r"(\d+)\s*(?:vagas?|garagens?|parking)\b",
        "area_m2": r"(\d[\d.,]*)\s*(?:m²|m2|metros quadrados)",
        "area_sqft": r"(\d[\d.,]*)\s*(?:sq\.?\s*ft|sqft|square feet)",
    }
    for campo, rx in pad.items():
        m = re.search(rx, t)
        if m:
            out[campo] = _num(m.group(1))
    m = re.search(r"(r\$|us\$|aed|usd|€|\$)\s*([\d.,]+(?:\s*(?:mil|milhões|milhão|m|k))?)", t)
    if m:
        out["preco_texto"] = (m.group(1).upper().replace("R$", "R$") + " " + m.group(2)).strip()
    return out


def _classificar(img: dict) -> str:
    if img.get("comodo"):
        return img["comodo"].lower()
    alvo = (img["src"].rsplit("/", 1)[-1] + " " + img.get("alt", "")).lower()
    for comodo, chaves in COMODOS:
        if any(k in alvo for k in chaves):
            return comodo
    return "outro"


def _boa_foto(img: dict) -> bool:
    src = img["src"].lower()
    if any(k in src for k in ("logo", "icon", "sprite", "avatar", "pixel", "tracking", ".svg", ".gif", "banner-ad")):
        return False
    for k in ("w", "h"):
        v = _num(img.get(k))
        if v is not None and v < 300:
            return False
    return True


def ler_anuncio(url: str) -> dict:
    html = baixar(url).decode("utf-8", errors="replace")
    p = _Leitor()
    p.feed(html)
    dados: dict = {"fonte": url}
    fontes: dict[str, str] = {}

    def por(campo, valor, origem):
        if valor in (None, "", []) or campo in dados:
            return
        dados[campo] = valor
        fontes[campo] = origem

    # 1. JSON-LD
    for o in _jsonld_objetos(p.jsonld):
        tipo = o.get("@type")
        tipo = " ".join(tipo) if isinstance(tipo, list) else str(tipo or "")
        if not re.search(r"Product|Offer|Residence|Apartment|House|Accommodation|RealEstate|SingleFamily|Place", tipo):
            continue
        por("nome", o.get("name"), "json-ld")
        por("descricao", o.get("description"), "json-ld")
        end = o.get("address")
        if isinstance(end, dict):
            local = ", ".join(x for x in [end.get("streetAddress"), end.get("addressLocality"), end.get("addressRegion")] if x)
            por("local", local, "json-ld")
        elif isinstance(end, str):
            por("local", end, "json-ld")
        por("quartos", _num(o.get("numberOfRooms") or o.get("numberOfBedrooms")), "json-ld")
        por("banheiros", _num(o.get("numberOfBathroomsTotal") or o.get("numberOfBathrooms")), "json-ld")
        fs = o.get("floorSize")
        if isinstance(fs, dict):
            und = str(fs.get("unitCode") or fs.get("unitText") or "").upper()
            por("area_sqft" if und in ("FTK", "SQFT", "FT2") else "area_m2", _num(fs.get("value")), "json-ld")
        ofs = o.get("offers")
        ofs = ofs[0] if isinstance(ofs, list) and ofs else ofs
        if isinstance(ofs, dict) and ofs.get("price"):
            por("preco", _num(ofs["price"]), "json-ld")
            por("moeda", ofs.get("priceCurrency"), "json-ld")
        am = o.get("amenityFeature")
        if isinstance(am, list):
            por("comodidades", [a.get("name") for a in am if isinstance(a, dict) and a.get("name")], "json-ld")
    # 2. og / meta
    por("nome", p.meta.get("og:title"), "og:title")
    por("descricao", p.meta.get("og:description") or p.meta.get("description"), "meta")
    # 3. marcações data-imovel
    for campo, valor in p.marcados.items():
        if campo in ("quartos", "banheiros", "suites", "vagas", "area_m2", "area_sqft", "preco", "andar"):
            por(campo, _num(valor), "data-imovel")
        elif campo in ("comodidades", "destaques"):
            por(campo, [x.strip() for x in re.split(r"[;•|\n]", valor) if x.strip()], "data-imovel")
        else:
            por(campo, valor, "data-imovel")
    # 4. texto corrido
    for campo, valor in _do_texto(" ".join(p.texto)).items():
        por(campo, valor, "texto da página")
    por("nome", p.titulo.strip(), "<title>")

    # fotos
    vistos, fotos = set(), []
    og_img = p.meta.get("og:image")
    cand = ([{"src": og_img, "alt": "og:image", "comodo": ""}] if og_img else []) + p.imgs
    for img in cand:
        absoluto = urllib.parse.urljoin(url if re.match(r"^[a-z]+://", url) else Path(url).resolve().as_uri(), img["src"])
        chave = re.sub(r"[?#].*$", "", absoluto)
        if chave in vistos or not _boa_foto(img):
            continue
        vistos.add(chave)
        fotos.append({"url": absoluto, "alt": img.get("alt", ""), "comodo": _classificar(img)})
    dados["fotos_encontradas"] = len(fotos)
    dados["_fontes"] = fontes
    return {"dados": dados, "fotos": fotos}


def escolher_fotos(fotos: list[dict], maximo: int = MAX_FOTOS) -> list[dict]:
    """No máximo `maximo` fotos: uma por cômodo na ordem de prioridade, depois o resto sem repetir demais."""
    por_comodo: dict[str, list[dict]] = {}
    for f in fotos:
        por_comodo.setdefault(f["comodo"], []).append(f)
    escolha = []
    for c in ORDEM + ["outro"]:
        if por_comodo.get(c):
            escolha.append(por_comodo[c].pop(0))
    for c in ORDEM + ["outro"]:
        while por_comodo.get(c) and len(escolha) < maximo:
            escolha.append(por_comodo[c].pop(0))
    return escolha[:maximo]


def salvar(url: str, projeto: Path, maximo: int = MAX_FOTOS) -> dict:
    lido = ler_anuncio(url)
    info = projeto / "imovel"
    orig = projeto / "fotos" / "original"
    info.mkdir(parents=True, exist_ok=True)
    orig.mkdir(parents=True, exist_ok=True)
    escolha = escolher_fotos(lido["fotos"], maximo)
    salvas = []
    for i, f in enumerate(escolha, 1):
        ext = Path(urllib.parse.urlparse(f["url"]).path).suffix.lower()
        ext = ext if ext in (".jpg", ".jpeg", ".png", ".webp") else ".jpg"
        nome = f"{i:02d}-{f['comodo']}{ext}"
        try:
            (orig / nome).write_bytes(baixar(f["url"]))
        except Exception as e:  # foto quebrada não derruba o resto
            print(f"  foto ignorada ({f['url']}): {e}")
            continue
        salvas.append({**f, "arquivo": f"fotos/original/{nome}", "interno": f["comodo"] in INTERNOS})
    anuncio = {"dados": lido["dados"], "fotos": salvas}
    (info / "anuncio.json").write_text(json.dumps(anuncio, ensure_ascii=False, indent=1) + "\n")
    return anuncio
