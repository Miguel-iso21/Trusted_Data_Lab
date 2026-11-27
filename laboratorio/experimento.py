"""Experimento E2 (ruta ingenieria): configuracion de la puerta de calidad bronce -> plata.

Pregunta: que combinacion de formato de escritura, motor de validacion y tamano de lote procesa
los datos en menos tiempo sin dejar de detectar los registros invalidos.

Todo corre contra una COPIA LOCAL de data/bronce/banxico (en una carpeta temporal); nunca contra
las APIs de Banxico o INEGI. A cada lote se le inyecta un 2 % de registros invalidos conocidos para
medir, ademas del tiempo, cuantos registros clasifica mal la puerta.

Partes:
  1. 2^3 con 2 replicas (cada replica es un bloque) y orden aleatorio  -> ANOVA, efectos, supuestos
  2. Dos factores con 3 niveles (formato x tamano), 3 replicas          -> ANOVA de dos vias
  3. Matrices 2^4 completo y 2^(4-1) fraccionado (D = ABC) con alias
  4. Corrida de confirmacion del optimo contra la configuracion actual

Uso:  python -m laboratorio.experimento                  mide y analiza (los tiempos varian un poco)
      python -m laboratorio.experimento --solo-analisis  recalcula todo desde los CSV crudos guardados
Resultados en laboratorio/salidas/experimento/.
"""
import itertools
import json
import sys
import tempfile
import time
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from scipy import stats
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.diagnostic import het_breuschpagan

from pipeline import limpieza
from pipeline.config import RAIZ, RANGOS

SALIDAS = RAIZ / "laboratorio" / "salidas" / "experimento"
SEMILLA = 20261126
TASA_INVALIDOS = 0.02
FACTORES = {
    "A": ("formato", {-1: "csv", 1: "parquet"}),
    "B": ("motor", {-1: "fila_por_fila", 1: "pandera"}),
    "C": ("tamano", {-1: 1, 1: 20}),
}
N_CONFIRMACION = 5


# ----------------------------------------------------------------------------- datos
def datos_base() -> pd.DataFrame:
    """Registros validos de bronce Banxico, sin fechas duplicadas, con las columnas de la puerta."""
    crudo = limpieza.cargar_bronce("banxico")
    crudo = crudo.sort_values("capturado_en").drop_duplicates(["serie", "fecha"], keep="last")
    lo, hi = RANGOS["banxico"]
    ok = crudo["valor"].between(lo, hi) & crudo["fecha"].astype(str).str.match(r"^\d{4}-\d{2}-\d{2}$")
    return crudo.loc[ok, ["fecha", "serie", "valor"]].reset_index(drop=True)


def preparar(base: pd.DataFrame, veces: int, rng: np.random.Generator) -> tuple[pd.DataFrame, np.ndarray]:
    """Replica la base `veces` veces e inyecta 2 % de invalidos de tres tipos. Devuelve (df, es_invalido)."""
    df = pd.concat([base] * veces, ignore_index=True)
    df["serie"] = df["serie"].astype(str)
    df["fecha"] = df["fecha"].astype(str)
    df["valor"] = df["valor"].astype(object)
    n_malos = int(round(len(df) * TASA_INVALIDOS))
    idx = rng.choice(len(df), size=n_malos, replace=False)
    for k, i in enumerate(idx):
        tipo = k % 3
        if tipo == 0:
            df.at[i, "valor"] = 999.0  # fuera de rango
        elif tipo == 1:
            df.at[i, "valor"] = None  # faltante (como el N/E de Banxico)
        else:
            df.at[i, "fecha"] = "02/01/2024"  # formato de fecha invalido
    df["valor"] = pd.to_numeric(df["valor"])
    es_malo = np.zeros(len(df), dtype=bool)
    es_malo[idx] = True
    return df, es_malo


# ----------------------------------------------------------------------------- una corrida
def _escribir(df: pd.DataFrame, ruta: Path, formato: str) -> Path:
    destino = ruta.with_suffix("." + formato)
    if formato == "csv":
        df.to_csv(destino, index=False)
    elif formato == "parquet":
        df.to_parquet(destino, index=False)
    elif formato == "feather":
        df.reset_index(drop=True).to_feather(destino)
    else:
        raise ValueError(formato)
    return destino


