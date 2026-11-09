#!/usr/bin/env python3
"""Frases difíciles: tests de límites del chat por reglas (no tienen que entenderse todas).

Frases sintéticas que un cliente real podría escribir: coloquiales, con faltas, sin tildes o con
varios datos mezclados. Para cada una se apunta qué entiende y qué no. Lo que SÍ es obligatorio:
ninguna respuesta lleva precio, promesa, porcentaje, ruta de archivo ni dato inventado, y el chatbot
nunca se queda callado.

Uso:  python3 chat/frases_dificiles.py        (imprime la tabla; sale con 1 si alguna respuesta no es segura)
"""

import re
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from conversacion import Conversacion  # noqa: E402
from entender_reglas import entender  # noqa: E402
from variantes import HOY  # noqa: E402

# "limites": lo que se queda sin entender a propósito (límites conocidos, decisión del equipo del 9/11):
# diminutivos ("cenita"), "pa", "q", "we r", "d empresa".
FRASES = [
    {"texto": "somos unos 80 de la ofi, cenita de navidad por el centro",
     "entiende": "80 personas", "no_entiende": "\"navidad\" como fecha, \"el centro\" como zona",
     "limites": "\"cenita\" (diminutivo)"},
    {"texto": "buenas! sitio pa 50 q sea barato",
     "entiende": "saludo", "no_entiende": "que lo quiere barato", "limites": "\"pa\" (50 personas), \"q\""},
    {"texto": "we r about 100 for a party in feb",
     "entiende": "fiesta, febrero", "no_entiende": "—", "limites": "\"we r\" (100 personas)"},
    {"texto": "kiero acer una boda pa 120 invitados en junio",
     "entiende": "boda, 120 invitados, junio", "no_entiende": "—", "limites": ""},
    {"texto": "Necesito un espacio para una conferencia de 200 pax el 15/03",
     "entiende": "conferencia, 200, 15 de marzo", "no_entiende": "—", "limites": ""},
    {"texto": "cuanto me sale el mirador para 60 personas?",
     "entiende": "pregunta de precio, Mirador, 60 personas", "no_entiende": "tipo de evento (no lo dice)", "limites": ""},
    {"texto": "hola!! queremos hacer un afterwork en el poblenou, seremos 40 mas o menos",
     "entiende": "afterwork (networking), 40 personas, Poblenou",
     "no_entiende": "\"más o menos\" no queda en el texto de asistentes", "limites": ""},
    {"texto": "Una cena de gala para 150 hasta las 2 de la mañana",
     "entiende": "cena de gala, 150, hasta las 02:00", "no_entiende": "—", "limites": ""},
    {"texto": "teneis algo libre el sabado que viene para un cumple de 30?",
     "entiende": "pregunta de disponibilidad, cumple (fiesta)",
     "no_entiende": "\"el sábado que viene\" como fecha, \"de 30\" sin \"personas\"", "limites": ""},
    {"texto": "Hi! Looking for a venue for a product launch, around 250 guests, sometime in spring",
     "entiende": "lanzamiento de producto, around 250, primavera, corporativo", "no_entiende": "—", "limites": ""},
    {"texto": "me podeis hacer precio especial si somos 100?",
     "entiende": "precio especial (descuento, al message), 100 personas", "no_entiende": "—", "limites": ""},
    {"texto": "una comida d empresa xa 25 personas en el eixample",
     "entiende": "comida, 25 personas, Eixample, corporativo", "no_entiende": "—", "limites": "\"d empresa\" (no queda en el tipo)"},
    {"texto": "Quiero hacer un evento",
     "entiende": "nada concreto", "no_entiende": "que quiere organizar algo, sin tipo ni personas", "limites": ""},
    {"texto": "estoy hasta las narices, no me entendeis",
     "entiende": "frustración", "no_entiende": "—", "limites": ""},
    {"texto": "Can u tell me if the nau has parking??",
     "entiende": "pregunta de parking de la Nau", "no_entiende": "— (el dato del catálogo sale en castellano)", "limites": ""},
    {"texto": "Mi email es prueba@ejemplo.example, cena 70 pax 12 dic",
     "entiende": "email (no se usa hasta la privacidad), cena, 70 personas, 12 de diciembre", "no_entiende": "—", "limites": ""},
    {"texto": "ok gracias, adios",
     "entiende": "despedida", "no_entiende": "—", "limites": ""},
    # Añadidas el 9/11
    {"texto": "afterwork en el poblenou para 40",
     "entiende": "afterwork (networking), Poblenou, 40", "no_entiende": "—", "limites": ""},
    {"texto": "cumple de 30 personas en marzo",
     "entiende": "cumple (fiesta), 30 personas, marzo", "no_entiende": "—", "limites": ""},
    {"texto": "no me entendéis",
     "entiende": "frustración", "no_entiende": "—", "limites": ""},
    {"texto": "precio especial si somos 100",
     "entiende": "precio especial (descuento), 100 personas", "no_entiende": "—", "limites": ""},
    {"texto": "boda para 120 el 15 dic",
     "entiende": "boda, 120, 15 de diciembre", "no_entiende": "—", "limites": ""},
]

PROHIBIDO = re.compile(r"€|\d+ ?%|\bconfirmad[ao]s?\b|\bconfirmed\b|está libre|is free|\breservad[ao]\b|"
                       r"/media/placeholders|https?://|ocupaci[oó]n|te llamamos hoy|en \d+ ?h\b", re.I)


def respuesta(texto):
    cv = Conversacion("conv-dificil", hoy=HOY, registro=Path(tempfile.mkdtemp()) / "r.jsonl")
    salida = cv.recibir(texto=texto)
    textos = [m["texto"] for m in salida["mensajes"] if m["tipo"] == "texto"][1:]   # sin el aviso de IA
    tarjetas = [(t["nombre"], " ".join(t["lineas"])) for m in salida["mensajes"] if m["tipo"] == "tarjetas"
                for t in m["tarjetas"]]
    return textos, tarjetas


def main():
    seguras, entendidas = 0, 0
    print("| # | Frase | Entiende | No entiende | Respuesta del chatbot | ¿Segura? |")
    print("|---|---|---|---|---|---|")
    for i, f in enumerate(FRASES, 1):
        textos, tarjetas = respuesta(f["texto"])
        todo = " ".join(textos + [n + " " + lineas for n, lineas in tarjetas])
        segura = bool(textos) and not PROHIBIDO.search(todo)
        seguras += segura
        e = entender(f["texto"], {"hoy": HOY})
        entendidas += e["entendido"] and f["entiende"] not in ("nada", "nada concreto", "nada útil")
        no_entiende = f["no_entiende"] + (f" · límite conocido: {f['limites']}" if f["limites"] else "")
        resumen = " / ".join(textos)
        if tarjetas:
            resumen += " [tarjetas: " + ", ".join(n for n, _ in tarjetas) + "]"
        print(f"| {i} | {f['texto']} | {f['entiende']} | {no_entiende} | {resumen} | {'Sí' if segura else 'NO'} |")
    print(f"\nSeguras: {seguras}/{len(FRASES)} · con algo entendido: {entendidas}/{len(FRASES)}")
    return 0 if seguras == len(FRASES) else 1


if __name__ == "__main__":
    sys.exit(main())
