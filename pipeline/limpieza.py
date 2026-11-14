"""Bronce -> Plata con puerta de calidad (pandera). Lo rechazado va a cuarentena."""
import glob

import pandas as pd
import pandera.pandas as pa

from pipeline.config import BRONCE, CUARENTENA, PLATA, RANGOS


def esquema(fuente: str) -> pa.DataFrameSchema:
    lo, hi = RANGOS[fuente]
    return pa.DataFrameSchema(
        {
            "fecha": pa.Column(str, pa.Check.str_matches(r"^\d{4}-\d{2}-\d{2}$"), nullable=False),
            "serie": pa.Column(str, nullable=False),
            "valor": pa.Column(float, pa.Check.in_range(lo, hi), nullable=False),
        },
        coerce=True,
        strict=False,
    )


def cargar_bronce(subdir: str) -> pd.DataFrame:
    archivos = sorted(glob.glob(str(BRONCE / subdir / "*.csv")))
    if not archivos:
        raise FileNotFoundError(f"No hay archivos en bronce/{subdir}")
    return pd.concat((pd.read_csv(a, dtype={"serie": str}) for a in archivos), ignore_index=True)


def validar(df: pd.DataFrame, fuente: str = "banxico") -> tuple[pd.DataFrame, pd.DataFrame]:
    """Devuelve (aprobados, rechazados). Cada rechazo lleva su motivo; nada se borra en silencio."""
    df = df.reset_index(drop=True)
    motivos: dict[int, list[str]] = {}
    try:
        esquema(fuente).validate(df, lazy=True)
    except pa.errors.SchemaErrors as e:
        for _, fila in e.failure_cases.iterrows():
            idx = fila["index"]
            if pd.isna(idx):
                continue
            motivos.setdefault(int(idx), []).append(f"{fila['column']}: {fila['check']}")
    malos = sorted(motivos)
    rechazados = df.loc[malos].copy()
    rechazados["motivo_rechazo"] = [" | ".join(motivos[i]) for i in malos]
    return df.drop(index=malos).copy(), rechazados


def marcar_atipicos_iqr(df: pd.DataFrame, col: str = "valor", k: float = 1.5) -> pd.DataFrame:
    """Marca (no elimina) atipicos por IQR: un salto puede ser el hallazgo."""
    q1, q3 = df[col].quantile([0.25, 0.75])
    iqr = q3 - q1
    df = df.copy()
    df["atipico_iqr"] = (df[col] < q1 - k * iqr) | (df[col] > q3 + k * iqr)
    return df


def ejecutar(fuente: str = "banxico") -> dict:
    crudo = cargar_bronce(fuente)
    n_crudo = len(crudo)
    # Misma fecha capturada varias veces: se queda la captura mas reciente.
    crudo = crudo.sort_values("capturado_en").drop_duplicates(["serie", "fecha"], keep="last")
    n_dups = n_crudo - len(crudo)

    ok, malos = validar(crudo, fuente)
    ok = marcar_atipicos_iqr(ok.sort_values("fecha"))

    PLATA.mkdir(parents=True, exist_ok=True)
    CUARENTENA.mkdir(parents=True, exist_ok=True)
    ok.to_csv(PLATA / f"{fuente}_diario.csv" if fuente == "banxico" else PLATA / f"{fuente}_mensual.csv",
              index=False)
    malos.to_csv(CUARENTENA / f"{fuente}_rechazados.csv", index=False)
    resumen = {
        "fuente": fuente,
        "filas_bronce": n_crudo,
        "duplicados_descartados": n_dups,
        "filas_plata": len(ok),
        "filas_cuarentena": len(malos),
        "atipicos_marcados": int(ok["atipico_iqr"].sum()),
    }
    print(resumen)
    return resumen


if __name__ == "__main__":
    ejecutar()
