#!/usr/bin/env python3
"""Recomienda espacios aplicando las reglas de la sección 2 de
.claude/skills/recomendador-espacios/SKILL.md.

Uso:
  python3 scripts/recomendar.py --asistentes 120 --disposicion banquet
  python3 scripts/recomendar.py --asistentes 100 --disposicion cocktail --hora-fin 03:00
  python3 scripts/recomendar.py --asistentes 180 --disposicion theater --dias 5

Salida (JSON):
  recomendados: [{id, nombre, ocupacion, grupo, alternativa, avisos_zona}]   (máximo 3, ya ordenados)
                avisos_zona: zonas que cierran antes de la hora de fin pedida, p. ej.
                [{"zona": "terraza", "hasta": "23:30"}]
                foto: foto de la tarjeta {id, description, illustrative} (skill media-espacios §2):
                nunca una no aprobada ni de una zona con aviso de cierre; la de la misma
                disposition; si no hay, mejor una de interior (sin zone) que una de zona.
                Sin la ruta: el chat la muestra por id.

Media aprobada de un espacio (skill media-espacios §3), sin rutas:
  python3 scripts/recomendar.py --media sp-jardi-gracia --tipo foto

Validar el espacio que ha elegido el cliente (skill router-intenciones §3):
  python3 scripts/recomendar.py --validar sp-mirador-montjuic --asistentes 300 \
      --disposicion cocktail --dias 127
  Devuelve si encaja y, si no, TODOS los motivos (aforo, antelacion, horario)
  con el dato que falla, más las alternativas de la recomendación normal.
  También avisos_zona y la foto de la tarjeta (foto_tarjeta), igual que la recomendación normal.
  Si el espacio encaja pero queda en bajo_60, añade opcion_comodo: la mejor opción comodo
  de la recomendación normal (mismos criterios: aforo de la disposición, antelación, horario,
  avisos de zona y foto). Si no hay ninguna comodo, no se añade nada.
  descartados:  [{id, nombre, motivo, detalle}]    (solo por antelación u horario)

Solo lee data/espacios.json. No da precios ni disponibilidad.
"""

import argparse
import json
import re
import sys
from fractions import Fraction
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESPACIOS = RAIZ / "data" / "espacios.json"

DISPOSICIONES = ("cocktail", "theater", "banquet", "classroom")
MAX_RECOMENDADOS = 3
# Fracciones exactas: con decimales, 70 % y 90 % no saldrían a la misma distancia del 80 %.
OBJETIVO = Fraction(80, 100)       # dentro de cada grupo, la ocupación más cercana al 80 %
LIMITE_COMODO = Fraction(90, 100)  # más del 90 % → al_limite
MINIMO_COMODO = Fraction(60, 100)  # menos del 60 % → bajo_60
HORA_MADRUGADA = 8       # antes de las 08:00 cuenta como día siguiente
ORDEN_GRUPOS = {"comodo": 0, "al_limite": 1, "bajo_60": 2}
FORMATO_HORA = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


def minutos(hora):
    """'02:00' → minutos desde las 00:00 del día del evento (madrugada = +24 h)."""
    m = FORMATO_HORA.match(hora)
    if not m:
        raise ValueError(f"hora {hora!r} no tiene formato HH:MM")
    h, mi = int(m.group(1)), int(m.group(2))
    if h < HORA_MADRUGADA:
        h += 24
    return h * 60 + mi


def grupo(ocupacion):
    if ocupacion > LIMITE_COMODO:
        return "al_limite"
    if ocupacion >= MINIMO_COMODO:
        return "comodo"
    return "bajo_60"


TIPOS_MEDIA = ("foto", "plano", "tour360", "video")


def ficha_media(m):
    """Lo que se puede enseñar de un elemento de media: nunca la url."""
    return {"id": m["id"], "type": m["type"], "description": m["description"],
            "illustrative": m.get("illustrative", False)}


def foto_tarjeta(esp, disposicion, zonas_con_aviso=()):
    """Foto de la tarjeta:
    - solo fotos aprobadas y nunca de una zona que cierra antes del fin del evento;
    - la de la misma disposition;
    - si no hay, mejor una de interior (sin zone) que una de zona; dentro, la primera."""
    fotos = [m for m in esp.get("media", [])
             if m.get("type") == "foto" and m.get("approved") is True
             and m.get("zone") not in zonas_con_aviso]
    misma = [m for m in fotos if m.get("disposition") == disposicion]
    interior = [m for m in fotos if not m.get("zone")]
    elegida = (misma or interior or fotos or [None])[0]
    return ficha_media(elegida) if elegida else None


