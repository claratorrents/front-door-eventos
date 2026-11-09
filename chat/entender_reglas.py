"""ENTENDER por reglas: texto del cliente → intenciones, datos y señales.

Es la única parte que "lee" el mensaje. No decide nada: las decisiones las toman los
scripts (router.py, recomendar.py, datos_consulta.py, enviar_n8n.py) desde conversacion.py.

Interfaz fija (una versión con LLM, por ejemplo entender_llm.py, tendría que devolver
exactamente lo mismo):

    entender(texto, contexto) -> dict

    contexto: {"idioma": "es"|"en", "hoy": date, "esperando": [...]}  (esperando: lo que
              preguntó el chatbot en su último mensaje, p. ej. ["dia_exacto"] o ["privacidad"])

    salida:  {"idioma": "es"|"en"|None,
              "saludo": bool,
              "intenciones": [informacion, nuevo_evento, cambio_reserva, queja, privacidad,
                              persona, fuera_tema],
              "legal": bool,
              "datos": {tipo, tipo_base, disposicion, tarde, corporativo, asistentes,
                        asistentes_texto, fecha_nivel, fecha, fecha_pasada, hora_fin,
                        hora_ambigua, espacio, zona, presupuesto, necesidades,
                        sin_necesidades, email, telefono},
              "no_lo_sabe": bool,
              "si_no": "si"|"no"|None,
              "senales": {precio, descuento, disponibilidad, inyeccion, confirmar_reserva,
                          ofensivo, sensible, info, media, frustracion, retirar_email},
              "entendido": bool}
Solo devuelve en "datos" las claves que encuentra.
"""

import datetime
import re
import sys
import unicodedata
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))
from enviar_n8n import DNI, EMAIL, IBAN, TARJETA, TELEFONO  # noqa: E402  (mismas reglas que el envío)


def norm(texto):
    """Minúsculas y sin acentos, para comparar (los valores se sacan del texto original)."""
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").replace("’", "'")


def _hay(patron, t):
    return re.search(patron, t) is not None


# --- Idioma -------------------------------------------------------------------------
PAL_EN = {"the", "we", "we're", "were", "our", "for", "people", "guests", "hi", "hello", "hey", "how",
          "much", "does", "do", "can", "could", "you", "give", "us", "discount", "until", "till", "and",
          "please", "yes", "thanks", "thank", "would", "is", "it", "what", "around", "about", "planning",
          "company", "dinner", "need", "want", "like", "ignore", "your", "instructions", "booking", "i",
          "i'm", "my", "there", "good", "morning", "of", "at", "a", "an", "to", "be", "price", "cost",
          "midnight", "march", "euros", "catering", "and", "dj", "plus", "also", "any", "chance", "off",
          "get", "on", "finish", "rather", "not", "sure", "know", "talk", "speak", "person", "delete",
          "data", "complaint", "event", "venue", "looking", "book", "organise", "organize", "rules",
          "forget", "disregard", "confirm", "reservation", "roughly", "budget", "we'd", "we'll", "are"}
PAL_ES = {"hola", "queremos", "quiero", "para", "personas", "de", "la", "el", "que", "cuanto", "hasta",
          "si", "gracias", "unos", "unas", "y", "una", "un", "por", "zona", "en", "tiene", "hay", "nos",
          "podeis", "hacer", "descuento", "buenas", "buenos", "dias", "tardes", "sera", "seria", "dia",
          "tenemos", "necesitamos", "pantalla", "sonido", "presentacion", "cena", "producto", "enero",
          "queja", "borreis", "mis", "datos", "ademas", "mes", "pasado", "fue", "desastre", "aparcar",
          "aparcamiento", "euros", "alrededor", "presupuesto", "invitados", "asistentes", "buscamos",
          "espacio", "sitio", "organizamos", "cerca", "falta", "haria", "equipo", "grande", "tambien",
          "eliminad", "eliminar", "borrad", "favor", "me", "mi", "reclamacion", "fatal", "salio",
          "pensamos", "seremos", "somos", "con", "como", "esta", "se", "puede", "lo", "al"}


