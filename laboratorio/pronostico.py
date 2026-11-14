"""Laboratorio estadistico E1: caracterizacion, estacionariedad, ACF/PACF, 4 modelos,
seleccion por error en datos de prueba, residuos y pronostico con intervalo.

Uso:  python -m laboratorio.pronostico [archivo_oro.csv] [columna]
Por defecto: data/oro/usd_mxn_mensual.csv, columna usd_media.
Cuando exista la serie del INPC de INEGI, se corre igual cambiando archivo y columna.
"""
import itertools
import sys
import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.exponential_smoothing.ets import ETSModel
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller

from pipeline.config import ORO, RAIZ

SALIDAS = RAIZ / "laboratorio" / "salidas"
H_PRUEBA = 12  # ultimos 12 meses como datos de prueba (el modelo no los ve)
H_FUTURO = 6
warnings.filterwarnings("ignore")


def cargar(archivo: Path, col: str) -> pd.Series:
    df = pd.read_csv(archivo, parse_dates=["mes"])
    s = df.set_index("mes")[col].astype(float)
    s.index = pd.DatetimeIndex(s.index).to_period("M").to_timestamp()
    return s.asfreq("MS")


def metricas(real: pd.Series, pred: np.ndarray) -> dict:
    e = real.values - np.asarray(pred)
    return {
        "MAE": float(np.mean(np.abs(e))),
        "RMSE": float(np.sqrt(np.mean(e**2))),
        "MAPE": float(np.mean(np.abs(e / real.values)) * 100),
    }


def ajustar_ets(y, trend, seasonal, damped=False):
    m = ETSModel(
        y,
        error="add",
        trend=trend,
        damped_trend=damped,
        seasonal=seasonal,
        seasonal_periods=12 if seasonal else None,
    )
    return m.fit(disp=False)


def elegir_arima(y: pd.Series, d: int):
    """Busca (p,q) en 0..2 por AIC, con d dado por Dickey-Fuller."""
    mejor = None
    for p, q in itertools.product(range(3), range(3)):
        try:
            r = SARIMAX(y, order=(p, d, q), trend="c" if d == 0 else "n").fit(disp=False)
        except Exception:
            continue
        if mejor is None or r.aic < mejor[0].aic:
            mejor = (r, (p, d, q))
    return mejor


def dickey_fuller(y: pd.Series):
    """Devuelve (d, tabla): diferencia hasta lograr estacionariedad (max 2)."""
    filas, serie, d = [], y.dropna(), 0
    while True:
        stat, p, *_ = adfuller(serie, autolag="AIC")
        filas.append({"diferencias": d, "estadistico_ADF": stat, "p_valor": p, "estacionaria": p < 0.05})
        if p < 0.05 or d == 2:
            return d, pd.DataFrame(filas)
        serie, d = serie.diff().dropna(), d + 1


