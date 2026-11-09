# Integración: usar `chat/` como backend de otro front

Esta guía es para quien va a hacer otra web (otro front) del chatbot de eventos y quiere usar nuestro servidor como backend: las skills, los scripts de decisión y el envío a n8n ya están dentro. No hace falta haber visto el proyecto.

**Resumen:** el front solo pinta lo que devuelve el servidor y le manda lo que escribe o pulsa el cliente. Todas las decisiones las toma el servidor: qué espacios recomendar, qué preguntar, cuándo pedir los datos, qué se envía a n8n y qué se guarda en el registro.

---

## 1. Arrancar el backend

Desde la carpeta del proyecto, con Python 3 (solo biblioteca estándar, no hay que instalar nada):

```bash
python3 chat/servidor.py
```

Al arrancar escribe una línea como esta:

```
Chat en http://127.0.0.1:8000 · envío SIMULADO (sin N8N_WEBHOOK_URL / N8N_API_KEY) · CORS: no · registro en …/registros
```

| Variable de entorno | Para qué | Por defecto |
|---|---|---|
| `CHAT_PUERTO` | Puerto del servidor | `8000` |
| `CHAT_CORS_ORIGIN` | Dirección exacta del otro front, si está en otro puerto o dominio (ver §4) | vacía: sin CORS |
| `N8N_WEBHOOK_URL`, `N8N_API_KEY` | Envío real a n8n. Sin ellas, el envío es **simulado** | vacías |

- **Dirección:** el servidor solo escucha en `127.0.0.1`, es decir, en el mismo ordenador. **No existe una variable `CHAT_HOST`**. Si el front tiene que llegar desde otra máquina, hay que pedirlo: hoy no está previsto.
- **Registro:** el registro anónimo de conversaciones se escribe en `registros/conversaciones.jsonl` **de la carpeta desde la que se arranca** (git lo ignora).
- **Memoria:** el estado de cada conversación vive en memoria. Si se reinicia el servidor, las conversaciones abiertas dejan de existir (ver "Sesión perdida", §3.6).
- **Inactividad:** a los 30 minutos sin mensajes, la conversación se cierra y se registra.

---

## 2. Cómo es una conversación

1. El front pide una sesión: `POST /api/nueva`.
2. Cada mensaje o botón del cliente: `POST /api/mensaje` con `sesion` y **una** de estas tres cosas: `texto`, `accion` o `formulario`.
3. El servidor responde siempre con el mismo formato: los mensajes que hay que pintar, los botones de respuesta rápida, si hay que enseñar el formulario, el idioma y si la conversación se ha cerrado.
4. Al terminar (botón "Terminar") o al cerrar la pestaña: `POST /api/cerrar`.

El primer mensaje del cliente siempre recibe antes el **aviso de IA** (obligatorio por la skill de consentimiento). Lo pone el servidor; el front no tiene que añadir nada.

---

## 3. Contrato de la API

Todas las peticiones son `POST` con cuerpo JSON (`Content-Type: application/json`), salvo `/media/<id>`, que es `GET`. Todas las respuestas son JSON.

| Ruta | Envía | Devuelve |
|---|---|---|
| `POST /api/nueva` | `{}` (o, tras una sesión perdida, `{"motivo": "sesion_perdida", "idioma": "es"}`) | `sesion`, `idioma`, `ui`, `mensajes` |
| `POST /api/mensaje` | `{"sesion": …, "texto": …}` · `{"sesion": …, "accion": …}` · `{"sesion": …, "formulario": {…}}` | respuesta de turno (§3.2) |
| `POST /api/cerrar` | `{"sesion": …}` | respuesta de turno con `"cerrada": true` |
| `GET /media/<id>` | — | la imagen (JPG o SVG) |

> No hay una ruta `/plano/<id>.svg`: los planos se piden como cualquier otra media, con el `url` que da el servidor (`/media/<id del plano>`, y `/media/<id del plano>.en` para la versión en inglés). El front nunca construye estas URL: usa siempre la que viene en la respuesta.

### 3.1 `POST /api/nueva`

