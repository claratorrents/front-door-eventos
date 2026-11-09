"""Configuración del chat web. Lo que cambia con la empresa está aquí, en un solo sitio."""

# Nombre de la empresa: sustituye a "[EMPRESA]" en todas las frases y en la interfaz.
EMPRESA = "[EMPRESA]"

# Servidor: solo en este ordenador
HOST = "127.0.0.1"
PUERTO = 8000

# Fin de la conversación por inactividad (decisión 5)
INACTIVIDAD_MINUTOS = 30

# Límites de entrada
MAX_TEXTO = 1000          # caracteres por mensaje
MAX_CUERPO = 16 * 1024    # bytes por petición

# Protección cuando el servidor está expuesto (p. ej. en Render)
MAX_SESIONES = 500                # conversaciones abiertas en memoria; si se supera, se cierran las más antiguas
LIMITE_PETICIONES_MINUTO = 60     # peticiones a /api/ por IP y minuto; si se supera, 429

# Idiomas del chat (decisión del equipo): castellano e inglés
IDIOMAS = ("es", "en")
