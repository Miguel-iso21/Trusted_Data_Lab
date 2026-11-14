"""Pruebas del calculo de MTBF, MTTR y disponibilidad con bitacoras sinteticas."""
import pandas as pd

from pipeline.fiabilidad import medir


def _bitacora(eventos):
    return pd.DataFrame(
        [{"timestamp_utc": t, "fuente": f, "estado": e} for t, f, e in eventos]
    )


def test_una_falla_reparada():
    # 4 dias diarios, una falla el dia 2 reparada 2 h despues
    b = _bitacora([
        ("2026-11-01T14:00:00+00:00", "x", "ok"),
        ("2026-11-02T14:00:00+00:00", "x", "falla"),
        ("2026-11-02T16:00:00+00:00", "x", "ok"),
        ("2026-11-04T14:00:00+00:00", "x", "ok"),
    ])
    r = medir(b).iloc[0]
    assert r["fallas"] == 1 and r["tasa_exito"] == 0.75
    assert r["mttr_horas"] == 2.0
    assert r["mtbf_horas"] == 70.0  # 72 h observadas - 2 h caida
    assert abs(r["disponibilidad"] - 70 / 72) < 1e-4


def test_sin_fallas_disponibilidad_total():
    b = _bitacora([
        ("2026-11-01T14:00:00+00:00", "x", "ok"),
        ("2026-11-02T14:00:00+00:00", "x", "ok"),
    ])
    r = medir(b).iloc[0]
    assert r["fallas"] == 0 and r["disponibilidad"] == 1.0
    assert pd.isna(r["mtbf_horas"]) and pd.isna(r["mttr_horas"])


def test_separa_por_fuente():
    b = _bitacora([
        ("2026-11-01T14:00:00+00:00", "a", "ok"),
        ("2026-11-01T14:00:00+00:00", "b", "falla"),
    ])
    assert sorted(medir(b)["fuente"]) == ["a", "b"]
