#!/usr/bin/env python3
"""Valida data/espacios.json y data/inventario.json.

Uso:  python3 scripts/validar_datos.py
Sale con código 0 si todo está bien y 1 si hay errores.
Solo lee los archivos: nunca los modifica.
"""

import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESPACIOS = RAIZ / "data" / "espacios.json"
INVENTARIO = RAIZ / "data" / "inventario.json"

NUM_ESPACIOS = 6
CAMPOS_ESPACIO = [
    "id", "name", "city", "neighborhood", "tagline", "full_profile",
    "best_for", "event_types", "pricing", "capacities", "amenities_included",
    "chatbot_guardrails", "media", "n8n_routing",
]
ORDEN_AFOROS = ["cocktail", "theater", "banquet", "classroom"]
CAMPOS_PROHIBIDOS = {"description", "max_capacity_alert", "default_lead_tier"}
PALABRAS_PROHIBIDAS = ["ficticio", "ficticia"]
CAMPOS_MEDIA = ["id", "type", "url", "description", "approved", "illustrative"]
TIPOS_MEDIA = {"foto", "plano", "tour360", "video"}
CAMPOS_ITEM = ["id", "name", "stock", "usable_in"]
# Hora de fin HH:MM (00:00 a 23:59). Antes de las 08:00 = madrugada del día siguiente.
FORMATO_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

errores = []


def error(msg):
    errores.append(msg)