def _leer(ruta: Path, formato: str) -> pd.DataFrame:
    lector = {"csv": pd.read_csv, "parquet": pd.read_parquet, "feather": pd.read_feather}[formato]
    return lector(ruta)


def correr(df: pd.DataFrame, es_malo: np.ndarray, formato: str, motor: str, carpeta: Path) -> dict:
    """Puerta de calidad real (limpieza.validar) + escritura de plata y cuarentena + lectura de plata."""
    previo = limpieza.HAS_PANDERA
    limpieza.HAS_PANDERA = motor == "pandera"
    try:
        t0 = time.perf_counter()
        ok, malos = limpieza.validar(df.copy(), "banxico")
        plata = _escribir(ok.drop(columns="motivo_rechazo", errors="ignore"), carpeta / "plata", formato)
        _escribir(malos, carpeta / "cuarentena", formato)
        leido = _leer(plata, formato)
        segundos = time.perf_counter() - t0
    finally:
        limpieza.HAS_PANDERA = previo
    if len(leido) != len(ok):
        raise RuntimeError("la lectura de plata no coincide con lo escrito")
    rechazado = np.zeros(len(df), dtype=bool)
    rechazado[malos.index.to_numpy()] = True
    return {"segundos": segundos, "mal_clasificados": int((rechazado != es_malo).sum())}


def solo_io(df: pd.DataFrame, formato: str, carpeta: Path) -> float:
    """Escritura + lectura de la capa plata (para el diseno de dos factores)."""
    t0 = time.perf_counter()
    _leer(_escribir(df, carpeta / "plata_io", formato), formato)
    return time.perf_counter() - t0


# ----------------------------------------------------------------------------- matrices 2^k
def matriz_completa(k: int) -> pd.DataFrame:
    letras = "ABCDEFG"[:k]
    filas = [dict(zip(letras, reversed(c), strict=True)) for c in itertools.product([-1, 1], repeat=k)]
    return pd.DataFrame(filas)[list(letras)]  # orden estandar de Yates: A cambia mas rapido


def matriz_2_4_1() -> pd.DataFrame:
    """Fraccion media 2^(4-1) con generador D = ABC (relacion definidora I = ABCD, resolucion IV)."""
    m = matriz_completa(3)
    m["D"] = m["A"] * m["B"] * m["C"]
    return m


def _producto(p: str, q: str) -> str:
    """Multiplica dos palabras de efectos (A*A = I)."""
    letras = sorted(set(p) ^ set(q))
    return "".join(letras) or "I"


def alias_2_4_1() -> pd.DataFrame:
    definidora = "ABCD"
    efectos = ["".join(c) for r in (1, 2, 3) for c in itertools.combinations("ABCD", r)]
    vistos, filas = set(), []
    for e in efectos:
        alias = _producto(e, definidora)
        par = frozenset((e, alias))
        if par in vistos:
            continue
        vistos.add(par)
        filas.append({"efecto": e, "alias": alias, "orden_efecto": len(e), "orden_alias": len(alias)})
    return pd.DataFrame(filas)


# ----------------------------------------------------------------------------- analisis
def _guardar_fig(fig, nombre):
    fig.savefig(SALIDAS / nombre, dpi=120, bbox_inches="tight")
    plt.close(fig)


def _para_modelo(res: pd.DataFrame) -> pd.DataFrame:
    return res.rename(columns={"C": "T"}).assign(blq=res["bloque"].astype(str))


def _nombre(termino: str) -> str:
    return "bloque" if termino == "blq" else termino.replace("T", "C")