```json
POST /api/nueva
{}
→ 200
{
  "sesion": "conv-68dc26ae06e9091b",
  "idioma": "es",
  "ui": {
    "cabecera": "[EMPRESA] · Asistente de eventos",
    "pie": "Prototipo académico con datos ficticios.",
    "campo": "Escribe tu mensaje…",
    "enviar": "Enviar",
    "privacidad_si": "Sí, acepto", "privacidad_no": "No, gracias",
    "publicidad_si": "Sí, quiero", "publicidad_no": "No, gracias",
    "ver_plano": "Ver plano", "ver_fotos": "Ver fotos", "elegir": "Elegir este",
    "f_nombre": "Nombre y apellidos*", "f_email": "Email*",
    "f_empresa": "Empresa (si es para una empresa)", "f_telefono": "Teléfono (opcional)",
    "f_enviar": "Enviar mis datos",
    "terminar": "Terminar",
    "error": "Algo ha fallado por nuestra parte. Inténtalo de nuevo en un momento.",
    "alt_foto": "Foto ilustrativa de {nombre}", "alt_plano": "Plano orientativo de {nombre}",
    "si": "Sí", "no": "No", "oferta_si": "Sí, envíalo", "oferta_no": "No, sigamos"
  },
  "mensajes": []
}
```

- **`sesion`:** se guarda **solo en memoria** (en una variable), y se manda en cada petición.
- **`ui`:** son los textos fijos de la interfaz en el idioma de la conversación. Viene en todas las respuestas; si cambia el idioma, cambian.
  - `alt_foto` y `alt_plano` llevan el hueco `{nombre}`.
  - `[EMPRESA]` ya viene sustituido por el nombre configurado en `chat/config.py`.

### 3.2 Respuesta de turno (`/api/mensaje` y `/api/cerrar`)

```json
{
  "idioma": "es",
  "ui": { … },
  "mensajes": [ … ],
  "botones": [ {"texto": "Sí, acepto", "accion": "privacidad:si"}, … ],
  "formulario": false,
  "cerrada": false
}
```

| Campo | Qué es | Qué hace el front |
|---|---|---|
| `idioma` | `es` o `en`. Sigue al idioma del cliente | Cambiar los textos de la interfaz (`ui`) y el `lang` de la página |
| `mensajes` | Lista ordenada de elementos (§3.3) | Pintarlos en ese orden |
| `botones` | Botones de respuesta rápida. Puede venir vacía | Si viene con elementos, **sustituyen** a los anteriores; si viene vacía, se dejan los que había |
| `formulario` | `true`: enseñar el formulario de datos | Enseñarlo; ocultarlo cuando llegue `false` |
| `cerrada` | `true`: la conversación ha terminado | Desactivar el campo de texto y los botones |

### 3.3 Tipos de mensaje y cómo se pintan

**`texto`**: burbuja del chatbot.
```json
{"tipo": "texto", "texto": "¿Qué evento tenéis en mente?"}
```

**`tarjetas`**: una o varias tarjetas de espacio, en el orden que vienen (el orden lo decide el recomendador; no se reordena).
```json
{
  "tipo": "tarjetas",
  "tarjetas": [{
    "id": "sp-llum-poblenou",
    "nombre": "Llum del Poblenou",
    "lineas": ["Antigua nave textil reconvertida con luz cenital e interior industrial.",
               "Hasta 200 personas en teatro; pensado para presentaciones."],
    "foto": {"url": "/media/llum-poblenou-foto-02", "alt": "Foto ilustrativa de Llum del Poblenou",
             "pie": ["Montaje de teatro frente a la pantalla de 4x3 m", "Imagen ilustrativa"]},
    "botones": [{"texto": "Ver plano", "accion": "plano:sp-llum-poblenou"},
                {"texto": "Ver fotos", "accion": "fotos:sp-llum-poblenou"},
                {"texto": "Elegir este", "accion": "elegir:sp-llum-poblenou"}]
  }]
}
```
- **Contenido:** foto (con `alt`) y su pie, una línea por elemento de `pie`; el último siempre es "Imagen ilustrativa". Después, el nombre como título, una línea por elemento de `lineas` y los botones de la tarjeta.
- **`foto`:** puede faltar.
- **En inglés:** las tarjetas no llevan tagline ni descripción de la foto (los datos del catálogo están en castellano).
- **Botones de la tarjeta:** se desactiva solo el pulsado mientras se envía, y si la petición falla se vuelve a activar. Así "Ver plano" no bloquea "Elegir este".

**`galeria`**: fotos de un espacio.
```json
{"tipo": "galeria", "titulo": "Fotos de Llum del Poblenou",
 "fotos": [{"url": "/media/llum-poblenou-foto-01", "alt": "Foto ilustrativa de Llum del Poblenou",
            "pie": "Imagen ilustrativa"}, …]}
```
Título y una rejilla de fotos, cada una con su pie ("Imagen ilustrativa").

**`plano`**: plano orientativo de un espacio (SVG generado con los datos del catálogo).
```json
{"tipo": "plano", "url": "/media/llum-poblenou-plano", "alt": "Plano orientativo de Llum del Poblenou"}
```
Se pinta como imagen. El texto "Plano orientativo · [nombre]" ya va dentro del SVG, en el idioma de la conversación.

