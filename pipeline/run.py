"""Corre bronce -> plata -> oro para todas las fuentes. Falla (exit 1) si la puerta rechaza demasiado."""
import sys

from pipeline import limpieza, oro
from pipeline.config import BRONCE

MAX_RECHAZO = 0.05  # objetivo de calidad: <= 5% de registros en cuarentena

if __name__ == "__main__":
    peor = 0.0
    fuentes = ["banxico", "inegi"]
    if (BRONCE / "denue").exists():
        fuentes.append("denue")

    for fuente in fuentes:
        r = limpieza.ejecutar(fuente)
        tasa = r["filas_cuarentena"] / max(r["filas_plata"] + r["filas_cuarentena"], 1)
        print(f"[{fuente}] tasa de rechazo: {tasa:.2%}")
        peor = max(peor, tasa)

    oro.ejecutar()
    sys.exit(0 if peor <= MAX_RECHAZO else 1)