def cargar(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: no se puede leer {ruta.name}: {e}")
        sys.exit(1)


def buscar_campos_prohibidos(nodo, ruta, en_media=False):
    """Busca claves prohibidas en cualquier nivel.

    'description' sí está permitido dentro de cada elemento de media.
    """
    if isinstance(nodo, dict):
        for clave, valor in nodo.items():
            permitido = clave == "description" and en_media
            if clave in CAMPOS_PROHIBIDOS and not permitido:
                error(f"{ruta}: el campo '{clave}' ya no debería existir")
            buscar_campos_prohibidos(valor, f"{ruta}.{clave}")
    elif isinstance(nodo, list):
        es_media = ruta.endswith(".media")
        for i, valor in enumerate(nodo):
            buscar_campos_prohibidos(valor, f"{ruta}[{i}]", en_media=es_media)


def revisar_texto_cliente(texto, donde):
    if not isinstance(texto, str):
        return
    bajo = texto.lower()
    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in bajo:
            error(f"{donde}: el texto para el cliente contiene '{palabra}'")


def validar_espacios(datos):
    espacios = datos.get("venues", [])
    if len(espacios) != NUM_ESPACIOS:
        error(f"espacios: hay {len(espacios)} y deberían ser {NUM_ESPACIOS}")

    buscar_campos_prohibidos(datos, "espacios")

    ids_espacio, ids_media, no_aprobada = set(), set(), []
    total_media = 0

    for esp in espacios:
        eid = esp.get("id", "<sin id>")
        if eid in ids_espacio:
            error(f"{eid}: id de espacio repetido")
        ids_espacio.add(eid)

        for campo in CAMPOS_ESPACIO:
            if campo not in esp or esp[campo] in (None, "", [], {}):
                error(f"{eid}: falta el campo '{campo}' o está vacío")

        # Aforos
        cap = esp.get("capacities", {})
        valores = [cap.get(k) for k in ORDEN_AFOROS]
        if any(not isinstance(v, int) for v in valores):
            error(f"{eid}: faltan aforos o no son números ({cap})")
        else:
            if not all(a > b for a, b in zip(valores, valores[1:])):
                detalle = " > ".join(f"{k} {v}" for k, v in zip(ORDEN_AFOROS, valores))
                error(f"{eid}: aforos no cumplen cocktail > theater > banquet > classroom ({detalle})")
            if cap.get("absolute_max") != max(valores):
                error(f"{eid}: absolute_max {cap.get('absolute_max')} distinto del aforo mayor {max(valores)}")

        # Tipos de evento: lista de textos no vacíos
        tipos = esp.get("event_types")
        if isinstance(tipos, list) and not all(isinstance(t, str) and t.strip() for t in tipos):
            error(f"{eid}: event_types debe ser una lista de textos no vacíos")

        # Hora máxima de fin
        hora = esp.get("chatbot_guardrails", {}).get("max_end_time")
        if hora is None:
            error(f"{eid}: falta chatbot_guardrails.max_end_time")
        elif not isinstance(hora, str) or not FORMATO_HORA.match(hora):
            error(f"{eid}: max_end_time {hora!r} no tiene formato HH:MM")

        # Horarios por zona (opcional): {"zona": "HH:MM"}
        zonas = esp.get("chatbot_guardrails", {}).get("zone_end_times")
        if zonas is not None:
            if not isinstance(zonas, dict) or not zonas:
                error(f"{eid}: zone_end_times debe ser un objeto {{zona: HH:MM}} no vacío")
            else:
                for zona, h in zonas.items():
                    if not isinstance(h, str) or not FORMATO_HORA.match(h):
                        error(f"{eid}: zone_end_times.{zona} {h!r} no tiene formato HH:MM")

        # Textos que ve el cliente
        revisar_texto_cliente(esp.get("tagline"), f"{eid}.tagline")
        revisar_texto_cliente(esp.get("full_profile"), f"{eid}.full_profile")

        # Media
        tiene_foto_aprobada = tiene_plano = False
        for m in esp.get("media", []):
            total_media += 1
            mid = m.get("id", "<sin id>")
            for campo in CAMPOS_MEDIA:
                if campo not in m:
                    error(f"{eid}/{mid}: falta el campo '{campo}'")
            if mid in ids_media:
                error(f"{eid}/{mid}: id de media repetido")
            ids_media.add(mid)
            if m.get("type") not in TIPOS_MEDIA:
                error(f"{eid}/{mid}: type '{m.get('type')}' no está en {sorted(TIPOS_MEDIA)}")
            desc = m.get("description")
            if not isinstance(desc, str) or not desc.strip():
                error(f"{eid}/{mid}: descripción vacía")
            revisar_texto_cliente(desc, f"{eid}/{mid}.description")
            aprobada = m.get("approved")
            if not isinstance(aprobada, bool):
                error(f"{eid}/{mid}: approved debe ser true o false (es {aprobada!r})")
            if aprobada is False:
                no_aprobada.append((eid, mid, desc))
            if "illustrative" in m and not isinstance(m["illustrative"], bool):
                error(f"{eid}/{mid}: illustrative debe ser true o false (es {m['illustrative']!r})")
            if "zone" in m and (not isinstance(m["zone"], str) or not m["zone"].strip()):
                error(f"{eid}/{mid}: zone debe ser un texto no vacío")
            # disposition: obligatoria en fotos aprobadas; solo las fotos la llevan
            if m.get("type") == "foto":
                disp = m.get("disposition")
                if aprobada is True and disp not in ORDEN_AFOROS:
                    error(f"{eid}/{mid}: foto aprobada sin disposition válida ({disp!r}); debe ser una de {ORDEN_AFOROS}")
                elif disp is not None and disp not in ORDEN_AFOROS:
                    error(f"{eid}/{mid}: disposition {disp!r} no es una de {ORDEN_AFOROS}")
            elif "disposition" in m:
                error(f"{eid}/{mid}: solo las fotos llevan disposition")
            if m.get("type") == "foto" and aprobada is True:
                tiene_foto_aprobada = True
            if m.get("type") == "plano" and aprobada is True:
                tiene_plano = True
        if not tiene_foto_aprobada:
            error(f"{eid}: no tiene ninguna foto aprobada")
        if not tiene_plano:
            error(f"{eid}: no tiene ningún plano aprobado")

    return ids_espacio, total_media, no_aprobada


def validar_inventario(datos, ids_espacio):
    items = datos.get("items", [])
    buscar_campos_prohibidos(datos, "inventario")
    ids = set()
    for it in items:
        iid = it.get("id", "<sin id>")
        if iid in ids:
            error(f"inventario/{iid}: id repetido")
        ids.add(iid)
        for campo in CAMPOS_ITEM:
            if campo not in it:
                error(f"inventario/{iid}: falta el campo '{campo}'")
        stock = it.get("stock")
        if not isinstance(stock, (int, float)) or stock <= 0:
            error(f"inventario/{iid}: stock debe ser mayor que 0 (es {stock!r})")
        for eid in it.get("usable_in", []):
            if eid not in ids_espacio:
                error(f"inventario/{iid}: usable_in incluye '{eid}', que no existe")
    return len(items)


def main():
    espacios = cargar(ESPACIOS)
    inventario = cargar(INVENTARIO)

    ids_espacio, total_media, no_aprobada = validar_espacios(espacios)
    total_items = validar_inventario(inventario, ids_espacio)

    print("=== Validación de datos ===")
    print(f"Espacios:          {len(ids_espacio)}")
    print(f"Elementos de media: {total_media} ({total_media - len(no_aprobada)} aprobados)")
    print(f"Artículos de inventario: {total_items}")
    print()

    print("Media NO aprobada (no se enseña al cliente):")
    if no_aprobada:
        for eid, mid, desc in no_aprobada:
            print(f"  - {eid} / {mid}: {desc}")
    else:
        print("  (ninguna)")
    print()

    if errores:
        print(f"RESULTADO: {len(errores)} error(es)")
        for e in errores:
            print(f"  ✗ {e}")
        sys.exit(1)
    print("RESULTADO: todo correcto ✓")


if __name__ == "__main__":
    main()
