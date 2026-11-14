"""Fuente 2: INEGI, Banco de Indicadores (BISE). Requiere token gratuito.

Indicador 716898: Encuesta Mensual de Servicios (base 2018), 541941 Servicios veterinarios
para mascotas del sector privado, Ingresos totales por suministro de bienes y servicios,
indice base 2018=100, mensual, nacional. Es una estimacion de encuesta (tiene error muestral).

El token se lee de la variable de entorno INEGI_TOKEN (nunca va en el repo).
Uso:  python -m extractores.inegi
"""
import csv
import os
import sys
import time
from datetime import UTC, datetime

import pandas as pd

from extractores.base import ExtractorEtico
from pipeline.config import BITACORA, BRONCE, INEGI_INDICADOR

FUENTE = "inegi-bise"
URL = (
    "https://www.inegi.org.mx/app/api/indicadores/desarrolladores/jsonxml/INDICATOR/"
    "{ind}/es/00/false/BISE/2.0/{token}?type=json"
)


def parsear(payload: dict, url_sin_token: str) -> pd.DataFrame:
    serie = payload["Series"][0]
    filas = []
    for o in serie["OBSERVATIONS"]:
        anio, mes = o["TIME_PERIOD"].split("/")
        valor = o["OBS_VALUE"]
        filas.append(
            {
                "fecha": f"{anio}-{mes}-01",
                "serie": str(serie["INDICADOR"]),
                "valor": float(valor) if valor not in (None, "") else None,
            }
        )
    df = pd.DataFrame(filas, columns=["fecha", "serie", "valor"]).sort_values("fecha")
    df["fuente"] = FUENTE
    df["url_origen"] = url_sin_token
    df["capturado_en"] = datetime.now(UTC).isoformat(timespec="seconds")
    return df.reset_index(drop=True)


def capturar(extractor: ExtractorEtico | None = None) -> pd.DataFrame:
    token = os.environ.get("INEGI_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno INEGI_TOKEN")
    url = URL.format(ind=INEGI_INDICADOR, token=token)
    r = (extractor or ExtractorEtico()).get(url)
    return parsear(r.json(), url.replace(token, "<TOKEN>"))


def registrar_bitacora(estado, filas, segundos, error=""):
    BITACORA.parent.mkdir(parents=True, exist_ok=True)
    nuevo = not BITACORA.exists()
    with open(BITACORA, "a", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if nuevo:
            w.writerow(["timestamp_utc", "fuente", "estado", "filas", "segundos", "error"])
        ahora = datetime.now(UTC).isoformat(timespec="seconds")
        w.writerow([ahora, FUENTE, estado, filas, round(segundos, 2), error])


def main() -> int:
    t0 = time.time()
    token = os.environ.get("INEGI_TOKEN", "")
    try:
        df = capturar()
        destino = BRONCE / "inegi"
        destino.mkdir(parents=True, exist_ok=True)
        sello = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
        df.to_csv(destino / f"indicadores_{sello}.csv", index=False)
        registrar_bitacora("ok", len(df), time.time() - t0)
        print(f"OK: {len(df)} filas guardadas en bronce")
        return 0
    except Exception as e:  # la falla tambien se registra; el token nunca se escribe
        msg = str(e).replace(token, "<TOKEN>") if token else str(e)
        registrar_bitacora("falla", 0, time.time() - t0, msg[:200])
        print(f"FALLA: {msg}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
