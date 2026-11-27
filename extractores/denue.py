"""Fuente 3 (especializada, geoespacial): INEGI DENUE, Directorio Estadístico Nacional de Unidades Económicas.

Captura los establecimientos del Estado de Colima (clave de entidad 06) de las clases SCIAN definidas en
pipeline/config.py (DENUE_SECTORES), con el método oficial BuscarAreaAct de la API del DENUE:

  https://www.inegi.org.mx/app/api/denue/v1/consulta/BuscarAreaAct/
      {entidad}/{municipio}/{localidad}/{AGEB}/{manzana}/{sector}/{subsector}/{rama}/{clase}/{nombre}/
      {registro_inicial}/{registro_final}/{Id}/{token}

Reglas:
- El token del DENUE es distinto del Banco de Indicadores; se lee de la variable de entorno DENUE_TOKEN
  y nunca se escribe en el repositorio (la URL se guarda con <TOKEN>).
- CERO DATOS PERSONALES (LFPDPPP): la razón social (que en personas físicas es su nombre), el teléfono,
  el correo y el sitio web NO se copian del JSON; nunca llegan a la capa bronce.
- Si la API falla, la captura falla y queda en la bitácora. No hay datos de respaldo inventados.

Uso:  python -m extractores.denue
"""
import csv
import os
import sys
import time
import unicodedata
from datetime import UTC, datetime

import pandas as pd

from extractores.base import ExtractorEtico
from pipeline.config import (
    BITACORA,
    BRONCE,
    DENUE_ENTIDAD,
    DENUE_FILTRO_NOMBRE,
    DENUE_MUNICIPIOS,
    DENUE_SECTORES,
)

FUENTE = "inegi-denue"
URL_AREA_ACT = (
    "https://www.inegi.org.mx/app/api/denue/v1/consulta/BuscarAreaAct/"
    "{entidad}/0/0/0/0/0/0/0/{clase}/0/{inicio}/{fin}/0/{token}"
)
TAMANO_PAGINA = 1000

# Campos del JSON que se conservan -> nombre en bronce. Lo que no está aquí no se guarda.
CAMPOS = {
    "Id": "id_denue",
    "CLEE": "clee",
    "Nombre": "nombre_comercial",
    "Clase_actividad": "actividad_scian",
    "Estrato": "estrato_personal",
    "Tipo_vialidad": "tipo_vialidad",
    "Calle": "calle",
    "Num_Exterior": "numero_exterior",
    "Colonia": "colonia",
    "CP": "codigo_postal",
    "AGEB": "ageb",
    "Manzana": "manzana",
    "Fecha_Alta": "fecha_alta",
    "Latitud": "latitud",
    "Longitud": "longitud",
}
# Campos que pueden identificar a personas físicas: se descartan siempre.
CAMPOS_PERSONALES = [
    "Razon_social", "razon_social", "Telefono", "telefono", "Correo_e", "correo", "Sitio_internet",
    "sitio_internet", "nombre_propietario", "telefono_particular", "correo_personal", "curp",
    "rfc_persona_fisica",
]


def _sin_acentos(texto: str) -> str:
    base = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in base if not unicodedata.combining(c)).casefold().strip()


_MUNICIPIOS = {_sin_acentos(m): m for m in DENUE_MUNICIPIOS}


def municipio_de_ubicacion(ubicacion: str) -> str:
    """'LOCALIDAD, Municipio, ENTIDAD' -> nombre oficial del municipio de Colima (o el texto tal cual)."""
    partes = [p.strip() for p in str(ubicacion or "").split(",")]
    candidato = partes[1] if len(partes) >= 3 else (partes[0] if partes else "")
    return _MUNICIPIOS.get(_sin_acentos(candidato), candidato)


def sanitizar_privacidad(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina cualquier columna que pueda identificar a una persona física (LFPDPPP)."""
    return df.drop(columns=[c for c in CAMPOS_PERSONALES if c in df.columns])


def parsear(items: list[dict], clase: str, url_sin_token: str) -> pd.DataFrame:
    filas = []
    for item in items:
        fila = {destino: item.get(origen) for origen, destino in CAMPOS.items()}
        fila["codigo_actividad"] = str(item.get("CLASE_ACTIVIDAD_ID") or clase)
        fila["municipio"] = municipio_de_ubicacion(item.get("Ubicacion", ""))
        filas.append(fila)
    df = pd.DataFrame(filas, columns=[*CAMPOS.values(), "codigo_actividad", "municipio"])
    df["latitud"] = pd.to_numeric(df["latitud"], errors="coerce")
    df["longitud"] = pd.to_numeric(df["longitud"], errors="coerce")
    df["fuente"] = FUENTE
    df["url_origen"] = url_sin_token
    return df


def filtrar_por_nombre(df: pd.DataFrame, clase: str) -> pd.DataFrame:
    """En clases mixtas (DENUE_FILTRO_NOMBRE) conserva solo los establecimientos de mascotas."""
    patron = DENUE_FILTRO_NOMBRE.get(clase)
    if patron is None or df.empty:
        return df
    return df[df["nombre_comercial"].fillna("").str.upper().str.contains(patron, regex=True)]


def capturar(extractor: ExtractorEtico | None = None) -> pd.DataFrame:
    token = os.environ.get("DENUE_TOKEN")
    if not token:
        raise RuntimeError("Falta la variable de entorno DENUE_TOKEN (token de la API del DENUE)")
    ex = extractor or ExtractorEtico()
    partes = []
    for clase in DENUE_SECTORES:
        inicio = 1
        while True:
            fin = inicio + TAMANO_PAGINA - 1
            url = URL_AREA_ACT.format(entidad=DENUE_ENTIDAD, clase=clase, inicio=inicio, fin=fin, token=token)
            items = ex.get(url).json() or []
            if not isinstance(items, list):  # la API responde un objeto cuando no hay resultados
                items = []
            partes.append(filtrar_por_nombre(parsear(items, clase, url.replace(token, "<TOKEN>")), clase))
            if len(items) < TAMANO_PAGINA:
                break
            inicio = fin + 1
    df = pd.concat(partes, ignore_index=True)
    if df.empty:
        raise RuntimeError("La API del DENUE no devolvió establecimientos para Colima")
    df = sanitizar_privacidad(df.drop_duplicates(subset=["id_denue"]))
    df["capturado_en"] = datetime.now(UTC).isoformat(timespec="seconds")
    return df


def registrar_bitacora(estado: str, filas: int, segundos: float, error: str = ""):
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
    token = os.environ.get("DENUE_TOKEN", "")
    try:
        df = capturar()
        destino = BRONCE / "denue"
        destino.mkdir(parents=True, exist_ok=True)
        archivo = destino / f"denue_colima_{datetime.now(UTC):%Y%m%dT%H%M%S}.csv"
        df.to_csv(archivo, index=False)
        registrar_bitacora("ok", len(df), time.time() - t0)
        print(f"OK DENUE: {len(df)} establecimientos guardados en {archivo.name}")
        return 0
    except Exception as e:  # toda falla queda en la bitacora (dato de fiabilidad); el token nunca se escribe
        error = str(e).replace(token, "<TOKEN>") if token else str(e)
        registrar_bitacora("falla", 0, time.time() - t0, error[:200])
        print(f"FALLA DENUE: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
