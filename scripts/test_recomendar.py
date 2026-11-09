#!/usr/bin/env python3
"""Casos de prueba del recomendador, calculados por el equipo.

Uso:  python3 scripts/test_recomendar.py
Sale con código 0 si todos pasan y 1 si alguno falla.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from recomendar import media_aprobada, recomendar, validar_espacio  # noqa: E402

# (descripción, argumentos, recomendados esperados [(id, %, grupo)], descartados esperados [(id, motivo)])
CASOS = [
    ("120 banquet", dict(asistentes=120, disposicion="banquet"),
     [("sp-llum-poblenou", 80, "comodo"), ("sp-mirador-montjuic", 100, "al_limite")], []),
    ("140 banquet", dict(asistentes=140, disposicion="banquet"),
     [("sp-nau-besos", 64, "comodo"), ("sp-llum-poblenou", 93, "al_limite")], []),
    ("75 banquet", dict(asistentes=75, disposicion="banquet"),
     [("sp-forum-les-corts", 83, "comodo"), ("sp-mirador-montjuic", 62, "comodo")], []),
    ("33 banquet", dict(asistentes=33, disposicion="banquet"),
     [("sp-atelier-sant-antoni", 94, "al_limite"), ("sp-jardi-gracia", 55, "bajo_60")], []),
    ("150 theater", dict(asistentes=150, disposicion="theater"),
     [("sp-llum-poblenou", 75, "comodo"), ("sp-mirador-montjuic", 94, "al_limite")], []),
    ("100 cocktail, fin 03:00", dict(asistentes=100, disposicion="cocktail", hora_fin="03:00"),
     [("sp-mirador-montjuic", 48, "bajo_60"), ("sp-nau-besos", 25, "bajo_60")],
     [("sp-llum-poblenou", "horario"), ("sp-jardi-gracia", "horario"), ("sp-forum-les-corts", "horario")]),
    ("180 theater, 5 días", dict(asistentes=180, disposicion="theater", dias=5),
     [], [("sp-llum-poblenou", "antelacion"), ("sp-nau-besos", "antelacion")]),
    ("500 cocktail", dict(asistentes=500, disposicion="cocktail"), [], []),
    ("100 cocktail, fin 21:00 (al_limite único + alternativa)",
     dict(asistentes=100, disposicion="cocktail", hora_fin="21:00"),
     [("sp-jardi-gracia", 91, "al_limite"), ("sp-forum-les-corts", 59, "bajo_60")], []),
]


def espacio_prueba(id_, aforo_banquet):
    """Espacio de prueba mínimo (no es del catálogo) para forzar un empate."""
    return {"id": id_, "name": id_,
            "capacities": {"cocktail": aforo_banquet, "theater": aforo_banquet,
                           "banquet": aforo_banquet, "classroom": aforo_banquet},
            "chatbot_guardrails": {"min_lead_time_days": 0, "max_end_time": "05:00"}}


def test_desempate():
    """63 en banquete: A (aforo 90) = 70 % y B (aforo 70) = 90 %. Los dos son comodo y
    están a 10 puntos del 80 %. Gana B, que tiene menos aforo, en cualquier orden del JSON."""
    a, b = espacio_prueba("prueba-a-90", 90), espacio_prueba("prueba-b-70", 70)
    esperado = [("prueba-b-70", 90, "comodo"), ("prueba-a-90", 70, "comodo")]
    ok = True
    for orden in ([a, b], [b, a]):
        r = recomendar(63, "banquet", espacios=orden)
        obtenido = [(x["id"], x["ocupacion"], x["grupo"]) for x in r["recomendados"]]
        if obtenido != esperado:
            ok = False
            print(f"      esperado: {esperado}\n      obtenido: {obtenido}")
    print(f"{'OK   ' if ok else 'FALLO'} desempate (datos de prueba, los dos órdenes)")
    return ok


def test_aviso_zona():
    """Cena de 120 hasta las 00:00: el Mirador avisa de la terraza (23:30); Llum no avisa."""
    r = recomendar(120, "banquet", hora_fin="00:00")
    avisos = {x["id"]: x["avisos_zona"] for x in r["recomendados"]}
    esperado = {"sp-llum-poblenou": [], "sp-mirador-montjuic": [{"zona": "terraza", "hasta": "23:30"}]}
    sin_hora = recomendar(120, "banquet")
    ok = avisos == esperado and all(x["avisos_zona"] == [] for x in sin_hora["recomendados"])
    print(f"{'OK   ' if ok else 'FALLO'} aviso de zona (cena 120 hasta las 00:00)")
    if not ok:
        print(f"      esperado: {esperado}\n      obtenido: {avisos}")
    return ok


# Foto de la tarjeta (skill media-espacios §2): (descripción, argumentos, {id espacio: id foto})
CASOS_FOTO = [
    ("foto: cena 120 → Llum foto-01", dict(asistentes=120, disposicion="banquet"),
     {"sp-llum-poblenou": "llum-poblenou-foto-01"}),
    ("foto: conferencia 150 → Llum foto-02", dict(asistentes=150, disposicion="theater"),
     {"sp-llum-poblenou": "llum-poblenou-foto-02"}),
    ("foto: comida 33 → Atelier foto-01 y Jardí foto-01", dict(asistentes=33, disposicion="banquet"),
     {"sp-atelier-sant-antoni": "atelier-sant-antoni-foto-01", "sp-jardi-gracia": "jardi-gracia-foto-01"}),
    ("foto: fiesta 100 hasta las 03:00 → Mirador foto-02 (la terraza cierra antes)",
     dict(asistentes=100, disposicion="cocktail", hora_fin="03:00"),
     {"sp-mirador-montjuic": "mirador-montjuic-foto-02"}),
    ("foto: conferencia 150 → Mirador foto-03 (foto de teatro)",
     dict(asistentes=150, disposicion="theater"),
     {"sp-mirador-montjuic": "mirador-montjuic-foto-03"}),
    ("foto: formación 60 en aula → Mirador foto-02 (sin foto de aula: interior antes que terraza)",
     dict(asistentes=60, disposicion="classroom"),
     {"sp-mirador-montjuic": "mirador-montjuic-foto-02"}),
]

# Media aprobada por tipo (skill media-espacios §3): (descripción, espacio, tipo, ids esperados)
CASOS_MEDIA = [
    ("media: fotos del Jardí → solo foto-01 (la 02 no está aprobada)", "sp-jardi-gracia", "foto",
     ["jardi-gracia-foto-01"]),
    ("media: plano del Mirador", "sp-mirador-montjuic", "plano", ["mirador-montjuic-plano"]),
    ("media: tour de la Nau", "sp-nau-besos", "tour360", ["nau-besos-tour360"]),
    ("media: vídeo de la Nau → ninguno", "sp-nau-besos", "video", []),
]


def test_media():
    fallos = 0
    for nombre, espacio, tipo, esperado in CASOS_MEDIA:
        r = media_aprobada(espacio, tipo)
        ok = [x["id"] for x in r] == esperado and all("url" not in x for x in r)
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      esperado: {esperado}\n      obtenido: {r}")
    return fallos


def test_fotos():
    fallos = 0
    for nombre, args, esperado in CASOS_FOTO:
        fotos = {x["id"]: (x["foto"] or {}).get("id") for x in recomendar(**args)["recomendados"]}
        ok = all(fotos.get(e) == f for e, f in esperado.items())
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      esperado: {esperado}\n      obtenido: {fotos}")
    return fallos


# Validar el espacio elegido. 14 de marzo de 2027 visto desde el 7/11/2026 = 127 días.
# (descripción, argumentos, encaja, motivos esperados {motivo: (campo, valor)}, alternativas esperadas)
CASOS_VALIDAR = [
    ("validar: Mirador, 300 cocktail, 14 de marzo → no encaja: aforo en cóctel 210; alternativa Nau",
     dict(espacio_id="sp-mirador-montjuic", asistentes=300, disposicion="cocktail", dias=127),
     False, {"aforo": ("aforo", 210)}, ["sp-nau-besos"]),
    ("validar: Mirador, 100 banquet, 14 de marzo → encaja",
     dict(espacio_id="sp-mirador-montjuic", asistentes=100, disposicion="banquet", dias=127),
     True, {}, None),
    ("validar: Nau, 180 theater, dentro de 5 días → no encaja: antelación (necesita 14 días)",
     dict(espacio_id="sp-nau-besos", asistentes=180, disposicion="theater", dias=5),
     False, {"antelacion": ("necesita_dias", 14)}, None),
]

# Validar con horario por zona (adaptación a n8n): --validar devuelve avisos_zona
CASOS_VALIDAR_ZONA = [
    ("validar: Mirador, 100 banquet, hasta las 01:00 → encaja, con aviso de la terraza (23:30)",
     dict(espacio_id="sp-mirador-montjuic", asistentes=100, disposicion="banquet", hora_fin="01:00"),
     True, [{"zona": "terraza", "hasta": "23:30"}]),
]

# Validar devuelve la foto de la tarjeta (foto_tarjeta): nunca de una zona con aviso
CASOS_VALIDAR_FOTO = [
    ("validar: Mirador, 100 cocktail, hasta las 01:00 → foto del salón (foto-02), no la de la terraza",
     dict(espacio_id="sp-mirador-montjuic", asistentes=100, disposicion="cocktail", hora_fin="01:00"),
     "mirador-montjuic-foto-02"),
    ("validar: Llum, 120 banquet → foto de banquete (foto-01)",
     dict(espacio_id="sp-llum-poblenou", asistentes=120, disposicion="banquet"),
     "llum-poblenou-foto-01"),
]

# Zona del cliente: primero los de su zona; los demás con otra_zona: true
CASOS_ZONA = [
    ("zona Poblenou, presentación 120 → Llum primero; el resto con otra_zona",
     dict(asistentes=120, disposicion="theater", zona="Poblenou"),
     [("sp-llum-poblenou", False), ("sp-mirador-montjuic", True), ("sp-forum-les-corts", True)]),
    ("zona Gràcia, presentación 120 (en Gràcia no encaja ninguno) → todos con otra_zona",
     dict(asistentes=120, disposicion="theater", zona="Gràcia"),
     [("sp-mirador-montjuic", True), ("sp-llum-poblenou", True), ("sp-forum-les-corts", True)]),
    ('zona "Distrito 22@" = Poblenou → Llum primero',
     dict(asistentes=120, disposicion="theater", zona="Distrito 22@"),
     [("sp-llum-poblenou", False), ("sp-mirador-montjuic", True), ("sp-forum-les-corts", True)]),
]

# Validar un espacio que queda en bajo_60: opcion_comodo solo si la recomendación normal tiene una
CASOS_VALIDAR_AMPLIO = [
    ("validar: Nau, 100 banquet → bajo_60, opcion_comodo Mirador (con los campos foto y avisos_zona)",
     dict(espacio_id="sp-nau-besos", asistentes=100, disposicion="banquet"),
     "sp-mirador-montjuic"),
    ("validar: Mirador, fiesta 100 cocktail hasta las 01:00 → bajo_60, sin opcion_comodo",
     dict(espacio_id="sp-mirador-montjuic", asistentes=100, disposicion="cocktail", hora_fin="01:00"),
     None),
]


def test_validar():
    fallos = 0
    for nombre, args, encaja, motivos, alternativas in CASOS_VALIDAR:
        r = validar_espacio(**args)
        obtenidos = {m["motivo"]: m for m in r["motivos"]}
        ok = r["encaja"] == encaja and set(obtenidos) == set(motivos)
        ok &= all(obtenidos[m][campo] == valor for m, (campo, valor) in motivos.items() if m in obtenidos)
        if alternativas is not None:
            ok &= [x["id"] for x in r.get("alternativas", [])] == alternativas
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      obtenido: {r}")
    for nombre, args, esperado in CASOS_ZONA:
        r = recomendar(**args)["recomendados"]
        ok = [(x["id"], x["otra_zona"]) for x in r] == esperado
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      obtenido: {[(x['id'], x['otra_zona']) for x in r]}")
    for nombre, args, opcion in CASOS_VALIDAR_AMPLIO:
        r = validar_espacio(**args)
        ok = r["encaja"] and r.get("grupo") == "bajo_60"
        if opcion is None:
            ok &= "opcion_comodo" not in r
        else:
            o = r.get("opcion_comodo") or {}
            ok &= o.get("id") == opcion and o.get("grupo") == "comodo" and "foto" in o and "avisos_zona" in o
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      obtenido: {r}")
    for nombre, args, foto in CASOS_VALIDAR_FOTO:
        r = validar_espacio(**args)
        ok = (r.get("foto") or {}).get("id") == foto
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      obtenido: {r.get('foto')}")
    for nombre, args, encaja, avisos in CASOS_VALIDAR_ZONA:
        r = validar_espacio(**args)
        ok = r["encaja"] == encaja and r.get("avisos_zona") == avisos
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      obtenido: {r}")
    return fallos


def main():
    fallos = 0
    for nombre, args, esp_rec, esp_desc in CASOS:
        r = recomendar(**args)
        rec = [(x["id"], x["ocupacion"], x["grupo"]) for x in r["recomendados"]]
        desc = sorted((x["id"], x["motivo"]) for x in r["descartados"])
        ok = rec == esp_rec and desc == sorted(esp_desc)
        print(f"{'OK   ' if ok else 'FALLO'} {nombre}")
        if not ok:
            fallos += 1
            print(f"      esperado: {esp_rec} · descartados {sorted(esp_desc)}")
            print(f"      obtenido: {rec} · descartados {desc}")
    if not test_desempate():
        fallos += 1
    if not test_aviso_zona():
        fallos += 1
    fallos += test_fotos()
    fallos += test_media()
    fallos += test_validar()
    total = len(CASOS) + 2 + len(CASOS_FOTO) + len(CASOS_MEDIA) + len(CASOS_VALIDAR) + len(CASOS_VALIDAR_ZONA) + len(CASOS_VALIDAR_FOTO) + len(CASOS_VALIDAR_AMPLIO) + len(CASOS_ZONA)
    print(f"\n{total - fallos}/{total} casos correctos")
    sys.exit(1 if fallos else 0)


if __name__ == "__main__":
    main()
