# Prueba envio-n8n 02 · Ruta estrella repetida con los arreglos

Fecha: 9 de noviembre de 2026
Repite la ruta estrella de `pruebas/prueba-envio-n8n-01.md` después de los arreglos de hoy:
- **Zona en el recomendador:** `recomendar.py --zona`.
- **Preguntas pendientes:** `datos_consulta.py` con `--respondidos` y dos preguntas como máximo sin respuesta.
- **Consentimiento:** frase de privacidad con la empresa y repetición una sola vez.
- **Envío:** `enviar_n8n.py` con `resuelto_sin_humano` calculado y el registro en el directorio de trabajo.

Plugin 0.2.1.

Método:
- **Papeles:** igual que la 01. Yo hago de chatbot siguiendo las skills y de cliente sintético: "Marina Prueba", `alejandro+ie007-c99@alelabs.es`, empresa inventada "Demo Corp".
- **Envío:** SIMULADO (sin `N8N_WEBHOOK_URL` ni `N8N_API_KEY`).
- **Registro:** `enviar_n8n.py` se ha ejecutado desde una carpeta temporal, que hace de directorio de trabajo del chat, y el registro se ha creado ahí.

Hoy es 9/11/2026.

## Conversación

| Turno | Mensaje | Script / decisión interna |
|---|---|---|
| C0 | Hola. | Saludo: sin router |
| B0 | Hola, soy el asistente virtual de [EMPRESA]. Te ayudo a encontrar espacio para tu evento; una persona del equipo revisa las reservas y propuestas. ¿Qué evento tenéis en mente? | Aviso de IA |
| C1 | Queremos una presentación de producto para unas 120 personas en enero, por la zona de Poblenou. | `router.py nuevo_evento` → guardrails, recomendador, cualificador · si toca media, consentimiento, envio-n8n · `a_n8n` true · ruta `lead` |
| | | `recomendar.py --asistentes 120 --disposicion theater --zona Poblenou` → **Llum** `comodo` (`otra_zona` false, foto-02); Mirador `comodo` (`otra_zona` **true**, foto-03); Fòrum `al_limite` (`otra_zona` **true**, foto-01) |
| | | `datos_consulta.py --tipo "presentación de producto" --asistentes "unas 120" --zona Poblenou --fecha mes` → preguntas [dia_exacto, presupuesto] (esperan: este mensaje ya lleva dos preguntas) |
| B1 | Para una presentación lo normal es formato teatro; ¿os encaja?<br>**Llum del Poblenou.** Antigua nave textil reconvertida con luz cenital e interior industrial. Hasta 200 personas en teatro. Encaja para una presentación de producto. *[imagen: llum-poblenou-foto-02, Imagen ilustrativa]*<br>Fuera de Poblenou, también os encajaría…<br>**Mirador de Montjuïc.** Salón panorámico con terraza privada y vistas al mar y al puerto. Tiene sitio para 160 personas en formato teatro. *[imagen: mirador-montjuic-foto-03, Imagen ilustrativa]*<br>**Fòrum de les Corts.** Sala ejecutiva y polivalente junto a los principales centros de negocio. Hasta 130 personas en teatro. Cabe justo; si podéis ser alguno más, mejor el Llum. *[imagen: forum-les-corts-foto-01, Imagen ilustrativa]*<br>¿Cuál os encaja más? También puedo enseñaros el plano o el recorrido 360°. | Frase nueva del recomendador §3 para los de otra zona |
| C2 | Sí, teatro. Nos quedamos con el Llum. | `preferred_location` "Llum del Poblenou" |
| | | `datos_consulta.py … --espacio "Llum del Poblenou"` → preguntas [dia_exacto, presupuesto] |
| B2 | Perfecto, el Llum del Poblenou. ¿Tenéis ya un día concreto? ¿Y un presupuesto aproximado? | 1.ª vez: dia_exacto, presupuesto |
| C3 | ¿Tiene parking? | Cambia de tema: las preguntas siguen **pendientes** |
| | | `… --preguntados dia_exacto,presupuesto` → preguntas [dia_exacto, presupuesto] · listo **false** |
| B3 | El Llum tiene carga y descarga en puerta, y un parking público a 150 m. Y sobre lo de antes: ¿tenéis ya un día concreto? ¿Y un presupuesto aproximado? | Primero su tema; después se repite la pregunta pendiente (cualificador §4). 2.ª vez: dia_exacto, presupuesto |
| C4 | ¿Nos podéis hacer un 10 % de descuento? | `escalar_comercial`, `descuento` · al message. Segunda vez sin respuesta → dia_exacto y presupuesto **quedan cerrados** |
| | | `… --preguntados dia_exacto,presupuesto,dia_exacto,presupuesto` → preguntas [necesidades] · listo **false** |
| B4 | Los descuentos los valora el comercial; lo verás con él cuando te contacte. ¿Necesitaréis algo especial, como catering o audiovisuales? | 1.ª vez: necesidades |
| C5 | El día sería el 20 de enero de 2027. | Día exacto: dado → se revalida. Necesidades sin respuesta → pendiente |
| | | `recomendar.py --validar sp-llum-poblenou --asistentes 120 --disposicion theater --dias 72` → encaja, sin motivos ni avisos, `comodo`, foto-02.<br>`datos_consulta.py … --fecha dia --preguntados …,necesidades` → preguntas [necesidades] · listo **false** |
| B5 | Para el 20 de enero, el Llum del Poblenou llega bien. ¿Necesitaréis algo especial, como catering o audiovisuales? | 2.ª vez: necesidades |
| C6 | Tenemos un presupuesto de 8.000 € y necesitamos pantalla y sonido. | Presupuesto y necesidades: dados |
| | | `datos_consulta.py … --presupuesto "8.000 €" --necesidades "pantalla y sonido" … --respondidos necesidades` → faltan [] · **listo true** → consentimiento §4 |
| B6 | Apuntado. Para que el equipo prepare tu propuesta y se ponga en contacto contigo, necesito tu nombre y tu email (y el nombre de la empresa, si el evento es para una empresa). ¿Aceptas que los usemos solo para gestionar tu consulta, según nuestra política de privacidad? | Frase nueva, con la empresa: una presentación de producto es un evento corporativo. **La privacidad llega ahora, con el día, el presupuesto y las necesidades ya dados** |
| C7 | Sí, acepto. Me llamo Marina Prueba, mi email es alejandro+ie007-c99@alelabs.es y la empresa es Demo Corp. | `gdpr_consent: yes` |
| B7 | ¿Quieres recibir también novedades de espacios y eventos? Es opcional. | Publicidad, una vez |
| C8 | No, gracias. | `marketing_consent: no` → envio-n8n |
| | | `enviar_n8n.py` (sin variables de entorno) → `enviado` simulado · `respuesta` 202_simulada · `lead_id` CB-20261109-104838-Q84I · frase de éxito |
| B8 | Gracias. El equipo se pondrá en contacto contigo en breve. | envio-n8n §4 |

