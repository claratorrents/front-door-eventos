#!/usr/bin/env python3
"""Comprueba los planos SVG generados por generar_planos.py.

Uso:  python3 scripts/test_generar_planos.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from generar_planos import ESPACIOS, RAIZ, generar_svg, zonas  # noqa: E402

espacios = json.load(open(ESPACIOS, encoding="utf-8"))["venues"]
resultados = []


def comprobar(nombre, ok, detalle=""):
    resultados.append(ok)
    print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
    if not ok and detalle:
        print(f"      {detalle}")


for esp in espacios:
    svg = generar_svg(esp, "es")
    try:
        ET.fromstring(svg)
        xml_ok = True
    except ET.ParseError as e:
        xml_ok, svg = False, str(e)
    plano = next(m for m in esp["media"] if m["type"] == "plano")
    archivo = RAIZ / plano["url"].lstrip("/")
    cap = esp["capacities"]
    comprobar(f"{esp['id']}: SVG válido, nombre, pie, 4 aforos y sin description; archivo en la url",
              xml_ok and esp["name"] in svg and f"Plano orientativo · {esp['name']}" in svg
              and all(f">{cap[k]}<" in svg for k in ("cocktail", "theater", "banquet", "classroom"))
              and plano["description"] not in svg
              and archivo.exists() and archivo.read_text(encoding="utf-8") == svg)

z = {e["id"]: zonas(e) for e in espacios}
# Inglés y etiquetas de montaje (Taller / Workshop)
for esp in espacios:
    plano = next(m for m in esp["media"] if m["type"] == "plano")
    archivo_en = (RAIZ / plano["url"].lstrip("/")).with_name("plano.en.svg")
    svg_es, svg_en = generar_svg(esp, "es"), generar_svg(esp, "en")
    comprobar(f"{esp['id']}: etiquetas Cóctel/Teatro/Banquete/Taller y Cocktail/Theatre/Banquet/Workshop; plano.en.svg",
              all(x in svg_es for x in ("Cóctel", "Teatro", "Banquete", "Taller")) and "Escuela" not in svg_es
              and all(x in svg_en for x in ("Cocktail", "Theatre", "Banquet", "Workshop", "Indicative floor plan"))
              and archivo_en.exists() and archivo_en.read_text(encoding="utf-8") == svg_en)
comprobar("zona en inglés: Terrace en el Mirador",
          "Terrace" in generar_svg(next(e for e in espacios if e["id"] == "sp-mirador-montjuic"), "en"))

comprobar("zonas solo donde están en los datos: terraza del Mirador y patio del Jardí",
          z == {"sp-llum-poblenou": [], "sp-jardi-gracia": ["patio"], "sp-mirador-montjuic": ["terraza"],
                "sp-atelier-sant-antoni": [], "sp-forum-les-corts": [], "sp-nau-besos": []}, z)

print(f"\n{sum(resultados)}/{len(resultados)} casos correctos")
sys.exit(0 if all(resultados) else 1)
