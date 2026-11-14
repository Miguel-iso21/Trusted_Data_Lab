"""Plata -> Oro: series mensuales listas para analisis, con diccionario de datos."""
from datetime import date

import pandas as pd

from pipeline.config import ORO, PLATA

DICCIONARIO = [
    ("tabla", "columna", "tipo", "descripcion", "origen"),
    ("usd_mxn_mensual", "mes", "fecha", "Primer dia del mes (YYYY-MM-01)", "Banxico SIE, agregado"),
    ("usd_mxn_mensual", "usd_media", "float MXN", "Promedio mensual del tipo de cambio FIX", "SF43718"),
    ("usd_mxn_mensual", "usd_cierre", "float MXN", "Ultimo valor del mes", "SF43718"),
    ("usd_mxn_mensual", "n_obs", "int", "Dias habiles con dato en el mes", "calculado"),
    ("usd_mxn_mensual", "var_pct", "float %", "Variacion % de usd_media contra el mes anterior", "calculado"),
    ("usd_mxn_mensual", "usd_z", "float", "z-score de usd_media (estandarizacion)", "calculado"),
    ("usd_mxn_mensual", "usd_minmax", "float 0-1", "min-max de usd_media (normalizacion)", "calculado"),
    ("usd_mxn_mensual", "nivel", "texto", "Discretizacion por terciles: bajo/medio/alto", "calculado"),
    ("vet_ingresos_mensual", "mes", "fecha", "Primer dia del mes (YYYY-MM-01)", "INEGI EMS"),
    (
        "vet_ingresos_mensual",
        "indice_ingresos",
        "float",
        "Ingresos totales, servicios veterinarios para mascotas (541941), sector privado, "
        "indice base 2018=100. Estimacion de encuesta (con error muestral)",
        "INEGI BISE 716898",
    ),
    ("vet_ingresos_mensual", "ingresos_z", "float", "z-score de indice_ingresos", "calculado"),
    ("vet_ingresos_mensual", "ingresos_minmax", "float 0-1", "min-max de indice_ingresos", "calculado"),
    ("vet_ingresos_mensual", "nivel", "texto", "Discretizacion por terciles: bajo/medio/alto", "calculado"),
]


def _normalizar(m: pd.DataFrame, col: str, prefijo: str) -> pd.DataFrame:
    m[f"{prefijo}_z"] = (m[col] - m[col].mean()) / m[col].std()
    m[f"{prefijo}_minmax"] = (m[col] - m[col].min()) / (m[col].max() - m[col].min())
    # Terciles por frecuencia; rank evita bordes repetidos cuando hay valores empatados.
    m["nivel"] = pd.qcut(m[col].rank(method="first"), 3, labels=["bajo", "medio", "alto"]).astype(str)
    return m


def a_mensual(diario: pd.DataFrame, hoy: date | None = None) -> pd.DataFrame:
    """Dolar diario -> mensual (el mes en curso esta incompleto y no entra)."""
    d = diario.copy()
    d["fecha"] = pd.to_datetime(d["fecha"])
    g = d.groupby(d["fecha"].dt.to_period("M"))["valor"]
    m = pd.DataFrame({"usd_media": g.mean(), "usd_cierre": g.last(), "n_obs": g.count()})
    m = m[m.index < pd.Period(hoy or date.today(), "M")]
    m["var_pct"] = m["usd_media"].pct_change() * 100
    m = _normalizar(m, "usd_media", "usd")
    m.index = m.index.to_timestamp()
    m.index.name = "mes"
    return m.reset_index()


def ingresos_mensual(plata: pd.DataFrame) -> pd.DataFrame:
    m = plata[["fecha", "valor"]].rename(columns={"fecha": "mes", "valor": "indice_ingresos"}).copy()
    m["mes"] = pd.to_datetime(m["mes"])
    m = m.sort_values("mes").reset_index(drop=True)
    return _normalizar(m, "indice_ingresos", "ingresos")


def ejecutar() -> dict:
    ORO.mkdir(parents=True, exist_ok=True)
    usd = a_mensual(pd.read_csv(PLATA / "banxico_diario.csv"))
    vet = ingresos_mensual(pd.read_csv(PLATA / "inegi_mensual.csv"))
    usd.to_csv(ORO / "usd_mxn_mensual.csv", index=False)
    vet.to_csv(ORO / "vet_ingresos_mensual.csv", index=False)
    pd.DataFrame(DICCIONARIO[1:], columns=DICCIONARIO[0]).to_csv(ORO / "diccionario_oro.csv", index=False)
    print(f"Oro dolar: {len(usd)} meses | Oro ingresos veterinarios: {len(vet)} meses "
          f"({vet['mes'].min():%Y-%m} a {vet['mes'].max():%Y-%m})")
    return {"usd": len(usd), "vet": len(vet)}


if __name__ == "__main__":
    ejecutar()