### Payload enviado (simulado)
```json
{
  "lead_id": "CB-20261109-104838-Q84I",
  "timestamp": "2026-11-09T10:48:38Z",
  "name": "Marina Prueba",
  "email": "alejandro+ie007-c99@alelabs.es",
  "company": "Demo Corp",
  "phone": "",
  "preferred_location": "Llum del Poblenou",
  "event_type": "presentación de producto",
  "event_date": "2027-01-20",
  "guests": "unas 120",
  "budget_eur": "8.000 €",
  "message": "Necesitan pantalla y sonido. Pide un 10 % de descuento.",
  "conversation": "Client: Hola.\nBot: Hola, soy el asistente virtual de [EMPRESA]. …\n…\nClient: Sí, acepto. Me llamo Marina Prueba, mi email es alejandro+ie007-c99@alelabs.es y la empresa es Demo Corp.\nBot: ¿Quieres recibir también novedades de espacios y eventos? Es opcional.\nClient: No, gracias.",
  "gdpr_consent": "yes",
  "marketing_consent": "no"
}
```
`conversation` lleva los 17 turnos completos (C0 a C8); aquí se abrevia.

### Línea del registro anónimo
Escrita en `registros/conversaciones.jsonl` **de la carpeta de trabajo**. No se ha creado `registros/` ni en el proyecto ni en `plugins/eventos-front-door/`.
```json
{"id_conversacion": "conv-ruta-estrella-02", "fecha_hora": "2026-11-09T10:48:38Z", "idioma": "es", "ruta": "lead", "rutas_adicionales": [], "decision": "escalar_comercial", "motivo_escalado": "descuento", "espacio_elegido": "Llum del Poblenou", "enviado_n8n": "simulado", "respuesta_n8n": "202_simulada", "lead_id": "CB-20261109-104838-Q84I", "consentimiento_datos": "si", "consentimiento_publicidad": "no", "resuelto_sin_humano": "si"}
```
`resuelto_sin_humano` lo calcula el script: `si`, porque es una consulta enviada a n8n y el descuento va en el message, que es el proceso normal.

