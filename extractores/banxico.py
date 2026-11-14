"""Fuente 1: Banxico SIE, tipo de cambio FIX (MXN por USD). Requiere token gratuito.

El token se lee de la variable de entorno BANXICO_TOKEN (nunca va en el repo).
Uso:
    python -m extractores.banxico historico   # una vez: 2020-01-01 -> hoy
    python -m extractores.banxico reciente    # diario (GitHub Actions): ultimos 15 dias
Cada ejecucion queda registrada en calidad/bitacora_capturas.csv.
"""
import csv
import os
import sys
import time
from datetime import UTC, date, datetime, timedelta

import pandas as pd

from extractores.base import ExtractorEtico
from pipeline.config import BANXICO_SERIE_USD, BITACORA, BRONCE

FUENTE = "banxico-sie"
URL = "https://www.banxico.org.mx/SieAPIRest/service/v1/series/{serie}/datos/{ini}/{fin}"


def parsear(payload: dict, url: str) -> pd.DataFrame:
    serie = payload["bmx"]["series"][0]
    filas = []
    for d in serie.get("datos", []):
        valor = d["dato"].replace(",", "")
        filas.append(
            {
                "fecha": datetime.strptime(d["fecha"], "%d/%m/%Y").strftime("%Y-%m-%d"),
                "serie": serie["idSerie"],
                "valor": float(valor) if valor not in ("N/E", "") else None,
            }
        )
    df = pd.DataFrame(filas, columns=["fecha", "serie", "valor"])
    df["fuente"] = FUENTE
    df["url_origen"] = url
    df["capturado_en"] = datetime.now(UTC).isoformat(timespec="seconds")
    return df


def capturar(modo: str, extractor: ExtractorEtico | None = None) -> pd.DataFrame:
    token = os.environ.get("BANXICO_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno BANXICO_TOKEN")
    hoy = date.today()
    ini = date(2020, 1, 1) if modo == "historico" else hoy - timedelta(days=15)
    if modo not in ("historico", "reciente"):
        raise ValueError("modo debe ser 'historico' o 'reciente'")
    url = URL.format(serie=BANXICO_SERIE_USD, ini=ini.isoformat(), fin=hoy.isoformat())
    ex = extractor or ExtractorEtico()
    r = ex.get(url, headers={"Bmx-Token": token})
    return parsear(r.json(), url)


def registrar_bitacora(estado, filas, segundos, error=""):
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with open(BITACORA, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["timestamp_utc", "fuente", "estado", "filas", "segundos", "error"])
        ahora = datetime.now(UTC).isoformat(timespec="seconds")
        w.writerow([ahora, FUENTE, estado, filas, round(segundos, 2), error])


def main(modo: str) -> int:
    t0 = time.time()
    try:
        df = capturar(modo)
        destino = BRONCE / "banxico"
        destino.mkdir(parents=True, exist_ok=True)
        sello = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        df.to_csv(destino / f"{modo}_{sello}.csv", index=False)
        registrar_bitacora("ok", len(df), time.time() - t0)
        print(f"OK: {len(df)} filas guardadas en bronce")
        return 0
    except Exception as e:  # la falla tambien se registra: es dato de fiabilidad
        registrar_bitacora("falla", 0, time.time() - t0, str(e)[:200])
        print(f"FALLA: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "reciente"))