def detectar_idioma(t):
    palabras = re.findall(r"[a-z']+", t)
    en = sum(p in PAL_EN for p in palabras)
    es = sum(p in PAL_ES for p in palabras)
    if en > es:
        return "en"
    if es > en:
        return "es"
    return None


# --- Fechas -------------------------------------------------------------------------
MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6, "julio": 7,
         "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
         "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6, "july": 7,
         "august": 8, "september": 9, "october": 10, "november": 11, "december": 12}
RE_MES = "|".join(sorted(MESES, key=len, reverse=True))
RE_MES_SIN_MAY = "|".join(sorted((m for m in MESES if m != "may"), key=len, reverse=True))
TEMPORADA = (r"\b(primavera|verano|otono|invierno|el ano que viene|el proximo ano|"
             r"spring|summer|autumn|fall|winter|next year)\b")


def _fecha_dia(dia, mes, anio, hoy):
    """Día exacto. Sin año: la próxima vez que llega esa fecha (decisión 4). Devuelve
    (fecha, pasada) o None si la fecha no existe."""
    try:
        if anio:
            anio = int(anio) + (2000 if int(anio) < 100 else 0)
            f = datetime.date(anio, mes, dia)
            return f, f < hoy
        f = datetime.date(hoy.year, mes, dia)
        if f < hoy:
            f = datetime.date(hoy.year + 1, mes, dia)
        return f, False
    except ValueError:
        return None


def extraer_fecha(t, hoy):
    patrones = [
        (rf"\b(\d{{1,2}})\s+de\s+({RE_MES})(?:\s+(?:de|del)\s+(\d{{4}}))?\b", (1, 2, 3)),
        (rf"\b({RE_MES})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,?\s+(\d{{4}}))?\b", (2, 1, 3)),
        (rf"\b(\d{{1,2}})(?:st|nd|rd|th)?\s+(?:of\s+)?({RE_MES})(?:,?\s+(\d{{4}}))?\b", (1, 2, 3)),
    ]
    for patron, (gd, gm, ga) in patrones:
        m = re.search(patron, t)
        if m:
            r = _fecha_dia(int(m.group(gd)), MESES[m.group(gm)], m.group(ga), hoy)
            if r:
                return {"fecha_nivel": "dia", "fecha": r[0].isoformat(), "fecha_pasada": r[1]}
    m = re.search(r"\b(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?\b", t)   # dd/mm(/aaaa)
    if m:
        r = _fecha_dia(int(m.group(1)), int(m.group(2)), m.group(3), hoy)
        if r:
            return {"fecha_nivel": "dia", "fecha": r[0].isoformat(), "fecha_pasada": r[1]}
    # Solo el mes: "en enero", "in March" o el nombre del mes suelto ("may" en inglés solo con "in")
    if re.search(rf"\b(?:en|in|para|for|durante|during)\s+(?:el mes de\s+)?(?:{RE_MES})\b", t) or \
            re.search(rf"\b(?:{RE_MES_SIN_MAY})\b", t):
        return {"fecha_nivel": "mes"}
    if re.search(TEMPORADA, t):
        return {"fecha_nivel": "temporada"}
    return {}


