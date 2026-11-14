"""Prueba de punta a punta del pipeline (bronce -> plata -> oro) en carpetas temporales."""
import pandas as pd

from pipeline import limpieza, oro


def test_pipeline_completo_con_cuarentena(monkeypatch, tmp_path):
    for mod in (limpieza, oro):
        for nombre in ("BRONCE", "PLATA", "CUARENTENA", "ORO"):
            if hasattr(mod, nombre):
                monkeypatch.setattr(mod, nombre, tmp_path / nombre.lower())

    (tmp_path / "bronce" / "banxico").mkdir(parents=True)
    (tmp_path / "bronce" / "inegi").mkdir(parents=True)
    dias = pd.bdate_range("2023-01-02", "2023-06-30")
    usd = pd.DataFrame({"fecha": dias.strftime("%Y-%m-%d"), "serie": "SF43718", "valor": 17.0,
                        "capturado_en": "2024-01-01T00:00:00"})
    usd.loc[3, "valor"] = 999.0  # debe ir a cuarentena
    usd.to_csv(tmp_path / "bronce" / "banxico" / "a.csv", index=False)
    meses = pd.date_range("2020-01-01", periods=40, freq="MS")
    vet = pd.DataFrame({"fecha": meses.strftime("%Y-%m-%d"), "serie": "716898",
                        "valor": range(80, 120), "capturado_en": "2024-01-01T00:00:00"})
    vet.to_csv(tmp_path / "bronce" / "inegi" / "a.csv", index=False)

    r_usd = limpieza.ejecutar("banxico")
    r_vet = limpieza.ejecutar("inegi")
    assert r_usd["filas_cuarentena"] == 1 and r_vet["filas_cuarentena"] == 0
    rechazo = pd.read_csv(tmp_path / "cuarentena" / "banxico_rechazados.csv")
    assert "valor" in rechazo.loc[0, "motivo_rechazo"]

    res = oro.ejecutar()
    assert res == {"usd": 6, "vet": 40}
    assert (tmp_path / "oro" / "diccionario_oro.csv").exists()
