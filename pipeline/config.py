"""Rutas y constantes compartidas."""
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
BRONCE = RAIZ / "data" / "bronce"
PLATA = RAIZ / "data" / "plata"
ORO = RAIZ / "data" / "oro"
CUARENTENA = RAIZ / "data" / "cuarentena"
BITACORA = RAIZ / "calidad" / "bitacora_capturas.csv"

# Banxico SIE: tipo de cambio FIX pesos por dolar (diario, dias habiles)
BANXICO_SERIE_USD = "SF43718"
# INEGI Banco de Indicadores (BISE): EMS, Servicios veterinarios para mascotas (541941),
# Ingresos totales por suministro de bienes y servicios, indice base 2018=100, mensual.
INEGI_INDICADOR = "716898"

# Rangos validos por fuente para la puerta de calidad: (minimo, maximo)
RANGOS = {"banxico": (5.0, 50.0), "inegi": (10.0, 500.0)}
