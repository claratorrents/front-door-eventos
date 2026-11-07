#!/usr/bin/env python3
"""Puntúa un lead aplicando los niveles de la sección 2 y la decisión de la
sección 4 de .claude/skills/cualificador-leads/SKILL.md.

El chatbot traduce las frases del cliente a niveles con la tabla de la §3 de la
skill y pasa aquí esos niveles. El script hace lo que se puede calcular:
  - el tipo de evento contra el espacio de referencia
    (elegido > primero recomendado > ninguno), con data/espacios.json;
  - "este mes" según los días que quedan hasta fin de mes, con la fecha real.
Un criterio que no se pasa cuenta como el nivel más bajo (0 puntos).

Uso:
  python3 scripts/puntuar_lead.py --fecha mes_o_rango --asistentes concreto \\
      --presupuesto aproximado --tipo-evento cena --primer-recomendado sp-llum-poblenou \\
      --empresa corporativo_con_nombre --urgencia 14_dias_o_menos
  python3 scripts/puntuar_lead.py ... --fecha dia_exacto \\
      --espacio-elegido sp-llum-poblenou --antelacion-cumplida
  Para "este mes": --urgencia este_mes (opcional --hoy AAAA-MM-DD; por defecto, la fecha del sistema).

Salida (JSON): puntuacion, desglose, decision, motivo_escalado y condiciones_que_faltan.
La puntuación es un dato interno: nunca se enseña al cliente.
"""

import argparse
import calendar
import datetime
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESPACIOS = RAIZ / "data" / "espacios.json"

# Niveles fijos (sección 2 de la skill). "tipo" se calcula aparte.
NIVELES = {
    "fecha": {"dia_exacto": 25, "mes_o_rango": 15, "temporada_o_anio": 5, "nada": 0},
    "asistentes": {"concreto": 20, "aproximado": 10, "no_sabe": 0},
    "presupuesto": {"concreto": 20, "aproximado": 10, "no_sabe": 0},
    "empresa": {"corporativo_con_nombre": 10, "corporativo_sin_nombre": 5, "particular": 5, "sin_dato": 0},
    "urgencia": {"14_dias_o_menos": 10, "menos_de_un_mes": 5, "sin_prisa": 0},
}
PUNTOS_TIPO = {"en_event_types": 15, "otro_tipo_claro": 10, "no_claro": 0}
NIVEL_POR_DEFECTO = {c: min(n, key=n.get) for c, n in NIVELES.items()}
UMBRAL = 70             # bloqueo solo con MÁS de 70
DIAS_ESTE_MES = 14      # "este mes": 14 días o menos hasta fin de mes → 14_dias_o_menos


def cargar_espacios():
    with open(ESPACIOS, encoding="utf-8") as f:
        return {v["id"]: v for v in json.load(f)["venues"]}


def nivel_este_mes(hoy):
    ultimo = calendar.monthrange(hoy.year, hoy.month)[1]
    quedan = ultimo - hoy.day
    return ("14_dias_o_menos" if quedan <= DIAS_ESTE_MES else "menos_de_un_mes"), quedan


def puntuar(fecha=None, asistentes=None, presupuesto=None, tipo_evento=None,
            empresa=None, urgencia=None, espacio_elegido=None, primer_recomendado=None,
            antelacion_cumplida=False, hoy=None, espacios=None):
    if espacios is None:
        espacios = cargar_espacios()
    for nombre, esp_id in (("espacio_elegido", espacio_elegido), ("primer_recomendado", primer_recomendado)):
        if esp_id is not None and esp_id not in espacios:
            raise ValueError(f"{nombre}: el espacio {esp_id!r} no existe")

    desglose = {}

    # "este mes" se resuelve con la fecha real
    detalle_urgencia = None
    if urgencia == "este_mes":
        urgencia, quedan = nivel_este_mes(hoy or datetime.date.today())
        detalle_urgencia = f"'este mes': quedan {quedan} días hasta fin de mes"

    elegidos = dict(fecha=fecha, asistentes=asistentes, presupuesto=presupuesto,
                    empresa=empresa, urgencia=urgencia)
    for criterio, nivel in elegidos.items():
        nivel = nivel or NIVEL_POR_DEFECTO[criterio]
        if nivel not in NIVELES[criterio]:
            raise ValueError(f"{criterio}: nivel {nivel!r} no es uno de {list(NIVELES[criterio])}")
        desglose[criterio] = {"nivel": nivel, "puntos": NIVELES[criterio][nivel]}
    if detalle_urgencia:
        desglose["urgencia"]["detalle"] = detalle_urgencia

    # Tipo de evento contra el espacio de referencia: elegido > primero recomendado > ninguno
    referencia = espacio_elegido or primer_recomendado
    if not tipo_evento:
        nivel_tipo = "no_claro"
    elif referencia and tipo_evento in espacios[referencia].get("event_types", []):
        nivel_tipo = "en_event_types"
    else:
        nivel_tipo = "otro_tipo_claro"
    desglose["tipo"] = {"nivel": nivel_tipo, "puntos": PUNTOS_TIPO[nivel_tipo],
                        "tipo_evento": tipo_evento, "espacio_referencia": referencia}

    total = sum(d["puntos"] for d in desglose.values())

    # Decisión (sección 4): prerreserva solo si se cumplen las cuatro condiciones
    condiciones = {
        "mas_de_70": total > UMBRAL,
        "dia_exacto": desglose["fecha"]["nivel"] == "dia_exacto",
        "espacio_elegido": espacio_elegido is not None,
        "antelacion_cumplida": bool(antelacion_cumplida),
    }
    faltan = [c for c, ok in condiciones.items() if not ok]
    prerreserva = not faltan
    return {
        "puntuacion": total,
        "desglose": desglose,
        "decision": "prerreserva" if prerreserva else "escalar_comercial",
        "motivo_escalado": None if prerreserva else "lead",
        "condiciones_que_faltan": faltan,
    }


def main():
    p = argparse.ArgumentParser(description="Puntuación de leads por reglas fijas")
    for criterio, niveles in NIVELES.items():
        opciones = list(niveles) + (["este_mes"] if criterio == "urgencia" else [])
        p.add_argument(f"--{criterio}", choices=opciones)
    p.add_argument("--tipo-evento", help="tipo de evento claro (p. ej. cena); vacío si no está claro")
    p.add_argument("--espacio-elegido", help="id del espacio que ha elegido el cliente")
    p.add_argument("--primer-recomendado", help="id del primer espacio recomendado")
    p.add_argument("--antelacion-cumplida", action="store_true",
                   help="el espacio elegido cumple la antelación mínima para ese día")
    p.add_argument("--hoy", help="fecha de hoy AAAA-MM-DD (por defecto, la del sistema)")
    a = p.parse_args()
    hoy = datetime.date.fromisoformat(a.hoy) if a.hoy else None
    r = puntuar(a.fecha, a.asistentes, a.presupuesto, a.tipo_evento, a.empresa, a.urgencia,
                a.espacio_elegido, a.primer_recomendado, a.antelacion_cumplida, hoy)
    print(json.dumps(r, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        main()
    except ValueError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False))
        sys.exit(2)
