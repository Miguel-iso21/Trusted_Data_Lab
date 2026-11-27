"""Pruebas del experimento E2: matrices de diseno, alias y clasificacion correcta de la puerta."""
import numpy as np
import pandas as pd
import pytest

from laboratorio import experimento as ex


def test_matriz_2k3_completa_y_balanceada():
    m = ex.matriz_completa(3)
    assert len(m) == 8 and len(m.drop_duplicates()) == 8
    assert (m.sum() == 0).all()  # cada factor tiene 4 corridas en -1 y 4 en +1


def test_matriz_2k4_completo_tiene_16_corridas_unicas():
    m = ex.matriz_completa(4)
    assert len(m) == 16 and len(m.drop_duplicates()) == 16


def test_fraccion_2k4_1_usa_generador_d_igual_abc():
    m = ex.matriz_2_4_1()
    assert len(m) == 8
    assert (m["D"] == m["A"] * m["B"] * m["C"]).all()
    # es la mitad del 2^4 completo donde ABCD = +1
    completo = ex.matriz_completa(4)
    mitad = completo[completo.prod(axis=1) == 1]
    assert set(map(tuple, m.to_numpy())) == set(map(tuple, mitad.to_numpy()))


def test_alias_resolucion_iv():
    alias = ex.alias_2_4_1().set_index("efecto")["alias"].to_dict()
    assert alias["A"] == "BCD" and alias["D"] == "ABC"
    assert alias["AB"] == "CD" and alias["AC"] == "BD" and alias["AD"] == "BC"
    assert len(alias) == 7  # 14 efectos agrupados en 7 pares


def _base_chica():
    fechas = pd.bdate_range("2024-01-01", periods=200).strftime("%Y-%m-%d")
    return pd.DataFrame({"fecha": fechas, "serie": "SF43718", "valor": 17.0})


def test_preparar_inyecta_dos_por_ciento_de_invalidos():
    df, es_malo = ex.preparar(_base_chica(), 5, np.random.default_rng(0))
    assert len(df) == 1000 and es_malo.sum() == 20


@pytest.mark.parametrize("formato", ["csv", "parquet"])
@pytest.mark.parametrize("motor", ["fila_por_fila", "pandera"])
def test_puerta_clasifica_sin_errores_en_cada_configuracion(formato, motor, tmp_path):
    df, es_malo = ex.preparar(_base_chica(), 2, np.random.default_rng(1))
    r = ex.correr(df, es_malo, formato, motor, tmp_path)
    assert r["mal_clasificados"] == 0 and r["segundos"] > 0
