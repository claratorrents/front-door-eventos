#!/usr/bin/env python3
"""Genera los planos esquemáticos (SVG) de cada espacio con los datos de data/espacios.json.

Solo usa lo que hay en los datos (decisión del equipo, 9 de noviembre):
  - el nombre del espacio;
  - las zonas que aparecen en los datos: horarios por zona (chatbot_guardrails.zone_end_times)
    y zona de las fotos aprobadas (media[].zone). Hoy: la terraza del Mirador y el patio del Jardí;
  - los aforos por montaje.
No dibuja medidas ni proporciones reales y no usa la description del plano.
Pie: "Plano orientativo · [nombre del espacio]".

Las etiquetas salen en el idioma de la conversación: plano.svg (castellano, en la ruta de la url
de su elemento de media) y plano.en.svg (inglés, al lado). Montajes: Cóctel / Teatro / Banquete /
Taller y Cocktail / Theatre / Banquet / Workshop (decisión del equipo, 9 de noviembre).
Uso:  python3 scripts/generar_planos.py
"""

import json
from pathlib import Path
from xml.sax.saxutils import escape

RAIZ = Path(__file__).resolve().parent.parent
ESPACIOS = RAIZ / "data" / "espacios.json"

# Textos por idioma (montajes en el orden del catálogo)
TEXTOS = {
    "es": {"montajes": ["Cóctel", "Teatro", "Banquete", "Taller"], "pie": "Plano orientativo",
           "alt": "Plano orientativo de", "zonas": {"terraza": "Terraza", "patio": "Patio"}},
    "en": {"montajes": ["Cocktail", "Theatre", "Banquet", "Workshop"], "pie": "Indicative floor plan",
           "alt": "Indicative floor plan of", "zonas": {"terraza": "Terrace", "patio": "Courtyard"}},
}
CLAVES_MONTAJE = ["cocktail", "theater", "banquet", "classroom"]
ANCHO, ALTO = 640, 400


def zonas(esp):
    """Zonas que aparecen en los datos, sin repetir, en orden de aparición."""
    vistas = list(esp.get("chatbot_guardrails", {}).get("zone_end_times", {}))
    vistas += [m["zone"] for m in esp.get("media", []) if m.get("approved") is True and m.get("zone")]
    return list(dict.fromkeys(z.strip().lower() for z in vistas if z.strip()))


def generar_svg(esp, idioma="es"):
    tx = TEXTOS[idioma]
    nombre = escape(esp["name"])
    z = zonas(esp)
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ANCHO} {ALTO}" width="{ANCHO}" height="{ALTO}" '
        f'role="img" aria-label="{tx["alt"]} {nombre}" font-family="Helvetica, Arial, sans-serif">',
        f'<rect x="0" y="0" width="{ANCHO}" height="{ALTO}" fill="#ffffff"/>',
    ]
    # Bloque principal (sin escala) y, a su derecha, una caja por zona de los datos
    x0, y0, alto = 30, 30, 260
    ancho_principal = 380 if z else 580
    partes.append(f'<rect x="{x0}" y="{y0}" width="{ancho_principal}" height="{alto}" fill="#f4f1ec" '
                  f'stroke="#55524d" stroke-width="2"/>')
    partes.append(f'<text x="{x0 + ancho_principal / 2}" y="{y0 + alto / 2}" text-anchor="middle" '
                  f'font-size="20" fill="#2b2926">{nombre}</text>')
    if z:
        alto_zona = (alto - 10 * (len(z) - 1)) / len(z)
        for i, zona in enumerate(z):
            y = y0 + i * (alto_zona + 10)
            partes.append(f'<rect x="{x0 + ancho_principal + 10}" y="{y}" width="190" height="{alto_zona}" '
                          f'fill="#e6efe4" stroke="#55524d" stroke-width="2" stroke-dasharray="6 4"/>')
            partes.append(f'<text x="{x0 + ancho_principal + 105}" y="{y + alto_zona / 2}" text-anchor="middle" '
                          f'font-size="18" fill="#2b2926">{escape(tx["zonas"].get(zona, zona.capitalize()))}</text>')
    # Tabla de aforos por montaje
    cap = esp.get("capacities", {})
    y_tabla = y0 + alto + 35
    for i, (clave, etiqueta) in enumerate(zip(CLAVES_MONTAJE, tx["montajes"])):
        x = x0 + i * 145
        partes.append(f'<text x="{x}" y="{y_tabla}" font-size="15" fill="#55524d">{etiqueta}</text>')
        partes.append(f'<text x="{x}" y="{y_tabla + 22}" font-size="18" font-weight="bold" fill="#2b2926">'
                      f'{int(cap.get(clave, 0))}</text>')
    partes.append(f'<text x="{x0}" y="{ALTO - 12}" font-size="13" fill="#55524d">'
                  f'{tx["pie"]} · {nombre}</text>')
    partes.append("</svg>")
    return "\n".join(partes) + "\n"


def main():
    with open(ESPACIOS, encoding="utf-8") as f:
        espacios = json.load(f)["venues"]
    for esp in espacios:
        for m in esp.get("media", []):
            if m.get("type") == "plano" and m.get("approved") is True and m.get("url", "").endswith(".svg"):
                destino = RAIZ / m["url"].lstrip("/")
                destino.parent.mkdir(parents=True, exist_ok=True)
                destino.write_text(generar_svg(esp, "es"), encoding="utf-8")
                destino.with_name(destino.stem + ".en.svg").write_text(generar_svg(esp, "en"), encoding="utf-8")
                print(f"{esp['id']}: {destino.relative_to(RAIZ)} y .en.svg (zonas: {', '.join(zonas(esp)) or 'ninguna'})")


if __name__ == "__main__":
    main()
