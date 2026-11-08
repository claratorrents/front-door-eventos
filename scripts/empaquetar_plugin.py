#!/usr/bin/env python3
"""Genera el plugin de Claude Code `eventos-front-door` copiando desde el proyecto.

El proyecto es la única fuente: el plugin nunca se edita a mano. Cada vez que
cambia una skill, un script o los datos, se vuelve a ejecutar este script.

Uso:  python3 scripts/empaquetar_plugin.py

Qué genera:
  plugins/eventos-front-door/
    .claude-plugin/plugin.json    manifiesto del plugin
    skills/<skill>/SKILL.md       las skills de .claude/skills/, con las rutas adaptadas
    scripts/*.py                  los scripts del proyecto, sin los tests
    data/*.json                   los datos de data/
    media/                        las fotos (validar_datos.py comprueba que existen)
    KNOWLEDGE.md, AGENTS.md       el contexto del proyecto
    README.md
  .claude-plugin/marketplace.json marketplace del repositorio (en la raíz)

Rutas: en el proyecto, las skills citan `scripts/...`, `data/...` y `KNOWLEDGE.md`
desde la raíz. Instalado, el plugin vive en otra carpeta, así que al copiar se
cambian por `${CLAUDE_SKILL_DIR}/../../scripts/...` (y lo mismo para datos y KNOWLEDGE.md). Claude Code sustituye ${CLAUDE_SKILL_DIR}
por la carpeta de la skill al cargarla. Solo se cambia el cuerpo de la skill, no
el frontmatter. Las skills del proyecto no se tocan.
"""

import json
import re
import shutil
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
NOMBRE = "eventos-front-door"
VERSION = "0.1.0"
DESCRIPCION = ("Chatbot front door para una empresa de alquiler de espacios para eventos: "
               "router, guardrails, consentimiento, recomendador, cualificador y media, "
               "con scripts de reglas fijas y datos sintéticos.")
MARKETPLACE = "front-door-eventos"
DUENO = "Equipo front door eventos (La Salle)"

DESTINO = RAIZ / "plugins" / NOMBRE
MARCA = DESTINO / ".generado-por-empaquetar"  # solo se borra una carpeta que haya creado este script
ORIGEN_SKILLS = RAIZ / ".claude" / "skills"
ORIGEN_SCRIPTS = RAIZ / "scripts"
ORIGEN_DATOS = RAIZ / "data"
ORIGEN_MEDIA = RAIZ / "media"
EXCLUIR_SCRIPTS = {"empaquetar_plugin.py"}  # más todos los test_*.py
DOCUMENTOS = ["KNOWLEDGE.md", "AGENTS.md"]

# scripts/x.py o data/x.json que no van ya precedidos de / ni de una variable
RUTA = re.compile(r"(?<![\w/$}])(scripts/[\w.-]+|data/[\w.-]+|KNOWLEDGE\.md)")

README = f"""# {NOMBRE}

> Generado por `scripts/empaquetar_plugin.py`. No se edita a mano: los cambios se hacen en el proyecto y se vuelve a generar.

Plugin de Claude Code con las skills del chatbot "front door" de una empresa que alquila espacios para eventos (datos sintéticos, prototipo del máster en La Salle).

## Qué incluye
- **Skills:** router-intenciones, guardrails, consentimiento, recomendador-espacios, cualificador-leads y media-espacios.
- **Scripts de reglas fijas** (Python 3, sin dependencias): `recomendar.py` (recomendación, validación del espacio elegido y media aprobada), `puntuar_lead.py` (puntuación del lead), `router.py` (qué se hace con cada intención) y `validar_datos.py`.
- **Datos:** `data/espacios.json` (6 espacios) y `data/inventario.json`.
- **Media:** `media/placeholders/`, las fotos ilustrativas de los espacios (generadas con IA). `validar_datos.py` comprueba que cada foto aprobada tiene su archivo.
- **Contexto:** `KNOWLEDGE.md` (decisiones del equipo, que las skills citan) y `AGENTS.md` (las reglas del chatbot).

Las decisiones las toman los scripts; el LLM clasifica y redacta.

## Instalación
Desde Claude Code, con el repositorio del proyecto en tu ordenador:

```
/plugin marketplace add <ruta-al-repositorio>
/plugin install {NOMBRE}@{MARKETPLACE}
```

Las skills se usan con el prefijo del plugin, por ejemplo `/{NOMBRE}:router-intenciones`.

## Importante
El chatbot necesita además las reglas de `AGENTS.md` (las 5 reglas que nunca se rompen). `AGENTS.md` ya viene dentro del plugin: basta con copiarlo al proyecto donde lo uses y crear un `CLAUDE.md` con `@AGENTS.md`.
"""


