"""Testes sem rede e sem IA: extrator no anúncio-demo, brief e plano do vídeo.

  python3 -m unittest discover -s tests
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
from engine import brief, extrair, video  # noqa: E402

DEMO = RAIZ / "samples" / "anuncio-demo" / "index.html"


class TestExtrair(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_dados_do_demo(self):
        d = extrair.ler_anuncio(str(DEMO))["dados"]
        self.assertEqual(d["nome"], "Residencial Mirante Atlântico · apto 1202")
        self.assertEqual(d["local"], "Balneário Camboriú, SC")
        self.assertEqual((d["quartos"], d["banheiros"], d["area_m2"]), (3, 2, 118))
        self.assertEqual((d["preco"], d["moeda"]), (1890000, "BRL"))
        self.assertEqual(d["_fontes"]["preco"], "json-ld")
        self.assertIn("Sacada com churrasqueira", d["destaques"])

    def test_nao_inventa(self):
        f = self.tmp / "a.html"
        f.write_text("<html><head><title>Casa simples</title></head><body><p>Linda casa.</p></body></html>")
        d = extrair.ler_anuncio(str(f))["dados"]
        for campo in ("preco", "quartos", "area_m2", "local", "banheiros"):
            self.assertNotIn(campo, d)

    def test_fotos_sem_duplicata_e_limite(self):
        an = extrair.salvar(str(DEMO), self.tmp, maximo=4)
        self.assertEqual(len(an["fotos"]), 4)
        self.assertEqual(an["fotos"][0]["comodo"], "fachada")
        self.assertEqual(len({f["arquivo"] for f in an["fotos"]}), 4)
        for f in an["fotos"]:
            self.assertTrue((self.tmp / f["arquivo"]).stat().st_size > 10000)

    def test_texto_corrido(self):
        t = extrair._do_texto("Apartamento com 2 dormitórios, 1 suíte, 85,5 m² e 1 vaga por R$ 650.000")
        self.assertEqual((t["quartos"], t["suites"], t["vagas"], t["area_m2"]), (2, 1, 1, 85.5))


class TestBrief(unittest.TestCase):
    def test_preco_e_limite(self):
        b = brief.montar({"preco": 1890000, "moeda": "BRL", "quartos": 3, "suites": 1, "area_m2": 118,
                          "destaques": list("abcdefgh")})
        self.assertEqual(b["preco"], "R$ 1.890.000")
        self.assertEqual(b["fatos"][0]["texto"], "3 quartos · 1 suíte")
        self.assertLessEqual(len(b["fatos"]), 8)

    def test_sem_dado_sem_fato(self):
        self.assertEqual(brief.montar({"nome": "X"})["fatos"], [])


class TestPlano(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        extrair.salvar(str(DEMO), self.tmp)
        brief.salvar(self.tmp)
        (self.tmp / "fotos" / "decorada").mkdir(parents=True)
        shutil.copy(self.tmp / "fotos/original/02-sala.jpg", self.tmp / "fotos/decorada/02-sala.jpg")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_estrutura(self):
        pl = video.plano(self.tmp)
        tipos = [c["tipo"] for c in pl["cenas"]]
        self.assertEqual(tipos[0], "abertura")
        self.assertEqual(tipos[1], "preco")
        self.assertEqual(tipos[-1], "fecho")
        self.assertEqual(tipos.count("antes-depois"), 1)  # só a sala tem decorada
        self.assertTrue(pl["cenas"][-1]["aviso"])
        self.assertAlmostEqual(pl["total"], pl["cenas"][-1]["ini"] + pl["cenas"][-1]["dur"], places=3)

    def test_destaque_no_comodo_certo(self):
        cena = {c.get("comodo"): c.get("texto") for c in video.plano(self.tmp)["cenas"]}
        self.assertEqual(cena["sacada"], "Sacada com churrasqueira")
        self.assertEqual(cena["cozinha"], "Cozinha planejada")
        self.assertEqual(cena["sala"], "Janela panorâmica na sala")

    def test_html_tem_timeline(self):
        pl = video.plano(self.tmp)
        h = video.composicao(pl, {str(c[k]): "x.jpg" for c in pl["cenas"] for k in ("foto", "deco") if c.get(k)})
        self.assertIn('window.__timelines["main"]', h)
        self.assertIn("DECORAÇÃO VIRTUAL", h)
        self.assertNotIn("Math.random", h)
        self.assertEqual(h.count('class="clip cena"'), len(pl["cenas"]))


if __name__ == "__main__":
    unittest.main()
