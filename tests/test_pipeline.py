"""Pruebas de la puerta de calidad, el parser y la capa oro. Los datos son fixtures de prueba."""
from datetime import date

import pandas as pd

from extractores.banxico import parsear
from pipeline.limpieza import marcar_atipicos_iqr, validar
from pipeline.oro import a_mensual


def _fila(fecha, valor=18.0):
    return {"fecha": fecha, "serie": "SF43718", "valor": valor}


def test_parser_banxico_convierte_fechas_y_ne():
    payload = {
        "bmx": {
            "series": [
                {
                    "idSerie": "SF43718",
                    "datos": [
                        {"fecha": "02/01/2024", "dato": "16.9"},
                        {"fecha": "03/01/2024", "dato": "N/E"},
                    ],
                }
            ]
        }
    }
    df = parsear(payload, "http://x")
    assert df.loc[0, "fecha"] == "2024-01-02" and df.loc[0, "valor"] == 16.9
    assert pd.isna(df.loc[1, "valor"])


def test_puerta_aprueba_registro_valido():
    ok, malos = validar(pd.DataFrame([_fila("2024-01-02")]))
    assert len(ok) == 1 and malos.empty


def test_puerta_manda_a_cuarentena_con_motivo():
    df = pd.DataFrame(
        [
            _fila("2024-01-02"),
            _fila("2024-01-03", valor=180.0),  # fuera de rango
            _fila("2024-01-04", valor=None),  # faltante
            _fila("04/01/2024"),  # formato de fecha invalido
        ]
    )
    ok, malos = validar(df)
    assert len(ok) == 1 and len(malos) == 3
    assert malos["motivo_rechazo"].str.len().gt(0).all()


def test_atipicos_se_marcan_no_se_borran():
    df = pd.DataFrame([_fila(f"2024-01-{d:02d}", valor=17 + d % 3 * 0.1) for d in range(1, 29)])
    df.loc[0, "valor"] = 30.0
    out = marcar_atipicos_iqr(df)
    assert len(out) == len(df) and out.loc[0, "atipico_iqr"]


def test_oro_mensual_excluye_mes_en_curso():
    dias = pd.bdate_range("2024-01-01", "2024-04-10")
    df = pd.DataFrame([_fila(d.strftime("%Y-%m-%d"), 17 + i * 0.01) for i, d in enumerate(dias)])
    m = a_mensual(df, hoy=date(2024, 4, 10))
    assert list(m["mes"].dt.strftime("%Y-%m")) == ["2024-01", "2024-02", "2024-03"]
