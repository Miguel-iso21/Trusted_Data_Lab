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

# INEGI DENUE: directorio de establecimientos veterinarios y afines en Colima
DENUE_ENTIDAD = "06"  # Clave INEGI del Estado de Colima
DENUE_SECTORES = {
    "541941": "Servicios veterinarios para mascotas del sector privado",
    "541942": "Servicios veterinarios para el ganado y otros animales",
    "461121": "Comercio al por menor de alimentos y accesorios para mascotas",
    "812110": "Servicios de estética, baño y cuidado de mascotas",
}
DENUE_MUNICIPIOS = [
    "Colima",
    "Villa de Álvarez",
    "Manzanillo",
    "Tecomán",
    "Armería",
    "Comala",
    "Coquimatlán",
    "Cuauhtémoc",
    "Ixtlahuacán",
    "Minatitlán",
]
# Bounding box del Estado de Colima para validacion geografica
DENUE_BBOX_COLIMA = {
    "lat_min": 18.50,
    "lat_max": 19.60,
    "lon_min": -104.80,
    "lon_max": -103.40,
}