def media_aprobada(espacio_id, tipo, espacios=None):
    """Media aprobada de un espacio por tipo (foto, plano, tour360, video), sin rutas."""
    if tipo not in TIPOS_MEDIA:
        raise ValueError(f"tipo {tipo!r} no es uno de {TIPOS_MEDIA}")
    espacios = espacios if espacios is not None else cargar_espacios()
    esp = next((e for e in espacios if e["id"] == espacio_id), None)
    if esp is None:
        raise ValueError(f"el espacio {espacio_id!r} no existe")
    return [ficha_media(m) for m in esp.get("media", [])
            if m.get("type") == tipo and m.get("approved") is True]


def avisos_de_zona(reglas, fin):
    """Zonas que cierran antes de la hora de fin pedida (fin en minutos, o None)."""
    if fin is None:
        return []
    return [{"zona": zona, "hasta": h}
            for zona, h in reglas.get("zone_end_times", {}).items() if minutos(h) < fin]


def cargar_espacios():
    with open(ESPACIOS, encoding="utf-8") as f:
        return json.load(f)["venues"]


def recomendar(asistentes, disposicion, dias=None, hora_fin=None, espacios=None):
    if not isinstance(asistentes, int) or asistentes <= 0:
        raise ValueError("asistentes debe ser un entero mayor que 0")
    if disposicion not in DISPOSICIONES:
        raise ValueError(f"disposición {disposicion!r} no es una de {DISPOSICIONES}")
    if dias is not None and (not isinstance(dias, int) or dias < 0):
        raise ValueError("dias debe ser un entero de 0 o más")
    fin = minutos(hora_fin) if hora_fin is not None else None
    if espacios is None:
        espacios = cargar_espacios()

    candidatos, descartados = [], []
    for esp in espacios:
        aforo = esp["capacities"][disposicion]
        reglas = esp["chatbot_guardrails"]

        # 1. Aforo de la disposición pedida (nunca absolute_max)
        if aforo < asistentes:
            continue

        # 2. Antelación
        if dias is not None and dias < reglas["min_lead_time_days"]:
            descartados.append({
                "id": esp["id"], "nombre": esp["name"], "motivo": "antelacion",
                "detalle": f"necesita {reglas['min_lead_time_days']} días; faltan {dias}",
            })
            continue

        # 3. Horario
        if fin is not None and minutos(reglas["max_end_time"]) < fin:
            descartados.append({
                "id": esp["id"], "nombre": esp["name"], "motivo": "horario",
                "detalle": f"acaba a las {reglas['max_end_time']}; se pide hasta las {hora_fin}",
            })
            continue

        # 4. Ocupación
        ocupacion = Fraction(asistentes, aforo)
        # Aviso si alguna zona cierra antes de la hora de fin pedida
        avisos_zona = avisos_de_zona(reglas, fin)

        candidatos.append({
            "id": esp["id"], "nombre": esp["name"], "aforo": aforo, "avisos_zona": avisos_zona,
            "foto": foto_tarjeta(esp, disposicion, {a["zona"] for a in avisos_zona}),
            "ocupacion_exacta": ocupacion, "grupo": grupo(ocupacion),
        })

    # 5. Orden: grupo; dentro del grupo, cercanía al 80 %; empate: menos aforo primero
    candidatos.sort(key=lambda c: (ORDEN_GRUPOS[c["grupo"]],
                                   abs(c["ocupacion_exacta"] - OBJETIVO),
                                   c["aforo"]))

    # 4. bajo_60 solo si no queda ningún comodo ni al_limite.
    #    Si la única opción es al_limite, se añade como alternativa el primer bajo_60.
    for c in candidatos:
        c["alternativa"] = False
    principales = [c for c in candidatos if c["grupo"] != "bajo_60"]
    bajos = [c for c in candidatos if c["grupo"] == "bajo_60"]
    if principales:
        candidatos = principales
        if len(principales) == 1 and principales[0]["grupo"] == "al_limite" and bajos:
            bajos[0]["alternativa"] = True
            candidatos = principales + bajos[:1]

    # 6. Máximo 3
    recomendados = [
        {"id": c["id"], "nombre": c["nombre"],
         "ocupacion": round(float(c["ocupacion_exacta"]) * 100), "grupo": c["grupo"],
         "alternativa": c["alternativa"], "avisos_zona": c["avisos_zona"], "foto": c["foto"]}
        for c in candidatos[:MAX_RECOMENDADOS]
    ]

    # 7. Descartados por antelación u horario
    return {"recomendados": recomendados, "descartados": descartados}


