"""Tablero publico del Observatorio veterinario de Colima (Streamlit).

Solo LEE archivos ya generados por el pipeline y el laboratorio; no llama APIs.
Ejecutar:  streamlit run tablero/app.py
"""
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

RAIZ = Path(__file__).resolve().parents[1]
ORO = RAIZ / "data" / "oro"
CUARENTENA = RAIZ / "data" / "cuarentena"
PLATA = RAIZ / "data" / "plata"
SALIDAS = RAIZ / "laboratorio" / "salidas"
CALIDAD = RAIZ / "calidad"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
         "octubre", "noviembre", "diciembre"]


def mes_es(t) -> str:
    return f"{MESES[t.month - 1]} {t.year}"


st.set_page_config(page_title="Observatorio veterinario · Colima", page_icon="🐾", layout="wide")


@st.cache_data(ttl=3600)
def leer(ruta: Path, **kw) -> pd.DataFrame:
    return pd.read_csv(ruta, **kw)


vet = leer(ORO / "vet_ingresos_mensual.csv", parse_dates=["mes"])
usd = leer(ORO / "usd_mxn_mensual.csv", parse_dates=["mes"])
fut = leer(SALIDAS / "pronostico.csv", parse_dates=["mes"])
modelos = leer(SALIDAS / "comparacion_modelos.csv")
residuos = leer(SALIDAS / "residuos.csv")
bitacora = leer(CALIDAD / "bitacora_capturas.csv", parse_dates=["timestamp_utc"])

st.title("🐾 Observatorio veterinario de Colima")
st.caption(
    "Trusted Data Lab · Ingresos de servicios veterinarios para mascotas (INEGI, SCIAN 541941) "
    "y tipo de cambio (Banxico). Datos oficiales, limpiados y validados automáticamente."
)

ult = vet.iloc[-1]
hace_un_anio = vet[vet["mes"] == ult["mes"] - pd.DateOffset(years=1)]
var_anual = (ult["indice_ingresos"] / hace_un_anio["indice_ingresos"].iloc[0] - 1) * 100 \
    if not hace_un_anio.empty else None
ganador = modelos.sort_values("RMSE").iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric(f"Índice de ingresos ({mes_es(ult['mes'])})", f"{ult['indice_ingresos']:.1f}",
          f"{var_anual:+.1f}% vs. año anterior" if var_anual is not None else None)
c2.metric("Pronóstico próximo mes", f"{fut['mean'].iloc[0]:.1f}",
          f"IC 95%: {fut['inferior_95'].iloc[0]:.0f} a {fut['superior_95'].iloc[0]:.0f}", delta_color="off")
c3.metric("Dólar FIX (último mes)", f"${usd['usd_media'].iloc[-1]:.2f}")
c4.metric("Última captura", f"{bitacora['timestamp_utc'].max():%d/%m/%Y %H:%M} UTC")

tab_pron, tab_hist, tab_cal = st.tabs(["Pronóstico", "Historia y dólar", "Calidad de los datos"])

