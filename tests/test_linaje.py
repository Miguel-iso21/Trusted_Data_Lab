"""Pruebas de linaje y trazabilidad completa de registros de Capa Oro a Capa Bronce."""

import pandas as pd

from pipeline.config import ORO


def test_linaje_todas_las_tablas_oro_tienen_metadatos_de_origen():
    """Cada registro de la capa oro es rastreable hasta su archivo de bronce y su fecha de ingesta."""
    tablas = [
        (
            "usd_mxn_mensual.csv",
            ["mes", "usd_media", "archivo_bronce_origen", "fecha_ingesta", "fuente_origen"],
        ),
        (
            "vet_ingresos_mensual.csv",
            ["mes", "indice_ingresos", "archivo_bronce_origen", "fecha_ingesta", "fuente_origen"],
        ),
    ]
    if (ORO / "denue_colima_geo.csv").exists():
        tablas.append(
            (
                "denue_colima_geo.csv",
                ["id_denue", "nombre_comercial", "archivo_bronce_origen", "fecha_ingesta", "fuente_origen"],
            )
        )

    for nombre_archivo, columnas_esperadas in tablas:
        ruta = ORO / nombre_archivo
        assert ruta.exists(), f"Falta el archivo {nombre_archivo} en capa oro"
        df = pd.read_csv(ruta)
        assert not df.empty, f"El archivo {nombre_archivo} está vacío"
        faltan = set(columnas_esperadas) - set(df.columns)
        assert not faltan, f"Faltan columnas {sorted(faltan)} en {nombre_archivo}"

        for col in ["archivo_bronce_origen", "fecha_ingesta", "fuente_origen"]:
            assert col in df.columns, f"Falta columna de linaje '{col}' en {nombre_archivo}"
            assert df[col].notna().all(), (
                f"Hay valores nulos en la columna de linaje '{col}' de {nombre_archivo}"
            )
            assert (df[col].astype(str).str.strip() != "").all(), (
                f"Hay cadenas vacías en '{col}' de {nombre_archivo}"
            )


def test_diccionario_oro_incluye_columnas_de_linaje():
    """El diccionario de datos debe documentar las columnas de trazabilidad."""
    ruta_dic = ORO / "diccionario_oro.csv"
    assert ruta_dic.exists()
    dic = pd.read_csv(ruta_dic)
    columnas_doc = set(dic["columna"].unique())
    assert "archivo_bronce_origen" in columnas_doc
    assert "fecha_ingesta" in columnas_doc
    assert "fuente_origen" in columnas_doc
