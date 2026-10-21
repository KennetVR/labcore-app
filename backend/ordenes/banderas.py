"""Calculo de la bandera de un resultado contra el rango de referencia del examen.

La bandera se expresa con una sola letra porque el campo `OrdenItem.bandera`
admite cinco caracteres: "H" alto, "L" bajo y "" cuando el resultado esta dentro
del rango o no se puede comparar.
"""
import re
from decimal import Decimal

ALTO = "H"
BAJO = "L"

# Un numero con punto decimal (hasta cuatro decimales, como el modelo) o con
# coma decimal. La coma solo se acepta con uno o dos decimales: "1,000" es
# ambiguo entre 1.000 y 1000, asi que se rechaza en lugar de adivinar.
_NUMERO_PUNTO = re.compile(r"^[+-]?\d+(\.\d{1,4})?$")
_NUMERO_COMA = re.compile(r"^[+-]?\d+,\d{1,2}$")


def parsear_numero(resultado):
    """Devuelve el valor numerico del resultado o None si no es comparable."""
    if resultado is None:
        return None
    texto = str(resultado).strip()
    if not texto:
        return None
    if _NUMERO_PUNTO.match(texto):
        return Decimal(texto)
    if _NUMERO_COMA.match(texto):
        return Decimal(texto.replace(",", "."))
    return None


def estado_rango(examen, resultado):
    """Clasifica el resultado: alto, bajo, normal o sin_rango."""
    if getattr(examen, "resultado_tipo", "numerico") != "numerico":
        return "sin_rango"
    ref_min = examen.ref_min
    ref_max = examen.ref_max
    if ref_min is None and ref_max is None:
        return "sin_rango"
    valor = parsear_numero(resultado)
    if valor is None:
        return "sin_rango"
    if ref_min is not None and valor < ref_min:
        return "bajo"
    if ref_max is not None and valor > ref_max:
        return "alto"
    return "normal"


def calcular_bandera(examen, resultado):
    """Devuelve "H", "L" o "" segun el rango de referencia del examen."""
    estado = estado_rango(examen, resultado)
    if estado == "alto":
        return ALTO
    if estado == "bajo":
        return BAJO
    return ""