# ---------------------------------------------------------------- Pronóstico
with tab_pron:
    st.subheader("¿Qué se espera para los ingresos veterinarios?")
    st.info(
        f"**En palabras simples:** para {mes_es(fut['mes'].iloc[0])} esperamos un índice de ingresos "
        f"cercano a **{fut['mean'].iloc[0]:.0f}** puntos (2018 = 100). Con 95 % de confianza estará "
        f"entre **{fut['inferior_95'].iloc[0]:.0f} y {fut['superior_95'].iloc[0]:.0f}**. "
        f"Mientras más lejos el mes, más ancho el rango: para {mes_es(fut['mes'].iloc[-1])} va de "
        f"{fut['inferior_95'].iloc[-1]:.0f} a {fut['superior_95'].iloc[-1]:.0f}. "
        "El pronóstico es plano: el modelo no ve una tendencia clara a subir o bajar."
    )
    hist = vet[vet["mes"] >= vet["mes"].max() - pd.DateOffset(years=5)]
    base = alt.Chart(hist).mark_line(color="#2563eb").encode(
        x=alt.X("mes:T", title=None), y=alt.Y("indice_ingresos:Q", title="Índice (2018 = 100)",
                                                scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("mes:T", format="%b %Y"), alt.Tooltip("indice_ingresos:Q", format=".1f")],
    )
    banda = alt.Chart(fut).mark_area(opacity=0.2, color="#f97316").encode(
        x="mes:T", y="inferior_95:Q", y2="superior_95:Q")
    linea = alt.Chart(fut).mark_line(color="#f97316", strokeDash=[5, 3]).encode(
        x="mes:T", y="mean:Q",
        tooltip=[alt.Tooltip("mes:T", format="%b %Y"),
                 alt.Tooltip("mean:Q", format=".1f", title="pronóstico"),
                 alt.Tooltip("inferior_95:Q", format=".1f"), alt.Tooltip("superior_95:Q", format=".1f")])
    st.altair_chart(base + banda + linea, width="stretch")
    st.caption("Azul: datos reales de INEGI. Naranja: pronóstico con su intervalo de 95 %.")

    st.markdown("#### ¿Por qué este modelo?")
    st.write(
        f"Probamos cuatro modelos y escondimos los últimos 12 meses para ver cuál acertaba mejor en "
        f"datos que no conocía. Ganó **{ganador['modelo']}**: se equivocó en promedio "
        f"{ganador['MAE']:.1f} puntos ({ganador['MAPE']:.1f} %)."
    )
    st.dataframe(
        modelos[["modelo", "MAE", "RMSE", "MAPE", "AIC"]].sort_values("RMSE").round(2),
        hide_index=True, width="stretch",
    )
    r = residuos.iloc[0]
    if not bool(r["pasa"]):
        st.warning(
            f"**Advertencia estadística (puerta 3):** los errores del modelo todavía muestran un patrón "
            f"(prueba de Ljung-Box, p = {r['ljung_box_p']:.5f}). El pronóstico es útil como referencia, "
            "pero el intervalo puede quedarse corto. Estamos probando modelos que capturen ese patrón."
        )

# ---------------------------------------------------------------- Historia
with tab_hist:
    st.subheader("Ingresos veterinarios desde 2008")
    st.line_chart(vet.set_index("mes")["indice_ingresos"], height=280)
    st.subheader("Tipo de cambio promedio mensual (MXN por USD)")
    st.caption("Importa porque buena parte de medicamentos, vacunas y alimento para mascotas se importa.")
    st.line_chart(usd.set_index("mes")["usd_media"], height=240)

# ---------------------------------------------------------------- Calidad
with tab_cal:
    st.subheader("Puerta de calidad: ¿cuántos datos se rechazaron?")
    filas = []
    for fuente, archivo in [("banxico", "banxico_diario.csv"), ("inegi", "inegi_mensual.csv")]:
        ok = len(leer(PLATA / archivo))
        malos = len(leer(CUARENTENA / f"{fuente}_rechazados.csv"))
        filas.append({"fuente": fuente, "aprobados": ok, "en cuarentena": malos,
                      "tasa de rechazo %": round(100 * malos / max(ok + malos, 1), 2)})
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    st.caption("Ningún registro se borra en silencio: los rechazados se guardan con su motivo. "
               "Si se rechaza más de 5 %, el pipeline se detiene.")

    st.subheader("Bitácora de capturas automáticas")
    st.dataframe(bitacora.sort_values("timestamp_utc", ascending=False), hide_index=True,
                 width="stretch")
    fiab = CALIDAD / "fiabilidad.csv"
    if fiab.exists():
        st.subheader("Fiabilidad medida")
        st.dataframe(leer(fiab), hide_index=True, width="stretch")
        st.caption("La captura programada empezó el 13 de noviembre de 2026; la medición de 7 días "
                   "estará lista el 20 de noviembre.")
