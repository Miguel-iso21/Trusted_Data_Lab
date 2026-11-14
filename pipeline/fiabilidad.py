"""Fiabilidad y disponibilidad de la captura, medidas con la bitacora real.

Por fuente:
  - tasa de exito = ejecuciones ok / ejecuciones totales
  - MTTR = promedio del tiempo entre una falla y la siguiente ejecucion ok de esa fuente
  - MTBF = tiempo operando (periodo observado - tiempo caido) / numero de fallas
  - A = MTBF / (MTBF + MTTR)
Si no hay fallas, MTBF no esta definido (se reporta el periodo observado como cota inferior) y A = 1.

Uso: python -m pipeline.fiabilidad   -> imprime la tabla y la guarda en calidad/fiabilidad.csv
"""
import pandas as pd

from pipeline.config import BITACORA, RAIZ

SALIDA = RAIZ / "calidad" / "fiabilidad.csv"


def medir(bitacora: pd.DataFrame) -> pd.DataFrame:
    b = bitacora.copy()
    b["t"] = pd.to_datetime(b["timestamp_utc"], utc=True)
    filas = []
    for fuente, g in b.sort_values("t").groupby("fuente"):
        n = len(g)
        fallas = int((g["estado"] != "ok").sum())
        reparaciones = []
        caida_desde = None
        for t, estado in zip(g["t"], g["estado"], strict=True):
            if estado != "ok" and caida_desde is None:
                caida_desde = t
            elif estado == "ok" and caida_desde is not None:
                reparaciones.append((t - caida_desde).total_seconds() / 3600)
                caida_desde = None
        periodo_h = (g["t"].max() - g["t"].min()).total_seconds() / 3600
        caido_h = sum(reparaciones)
        if caida_desde is not None:  # sigue caida al final de la bitacora
            caido_h += (g["t"].max() - caida_desde).total_seconds() / 3600
        mttr = sum(reparaciones) / len(reparaciones) if reparaciones else None
        mtbf = (periodo_h - caido_h) / fallas if fallas else None
        if fallas == 0:
            disp = 1.0
        elif mtbf is not None and mttr is not None and mtbf + mttr > 0:
            disp = mtbf / (mtbf + mttr)
        else:
            disp = None
        filas.append({
            "fuente": fuente,
            "desde_utc": g["t"].min().isoformat(),
            "hasta_utc": g["t"].max().isoformat(),
            "dias_observados": round(periodo_h / 24, 2),
            "ejecuciones": n,
            "fallas": fallas,
            "tasa_exito": round((n - fallas) / n, 4),
            "mttr_horas": None if mttr is None else round(mttr, 4),
            "mtbf_horas": None if mtbf is None else round(mtbf, 4),
            "disponibilidad": None if disp is None else round(disp, 4),
        })
    return pd.DataFrame(filas)


if __name__ == "__main__":
    tabla = medir(pd.read_csv(BITACORA))
    tabla.to_csv(SALIDA, index=False)
    print(tabla.to_string(index=False))
