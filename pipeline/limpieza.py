"""Bronce -> Plata con puerta de calidad. Lo rechazado va a cuarentena con su motivo.

Incluye soporte para series temporales (Banxico e INEGI BISE) y datos geoespaciales
especializados de unidades económicas (INEGI DENUE) utilizando GeoPandas.
Garantiza trazabilidad completa registrando el archivo de origen en capa bronce.
"""
import glob
from pathlib import Path
import re

import pandas as pd

try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False

try:
    import pandera.pandas as pa
    HAS_PANDERA = True
except ImportError:
    HAS_PANDERA = False

from pipeline.config import (
    BRONCE,
    CUARENTENA,
    DENUE_BBOX_COLIMA,
    DENUE_MUNICIPIOS,
    DENUE_SECTORES,
    PLATA,
    RANGOS,
)


def esquema(fuente: str):
    """Esquema Pandera para fuentes temporales si pandera está instalado."""
    if not HAS_PANDERA:
        return None
    lo, hi = RANGOS[fuente]
    return pa.DataFrameSchema(
        {
            "fecha": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$"), nullable=False),
            "serie": pa.Column(str, nullable=False),
            "valor": pa.Column(float, pa.Check.in_range(lo, hi), nullable=False),
        },
        coerce=True,
        strict=False,
    )


def cargar_bronce(subdir: str) -> pd.DataFrame:
    """Carga los CSVs crudos de bronce preservando el nombre del archivo de origen para linaje."""
    archivos = sorted(glob.glob(str(BRONCE / subdir / "*.csv")))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos en bronce/{subdir}")
    dfs = []
    for a in archivos:
        df_parte = pd.read_csv(a, dtype={"serie": str, "id_denue": str})
        df_parte["archivo_bronce_origen"] = Path(a).name
        dfs.append(df_parte)
    return pd.concat(dfs, ignore_index=True)


def validar(df: pd.DataFrame, fuente: str = "banxico") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (aprobados, rechazados). Cada rechazo lleva su motivo; nada se borra en silencio."""
    if fuente == "denue":
        return validar_denue(df)

    df = df.reset_index(drop=True)
    motivos: dict[int, list[str]] = {}

    if HAS_PANDERA:
        try:
            esquema(fuente).validate(df, lazy=True)
        except pa.errors.SchemaErrors as e:
            for _, fila in e.failure_cases.iterrows():
                idx = fila["index"]
                if pd.isna(idx):
                    continue
                motivos.setdefault(int(idx), []).append(f"{fila['column']}: {fila['check']}")
    else:
        # Validación equivalente si pandera no está en el entorno local
        lo, hi = RANGOS[fuente]
        fecha_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
        for i, row in df.iterrows():
            f = str(row.get("fecha", ""))
            if not f or not fecha_regex.match(f):
                motivos.setdefault(i, []).append("fecha: formato_YYYY-MM-DD")
            if pd.isna(row.get("serie")):
                motivos.setdefault(i, []).append("serie: no_nulo")
            v = row.get("valor")
            if pd.isna(v) or v is None:
                motivos.setdefault(i, []).append("valor: no_nulo")
            else:
                try:
                    vf = float(v)
                    if vf < lo or vf > hi:
                        motivos.setdefault(i, []).append(f"valor: in_range({lo}, {hi})")
                except (ValueError, TypeError):
                    motivos.setdefault(i, []).append("valor: tipo_float")

    malos = sorted(motivos)
    rechazados = df.loc[malos].copy()
    rechazados["motivo_rechazo"] = [" | ".join(motivos[i]) for i in malos]
    return df.drop(index=malos).copy(), rechazados


def validar_denue(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Puerta de calidad geoespacial para INEGI DENUE."""
    df = df.reset_index(drop=True)
    motivos: dict[int, list[str]] = {}

    bbox = DENUE_BBOX_COLIMA
    for i, row in df.iterrows():
        id_d = row.get("id_denue")
        if pd.isna(id_d) or str(id_d).strip() == "":
            motivos.setdefault(i, []).append("id_denue: obligatorio")

        nombre = row.get("nombre_comercial")
        if pd.isna(nombre) or str(nombre).strip() == "":
            motivos.setdefault(i, []).append("nombre_comercial: obligatorio")

        lat = row.get("latitud")
        lon = row.get("longitud")
        if pd.isna(lat) or pd.isna(lon):
            motivos.setdefault(i, []).append("coordenadas: latitud_o_longitud_nula")
        else:
            try:
                flat, flon = float(lat), float(lon)
                if not (bbox["lat_min"] <= flat <= bbox["lat_max"]):
                    motivos.setdefault(i, []).append(
                        f"latitud: fuera_de_rango_colima({bbox['lat_min']}, {bbox['lat_max']})"
                    )
                if not (bbox["lon_min"] <= flon <= bbox["lon_max"]):
                    motivos.setdefault(i, []).append(
                        f"longitud: fuera_de_rango_colima({bbox['lon_min']}, {bbox['lon_max']})"
                    )
            except (ValueError, TypeError):
                motivos.setdefault(i, []).append("coordenadas: tipo_invalido")

        muni = str(row.get("municipio", "")).strip()
        if muni not in DENUE_MUNICIPIOS:
            motivos.setdefault(i, []).append(f"municipio: no_pertenece_a_colima ({muni})")

        cod = str(row.get("codigo_actividad", "")).strip()
        if cod not in DENUE_SECTORES:
            motivos.setdefault(i, []).append(f"codigo_actividad: sector_no_monitoreado ({cod})")

    malos = sorted(motivos)
    rechazados = df.loc[malos].copy()
    rechazados["motivo_rechazo"] = [" | ".join(motivos[i]) for i in malos]
    aprobados = df.drop(index=malos).copy()
    return aprobados, rechazados