def analizar_2k3(res: pd.DataFrame) -> dict:
    res = res.assign(ly=np.log(res["segundos"]))
    # En la formula el factor C se llama T: "C" choca con la funcion C() de patsy.
    dm = _para_modelo(res)
    modelo = smf.ols("ly ~ A * B * T + blq", data=dm).fit()
    # Puerta 3: si la varianza no es constante, los efectos se confirman con errores robustos HC3.
    robusto = smf.ols("ly ~ A * B * T + blq", data=dm).fit(cov_type="HC3")
    anova = anova_lm(modelo, typ=2)
    anova.index = [_nombre(t) for t in anova.index]
    anova.to_csv(SALIDAS / "anova_2k3.csv")

    terminos = ["A", "B", "C", "A:B", "A:C", "B:C", "A:B:C"]
    efectos = pd.DataFrame({
        "termino": terminos,
        "efecto_log": [2 * modelo.params[t.replace("C", "T")] for t in terminos],
        "p_valor": [modelo.pvalues[t.replace("C", "T")] for t in terminos],
        "p_valor_hc3": [robusto.pvalues[t.replace("C", "T")] for t in terminos],
    })
    efectos["factor_multiplicativo"] = np.exp(efectos["efecto_log"])
    efectos.to_csv(SALIDAS / "efectos_2k3.csv", index=False)

    # Supuestos sobre los residuos
    resid = modelo.resid
    shapiro_p = float(stats.shapiro(resid).pvalue)
    # Varianza constante: Breusch-Pagan sobre los residuos. Levene por tratamiento no sirve aqui:
    # con 2 replicas por celda las desviaciones a la mediana son identicas y la prueba degenera.
    bp_p = float(het_breuschpagan(resid, modelo.model.exog)[1])
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.8))
    stats.probplot(resid, dist="norm", plot=ax[0])
    ax[0].set_title(f"Q-Q de residuos (Shapiro p = {shapiro_p:.3f})")
    ax[1].scatter(modelo.fittedvalues, resid)
    ax[1].axhline(0, color="k", lw=0.8)
    ax[1].set_xlabel("ajustado (log s)")
    ax[1].set_ylabel("residuo")
    ax[1].set_title(f"Residuos vs ajustados (Breusch-Pagan p = {bp_p:.3f})")
    _guardar_fig(fig, "supuestos_2k3.png")

    # Efectos principales e interacciones (en segundos, escala original)
    fig, ax = plt.subplots(1, 3, figsize=(12, 3.5), sharey=True)
    for i, f in enumerate("ABC"):
        nombre, niveles = FACTORES[f]
        m = res.groupby(f)["segundos"].mean()
        ax[i].plot([str(niveles[-1]), str(niveles[1])], [m[-1], m[1]], "o-")
        ax[i].set_title(f"{f} · {nombre}")
    ax[0].set_ylabel("segundos (media)")
    _guardar_fig(fig, "efectos_principales_2k3.png")

    fig, ax = plt.subplots(1, 3, figsize=(12, 3.5))
    for i, (f1, f2) in enumerate([("A", "B"), ("A", "C"), ("B", "C")]):
        for nivel, g in res.groupby(f2):
            m = g.groupby(f1)["segundos"].mean()
            ax[i].plot([str(FACTORES[f1][1][-1]), str(FACTORES[f1][1][1])], [m[-1], m[1]], "o-",
                       label=f"{FACTORES[f2][0]} = {FACTORES[f2][1][nivel]}")
        ax[i].set_title(f"Interaccion {f1} x {f2}")
        ax[i].set_yscale("log")
        ax[i].legend(fontsize=7)
    ax[0].set_ylabel("segundos (escala log)")
    _guardar_fig(fig, "interacciones_2k3.png")

    # Optimo controlable (A, B) para el lote grande (C = +1)
    celdas = pd.DataFrame([{"A": a, "B": b, "T": 1} for a in (-1, 1) for b in (-1, 1)])
    pred = []
    for _, c in celdas.iterrows():
        p = [modelo.get_prediction(pd.DataFrame([{**c.to_dict(), "blq": blq}])).summary_frame(alpha=0.05)
             for blq in sorted(dm["blq"].unique())]
        pred.append({"A": c["A"], "B": c["B"],
                     "pred_log": float(np.mean([x["mean"].iloc[0] for x in p])),
                     "pi_inf_log": float(np.mean([x["obs_ci_lower"].iloc[0] for x in p])),
                     "pi_sup_log": float(np.mean([x["obs_ci_upper"].iloc[0] for x in p]))})
    pred = pd.DataFrame(pred).sort_values("pred_log")
    pred.to_csv(SALIDAS / "predicciones_lote_grande.csv", index=False)
    return {"modelo": modelo, "anova": anova, "efectos": efectos, "shapiro_p": shapiro_p,
            "breusch_pagan_p": bp_p, "optimo": pred.iloc[0].to_dict(), "predicciones": pred}


