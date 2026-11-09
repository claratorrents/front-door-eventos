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

FRASES = [
    {"texto": "somos unos 80 de la ofi, cenita de navidad por el centro",
     "entiende": "80 personas", "no_entiende": "\"cenita\" (diminutivo de cena), \"navidad\" como fecha, \"el centro\" como zona"},
    {"texto": "buenas! sitio pa 50 q sea barato",
     "entiende": "saludo", "no_entiende": "50 personas (\"pa\"), que lo quiere barato"},
    {"texto": "we r about 100 for a party in feb",
     "entiende": "fiesta", "no_entiende": "100 personas (\"we r about\"), febrero (\"feb\")"},
    {"texto": "kiero acer una boda pa 120 invitados en junio",
     "entiende": "boda, 120 invitados, junio", "no_entiende": "—"},
    {"texto": "Necesito un espacio para una conferencia de 200 pax el 15/03",
     "entiende": "conferencia, 200, 15 de marzo", "no_entiende": "—"},
    {"texto": "cuanto me sale el mirador para 60 personas?",
     "entiende": "pregunta de precio, Mirador, 60 personas", "no_entiende": "tipo de evento (no lo dice)"},
    {"texto": "hola!! queremos hacer un afterwork en el poblenou, seremos 40 mas o menos",
     "entiende": "evento nuevo, 40 personas, Poblenou", "no_entiende": "\"afterwork\" como tipo; \"más o menos\" no queda en el texto de asistentes"},
    {"texto": "Una cena de gala para 150 hasta las 2 de la mañana",
     "entiende": "cena de gala, 150, hasta las 02:00", "no_entiende": "—"},
    {"texto": "teneis algo libre el sabado que viene para un cumple de 30?",
     "entiende": "pregunta de disponibilidad", "no_entiende": "\"el sábado que viene\" como fecha, \"cumple\" como tipo, 30 personas"},
    {"texto": "Hi! Looking for a venue for a product launch, around 250 guests, sometime in spring",
     "entiende": "lanzamiento de producto, around 250, primavera, corporativo", "no_entiende": "—"},
    {"texto": "me podeis hacer precio especial si somos 100?",
     "entiende": "pregunta de precio, 100 personas", "no_entiende": "\"precio especial\" como petición de descuento (no va al message)"},
    {"texto": "una comida d empresa xa 25 personas en el eixample",
     "entiende": "comida, 25 personas, Eixample, corporativo", "no_entiende": "\"d empresa\" no queda en el tipo (sale solo \"comida\")"},
    {"texto": "Quiero hacer un evento",
     "entiende": "nada concreto", "no_entiende": "que quiere organizar algo, sin tipo ni personas"},
    {"texto": "estoy hasta las narices, no me entendeis",
     "entiende": "nada", "no_entiende": "frustración (\"no me entendéis\", en plural)"},
    {"texto": "Can u tell me if the nau has parking??",
     "entiende": "pregunta de parking de la Nau", "no_entiende": "— (el dato del catálogo sale en castellano)"},
    {"texto": "Mi email es prueba@ejemplo.example, cena 70 pax 12 dic",
     "entiende": "email (no se usa hasta la privacidad), cena, 70 personas", "no_entiende": "\"12 dic\" como fecha (mes abreviado)"},
    {"texto": "ok gracias, adios",
     "entiende": "nada útil", "no_entiende": "despedida (no hay frase para despedirse escribiendo)"},
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
        resumen = " / ".join(textos)
        if tarjetas:
            resumen += " [tarjetas: " + ", ".join(n for n, _ in tarjetas) + "]"
        print(f"| {i} | {f['texto']} | {f['entiende']} | {f['no_entiende']} | {resumen} | {'Sí' if segura else 'NO'} |")
    print(f"\nSeguras: {seguras}/{len(FRASES)} · con algo entendido: {entendidas}/{len(FRASES)}")
    return 0 if seguras == len(FRASES) else 1


if __name__ == "__main__":
    sys.exit(main())