def marcar_atipicos_iqr(df: pd.DataFrame, col: str = "valor", k: float = 1.5) -> pd.DataFrame:
    """Marca (no elimina) atípicos por IQR: un salto puede ser el hallazgo."""
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    df = df.copy()
    df["atipico_iqr"] = (df[col] < q1 - k * iqr) | (df[col] > q3 + k * iqr)
    return df


def ejecutar(fuente: str = "banxico") -> dict:
    PLATA.mkdir(parents=True, exist_ok=True)
    CUARENTENA.mkdir(parents=True, exist_ok=True)

    crudo = cargar_bronce(fuente)
    n_crudo = len(crudo)

    if fuente == "denue":
        # Descartar duplicados de unidad económica conservando la captura más reciente
        if "capturado_en" in crudo.columns:
            crudo = crudo.sort_values("capturado_en").drop_duplicates(["id_denue"], keep="last")
        n_dups = n_crudo - len(crudo)
        ok, malos = validar_denue(crudo)

        # Generación de GeoDataFrame con GeoPandas (CRS EPSG:4326 - WGS84)
        if HAS_GEOPANDAS and not ok.empty:
            gdf = gpd.GeoDataFrame(
                ok,
                geometry=gpd.points_from_xy(ok["longitud"], ok["latitud"]),
                crs="EPSG:4326",
            )
            # Guardar GeoJSON para consumo GIS/cartográfico sin dependencia de GDAL nativo
            with open(PLATA / "denue_colima.geojson", "w", encoding="utf-8") as f:
                f.write(gdf.to_json())

        ok.to_csv(PLATA / "denue_colima.csv", index=False)
        malos.to_csv(CUARENTENA / "denue_rechazados.csv", index=False)

        resumen = {
            "fuente": fuente,
            "filas_bronce": n_crudo,
            "duplicados_descartados": n_dups,
            "filas_plata": len(ok),
            "filas_cuarentena": len(malos),
            "atipicos_marcados": 0,
        }
        print(resumen)
        return resumen

    # Fuentes temporales: Banxico e INEGI BISE
    crudo = crudo.sort_values("capturado_en").drop_duplicates(["serie", "fecha"], keep="last")
    n_dups = n_crudo - len(crudo)

    ok, malos = validar(crudo, fuente)
    ok = marcar_atipicos_iqr(ok.sort_values("fecha"))

    ok.to_csv(
        PLATA / f"{fuente}_diario.csv" if fuente == "banxico" else PLATA / f"{fuente}_mensual.csv",
        index=False,
    )
    malos.to_csv(CUARENTENA / f"{fuente}_rechazados.csv", index=False)
    resumen = {
        "fuente": fuente,
        "filas_bronce": n_crudo,
        "duplicados_descartados": n_dups,
        "filas_plata": len(ok),
        "filas_cuarentena": len(malos),
        "atipicos_marcados": int(ok["atipico_iqr"].sum()),
    }
    print(resumen)
    return resumen


if __name__ == "__main__":
    ejecutar()