def validar_espacio(espacio_id, asistentes, disposicion, dias=None, hora_fin=None, espacios=None):
    """Comprueba el espacio elegido con las reglas 1-3 de la recomendación (aforo de la
    disposición, antelación y horario). Devuelve todos los motivos que fallan, no solo el
    primero, y las alternativas que daría la recomendación normal si no encaja."""
    if espacios is None:
        espacios = cargar_espacios()
    esp = next((e for e in espacios if e["id"] == espacio_id), None)
    if esp is None:
        raise ValueError(f"el espacio {espacio_id!r} no existe")
    # Misma validación de entrada que recomendar()
    if not isinstance(asistentes, int) or asistentes <= 0:
        raise ValueError("asistentes debe ser un entero mayor que 0")
    if disposicion not in DISPOSICIONES:
        raise ValueError(f"disposición {disposicion!r} no es una de {DISPOSICIONES}")
    fin = minutos(hora_fin) if hora_fin is not None else None

    aforo = esp["capacities"][disposicion]
    reglas = esp["chatbot_guardrails"]
    motivos = []
    if aforo < asistentes:
        motivos.append({"motivo": "aforo", "disposicion": disposicion, "aforo": aforo,
                        "asistentes": asistentes,
                        "detalle": f"en {disposicion} caben {aforo}; se piden {asistentes}"})
    if dias is not None and dias < reglas["min_lead_time_days"]:
        motivos.append({"motivo": "antelacion", "necesita_dias": reglas["min_lead_time_days"],
                        "faltan_dias": dias,
                        "detalle": f"necesita {reglas['min_lead_time_days']} días; faltan {dias}"})
    if fin is not None and minutos(reglas["max_end_time"]) < fin:
        motivos.append({"motivo": "horario", "acaba": reglas["max_end_time"], "hora_fin": hora_fin,
                        "detalle": f"acaba a las {reglas['max_end_time']}; se pide hasta las {hora_fin}"})

    encaja = not motivos
    avisos_zona = avisos_de_zona(reglas, fin)
    resultado = {"espacio": esp["id"], "nombre": esp["name"], "encaja": encaja, "motivos": motivos,
                 "avisos_zona": avisos_zona,
                 "foto": foto_tarjeta(esp, disposicion, {a["zona"] for a in avisos_zona})}
    if encaja:
        resultado["ocupacion"] = round(asistentes / aforo * 100)
        resultado["grupo"] = grupo(Fraction(asistentes, aforo))
        if resultado["grupo"] == "bajo_60":
            # Espacio amplio: la mejor opción comodo de la recomendación normal, si la hay
            comodos = [r for r in recomendar(asistentes, disposicion, dias, hora_fin, espacios)["recomendados"]
                       if r["grupo"] == "comodo" and r["id"] != esp["id"]]
            if comodos:
                resultado["opcion_comodo"] = comodos[0]
    else:
        resultado["alternativas"] = recomendar(asistentes, disposicion, dias, hora_fin, espacios)["recomendados"]
    return resultado


def main():
    p = argparse.ArgumentParser(description="Recomendador de espacios por reglas fijas")
    p.add_argument("--asistentes", type=int)
    p.add_argument("--disposicion", choices=DISPOSICIONES)
    p.add_argument("--dias", type=int, help="días que faltan hasta el evento")
    p.add_argument("--hora-fin", help="hora de fin HH:MM (antes de 08:00 = madrugada)")
    p.add_argument("--media", metavar="ID_ESPACIO", help="devuelve la media aprobada de este espacio")
    p.add_argument("--tipo", choices=TIPOS_MEDIA, help="tipo de media con --media")
    p.add_argument("--validar", metavar="ID_ESPACIO", help="valida el espacio elegido por el cliente")
    a = p.parse_args()
    try:
        if a.validar:
            if a.asistentes is None or a.disposicion is None:
                raise ValueError("--validar necesita --asistentes y --disposicion")
            resultado = validar_espacio(a.validar, a.asistentes, a.disposicion, a.dias, a.hora_fin)
        elif a.media:
            if not a.tipo:
                raise ValueError("--media necesita --tipo")
            resultado = media_aprobada(a.media, a.tipo)
        else:
            if a.asistentes is None or a.disposicion is None:
                raise ValueError("faltan --asistentes y --disposicion")
            resultado = recomendar(a.asistentes, a.disposicion, a.dias, a.hora_fin)
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(2)
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