# --- Hora de fin --------------------------------------------------------------------
def extraer_hora(t):
    if _hay(r"\b(medianoche|las doce de la noche|las 12 de la noche|midnight)\b|\b(00|24):00\b", t):
        return {"hora_fin": "00:00"}
    m = re.search(r"\b(?:hasta|until|till|til|finish(?:ing)? at|acabar\w* a|terminar\w* a)\s+"
                  r"(?:las?\s+|about\s+|around\s+|aprox\w*\s+)?(\d{1,2})(?:[:.](\d{2}))?\s*"
                  r"(am|pm|a\.m\.|p\.m\.|h\b|de la (?:manana|tarde|noche|madrugada)|at night|in the morning)?", t)
    if not m:
        return {}
    h, mi, q = int(m.group(1)), int(m.group(2) or 0), (m.group(3) or "").replace(".", "")
    if h > 24 or mi > 59:
        return {}
    if q in ("pm", "de la tarde", "de la noche", "at night"):
        h = h % 12 + 12 if not (q in ("de la noche", "at night") and h == 12) else 0
    elif q in ("am", "de la manana", "de la madrugada", "in the morning"):
        h = 0 if h == 12 else h
    elif h >= 13 or h == 0:
        pass
    elif 1 <= h <= 7:
        pass                       # de 1 a 7 sin más contexto: madrugada (recomendador §1)
    else:
        return {"hora_ambigua": h}  # de 8 a 12 sin "de la mañana/noche": se pregunta
    return {"hora_fin": f"{h % 24:02d}:{mi:02d}"}


# --- Tipo de evento -----------------------------------------------------------------
# (patrón normalizado, tipo_base, disposicion, suele acabar tarde, event_type del catálogo)
TIPOS = [
    (r"presentaci\w*|present(?:ar|amos|ation|ing)\b", "presentacion", "theater", False, "presentacion"),
    (r"lanzamiento\w*|launch\w*", "lanzamiento", "theater", False, "presentacion"),
    (r"conferencia\w*|congreso\w*|conference\w*", "conferencia", "theater", False, "conferencia"),
    (r"cena\w*|dinner\w*", "cena", "banquet", True, "cena"),
    (r"comida\w*|almuerzo\w*|lunch\w*", "comida", "banquet", False, None),
    (r"boda\w*|wedding\w*", "boda", "banquet", True, None),
    (r"gala\w*", "gala", "banquet", True, "gala"),
    (r"networking", "networking", "cocktail", False, "networking"),
    (r"coctel\w*|cocktail\w*", "coctel", "cocktail", False, None),
    (r"fiesta\w*|party|parties", "fiesta", "cocktail", True, None),
    (r"formacion\w*|curso\w*|training|course\w*", "formacion", "classroom", False, "formacion"),
    (r"taller\w*|workshop\w*", "taller", "classroom", False, "taller"),
]
CALIF_ES = r"(?:\s+(?:de|para)\s+(?:producto|empresa|equipo|navidad|gala|clientes|fin de ano))?"
CALIF_EN = r"(?:(?:company|team|business|corporate|christmas|product|gala|client)\s+)?"
CORPORATIVO = (r"\b(empresa\w*|corporativ\w*|producto\w*|equipo|clientes|compania|negocio|"
               r"company|corporate|business|team|product|client\w*|ltd|s\.?l\.?)\b")


def extraer_tipo(texto, t):
    for patron, base, disp, tarde, etype in TIPOS:
        m = re.search(rf"\b{CALIF_EN}(?:{patron}){CALIF_ES}", t)
        if m:
            original = texto[m.start():m.end()]   # norm() conserva la longitud del texto
            return {"tipo": original.strip(), "tipo_base": base, "disposicion": disp, "tarde": tarde,
                    "event_type": etype}
    return {}


# --- Espacios y zonas ---------------------------------------------------------------
ESPACIOS = [("sp-llum-poblenou", r"llum(?: del poblenou)?"), ("sp-jardi-gracia", r"jardi(?: de gracia)?"),
            ("sp-mirador-montjuic", r"mirador(?: de montjuic)?"), ("sp-atelier-sant-antoni", r"atelier(?: de sant antoni)?"),
            ("sp-forum-les-corts", r"forum(?: de les corts)?"), ("sp-nau-besos", r"nau(?: del besos)?")]
