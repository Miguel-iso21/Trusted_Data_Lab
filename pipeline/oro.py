"""Plata -> Oro: series y datos geoespaciales listos para análisis, con linaje completo y diccionario.

Cada registro en la Capa Oro conserva trazabilidad completa hacia su archivo de origen
en Capa Bronce y su marca de tiempo de ingesta original.
"""

from datetime import date

import pandas as pd

try:
    import geopandas as gpd

    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

from pipeline.config import ORO, PLATA

DICCIONARIO = [
    ("tabla", "columna", "tipo", "descripcion", "origen"),
    # usd_mxn_mensual
    ("usd_mxn_mensual", "mes", "fecha", "Primer día del mes (YYYY-MM-01)", "Banxico SIE, agregado"),
    ("usd_mxn_mensual", "usd_media", "float MXN", "Promedio mensual del tipo de cambio FIX", "SF43718"),
    ("usd_mxn_mensual", "usd_cierre", "float MXN", "Último valor del mes", "SF43718"),
    ("usd_mxn_mensual", "n_obs", "int", "Días hábiles con dato en el mes", "calculado"),
    ("usd_mxn_mensual", "var_pct", "float %", "Variación % de usd_media contra el mes anterior", "calculado"),
    ("usd_mxn_mensual", "usd_z", "float", "z-score de usd_media (estandarización)", "calculado"),
    ("usd_mxn_mensual", "usd_minmax", "float 0-1", "min-max de usd_media (normalización)", "calculado"),
    ("usd_mxn_mensual", "nivel", "texto", "Discretización por terciles: bajo/medio/alto", "calculado"),
    (
        "usd_mxn_mensual",
        "archivo_bronce_origen",
        "texto",
        "Archivo CSV crudo en data/bronce/banxico/",
        "trazabilidad linaje",
    ),
    (
        "usd_mxn_mensual",
        "fecha_ingesta",
        "timestamp ISO",
        "Fecha y hora UTC de la captura en capa bronce",
        "trazabilidad linaje",
    ),
    (
        "usd_mxn_mensual",
        "fuente_origen",
        "texto",
        "Identificador del proveedor oficial (banxico-sie)",
        "trazabilidad linaje",
    ),
    # vet_ingresos_mensual
    ("vet_ingresos_mensual", "mes", "fecha", "Primer día del mes (YYYY-MM-01)", "INEGI EMS"),
    (
        "vet_ingresos_mensual",
        "indice_ingresos",
        "float",
        "Ingresos totales, servicios veterinarios para mascotas (541941), sector privado, "
        "índice base 2018=100. Estimación de encuesta (con error muestral)",
        "INEGI BISE 716898",
    ),
    ("vet_ingresos_mensual", "ingresos_z", "float", "z-score de indice_ingresos", "calculado"),
    ("vet_ingresos_mensual", "ingresos_minmax", "float 0-1", "min-max de indice_ingresos", "calculado"),
    ("vet_ingresos_mensual", "nivel", "texto", "Discretización por terciles: bajo/medio/alto", "calculado"),
    (
        "vet_ingresos_mensual",
        "archivo_bronce_origen",
        "texto",
        "Archivo CSV crudo en data/bronce/inegi/",
        "trazabilidad linaje",
    ),
    (
        "vet_ingresos_mensual",
        "fecha_ingesta",
        "timestamp ISO",
        "Fecha y hora UTC de la captura en capa bronce",
        "trazabilidad linaje",
    ),
    (
        "vet_ingresos_mensual",
        "fuente_origen",
        "texto",
        "Identificador del proveedor oficial (inegi-bise)",
        "trazabilidad linaje",
    ),
    # denue_colima_geo
    (
        "denue_colima_geo",
        "id_denue",
        "int/texto",
        "Identificador único de unidad económica en DENUE",
        "INEGI DENUE",
    ),
    (
        "denue_colima_geo",
        "nombre_comercial",
        "texto",
        "Nombre público o comercial del establecimiento",
        "INEGI DENUE",
    ),
    ("denue_colima_geo", "clee", "texto", "Clave Estadística Empresarial del establecimiento", "INEGI DENUE"),
    (
        "denue_colima_geo",
        "actividad_scian",
        "texto",
        "Descripción de la clase de actividad SCIAN",
        "INEGI DENUE",
    ),
    ("denue_colima_geo", "ageb", "texto", "Área geoestadística básica donde se ubica", "INEGI DENUE"),
    ("denue_colima_geo", "manzana", "texto", "Manzana dentro del AGEB", "INEGI DENUE"),
    (
        "denue_colima_geo",
        "fecha_alta",
        "texto",
        "Fecha de alta del establecimiento en el DENUE",
        "INEGI DENUE",
    ),
    ("denue_colima_geo", "codigo_actividad", "texto", "Código de 6 dígitos del SCIAN", "INEGI DENUE"),
    (
        "denue_colima_geo",
        "categoria_servicio",
        "texto",
        "Categoría estandarizada en el observatorio",
        "calculado",
    ),
    (
        "denue_colima_geo",
        "estrato_personal",
        "texto",
        "Rango de personas ocupadas (0 a 5, 6 a 10, etc.)",
        "INEGI DENUE",
    ),
    ("denue_colima_geo", "municipio", "texto", "Municipio del Estado de Colima", "INEGI DENUE"),
    (
        "denue_colima_geo",
        "zona_urbana",
        "texto",
        "Agrupación geográfica funcional del estado",
        "calculado espacial",
    ),
    ("denue_colima_geo", "latitud", "float", "Latitud en grados decimales (WGS84)", "INEGI DENUE"),
    ("denue_colima_geo", "longitud", "float", "Longitud en grados decimales (WGS84)", "INEGI DENUE"),
    (
        "denue_colima_geo",
        "archivo_bronce_origen",
        "texto",
        "Archivo CSV crudo en data/bronce/denue/",
        "trazabilidad linaje",
    ),
    (
        "denue_colima_geo",
        "fecha_ingesta",
        "timestamp ISO",
        "Fecha y hora UTC de captura en capa bronce",
        "trazabilidad linaje",
    ),
    (
        "denue_colima_geo",
        "fuente_origen",
        "texto",
        "Identificador del proveedor oficial (inegi-denue)",
        "trazabilidad linaje",
    ),
    # denue_resumen_municipal
    ("denue_resumen_municipal", "municipio", "texto", "Nombre del municipio de Colima", "INEGI DENUE"),
    ("denue_resumen_municipal", "zona_urbana", "texto", "Región funcional del estado", "calculado"),
    (
        "denue_resumen_municipal",
        "total_establecimientos",
        "int",
        "Conteo total de establecimientos del sector animal",
        "calculado",
    ),
    (
        "denue_resumen_municipal",
        "total_veterinarias",
        "int",
        "Conteo de clínicas y consultorios veterinarios (541941)",
        "calculado",
    ),
    (
        "denue_resumen_municipal",
        "total_pet_shops",
        "int",
        "Conteo de tiendas de mascotas y alimentos (461121)",
        "calculado",
    ),
    (
        "denue_resumen_municipal",
        "total_esteticas",
        "int",
        "Conteo de estéticas, hoteles y cuidado de mascotas (812990 filtrado)",
        "calculado",
    ),
    (
        "denue_resumen_municipal",
        "pct_micro_0_a_5",
        "float %",
        "Porcentaje de microestablecimientos de 0 a 5 personas",
        "calculado",
    ),
    ("denue_resumen_municipal", "fuente_origen", "texto", "Fuente de datos oficial", "trazabilidad linaje"),
    (
        "denue_resumen_municipal",
        "fecha_actualizacion",
        "fecha",
        "Fecha de generación del resumen (YYYY-MM-DD)",
        "calculado",
    ),
]


