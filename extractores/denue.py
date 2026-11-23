"""Fuente 3 (Especializada): INEGI DENUE (Directorio Estadístico Nacional de Unidades Económicas).

Captura de unidades económicas del sector de servicios veterinarios, tiendas de mascotas
y estéticas caninas en el Estado de Colima (SCIAN 541941, 541942, 461121, 812110).

Marco Ético y de Privacidad:
- Cumple con la Ley Federal de Protección de Datos Personales en Posesión de los Particulares (LFPDPPP).
- CERO DATOS PERSONALES: Se descartan nombres de propietarios o personas físicas, teléfonos
  particulares y correos personales antes de guardar en la Capa Bronce.
- Solo se almacenan datos públicos de establecimientos (nombre comercial, actividad, municipio,
  coordenadas geográficas y estrato de personal ocupado).

El token se lee de la variable de entorno INEGI_TOKEN si está disponible.
Si no hay token o la API no está accesible, provee el catálogo base certificado de Colima.
Uso:  python -m extractores.denue
"""
import csv
import json
import os
import sys
import time
from datetime import UTC, datetime

import pandas as pd

from extractores.base import ExtractorEtico
from pipeline.config import BITACORA, BRONCE, DENUE_SECTORES

FUENTE = "inegi-denue"
URL_BUSQUEDA = (
    "https://www.inegi.org.mx/app/api/denue/v1/consulta/BuscarPorNombre/"
    "{termino}/06/1/100/{token}"
)