ZONAS = ["poblenou", "22@", "gracia", "eixample", "sant antoni", "montjuic", "sants", "les corts",
         "diagonal", "besos", "sant marti"]


def extraer_espacio_y_zona(texto, t):
    out, resto = {}, t
    for eid, patron in ESPACIOS:
        m = re.search(rf"\b(?:el |la |the |at )?{patron}\b", resto)
        if m:
            out.setdefault("espacio", eid)
            resto = resto[:m.start()] + " " * (m.end() - m.start()) + resto[m.end():]
    for z in sorted(ZONAS, key=len, reverse=True):
        m = re.search(rf"(?<![\w@]){re.escape(z)}(?![\w@])", resto)
        if m:
            out["zona"] = texto[m.start():m.end()]
            break
    return out


# --- Números: asistentes y presupuesto ----------------------------------------------
APROX = r"(?:unos|unas|alrededor de|aproximadamente|cerca de|about|around|roughly|approximately|some)"
NUM = r"\d{1,3}(?:[.,]\d{3})+|\d+(?:[.,]\d+)?"
MONEDA = r"(?:€|euros?\b|eur\b)"


def _a_int(numero):
    return int(re.sub(r"[.,]", "", numero))


def extraer_presupuesto(texto, t):
    patrones = [
        rf"(?:{APROX}\s+)?(?:{MONEDA}\s*)({NUM})\s*(k|mil)?\b",
        rf"(?:{APROX}\s+)?({NUM})\s*(k|mil)?\s*{MONEDA}",
        rf"(?:presupuesto|budget)\s+(?:de|es de|of|is|is around|is about|de unos|de unas)?\s*(?:{APROX}\s+)?({NUM})\s*(k|mil)?",
    ]
    for p in patrones:
        m = re.search(p, t)
        if m:
            inicio = m.start()
            m2 = re.search(rf"(?:{APROX})\s*$", t[:inicio])   # "unos" justo antes
            if m2:
                inicio = m2.start()
            frag = texto[inicio:m.end()].strip(" ,.")
            frag = re.sub(r"^(?:tenemos|nuestro|our|presupuesto de|budget of|budget is)\s+", "", frag, flags=re.I)
            return {"presupuesto": frag}, (inicio, m.end())
    return {}, None


def extraer_asistentes(texto, t, ocupado):
    patrones = [
        rf"(?:({APROX})\s+)?(\d{{1,4}})\s*(?:personas|persona|invitados|asistentes|pax|people|guests|attendees|persons)\b",
        rf"\b(?:somos|seremos|we are|we're|were|we'll be|there will be)\s+(?:({APROX})\s+)?(\d{{1,4}})\b(?!\s*(?:€|euro|%|k\b))",
        rf"\b(?:para|for)\s+(?:({APROX})\s+)?(\d{{1,4}})\b(?!\s*(?:€|euro|%|k\b|de\s+(?:{RE_MES})|/))",
    ]
    for p in patrones:
        for m in re.finditer(p, t):
            if ocupado and not (m.end() <= ocupado[0] or m.start() >= ocupado[1]):
                continue
            n = int(m.group(2))
            if n <= 0:
                continue
            aprox = texto[m.start(1):m.end(1)] if m.group(1) else ""
            return {"asistentes": n, "asistentes_texto": (aprox + " " + m.group(2)).strip()}
    return {}


# --- Necesidades --------------------------------------------------------------------
NECESIDADES = (r"\b(catering|audiovisual\w*|pantalla\w*|sonido|proyector\w*|microfono\w*|dj|musica en directo|"
               r"mobiliario|decoracion|fotograf\w*|seguridad|iluminacion|escenario|azafat\w*|traduccion|"
               r"av|screen\w*|sound|projector\w*|microphone\w*|mics?|furniture|decoration\w*|photographer\w*|"
               r"security|lighting|stage)\b")
SIN_NECESIDADES = r"^(?:no,?\s*)?(nada( especial| mas)?|no necesitamos nada|ninguna|nothing( special| else)?|no,? nothing|none)\b"