def _normalizar(m: pd.DataFrame, col: str, prefijo: str) -> pd.DataFrame:
    m[f"{prefijo}_z"] = (m[col] - m[col].mean()) / m[col].std()
    m[f"{prefijo}_minmax"] = (m[col] - m[col].min()) / (m[col].max() - m[col].min())
    m["nivel"] = pd.qcut(m[col].rank(method="first"), 3, labels=["bajo", "medio", "alto"]).astype(str)
    return m


def a_mensual(diario: pd.DataFrame, hoy: date | None = None) -> pd.DataFrame:
    """Dólar diario -> mensual agregando con trazabilidad hacia capa bronce."""
    d = diario.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    g = d.groupby(d["fecha"].dt.to_period("M"))

    archivo_orig = (
        g["archivo_bronce_origen"].last() if "archivo_bronce_origen" in d.columns else "desconocido"
    )
    ingesta_orig = g["capturado_en"].last() if "capturado_en" in d.columns else "desconocido"

    m = pd.DataFrame(
        {
            "usd_media": g["valor"].mean(),
            "usd_cierre": g["valor"].last(),
            "n_obs": g["valor"].count(),
            "archivo_bronce_origen": archivo_orig,
            "fecha_ingesta": ingesta_orig,
            "fuente_origen": "banxico-sie",
        }
    )
    m = m[m.index < pd.Period(hoy or date.today(), "M")]
    m["var_pct"] = m["usd_media"].pct_change() * 100
    m = _normalizar(m, "usd_media", "usd")
    m.index = m.index.to_timestamp()
    m.index.name = "mes"
    return m.reset_index()