def preparar_destino():
    if DESTINO.exists():
        if not MARCA.exists():
            sys.exit(f"ERROR: {DESTINO} existe y no lo creó este script; no lo borro.")
        shutil.rmtree(DESTINO)
    DESTINO.mkdir(parents=True)
    MARCA.write_text("Carpeta generada por scripts/empaquetar_plugin.py. No editar a mano.\n", encoding="utf-8")


def adaptar_rutas(texto):
    """Cambia scripts/... y data/... del cuerpo de la skill; deja el frontmatter igual."""
    m = re.match(r"(---\n.*?\n---\n)(.*)", texto, re.S)
    cabecera, cuerpo = (m.group(1), m.group(2)) if m else ("", texto)
    cuerpo, n = RUTA.subn(r"${CLAUDE_SKILL_DIR}/../../\1", cuerpo)
    return cabecera + cuerpo, n


def copiar_skills():
    resumen = []
    for origen in sorted(ORIGEN_SKILLS.glob("*/SKILL.md")):
        nombre = origen.parent.name
        texto, n = adaptar_rutas(origen.read_text(encoding="utf-8"))
        destino = DESTINO / "skills" / nombre / "SKILL.md"
        destino.parent.mkdir(parents=True)
        destino.write_text(texto, encoding="utf-8")
        resumen.append((nombre, n))
    return resumen


def copiar_scripts():
    destino = DESTINO / "scripts"
    destino.mkdir()
    copiados = []
    for f in sorted(ORIGEN_SCRIPTS.glob("*.py")):
        if f.name.startswith("test_") or f.name in EXCLUIR_SCRIPTS:
            continue
        shutil.copy2(f, destino / f.name)
        copiados.append(f.name)
    return copiados


def copiar_datos():
    destino = DESTINO / "data"
    destino.mkdir()
    copiados = []
    for f in sorted(ORIGEN_DATOS.glob("*.json")):
        shutil.copy2(f, destino / f.name)
        copiados.append(f.name)
    return copiados


def copiar_media():
    """Copia media/ tal cual (sin archivos del sistema como .DS_Store)."""
    shutil.copytree(ORIGEN_MEDIA, DESTINO / "media", ignore=shutil.ignore_patterns(".DS_Store"))
    destino = DESTINO / "media"
    return sorted(str(f.relative_to(destino)) for f in destino.rglob("*") if f.is_file())


def copiar_documentos():
    for nombre in DOCUMENTOS:
        shutil.copy2(RAIZ / nombre, DESTINO / nombre)
    return DOCUMENTOS


def escribir_json(ruta, datos):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    preparar_destino()
    skills = copiar_skills()
    scripts = copiar_scripts()
    datos = copiar_datos()
    media = copiar_media()
    documentos = copiar_documentos()
    escribir_json(DESTINO / ".claude-plugin" / "plugin.json",
                  {"name": NOMBRE, "version": VERSION, "description": DESCRIPCION,
                   "author": {"name": DUENO}})
    (DESTINO / "README.md").write_text(README, encoding="utf-8")
    escribir_json(RAIZ / ".claude-plugin" / "marketplace.json", {
        "name": MARKETPLACE,
        "owner": {"name": DUENO},
        "description": "Marketplace del proyecto front-door-eventos: instala el plugin desde este repositorio.",
        "plugins": [{"name": NOMBRE, "source": f"./plugins/{NOMBRE}", "description": DESCRIPCION}],
    })

    print(f"Plugin generado en {DESTINO.relative_to(RAIZ)}")
    for nombre, n in skills:
        print(f"  skill  {nombre}: {n} ruta(s) adaptada(s)")
    print(f"  scripts: {', '.join(scripts)}")
    print(f"  datos:   {', '.join(datos)}")
    print(f"  media:   {len(media)} archivo(s)")
    print(f"  documentos: {', '.join(documentos)}")
    print(f"Marketplace: .claude-plugin/marketplace.json ({MARKETPLACE})")


if __name__ == "__main__":
    main()