def extraer_necesidades(texto, t):
    if _hay(SIN_NECESIDADES, t.strip()):
        return {"sin_necesidades": True}
    encontradas = re.findall(NECESIDADES, t)
    if not encontradas:
        return {}
    if len(texto) <= 80:   # mensaje corto: lo que pide, en sus palabras
        frase = re.sub(r"^(?:s[ií],?\s+|yes,?\s+)", "", texto.strip(), flags=re.I).strip(" .")
        return {"necesidades": frase[:1].upper() + frase[1:]}
    return {"necesidades": ", ".join(dict.fromkeys(encontradas)).capitalize()}


# --- Intenciones y señales ----------------------------------------------------------
SALUDO = (r"^(hola|buenas|buenos dias|buenas tardes|buenas noches|hey|hi|hello|good morning|"
          r"good afternoon|good evening|hi there|hello there)\b[\s!.,]*")
PLANIFICAR = (r"\b(queremos|quiero|quisieramos|buscamos|busco|necesitamos|organiz\w*|celebrar|"
              r"preparar|hacer una|hacer un|otra|otro|we're planning|we are planning|planning|we'd like|"
              r"we would like|we want|looking (?:for|to)|organis\w*|organiz\w*|book|need a venue|"
              r"espacio para|sitio para|venue for)\b")
QUEJA = (r"\b(queja\w*|quejar\w*|reclamacion\w*|reclamar|reclamo|desastre|fatal|decepcion\w*|"
         r"complaint\w*|complain\w*|terrible|disappointed|awful|refund)\b")
LEGAL = r"\b(abogad\w*|denuncia\w*|demanda\w*|contrato|incumpl\w*|lawyer|sue|legal|contract)\b"
PRIVACIDAD = (r"\b(borr\w*|elimin\w*|suprim\w*|delete|remove|erase)\b.*\b(datos|informacion personal|"
              r"data|information|details)\b|\b(rgpd|gdpr|proteccion de datos|data protection|"
              r"darme de baja|unsubscribe)\b")
RETIRAR_EMAIL = r"\b(no (?:useis|utiliceis|uses|guardeis) mi (?:email|correo)|don't use my email|do not use my email)\b"
CAMBIO = (r"\b(mi|nuestra|my|our) (reserva|booking|reservation)\b|\b(cancelar|anular|cancel|reschedule)\b"
          r".*\b(reserva|booking|reservation)\b")
PERSONA = (r"\bhablar con (?:una persona|alguien|un humano|un agente|el equipo|una persona real)\b|"
           r"\b(?:speak|talk) to (?:a |someone|somebody|a real |an? )?(?:person|human|agent|someone|team)\b|"
           r"\breal person\b|\bpersona real\b")
FRUSTRACION = (r"\b(no me entiendes|no me estas entendiendo|ya te lo he dicho|no me escuchas|"
               r"you don't understand|you dont understand|i already told you|i've already said)\b")
FUERA_TEMA = (r"\b(tiempo hara|el tiempo|clima|futbol|receta\w*|chiste\w*|weather|football|soccer|"
              r"recipe\w*|joke\w*|politica|politics)\b")
PRECIO = (r"\b(cuanto cuesta|cuanto vale|cuanto sale|precio\w*|tarifa\w*|coste\w*|how much|price\w*|"
          r"cost\w*|rate\w*|quote)\b")
DESCUENTO = r"\b(descuento\w*|rebaja\w*|mas barato|oferta|discount\w*|cheaper|deal)\b|\d+\s*%\s*off|% off"
DISPONIBILIDAD = r"\b(libre|disponible\w*|disponibilidad|ocupad\w*|available|availability|free on)\b"
INYECCION = (r"\b(ignora\w*|ignore\w*|olvida\w*|forget|disregard)\b.*\b(instruccion\w*|instructions?|rules?|"
             r"reglas?|normas?|you were given)\b|\b(system prompt|tu prompt|your prompt|el prompt)\b|"
             r"\b(actua como|pretend (?:you|to be)|you are now)\b")