def analizar_dos_factores(res: pd.DataFrame) -> pd.DataFrame:
    res = res.assign(ly=np.log(res["segundos"]))
    modelo = smf.ols("ly ~ C(formato) * C(tamano)", data=res).fit()
    anova = anova_lm(modelo, typ=2)
    anova.to_csv(SALIDAS / "anova_dos_factores.csv")
    fig, ax = plt.subplots(figsize=(6, 4))
    for formato, g in res.groupby("formato"):
        m = g.groupby("tamano")["segundos"].mean()
        ax.plot(m.index.astype(str), m.values, "o-", label=formato)
    ax.set_yscale("log")
    ax.set_xlabel("tamano del lote (veces los datos reales)")
    ax.set_ylabel("segundos escritura + lectura (log)")
    ax.set_title("Interaccion formato x tamano")
    ax.legend()
    _guardar_fig(fig, "interaccion_dos_factores.png")
    return anova


# ----------------------------------------------------------------------------- orquestacion
def medir() -> None:
    """Corre todas las mediciones y guarda los datos crudos. Los tiempos cambian un poco en cada corrida."""
    SALIDAS.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEMILLA)
    base = datos_base()
    lotes = {v: preparar(base, v, np.random.default_rng(SEMILLA + v)) for v in (1, 10, 20, 50)}
    print(f"Base: {len(base)} registros validos de Banxico; invalidos inyectados: {TASA_INVALIDOS:.0%}")

    with tempfile.TemporaryDirectory() as tmp:
        carpeta = Path(tmp)
        # calentamiento (no se mide): primeras importaciones y caches del sistema
        for formato, motor in itertools.product(("csv", "parquet"), ("fila_por_fila", "pandera")):
            correr(*lotes[1], formato, motor, carpeta)

        # 1. 2^3 con 2 replicas; cada replica es un bloque con su propio orden aleatorio
        diseno = []
        for bloque in (1, 2):
            orden = rng.permutation(len(matriz_completa(3)))
            for tratamiento in orden:
                fila = matriz_completa(3).iloc[tratamiento].to_dict()
                diseno.append({"bloque": bloque, "tratamiento": int(tratamiento) + 1, **fila})
        diseno = pd.DataFrame(diseno)
        diseno.insert(0, "orden_corrida", range(1, len(diseno) + 1))
        filas = []
        for _, d in diseno.iterrows():
            formato, motor, tamano = (FACTORES[f][1][d[f]] for f in "ABC")
            r = correr(*lotes[tamano], formato, motor, carpeta)
            filas.append({**d.to_dict(), "formato": formato, "motor": motor, "tamano": tamano, **r})
            print(f"  corrida {d['orden_corrida']:>2}: {formato:7} {motor:13} x{tamano:<2} "
                  f"-> {r['segundos']:.3f} s, mal clasificados {r['mal_clasificados']}")
        res = pd.DataFrame(filas)
        res.to_csv(SALIDAS / "resultados_2k3.csv", index=False)
        a = analizar_2k3(res)  # el optimo decide que se confirma

        # 2. Dos factores, 3 niveles cada uno, 3 replicas, orden aleatorio
        celdas = [(f, t) for f in ("csv", "parquet", "feather") for t in (1, 10, 50)] * 3
        filas2 = []
        for i in rng.permutation(len(celdas)):
            formato, tamano = celdas[i]
            ok = lotes[tamano][0]
            filas2.append({"formato": formato, "tamano": tamano, "segundos": solo_io(ok, formato, carpeta)})
        res2 = pd.DataFrame(filas2)
        res2.insert(0, "orden_corrida", range(1, len(res2) + 1))
        res2.to_csv(SALIDAS / "resultados_dos_factores.csv", index=False)

        # 4. Confirmacion: optimo vs configuracion actual (csv + pandera), lote grande, intercalados
        opt = a["optimo"]
        opt_cfg = (FACTORES["A"][1][int(opt["A"])], FACTORES["B"][1][int(opt["B"])])
        actual_cfg = ("csv", "pandera")
        corridas = [("optimo", opt_cfg)] * N_CONFIRMACION + [("actual", actual_cfg)] * N_CONFIRMACION
        filas3 = []
        for i in rng.permutation(len(corridas)):
            etiqueta, (formato, motor) = corridas[i]
            r = correr(*lotes[20], formato, motor, carpeta)
            filas3.append({"configuracion": etiqueta, "formato": formato, "motor": motor, **r})
        conf = pd.DataFrame(filas3)
        conf.insert(0, "orden_corrida", range(1, len(conf) + 1))
        conf.to_csv(SALIDAS / "confirmacion.csv", index=False)

    parametros = {"semilla": SEMILLA, "registros_base": len(base), "tasa_invalidos": TASA_INVALIDOS,
                  "medido_el": time.strftime("%Y-%m-%d %H:%M")}
    (SALIDAS / "parametros.json").write_text(json.dumps(parametros, indent=2), encoding="utf-8")