## Reglas: ¿se cumplieron?

| # | Regla | 01 | 02 |
|---|---|---|---|
| 1 | Aviso de IA en el primer mensaje, sin pedir datos | Sí | Sí |
| 2 | Router: `nuevo_evento`, ruta `lead`, `a_n8n` true, envio-n8n entre las skills | Sí | Sí |
| 3 | Disposición deducida y confirmada en la misma frase, recomendando en el mismo mensaje | Sí | Sí |
| 4 | Máximo dos preguntas por mensaje entre todas las skills | Sí | Sí |
| 5 | Recomendación: espacios, orden y fotos del script; sin porcentajes ni precio; "por qué encaja" solo con `event_types` | Sí | Sí |
| 6 | La zona del cliente (Poblenou) va primero; los de otras zonas, aparte y marcados | **No** | **Sí**: el Llum, primero; Mirador y Fòrum con `otra_zona` y "Fuera de Poblenou, también os encajaría…" |
| 7 | Espacio elegido → `preferred_location` con el nombre completo | Sí | Sí |
| 8 | Información dentro del evento (parking), con los datos del espacio, sin cambiar la ruta | Sí | Sí |
| 9 | Descuento: no se concede, va al `message`, sin plazos | Sí | Sí |
| 10 | Día exacto después de elegir → se revalida | Sí | Sí |
| 11 | Si cambia de tema, la pregunta sigue pendiente y se repite una vez después de atender su tema; tras dos veces sin respuesta, queda cerrada | — (regla nueva) | **Sí**: B3 repite día y presupuesto; B5 repite necesidades |
| 12 | La privacidad no llega hasta tener día, presupuesto y necesidades (o dos preguntas sin respuesta) | **No** | **Sí**: llega en B6, con los tres datos ya dados |
| 13 | Consentimiento: frase con la empresa si el evento es corporativo; solo cuenta un "sí" claro | Sí (sin empresa) | **Sí**, con la empresa |
| 14 | La pregunta de privacidad se repite una vez como máximo | No cubierto | Sí (no hizo falta repetirla) |
| 15 | Publicidad: una vez, después del "sí", aparte | Sí | Sí |
| 16 | Envío: una sola vez, solo con ruta `lead` y la privacidad respondida | Sí | Sí |
| 17 | Payload: 15 campos de texto; `event_date` solo con día exacto; `message` con necesidades y escalado | Sí | Sí |
| 18 | `company` llega con la empresa | No (vacío) | **Sí**: "Demo Corp" |
| 19 | Sin URL ni clave: envío simulado (202_simulada) y frase de envio-n8n §4 | Sí | Sí |
| 20 | `resuelto_sin_humano` calculado por el script | No (venía en la entrada) | **Sí**: `si` |
| 21 | Registro anónimo sin datos personales, en el directorio de trabajo y nunca en la carpeta del plugin | Sí (pero junto al script) | **Sí** |

**Resultado:** las 21 reglas se cumplen. Los dos fallos de la 01 (zona y privacidad demasiado pronto) y los dos puntos sin cubrir (empresa y `resuelto_sin_humano`) quedan resueltos.

## Comentarios

1. **Cualificador §4.** La skill todavía dice "Cada dato se pregunta una sola vez. Si el cliente no lo sabe o no contesta, no se insiste: cuenta como preguntado". Eso choca con la definición nueva de `listo_para_enviar` (si no contesta, se repite una vez). En esta prueba he seguido la definición nueva y el script.
2. **Día y presupuesto cerrados sin respuesta.** Tras dos preguntas sin respuesta (B2 y B3) quedaron cerrados. El cliente los dio después por su cuenta (C5 y C6) y se enviaron igual. Si no los hubiera dado, la consulta habría salido sin ellos, como dice la regla.
3. **La skill del recomendador no dice que se pase `--zona`.** La §2 sigue nombrando solo asistentes, disposición, días y hora de fin. En la prueba lo he pasado porque lo pide la frase nueva de la §3.
4. **Zona con solo espacios `bajo_60`.** Con "Sant Martí", el único espacio de la zona es la Nau, en `bajo_60`, y sale primero. La frase de `bajo_60` ("…pero es el que encaja con [horario / fecha]") no encaja con un motivo de zona.