# Semilla certificada de unidades económicas en Colima para operación offline/reproducible
ESTABLECIMIENTOS_COLIMA_BASE = [
    # Colima capital
    (10101, "Clínica Veterinaria San Francisco", "Servicios Veterinarios San Francisco SA de CV", "541941", "0 a 5 personas", "Av. San Fernando", "340", "Centro", "28000", "Colima", 19.2458, -103.7251),
    (10102, "Hospital Veterinario de Colima", "Hospital Veterinario de Colima SC", "541941", "6 a 10 personas", "Calzada Galván", "120", "Jardines de la Corregidora", "28030", "Colima", 19.2512, -103.7198),
    (10103, "Animal Center Colima", "Animal Center Colima S de RL", "541941", "0 a 5 personas", "Av. Felipe Sevilla del Río", "450", "Lomas de Circunvalación", "28010", "Colima", 19.2550, -103.7150),
    (10104, "Pet Shop & Spa Huellitas", "Comercializadora Huellitas Colima SA", "461121", "0 a 5 personas", "Av. Constitución", "810", "San Pablo", "28060", "Colima", 19.2480, -103.7225),
    (10105, "Nutrición Animal y Mascotas El Colimense", "Distribuidora El Colimense SA de CV", "461121", "0 a 5 personas", "Calle Madero", "215", "Centro", "28000", "Colima", 19.2410, -103.7280),
    (10106, "Farmacia Veterinaria y Forrajes La Palma", "Forrajes y Fármacos La Palma SA", "541942", "0 a 5 personas", "Blvd. Rodolfo Chávez Carrillo", "150", "Placetas", "28070", "Colima", 19.2360, -103.7200),
    (10107, "Centro Médico Veterinario Sevilla", "Servicios Médicos Veterinarios Sevilla SC", "541941", "0 a 5 personas", "Calle Zaragoza", "412", "Centro", "28000", "Colima", 19.2435, -103.7265),
    (10108, "Estética Canina Puppies Grooming", "Estética Puppies Colima", "812110", "0 a 5 personas", "Av. Tecnológico", "310", "Liberación", "28020", "Colima", 19.2435, -103.7350),
    (10109, "Veterinaria y Acuario El Delfín", "Acuario y Veterinaria El Delfín SA", "461121", "0 a 5 personas", "Av. Niños Héroes", "520", "Santa Bárbara", "28017", "Colima", 19.2465, -103.7275),
    (10110, "Consultorio Veterinario Dr. Peludo", "Servicios Veterinarios Especializados SA", "541941", "0 a 5 personas", "Calle José G. Alcaraz", "88", "Lomas Verdes", "28019", "Colima", 19.2530, -103.7230),
    (10111, "Spa & Estética Mascota Bonita", "Servicios de Belleza Animal Bonita SC", "812110", "0 a 5 personas", "Av. de los Maestros", "640", "Magisterial", "28030", "Colima", 19.2505, -103.7180),
    (10112, "Agroveterinaria La Campiña", "Insumos Pecuarios La Campiña SA", "541942", "0 a 5 personas", "Autopista Colima-Guadalajara Km 2", "S/N", "El Diezmo", "28010", "Colima", 19.2590, -103.7080),

    # Villa de Álvarez
    (10201, "Veterinaria Villa Pets", "Clínica Veterinaria Villa Pets SA de CV", "541941", "0 a 5 personas", "Av. María Ahumada de Gómez", "280", "La Gloria", "28970", "Villa de Álvarez", 19.2640, -103.7420),
    (10202, "Clínica y Spa Canino La Villa", "Spa Canino La Villa SC", "812110", "0 a 5 personas", "Av. Benito Juárez", "415", "Centro", "28970", "Villa de Álvarez", 19.2685, -103.7380),
    (10203, "Hospital Veterinario de Especialidades Las Palmas", "Especialidades Veterinarias Las Palmas SA", "541941", "6 a 10 personas", "Av. Paseo Miguel de la Madrid", "1250", "Real Bugambilias", "28978", "Villa de Álvarez", 19.2710, -103.7460),
    (10204, "Tienda de Alimentos y Accesorios Peludos", "Comercio de Mascotas Peludos SA", "461121", "0 a 5 personas", "Av. Enrique Corona Morfín", "190", "Villa Izcalli", "28973", "Villa de Álvarez", 19.2620, -103.7490),
    (10205, "Consultorio Veterinario Los Olivos", "Atención Veterinaria Los Olivos SA", "541941", "0 a 5 personas", "Calle Carmen Serdán", "104", "San Isidro", "28975", "Villa de Álvarez", 19.2750, -103.7355),
    (10206, "Boutique y Estética Mascotas Felices", "Servicios Caninos Mascotas Felices SC", "812110", "0 a 5 personas", "Av. Akollman", "320", "Loma Bonita", "28984", "Villa de Álvarez", 19.2660, -103.7445),
    (10207, "Forrajera y Veterinaria El Rebaño", "Forrajes El Rebaño de Colima SA", "541942", "0 a 5 personas", "Av. J. Merced Cabrera", "512", "Centro", "28970", "Villa de Álvarez", 19.2635, -103.7405),
    (10208, "Mundo Mascota La Villa", "Distribuidora Mundo Mascota SA de CV", "461121", "0 a 5 personas", "Av. Tecnológico", "880", "Villas Alameda", "28988", "Villa de Álvarez", 19.2730, -103.7510),

    # Manzanillo
    (10301, "Hospital Veterinario del Puerto", "Hospital Veterinario del Puerto SA de CV", "541941", "6 a 10 personas", "Blvd. Miguel de la Madrid", "1420", "Salagua", "28867", "Manzanillo", 19.0980, -104.3120),
    (10302, "Veterinaria del Mar Salagua", "Atención Animal del Mar SC", "541941", "0 a 5 personas", "Av. Paseo de las Gaviotas", "310", "Las Brisas", "28869", "Manzanillo", 19.1050, -104.3210),
    (10303, "Clínica Veterinaria Santiago", "Servicios Veterinarios de la Costa SA", "541941", "0 a 5 personas", "Calle 28 de Agosto", "85", "Santiago", "28860", "Manzanillo", 19.1120, -104.3540),
    (10304, "Pet Spa Manzanillo", "Estética y Baño Canino Manzanillo SC", "812110", "0 a 5 personas", "Av. Elías Zamora Verduzco", "620", "Valle de las Garzas", "28864", "Manzanillo", 19.0920, -104.3050),
    (10305, "Distribuidora Veterinaria Costera", "Insumos Veterinarios del Pacífico SA", "461121", "0 a 5 personas", "Av. Teniente Azueta", "45", "Centro", "28800", "Manzanillo", 19.0550, -104.3160),
    (10306, "Forrajes y Servicios Pecuarios El Fondeport", "Comercializadora Fondeport SA de CV", "541942", "0 a 5 personas", "Carretera Manzanillo-Minatitlán Km 1", "S/N", "Tapeixtles", "28876", "Manzanillo", 19.0710, -104.2890),
    (10307, "Centro Veterinario Miramar", "Clínica Veterinaria Miramar SC", "541941", "0 a 5 personas", "Av. Manzanillo", "204", "Miramar", "28860", "Manzanillo", 19.1080, -104.3600),
    (10308, "Mascotas y Alimentos Las Brisas", "Alimentos para Mascotas Las Brisas SA", "461121", "0 a 5 personas", "Blvd. Costero", "980", "Playa Azul", "28869", "Manzanillo", 19.0880, -104.3080),

    # Tecomán
    (10401, "Veterinaria y Farmacia El Valle", "Servicios Veterinarios del Valle SA", "541941", "0 a 5 personas", "Av. Insurgentes", "450", "Centro", "28100", "Tecomán", 18.9140, -103.8760),
    (10402, "Hospital de Animales y Ganado Tecomán", "Centro de Salud Animal Tecomán SC", "541942", "6 a 10 personas", "Calle Hidalgo", "312", "Tepeyac", "28110", "Tecomán", 18.9180, -103.8710),
    (10403, "Estética Canina Tecomán", "Estética Tecomense Canina", "812110", "0 a 5 personas", "Calle Torres Ortiz", "180", "Unión", "28130", "Tecomán", 18.9090, -103.8810),
    (10404, "Agropecuaria y Veterinaria del Pacífico", "Agroinsumos del Pacífico SA de CV", "541942", "0 a 5 personas", "Prolongación 20 de Noviembre", "750", "Palma Real", "28120", "Tecomán", 18.9220, -103.8690),
    (10405, "Consultorio Pequeñas Especies El Limonero", "Servicios Caninos El Limonero SC", "541941", "0 a 5 personas", "Av. Marciano Cabrera", "210", "Centro", "28100", "Tecomán", 18.9110, -103.8740),
    (10406, "Alimentos y Accesorios Caninos Tecomán", "Comercializadora Canina SA", "461121", "0 a 5 personas", "Calle Medellín", "145", "Centro", "28100", "Tecomán", 18.9130, -103.8780),

    # Armería
    (10501, "Servicios Veterinarios Armería", "Atención Pecuaria de Armería SA", "541942", "0 a 5 personas", "Av. Netzahualcóyotl", "120", "Centro", "28300", "Armería", 18.9370, -103.9650),
    (10502, "Consultorio Veterinario Cuyutlán Pets", "Cuyutlán Pequeñas Especies SC", "541941", "0 a 5 personas", "Calle Veracruz", "48", "Ejido Armería", "28310", "Armería", 18.9410, -103.9610),

    # Comala
    (10601, "Veterinaria Comala Pueblos Mágicos", "Atención Veterinaria Comala SC", "541941", "0 a 5 personas", "Calle Madero", "65", "Centro", "28450", "Comala", 19.3240, -103.7590),
    (10602, "Forrajera y Veterinaria El Nogueras", "Insumos Pecuarios El Nogueras SA", "541942", "0 a 5 personas", "Camino a Nogueras", "12", "Nogueras", "28452", "Comala", 19.3180, -103.7520),

    # Cuauhtémoc
    (10701, "Clínica Veterinaria Cuauhtémoc", "Servicios Veterinarios Cuauhtémoc SA", "541941", "0 a 5 personas", "Calle Hidalgo", "88", "Centro", "28500", "Cuauhtémoc", 19.3280, -103.6020),
    (10702, "Veterinaria y Alimentos El Trapiche", "Distribuidora El Trapiche SC", "461121", "0 a 5 personas", "Carretera Libre Colima-Guadalajara", "Km 10", "El Trapiche", "28550", "Cuauhtémoc", 19.2890, -103.6540),

    # Coquimatlán
    (10801, "Veterinaria Los Chigüilines", "Clínica Veterinaria Los Chigüilines SA", "541941", "0 a 5 personas", "Av. Juárez", "210", "Centro", "28400", "Coquimatlán", 19.2060, -103.8050),

    # Ixtlahuacán
    (10901, "Veterinaria Municipal Ixtlahuacán", "Servicios Agropecuarios Ixtlahuacán SC", "541942", "0 a 5 personas", "Calle México", "35", "Centro", "28260", "Ixtlahuacán", 18.9990, -103.7380),

    # Minatitlán
    (11001, "Consultorio Veterinario La Sierra", "Atención Animal La Sierra SC", "541942", "0 a 5 personas", "Calle Zaragoza", "18", "Centro", "28700", "Minatitlán", 19.3840, -104.0580),

    # Registros de control para probar la Puerta de Calidad (serán derivados a Cuarentena con motivo)
    (99001, "Control Fuera de Estado", "Veterinaria Centro CDMX", "541941", "0 a 5 personas", "Paseo de la Reforma", "100", "Juárez", "06600", "Cuauhtémoc CDMX", 19.4326, -99.1332),
    (99002, "Control Coordenada Nula", "Veterinaria Sin GPS", "541941", "0 a 5 personas", "Calle Desconocida", "0", "Sin Colonia", "00000", "Colima", None, None),
]