CONFIRMAR = (r"\b(confirm\w*)\b.*\b(reserva|booking|reservation)\b|\b(booking|reserva) (?:is|esta) confirm\w*|"
             r"\breserva confirmada\b")
INSULTOS = r"(inutil\w*|idiota\w*|estupid\w*|imbecil\w*|gilipollas|basura|useless|idiot\w*|stupid|moron\w*|garbage)"
OFENSIVO = (rf"\b(eres|sois|es usted|you are|you're|youre|ur|menudo|vaya|que)\b[\w\s,]{{0,20}}\b{INSULTOS}\b|"
            rf"^{INSULTOS}\b|\b(callate|calla ya|shut up)\b")
PREGUNTA_INFO = r"\?|^(tiene|teneis|tienen|hay|se puede|do you|does it|is there|are there|can we|has it)\b"
INFO = [("parking", r"\b(parking|aparcamiento|aparcar|park\w*)\b"),
        ("accesibilidad", r"\b(accesib\w*|silla de ruedas|wheelchair|accessib\w*|ascensor|lift|elevator)\b"),
        ("catering", r"\b(catering|cocina|kitchen)\b"),
        ("horario", r"\b(musica|music|hasta que hora|horario|ruido|until what time|noise)\b"),
        ("equipamiento", r"\b(wifi|proyector\w*|pantalla\w*|projector\w*|screen\w*|microfono\w*|microphone\w*)\b")]
MEDIA = [("video", r"\b(video\w*)\b"), ("plano", r"\b(plano\w*|floor ?plan\w*|plan del|layout)\b"),
         ("fotos", r"\b(fotos?|fotografias|photos?|pictures?|imagenes)\b")]
SI = (r"^(si|sí|vale|de acuerdo|acepto|claro|ok|okay|perfecto|adelante|por supuesto|yes|yeah|yep|sure|"
      r"i agree|of course|go ahead|please do)\b")
NO = r"^(no|nope|prefiero no|mejor no|i'd rather not|id rather not|no thanks|no, thanks)\b"
NO_LO_SE = (r"\b(no lo se|no se|aun no|todavia no|ya veremos|ni idea|sin decidir|no lo tenemos|"
            r"don't know|dont know|not sure|not yet|no idea|tbd|to be decided)\b")