### 3.4 Botones de respuesta rápida y valores de `accion`

El front manda el `accion` del botón pulsado tal cual, **sin inventar ni construir valores**. Los que puede devolver el servidor:

| `accion` | Cuándo aparece |
|---|---|
| `elegir:<id>` · `plano:<id>` · `fotos:<id>` | En las tarjetas |
| `privacidad:si` · `privacidad:no` | Pregunta de privacidad (botones "Sí, acepto" / "No, gracias") |
| `publicidad:si` · `publicidad:no` | Pregunta de publicidad |
| `oferta:si` · `oferta:no` | El cliente pide una persona con una consulta en marcha ("Sí, envíalo" / "No, sigamos") |

```json
POST /api/mensaje
{"sesion": "conv-68dc26ae06e9091b", "accion": "elegir:sp-llum-poblenou"}
→ 200
{"idioma": "es", "ui": {…},
 "mensajes": [{"tipo": "texto", "texto": "Perfecto, el Llum."},
              {"tipo": "texto", "texto": "¿Tenéis ya un día concreto? ¿Y un presupuesto aproximado?"}],
 "botones": [], "formulario": false, "cerrada": false}
```

- **Burbuja del cliente:** el front puede pintar el texto del botón pulsado como si lo hubiera escrito el cliente.
- **Botones rápidos:** al pulsar uno se desactivan todos los del grupo.

### 3.5 Formulario de datos

Aparece cuando el cliente acepta la privacidad (`"formulario": true`). Tiene cuatro campos, con las etiquetas de `ui`:

| Campo | Etiqueta (`ui`) | Obligatorio |
|---|---|---|
| `nombre` | `f_nombre` | sí |
| `email` | `f_email` | sí |
| `empresa` | `f_empresa` | no |
| `telefono` | `f_telefono` | no |

```json
POST /api/mensaje
{"sesion": "conv-68dc26ae06e9091b",
 "formulario": {"nombre": "Marina Prueba", "email": "alejandro+ie007-c99@alelabs.es", "empresa": "Demo Corp", "telefono": ""}}
→ 200
{"idioma": "es", "ui": {…},
 "mensajes": [{"tipo": "texto", "texto": "¿Quieres recibir también novedades de espacios y eventos? Es opcional."}],
 "botones": [{"texto": "Sí, quiero", "accion": "publicidad:si"}, {"texto": "No, gracias", "accion": "publicidad:no"}],
 "formulario": false, "cerrada": false}
```

- **Datos incompletos:** si falta el nombre o el email no es válido, el servidor responde "Me falta tu nombre / un email válido…" con `"formulario": true` otra vez.
- **Validación:** la que haga el front es solo de comodidad; la que cuenta es la del servidor.
- **Envío:** con la respuesta a la publicidad, el servidor envía la consulta a n8n y devuelve la frase final ("Gracias. El equipo se pondrá en contacto contigo en breve.").

### 3.6 Cerrar y sesión perdida

```json
POST /api/cerrar
{"sesion": "conv-68dc26ae06e9091b"}
→ 200
{"idioma": "es", "ui": {…},
 "mensajes": [{"tipo": "texto", "texto": "Gracias por escribirnos. ¡Hasta pronto!"}],
 "botones": [], "formulario": false, "cerrada": true}
```

**Sesión perdida.** Si la sesión ya no existe (servidor reiniciado, o 30 minutos de inactividad), cualquier `/api/mensaje` devuelve **404** con la marca `sesion_perdida`:

```json
→ 404
{"error": "Algo ha fallado por nuestra parte. Inténtalo de nuevo en un momento.", "sesion_perdida": true}
```

El front no enseña el error genérico. Hace esto:
1. Desactiva los botones de la conversación anterior.
2. Pide una sesión nueva en el mismo idioma:

```json
POST /api/nueva
{"motivo": "sesion_perdida", "idioma": "es"}
→ 200
{"sesion": "conv-503f8a4aaa0aaad6", "idioma": "es", "ui": {…},
 "mensajes": [{"tipo": "texto", "texto": "Parece que esta conversación se ha cerrado. Empecemos de nuevo: ¿qué evento tenéis en mente?"}]}
```

3. Pinta ese mensaje y sigue con la sesión nueva, sin botones. El aviso de IA no se repite.

**Otros errores:**

| Código | Cuándo |
|---|---|
| `400` | Cuerpo que no es JSON |
| `413` | Petición de más de 16 KB (los mensajes de texto se cortan a 1.000 caracteres) |
| `500` | Fallo interno. El cuerpo trae `error` con la frase genérica, que es lo que se enseña |