def ingresos_mensual(plata: pd.DataFrame) -> pd.DataFrame:
    """Ingresos mensuales de servicios veterinarios con trazabilidad a capa bronce."""
    cols = ["fecha", "valor"]
    for c in ["archivo_bronce_origen", "capturado_en", "fuente"]:
        if c in plata.columns:
            cols.append(c)

    m = plata[cols].rename(columns={"fecha": "mes", "valor": "indice_ingresos"}).copy()
    if "capturado_en" in m.columns:
        m = m.rename(columns={"capturado_en": "fecha_ingesta"})
    else:
        m["fecha_ingesta"] = "desconocido"

    if "archivo_bronce_origen" not in m.columns:
        m["archivo_bronce_origen"] = "desconocido"

    if "fuente" in m.columns:
        m = m.rename(columns={"fuente": "fuente_origen"})
    else:
        m["fuente_origen"] = "inegi-bise"

    m["mes"] = pd.to_datetime(m["mes"])
    m = m.sort_values("mes").reset_index(drop=True)
    return _normalizar(m, "indice_ingresos", "ingresos")


def procesar_denue_oro(plata: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Genera la capa oro geoespacial de DENUE y la agregación municipal con linaje."""
    df = plata.copy()

    zonas = {
        "Colima": "Metropolitana Colima-Villa de Álvarez",
        "Villa de Álvarez": "Metropolitana Colima-Villa de Álvarez",
        "Manzanillo": "Costera Manzanillo",
        "Tecomán": "Valle Tecomán-Armería",
        "Armería": "Valle Tecomán-Armería",
        "Comala": "Norte y Periférica",
        "Coquimatlán": "Norte y Periférica",
        "Cuauhtémoc": "Norte y Periférica",
        "Ixtlahuacán": "Norte y Periférica",
        "Minatitlán": "Norte y Periférica",
    }
    df["zona_urbana"] = df["municipio"].map(zonas).fillna("Otras Regiones")

    cat_map = {
        "541941": "Clínica Veterinaria para Mascotas",
        "541942": "Servicios Veterinarios Pecuarios",
        "461121": "Tienda de Alimentos y Accesorios (Pet Shop)",
        "812990": "Estética, Hotel y Cuidado de Mascotas",
    }
    df["categoria_servicio"] = df["codigo_actividad"].astype(str).map(cat_map).fillna("Otro Servicio Animal")

    if "archivo_bronce_origen" not in df.columns:
        df["archivo_bronce_origen"] = "desconocido"

    if "capturado_en" in df.columns:
        df["fecha_ingesta"] = df["capturado_en"]
    elif "fecha_ingesta" not in df.columns:
        df["fecha_ingesta"] = "desconocido"

    df["fuente_origen"] = "inegi-denue"

    # Resumen municipal
    resumen = (
        df.groupby(["municipio", "zona_urbana"])
        .agg(
            total_establecimientos=("id_denue", "count"),
            total_veterinarias=("codigo_actividad", lambda s: (s.astype(str) == "541941").sum()),
            total_pet_shops=("codigo_actividad", lambda s: (s.astype(str) == "461121").sum()),
            total_esteticas=("codigo_actividad", lambda s: (s.astype(str) == "812990").sum()),
            pct_micro_0_a_5=("estrato_personal", lambda s: round(100 * (s == "0 a 5 personas").mean(), 1)),
        )
        .reset_index()
    )
    resumen["fuente_origen"] = "inegi-denue"
    resumen["fecha_actualizacion"] = date.today().isoformat()

    return df, resumen


def ejecutar() -> dict:
    ORO.mkdir(parents=True, exist_ok=True)
    usd = a_mensual(pd.read_csv(PLATA / "banxico_diario.csv"))
    vet = ingresos_mensual(pd.read_csv(PLATA / "inegi_mensual.csv"))

    usd.to_csv(ORO / "usd_mxn_mensual.csv", index=False)
    vet.to_csv(ORO / "vet_ingresos_mensual.csv", index=False)

    resultados = {"usd": len(usd), "vet": len(vet)}

    denue_plata = PLATA / "denue_colima.csv"
    if denue_plata.exists():
        df_geo, df_resumen = procesar_denue_oro(pd.read_csv(denue_plata))
        df_geo.to_csv(ORO / "denue_colima_geo.csv", index=False)
        df_resumen.to_csv(ORO / "denue_resumen_municipal.csv", index=False)
        if HAS_GEOPANDAS and not df_geo.empty:
            gdf = gpd.GeoDataFrame(
                df_geo,
                geometry=gpd.points_from_xy(df_geo["longitud"], df_geo["latitud"]),
                crs="EPSG:4326",
            )
            with open(ORO / "denue_colima_geo.geojson", "w", encoding="utf-8") as f:
                f.write(gdf.to_json())
        resultados["denue"] = len(df_geo)
        print(f"Oro DENUE Geo: {len(df_geo)} establecimientos | {len(df_resumen)} municipios agregados")

    pd.DataFrame(DICCIONARIO[1:], columns=DICCIONARIO[0]).to_csv(ORO / "diccionario_oro.csv", index=False)
    print(
        f"Oro dolar: {len(usd)} meses | Oro ingresos veterinarios: {len(vet)} meses "
        f"({vet['mes'].min():%Y-%m} a {vet['mes'].max():%Y-%m})"
    )
    return resultados


if __name__ == "__main__":
    ejecutar()