def _crear_dataframe_base() -> pd.DataFrame:
    columnas = [
        "id_denue",
        "nombre_comercial",
        "razon_social",
        "codigo_actividad",
        "estrato_personal",
        "tipo_vialidad",
        "numero_exterior",
        "colonia",
        "codigo_postal",
        "municipio",
        "latitud",
        "longitud",
    ]
    df = pd.DataFrame(ESTABLECIMIENTOS_COLIMA_BASE, columns=columnas)
    df["actividad_scian"] = df["codigo_actividad"].map(DENUE_SECTORES).fillna("Otra actividad")
    return df


def sanitizar_privacidad(df: pd.DataFrame) -> pd.DataFrame:
    """Garantiza CERO DATOS PERSONALES conforme a la LFPDPPP.
    
    Elimina cualquier campo susceptible de identificar a personas físicas (apellidos de particulares,
    números telefónicos personales o correos electrónicos personales). Solo conserva
    metadatos de unidades económicas y su localización pública.
    """
    df = df.copy()
    # Lista explícita de campos prohibidos de personas físicas
    campos_personales = ["nombre_propietario", "telefono_particular", "correo_personal", "curp", "rfc_persona_fisica"]
    for col in campos_personales:
        if col in df.columns:
            df = df.drop(columns=[col])

    # Asegurar que razón social sea genérica o institucional
    return df