### 3.7 `GET /media/<id>`

- **Qué sirve:** solo fotos y planos **aprobados** del catálogo, por su id. Cualquier otra cosa da 404: fotos no aprobadas, tours, rutas o `..`.
- **Origen:** las URL que da el servidor son relativas (`/media/…`). Si el front está en otro origen, se les pone delante la dirección del backend, por ejemplo `http://127.0.0.1:8000/media/llum-poblenou-foto-02`.

---

## 4. Front en otra dirección: CORS

Si el front está en otro puerto o dominio (por ejemplo, `http://localhost:5173`), el navegador bloquea las peticiones al backend si este no lo permite. Para permitirlo:

```bash
CHAT_CORS_ORIGIN=http://localhost:5173 python3 chat/servidor.py
```

- **Con la variable:** el servidor responde con `Access-Control-Allow-Origin: http://localhost:5173` (y `Vary: Origin`) en todas las respuestas. A la petición previa `OPTIONS` contesta `204` con `Access-Control-Allow-Methods: GET, POST, OPTIONS` y `Access-Control-Allow-Headers: Content-Type`.
- **Sin la variable** (por defecto): no hay cabeceras CORS y `OPTIONS` devuelve 405.
- **Nunca `*`:** si se pone `CHAT_CORS_ORIGIN="*"`, el servidor no arranca. Hay que poner la dirección exacta del front, con protocolo y puerto.
- **Mismo ordenador:** recordad que el backend solo escucha en `127.0.0.1`, así que el front tiene que ejecutarse en el mismo ordenador.

---

## 5. Reglas que el front tiene que respetar

1. **Nunca rutas de archivo.** Solo las URL `/media/<id>` que da el servidor. Nada de `media/placeholders/…` ni nombres de archivo en pantalla.
2. **Escapar siempre el HTML.** Todo el texto del servidor y del cliente se pinta como texto (`textContent` o equivalente), nunca como HTML (`innerHTML`). Aunque venga del servidor, puede incluir lo que escribió el cliente.
3. **"Imagen ilustrativa" en todas las fotos** (viene en el `pie`) y **"Plano orientativo" en los planos** (va dentro del SVG). No se quitan ni se esconden: las fotos están generadas con IA y los planos son esquemáticos.
4. **Llamar a `/api/cerrar`** al pulsar "Terminar" y al cerrar o salir de la pestaña. Para la salida, con `navigator.sendBeacon(url, JSON.stringify({sesion}))` en el evento `pagehide`. Así queda la línea en el registro anónimo. Si el cliente ya había dado sus datos y solo faltaba la pregunta de publicidad, en ese momento se envía la consulta (con publicidad "no").
5. **No guardar nada de la conversación en el navegador:** ni `localStorage`, ni `sessionStorage`, ni cookies, ni IndexedDB. La sesión vive en una variable y se pierde al recargar, que es lo que queremos.
6. **No cambiar las frases.** Los textos del chatbot y de `ui` salen de `chat/frases.json` (los escribe el equipo); el front los pinta tal cual. Si hace falta otra frase, se pide al equipo.
7. **No reordenar ni filtrar** las tarjetas, los mensajes ni los botones.
8. **No poner precios, disponibilidad ni promesas** en la interfaz (por ejemplo, un "¡Reserva ya!"). Las reglas del chatbot lo prohíben (`AGENTS.md`).

## 6. Lo que el front NO puede hacer

- **La URL y la clave de n8n** (`N8N_WEBHOOK_URL`, `N8N_API_KEY`) solo viven en el servidor, como variables de entorno. Nunca en el código del front, en el navegador, en el repositorio ni en el chat. Si el navegador las tuviera, cualquiera podría mandar consultas falsas que disparan emails reales.
- **Sin esas variables, el envío es simulado** (`202_simulada`): el chatbot funciona igual y no sale nada hacia n8n. Es lo normal mientras se desarrolla.
- **El front nunca habla con n8n directamente** ni monta el envío: lo hace `scripts/enviar_n8n.py` en el servidor, que también tapa tarjetas, IBAN y DNI y, sin consentimiento, los datos personales.
- **No decide nada:** ni qué espacio recomendar, ni qué preguntar, ni cuándo pedir datos. Si el front necesita otro comportamiento, se cambia en el servidor (y en sus tests), no en el navegador.

---

## 7. Dónde está cada cosa