def main(archivo: Path, col: str):
    SALIDAS.mkdir(parents=True, exist_ok=True)
    y = cargar(archivo, col)
    print(f"Serie: {col}, {len(y)} periodos ({y.index.min():%Y-%m} a {y.index.max():%Y-%m})")

    # 1. Caracterizacion y descomposicion (multiplicativa si la amplitud crece con el nivel)
    modelo_desc = "multiplicative" if (y > 0).all() else "additive"
    dec = seasonal_decompose(y, model=modelo_desc, period=12)
    dec.plot().savefig(SALIDAS / "descomposicion.png", dpi=120)
    plt.close("all")

    # 2. Estacionariedad
    d, tabla_adf = dickey_fuller(y)
    tabla_adf.to_csv(SALIDAS / "dickey_fuller.csv", index=False)
    print(tabla_adf.to_string(index=False))

    # 3. ACF y PACF sobre la serie diferenciada d veces
    yd = y.diff(d).dropna() if d else y
    fig, ax = plt.subplots(1, 2, figsize=(11, 3.5))
    plot_acf(yd, lags=24, ax=ax[0])
    plot_pacf(yd, lags=24, ax=ax[1], method="ywm")
    fig.savefig(SALIDAS / "acf_pacf.png", dpi=120)
    plt.close("all")

    # 4. Cuatro modelos entrenados con train y evaluados en test
    train, test = y.iloc[:-H_PRUEBA], y.iloc[-H_PRUEBA:]
    arima_tr, orden = elegir_arima(train, d)
    ajustes = {
        "Suavizamiento simple": lambda s: ajustar_ets(s, None, None),
        "Holt": lambda s: ajustar_ets(s, "add", None),
        "Holt-Winters": lambda s: ajustar_ets(s, "add", "add"),
    }
    filas, preds = [], {}
    for nombre, f in ajustes.items():
        r = f(train)
        preds[nombre] = r.forecast(H_PRUEBA).values
        filas.append({"modelo": nombre, "parametros": "", "AIC": r.aic, **metricas(test, preds[nombre])})
    preds[f"ARIMA{orden}"] = arima_tr.forecast(H_PRUEBA).values
    filas.append({"modelo": f"ARIMA{orden}", "parametros": "elegido por AIC", "AIC": arima_tr.aic,
                  **metricas(test, preds[f"ARIMA{orden}"])})
    tabla = pd.DataFrame(filas).sort_values("RMSE")
    tabla.to_csv(SALIDAS / "comparacion_modelos.csv", index=False)
    print(tabla.to_string(index=False))

    ganador = tabla.iloc[0]["modelo"]
    print(f"\nModelo ganador (menor RMSE en datos de prueba): {ganador}")

    # 5. Reajustar al ganador con TODA la serie, residuos y pronostico con intervalo
    if ganador.startswith("ARIMA"):
        r = SARIMAX(y, order=orden, trend="c" if d == 0 else "n").fit(disp=False)
        fut = r.get_forecast(H_FUTURO).summary_frame(alpha=0.05)
        fut = fut.rename(columns={"mean_ci_lower": "inferior_95", "mean_ci_upper": "superior_95"})
        residuos = r.resid.iloc[d + 1:] if d else r.resid
    else:
        configs = {
            "Suavizamiento simple": (None, None),
            "Holt": ("add", None),
            "Holt-Winters": ("add", "add"),
        }
        cfg = configs[ganador]
        r = ajustar_ets(y, *cfg)
        fut = r.get_prediction(start=len(y), end=len(y) + H_FUTURO - 1).summary_frame(alpha=0.05)
        fut = fut.rename(columns={"pi_lower": "inferior_95", "pi_upper": "superior_95"})
        residuos = r.resid
    fut = fut[["mean", "inferior_95", "superior_95"]]
    fut.index = pd.date_range(y.index[-1] + pd.offsets.MonthBegin(), periods=H_FUTURO, freq="MS")
    fut.index.name = "mes"
    fut.to_csv(SALIDAS / "pronostico.csv")

    lb = acorr_ljungbox(residuos.dropna(), lags=[10], return_df=True)
    p_lb = float(lb["lb_pvalue"].iloc[0])
    print(f"Ljung-Box (10 rezagos) p={p_lb:.3f} -> "
          f"{'residuos sin autocorrelacion' if p_lb > 0.05 else 'HAY autocorrelacion residual'}")
    pd.DataFrame([{"modelo": ganador, "ljung_box_p": p_lb, "pasa": p_lb > 0.05}]).to_csv(
        SALIDAS / "residuos.csv", index=False)

    fig, ax = plt.subplots(figsize=(10, 4))
    y.plot(ax=ax, label="historico")
    test.plot(ax=ax, label="prueba (real)")
    for nombre, p in preds.items():
        ax.plot(test.index, p, "--", label=nombre, alpha=0.7)
    fut["mean"].plot(ax=ax, color="k", label=f"pronostico {ganador}")
    ax.fill_between(fut.index, fut["inferior_95"], fut["superior_95"], color="k", alpha=0.15)
    ax.set_title(f"{col}: modelos y pronostico a {H_FUTURO} meses (IC 95%)")
    ax.legend(fontsize=7)
    fig.savefig(SALIDAS / "pronostico.png", dpi=120, bbox_inches="tight")
    print("\nPronostico:\n", fut.round(3).to_string())


if __name__ == "__main__":
    arch = Path(sys.argv[1]) if len(sys.argv) > 1 else ORO / "usd_mxn_mensual.csv"
    main(arch, sys.argv[2] if len(sys.argv) > 2 else "usd_media")