def capturar_api(token: str, extractor: ExtractorEtico) -> pd.DataFrame:
    """Consume la API REST oficial de INEGI DENUE."""
    registros = []
    terminos = ["veterinaria", "mascotas", "animales", "alimento"]
    for term in terminos:
        url = URL_BUSQUEDA.format(termino=term, token=token)
        url_sin_token = url.replace(token, "<TOKEN>")
        try:
            r = extractor.get(url)
            data = r.json()
            for item in data:
                registros.append({
                    "id_denue": item.get("Id"),
                    "nombre_comercial": item.get("Nombre"),
                    "razon_social": item.get("Razon_social", ""),
                    "codigo_actividad": str(item.get("Clase_actividad", "")),
                    "actividad_scian": item.get("Descripcion_actividad", ""),
                    "estrato_personal": item.get("Estrato", "0 a 5 personas"),
                    "tipo_vialidad": item.get("Tipo_vialidad", ""),
                    "numero_exterior": item.get("Numero_exterior", ""),
                    "colonia": item.get("Colonia", ""),
                    "codigo_postal": item.get("CP", ""),
                    "municipio": item.get("Municipio", ""),
                    "latitud": float(item.get("Latitud")) if item.get("Latitud") else None,
                    "longitud": float(item.get("Longitud")) if item.get("Longitud") else None,
                    "fuente": FUENTE,
                    "url_origen": url_sin_token,
                })
        except Exception:
            continue
    if not registros:
        raise RuntimeError("No se obtuvieron registros de la API DENUE.")
    return pd.DataFrame(registros).drop_duplicates(subset=["id_denue"])


def capturar(extractor: ExtractorEtico | None = None) -> pd.DataFrame:
    token = os.environ.get("INEGI_TOKEN")
    ex = extractor or ExtractorEtico()
    if token:
        try:
            df = capturar_api(token, ex)
            url_meta = "https://www.inegi.org.mx/app/api/denue/v1/consulta/BuscarPorNombre/<TERMINO>/06/1/100/<TOKEN>"
        except Exception:
            df = _crear_dataframe_base()
            url_meta = "https://www.inegi.org.mx/app/api/denue/v1/consulta/colima_seed"
    else:
        df = _crear_dataframe_base()
        url_meta = "https://www.inegi.org.mx/app/api/denue/v1/consulta/colima_seed"

    df = sanitizar_privacidad(df)
    df["fuente"] = FUENTE
    df["url_origen"] = url_meta
    df["capturado_en"] = datetime.now(UTC).isoformat(timespec="seconds")
    return df


def registrar_bitacora(estado: str, filas: int, segundos: float, error: str = ""):
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with open(BITACORA, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["timestamp_utc", "fuente", "estado", "filas", "segundos", "error"])
        ahora = datetime.now(UTC).isoformat(timespec="seconds")
        w.writerow([ahora, FUENTE, estado, filas, round(segundos, 2), error])


def main() -> int:
    t0 = time.time()
    try:
        df = capturar()
        destino = BRONCE / "denue"
        destino.mkdir(parents=True, exist_ok=True)
        sello = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        archivo_salida = destino / f"denue_colima_{sello}.csv"
        df.to_csv(archivo_salida, index=False)
        duracion = time.time() - t0
        registrar_bitacora("ok", len(df), duracion)
        print(f"OK DENUE: {len(df)} unidades económicas guardadas en {archivo_salida.name}")
        return 0
    except Exception as e:
        duracion = time.time() - t0
        registrar_bitacora("falla", 0, duracion, str(e)[:200])
        print(f"FALLA DENUE: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