| Carpeta / archivo | Qué hay |
|---|---|
| `chat/servidor.py` | Servidor HTTP (API, media, CORS, inactividad) |
| `chat/conversacion.py` | Estado de cada conversación y orden de los pasos; llama a los scripts |
| `chat/entender_reglas.py` | Lee el mensaje del cliente: intención y datos, por palabras clave (es/en). Se podría cambiar por un LLM con la misma entrada y salida |
| `chat/frases.json` · `chat/config.py` | Todas las frases (es/en) · `[EMPRESA]` y puerto |
| `chat/index.html`, `chat/static/` | Nuestro front de referencia (HTML, CSS y JS sin dependencias) |
| `scripts/` | Scripts de decisión (tabla de abajo), validador y generador de planos |
| `data/espacios.json` · `data/inventario.json` | Catálogo de los 6 espacios (datos sintéticos) · extras |
| `media/placeholders/` | Fotos (generadas con IA) y planos SVG |
| `.claude/skills/` | Las skills del chatbot: las reglas escritas por el equipo |
| `KNOWLEDGE.md` · `AGENTS.md` | Decisiones del proyecto (§3.2: contrato con n8n) · las 5 reglas que nunca se rompen |
| `plugins/eventos-front-door/` | Plugin de Claude Code, generado (no se edita a mano) |

**Qué decide cada script:**

| Script | Decide |
|---|---|
| `scripts/router.py` | Qué intención va primero, la ruta, qué skills entran y si la conversación acabará en un envío a n8n |
| `scripts/recomendar.py` | Qué espacios recomendar y en qué orden (aforo, antelación, horario, zona), la foto de cada tarjeta y la validación del espacio elegido |
| `scripts/datos_consulta.py` | Qué datos faltan, qué preguntar después (máximo dos) y cuándo está lista la consulta |
| `scripts/enviar_n8n.py` | Monta los 15 campos del contrato, tapa datos, envía (o simula) una sola vez y escribe el registro anónimo |
| `scripts/validar_datos.py` | Que el catálogo y la media son coherentes |

**Si cambiáis el catálogo** (`data/espacios.json`):
1. `python3 scripts/validar_datos.py` tiene que dar "todo correcto".
2. Si cambian aforos o zonas: `python3 scripts/generar_planos.py` (regenera los planos SVG).
3. Pasad todos los tests (§8). Algunos esperados dependen de los datos: si fallan por el cambio, hay que hablarlo con el equipo antes de tocarlos.
4. Si se usa el plugin: `python3 scripts/empaquetar_plugin.py`.

---

## 8. Cómo probar que funciona

**Tests que ya existen** (sin red externa; el envío es simulado):

```bash
python3 scripts/validar_datos.py
python3 scripts/test_recomendar.py
python3 scripts/test_router.py
python3 scripts/test_datos_consulta.py
python3 scripts/test_enviar_n8n.py
python3 scripts/test_generar_planos.py
python3 chat/test_entender.py
python3 chat/test_rutas.py
python3 chat/frases_dificiles.py
```

- **`chat/test_rutas.py`:** recorre las 3 rutas de la demo con el guion fijo y con 5 variantes por paso, los casos de error y el servidor HTTP (media, sesión perdida, CORS).
- **`chat/frases_dificiles.py`:** comprueba que ninguna respuesta a frases coloquiales o con faltas lleva precio, promesa ni dato inventado.

**Ejemplo de conversación con curl** (con el servidor arrancado). Poned el JSON entre comillas simples: en zsh, algo como `"$a:s…"` dentro de comillas dobles se interpreta y rompe el JSON.

```bash
SESION=$(curl -s -X POST http://127.0.0.1:8000/api/nueva -H 'Content-Type: application/json' -d '{}' | python3 -c 'import json,sys; print(json.load(sys.stdin)["sesion"])')
```

```bash
curl -s -X POST http://127.0.0.1:8000/api/mensaje -H 'Content-Type: application/json' -d '{"sesion":"'"$SESION"'","texto":"Hola"}'
```

```bash
curl -s -X POST http://127.0.0.1:8000/api/mensaje -H 'Content-Type: application/json' -d '{"sesion":"'"$SESION"'","texto":"Queremos una presentación de producto para unas 120 personas en enero, por la zona de Poblenou"}'
```

```bash
curl -s -X POST http://127.0.0.1:8000/api/mensaje -H 'Content-Type: application/json' -d '{"sesion":"'"$SESION"'","accion":"elegir:sp-llum-poblenou"}'
```

```bash
curl -s -X POST http://127.0.0.1:8000/api/cerrar -H 'Content-Type: application/json' -d '{"sesion":"'"$SESION"'"}'
```

**Para ver el flujo completo en el navegador:** abrid `127.0.0.1:8000` con el servidor arrancado. Es nuestro front de referencia, y pinta cada tipo de elemento como se describe en §3.3.