def analizar() -> dict:
    """Recalcula todo a partir de los CSV crudos guardados: mismos datos, mismos numeros."""
    parametros = json.loads((SALIDAS / "parametros.json").read_text(encoding="utf-8"))
    res = pd.read_csv(SALIDAS / "resultados_2k3.csv")
    res2 = pd.read_csv(SALIDAS / "resultados_dos_factores.csv")
    conf = pd.read_csv(SALIDAS / "confirmacion.csv")
    a = analizar_2k3(res)
    anova2 = analizar_dos_factores(res2)
    opt = a["optimo"]
    opt_cfg = (FACTORES["A"][1][int(opt["A"])], FACTORES["B"][1][int(opt["B"])])

    # 3. Matrices completo vs fraccionado
    matriz_completa(4).to_csv(SALIDAS / "matriz_2k4_completo.csv", index=False)
    matriz_2_4_1().to_csv(SALIDAS / "matriz_2k4-1_fraccionado.csv", index=False)
    alias_2_4_1().to_csv(SALIDAS / "alias_2k4-1.csv", index=False)

    preds = a["predicciones"]
    pred_actual = float(preds.loc[(preds["A"] == -1) & (preds["B"] == 1), "pred_log"].iloc[0])
    obs_opt = conf.loc[conf["configuracion"] == "optimo", "segundos"]
    obs_act = conf.loc[conf["configuracion"] == "actual", "segundos"]
    welch = stats.ttest_ind(np.log(obs_opt), np.log(obs_act), equal_var=False)
    resumen = {
        "medido_el": parametros["medido_el"],
        "registros_base": parametros["registros_base"],
        "corridas_2k3": len(res),
        "mal_clasificados_total_2k3": int(res["mal_clasificados"].sum()),
        "shapiro_p_residuos": a["shapiro_p"],
        "breusch_pagan_p": a["breusch_pagan_p"],
        "optimo_lote_grande": {"formato": opt_cfg[0], "motor": opt_cfg[1]},
        "prediccion_optimo_s": float(np.exp(opt["pred_log"])),
        "intervalo_prediccion_95_s": [float(np.exp(opt["pi_inf_log"])), float(np.exp(opt["pi_sup_log"]))],
        "confirmacion_optimo_media_s": float(obs_opt.mean()),
        "confirmacion_actual_media_s": float(obs_act.mean()),
        "mejora_predicha_vs_actual_pct": float((1 - np.exp(opt["pred_log"] - pred_actual)) * 100),
        "mejora_observada_vs_actual_pct": float((1 - obs_opt.mean() / obs_act.mean()) * 100),
        "welch_p_log": float(welch.pvalue),
        "confirmacion_dentro_del_intervalo": bool(
            np.exp(opt["pi_inf_log"]) <= obs_opt.mean() <= np.exp(opt["pi_sup_log"])),
        "corridas_2k4_completo": 16,
        "corridas_2k4-1_fraccionado": 8,
        "anova_2k3_p": a["anova"]["PR(>F)"].dropna().round(6).to_dict(),
        "anova_dos_factores_p": anova2["PR(>F)"].dropna().round(6).to_dict(),
    }
    (SALIDAS / "resumen.json").write_text(json.dumps(resumen, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(resumen, indent=2, ensure_ascii=False))
    print("\nEfectos (factor multiplicativo sobre el tiempo):")
    print(a["efectos"].round(4).to_string(index=False))
    return resumen


def main(argv: list[str] | None = None) -> dict:
    if "--solo-analisis" not in (argv if argv is not None else sys.argv[1:]):
        medir()
    return analizar()


if __name__ == "__main__":
    main()