def entender(texto, contexto=None):
    contexto = contexto or {}
    hoy = contexto.get("hoy") or datetime.date.today()
    texto = unicodedata.normalize("NFC", (texto or "").strip())
    t = norm(texto)   # misma longitud que texto: los valores se recortan del original
    out = {"idioma": detectar_idioma(t), "saludo": False, "intenciones": [], "legal": False, "datos": {},
           "no_lo_sabe": False, "si_no": None, "senales": {}, "entendido": False}
    if not t:
        return out
    d, s, intenciones = out["datos"], out["senales"], []

    # Señales de guardrails
    if TARJETA.search(texto) or IBAN.search(texto) or DNI.search(texto) or _hay(r"\b(iban|dni|nie)\b", t):
        s["sensible"] = "tarjeta" if (TARJETA.search(texto) or _hay(r"\b(tarjeta|card)\b", t)) else "otro"
    if _hay(OFENSIVO, t):
        s["ofensivo"] = True
    if _hay(INYECCION, t):
        s["inyeccion"] = True
    if _hay(CONFIRMAR, t):
        s["confirmar_reserva"] = True
    if _hay(PRECIO, t) and not _hay(r"\b(presupuesto|budget)\b", t):
        s["precio"] = True
    if _hay(DESCUENTO, t):
        m = re.search(r"(\d{1,2})\s*%", t)
        s["descuento"] = int(m.group(1)) if m else True
    if _hay(DISPONIBILIDAD, t) and not _hay(r"\bdatos\b", t):
        s["disponibilidad"] = True
    if _hay(FRUSTRACION, t):
        s["frustracion"] = True
    if _hay(RETIRAR_EMAIL, t):
        s["retirar_email"] = True
    pregunta = _hay(PREGUNTA_INFO, t)
    for tema, patron in INFO:
        if pregunta and _hay(patron, t):
            s["info"] = tema
            break
    for tipo_media, patron in MEDIA:
        if _hay(patron, t):
            s["media"] = tipo_media
            break

    # Datos personales sueltos (no se usan hasta la pregunta de privacidad)
    m = EMAIL.search(texto)
    if m:
        d["email"] = m.group(0)
    sin_tarjeta = TARJETA.sub(" ", texto)
    m = TELEFONO.search(sin_tarjeta)
    if m:
        d["telefono"] = m.group(0)

    # Datos de la consulta
    if not s.get("sensible"):
        presupuesto, ocupado = extraer_presupuesto(texto, t)
    else:
        presupuesto, ocupado = {}, None
    d.update(presupuesto)
    d.update(extraer_asistentes(texto, t, ocupado))
    d.update(extraer_fecha(t, hoy))
    d.update(extraer_hora(t))
    d.update(extraer_tipo(texto, t))
    if d.get("tipo") and _hay(CORPORATIVO, t):
        d["corporativo"] = True
    d.update(extraer_espacio_y_zona(texto, t))
    if not s.get("info"):
        d.update(extraer_necesidades(texto, t))
    if s.get("sensible"):
        for k in ("asistentes", "asistentes_texto", "fecha", "fecha_nivel", "fecha_pasada", "telefono"):
            d.pop(k, None)
    if d.get("fecha_nivel") == "dia" and "fecha" not in d:
        d.pop("fecha_nivel")

    # Intenciones
    queja = _hay(QUEJA, t) and not s.get("ofensivo")
    if _hay(PRIVACIDAD, t) or s.get("retirar_email"):
        intenciones.append("privacidad")
    if queja:
        intenciones.append("queja")
        out["legal"] = _hay(LEGAL, t)
    if _hay(PERSONA, t):
        intenciones.append("persona")
    if _hay(CAMBIO, t) and not s.get("confirmar_reserva"):
        intenciones.append("cambio_reserva")
    planifica = _hay(PLANIFICAR, t)
    if queja:   # "la cena del mes pasado fue un desastre" no es un evento nuevo
        planifica = _hay(r"\b(organiz\w*|organis\w*|otra|otro|nueva|nuevo|another|new one|again)\b", t) \
            or bool(d.get("asistentes"))
    datos_evento = bool(d.get("tipo")) and bool(d.get("asistentes") or d.get("espacio") or d.get("fecha_nivel"))
    if (planifica and (d.get("tipo") or d.get("asistentes") or d.get("espacio"))) or (datos_evento and not queja):
        intenciones.append("nuevo_evento")
    if s.get("info") and "nuevo_evento" not in intenciones:
        intenciones.append("informacion")
    if _hay(FUERA_TEMA, t) and not intenciones:
        intenciones.append("fuera_tema")
    out["intenciones"] = intenciones

    # Respuestas cortas
    if _hay(SI, t):
        out["si_no"] = "si"
    elif _hay(NO, t) and not _hay(r"^no (lo )?se\b|^no idea|^not sure", t):
        out["si_no"] = "no"
    if _hay(NO_LO_SE, t):
        out["no_lo_sabe"] = True
    if _hay(SALUDO, re.sub(r"^[^\w]+", "", t)) and not intenciones and not d and not s:
        out["saludo"] = True

    out["entendido"] = bool(out["saludo"] or intenciones or d or s or out["si_no"] or out["no_lo_sabe"])
    return out
