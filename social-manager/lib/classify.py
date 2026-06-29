"""Clasificador de señal vs ruido para comentarios/DMs sociales.
Determinista, sin costo de API. Lo reusa el cerebro (Fase 2) para priorizar.

Devuelve (status, reason, category):
  status   = 'pending' (atender) | 'skipped' (no atender)
  reason   = 'internal' | 'noise' | 'low_value' | None
  category = 'question' | 'intent' | 'complaint' | 'other' | 'dm' | None
"""
import re
import unicodedata


def _norm(s):
    s = (s or "").lower()
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def _alnum(s):
    return sum(1 for ch in (s or "") if ch.isalnum())


# intención de compra / pregunta de venta -> SIEMPRE atender
INTENT = {
    "precio", "precios", "cuanto", "cuesta", "cuestan", "vale", "valen", "costo", "costos",
    "info", "informacion", "informes", "donde", "comprar", "compra", "adquirir", "pedido",
    "ordenar", "envio", "envios", "entrega", "disponible", "disponibilidad", "stock", "hay",
    "talla", "tallas", "color", "colores", "medida", "medidas", "modelo", "modelos",
    "contiene", "contienen", "ingrediente", "ingredientes", "sirve", "funciona", "dosis",
    "cantidad", "mayoreo", "factura", "garantia", "potencia", "ficha", "cotizar", "cotizacion",
    "catalogo", "link", "pagina", "whatsapp", "numero", "telefono", "direccion", "sucursal",
    "horario", "interesa", "interesado", "interesada", "quiero", "necesito", "venden", "vende",
}

# cumplidos / reacciones sin acción -> bajo valor
POSITIVE = {
    "gracias", "bonito", "bonita", "bonitos", "hermoso", "hermosa", "guapa", "guapo",
    "encanta", "encanto", "encantan", "amo", "amooo", "lindo", "linda", "genial",
    "excelente", "felicidades", "bravo", "top", "crack", "grande", "perfecto", "perfecta",
    "rico", "delicioso", "deliciosa", "gusta", "gustan", "increible", "hermosos", "padre",
    "padrisimo", "chido", "buenisimo", "buenisima", "wow", "guau",
}

# palabras-relleno (stopwords) que no aportan acción por sí solas
STOP = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "a", "y", "o",
    "que", "con", "sin", "por", "para", "en", "se", "lo", "le", "me", "te", "su", "mi", "tu",
    "es", "son", "muy", "mas", "todo", "toda", "todos", "ya", "si", "no", "este", "esta",
    "eso", "ese", "esa", "como", "pero", "tan", "bien",
}

_INTERJECTION = re.compile(
    r"^(ja+|je+|ji+|ha+|he+|wo+w+|ye+i+|ola+|hola+|uf+|ah+|oh+|aw+|ay+|noo+|sii+|"
    r"jaja\w*|jeje\w*|lol|xd+|uy+|uuu+|ooo+|aaa+)$"
)


def _is_filler(w):
    return w in STOP or w in POSITIVE or bool(_INTERJECTION.match(w))


def classify(item, internal_set):
    author = (item.get("author") or "").lower().lstrip("@")
    if author and author in internal_set:
        return "skipped", "internal", None

    if item.get("type") == "dm":
        return "pending", None, "dm"  # los DMs siempre se atienden

    body = item.get("body") or ""
    if _alnum(body) < 2:
        return "skipped", "noise", None

    n = _norm(body)
    words = set(re.findall(r"[a-z0-9]+", n))

    # 1) pregunta explícita o intención de compra -> atender
    if "?" in body or "¿" in body:
        return "pending", None, "question"
    if words & INTENT:
        return "pending", None, "intent"

    # 2) puro cumplido/reacción (toda palabra es relleno) -> bajo valor
    if words and all(_is_filler(w) for w in words):
        return "skipped", "low_value", None

    # 3) resto (quejas, dudas sin keyword, etc.) -> atender como 'other' (no perder)
    return "pending", None, "other"
