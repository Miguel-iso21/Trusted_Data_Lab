"""Tablero público del Observatorio veterinario de Colima (Streamlit).

Solo LEE archivos ya generados por el pipeline y el laboratorio; no llama APIs.
Incluye visualización cartográfica geoespacial (INEGI DENUE) y linaje de datos.
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

MESES = [
    "enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre",
    "octubre", "noviembre", "diciembre"
]


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

denue_geo_path = ORO / "denue_colima_geo.csv"
denue = leer(denue_geo_path) if denue_geo_path.exists() else pd.DataFrame()

denue_resumen_path = ORO / "denue_resumen_municipal.csv"
resumen_muni = leer(denue_resumen_path) if denue_resumen_path.exists() else pd.DataFrame()

st.title("🐾 Observatorio veterinario de Colima")
st.caption(
    "Trusted Data Lab · Ingresos de servicios veterinarios para mascotas (INEGI, SCIAN 541941), "
    "tipo de cambio (Banxico) y directorio geoespacial de clínicas y servicios de mascotas (INEGI DENUE). "
    "Datos oficiales con trazabilidad completa de Bronce a Oro y puerta de calidad."
)

ult = vet.iloc[-1]
hace_un_anio = vet[vet["mes"] == ult["mes"] - pd.DateOffset(years=1)]
var_anual = (
    (ult["indice_ingresos"] / hace_un_anio["indice_ingresos"].iloc[0] - 1) * 100
    if not hace_un_anio.empty
    else None
)
ganador = modelos.sort_values("RMSE").iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric(
    f"Índice de ingresos ({mes_es(ult['mes'])})",
    f"{ult['indice_ingresos']:.1f}",
    f"{var_anual:+.1f}% vs. año anterior" if var_anual is not None else None,
)
c2.metric(
    "Pronóstico próximo mes",
    f"{fut['mean'].iloc[0]:.1f}",
    f"IC 95%: {fut['inferior_95'].iloc[0]:.0f} a {fut['superior_95'].iloc[0]:.0f}",
    delta_color="off",
)
c3.metric("Dólar FIX (último mes)", f"${usd['usd_media'].iloc[-1]:.2f}")
c4.metric("Última captura", f"{bitacora['timestamp_utc'].max():%d/%m/%Y %H:%M} UTC")

tab_pron, tab_hist, tab_geo, tab_cal = st.tabs([
    "Pronóstico",
    "Historia y dólar",
    "Mapa geoespacial (DENUE)",
    "Calidad y linaje",
])

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
        x=alt.X("mes:T", title=None),
        y=alt.Y("indice_ingresos:Q", title="Índice (2018 = 100)", scale=alt.Scale(zero=False)),
        tooltip=[alt.Tooltip("mes:T", format="%b %Y"), alt.Tooltip("indice_ingresos:Q", format=".1f")],
    )
    banda = alt.Chart(fut).mark_area(opacity=0.2, color="#f97316").encode(
        x="mes:T", y="inferior_95:Q", y2="superior_95:Q"
    )
    linea = alt.Chart(fut).mark_line(color="#f97316", strokeDash=[5, 3]).encode(
        x="mes:T",
        y="mean:Q",
        tooltip=[
            alt.Tooltip("mes:T", format="%b %Y"),
            alt.Tooltip("mean:Q", format=".1f", title="pronóstico"),
            alt.Tooltip("inferior_95:Q", format=".1f"),
            alt.Tooltip("superior_95:Q", format=".1f"),
        ],
    )
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
        hide_index=True,
        width="stretch",
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

# ---------------------------------------------------------------- Geoespacial
with tab_geo:
    st.subheader("🗺️ Oferta geoespacial de servicios veterinarios y mascotas en Colima")
    st.info(
        "**Fuente especializada (E2):** INEGI DENUE georreferenciado mediante GeoPandas (EPSG:4326). "
        "Permite identificar la concentración de clínicas veterinarias, farmacias/alimentos y estéticas "
        "caninas en las tres principales zonas urbanas: Zona Metropolitana Colima-Villa de Álvarez, "
        "Costera (Manzanillo) y Valle Tecomán-Armería. **Cero datos personales:** solo unidades económicas públicas."
    )

    if not denue.empty:
        col_filtro1, col_filtro2, col_filtro3 = st.columns(3)
        with col_filtro1:
            municipios_unicos = ["Todos"] + sorted(denue["municipio"].unique().tolist())
            muni_sel = st.selectbox("Filtrar por municipio:", municipios_unicos)
        with col_filtro2:
            categorias_unicas = ["Todas"] + sorted(denue["categoria_servicio"].unique().tolist())
            cat_sel = st.selectbox("Filtrar por categoría:", categorias_unicas)
        with col_filtro3:
            zonas_unicas = ["Todas"] + sorted(denue["zona_urbana"].unique().tolist())
            zona_sel = st.selectbox("Filtrar por zona funcional:", zonas_unicas)

        df_mapa = denue.copy()
        if muni_sel != "Todos":
            df_mapa = df_mapa[df_mapa["municipio"] == muni_sel]
        if cat_sel != "Todas":
            df_mapa = df_mapa[df_mapa["categoria_servicio"] == cat_sel]
        if zona_sel != "Todas":
            df_mapa = df_mapa[df_mapa["zona_urbana"] == zona_sel]

        st.markdown(f"**Establecimientos visualizados:** {len(df_mapa)} de {len(denue)}")
        st.map(df_mapa[["latitud", "longitud"]], zoom=10)

        st.subheader("Distribución municipal de la oferta")
        chart_muni = (
            alt.Chart(df_mapa)
            .mark_bar()
            .encode(
                x=alt.X("municipio:N", title="Municipio", sort="-y"),
                y=alt.Y("count():Q", title="Número de establecimientos"),
                color=alt.Color("categoria_servicio:N", title="Categoría", scale=alt.Scale(scheme="category10")),
                tooltip=["municipio:N", "categoria_servicio:N", "count():Q"],
            )
        )
        st.altair_chart(chart_muni, width="stretch")

        st.subheader("Directorio detallado con trazabilidad")
        st.dataframe(
            df_mapa[[
                "id_denue",
                "nombre_comercial",
                "categoria_servicio",
                "municipio",
                "estrato_personal",
                "zona_urbana",
                "archivo_bronce_origen",
                "fecha_ingesta",
            ]],
            hide_index=True,
            width="stretch",
        )

        if not resumen_muni.empty:
            st.subheader("Resumen consolidado por municipio")
            st.dataframe(resumen_muni, hide_index=True, width="stretch")
    else:
        st.warning("No se encontró el dataset geoespacial en la capa oro. Ejecute el pipeline.")

# ---------------------------------------------------------------- Calidad
with tab_cal:
    st.subheader("Puerta de calidad: ¿cuántos datos se rechazaron?")
    fuentes_check = [
        ("banxico", "banxico_diario.csv", "banxico_rechazados.csv"),
        ("inegi", "inegi_mensual.csv", "inegi_rechazados.csv"),
    ]
    if (PLATA / "denue_colima.csv").exists():
        fuentes_check.append(("denue", "denue_colima.csv", "denue_rechazados.csv"))

    filas = []
    for fuente, arch_ok, arch_malos in fuentes_check:
        ruta_ok = PLATA / arch_ok
        ruta_malos = CUARENTENA / arch_malos
        ok = len(leer(ruta_ok)) if ruta_ok.exists() else 0
        malos = len(leer(ruta_malos)) if ruta_malos.exists() else 0
        filas.append({
            "fuente": fuente,
            "aprobados (plata)": ok,
            "en cuarentena": malos,
            "tasa de rechazo %": round(100 * malos / max(ok + malos, 1), 2),
        })
    st.dataframe(pd.DataFrame(filas), hide_index=True, width="stretch")
    st.caption(
        "Ningún registro se borra en silencio: los rechazados se guardan con su motivo en data/cuarentena/. "
        "Si se rechaza más de 5 %, el pipeline se detiene automáticamente."
    )

    st.subheader("🔗 Linaje y trazabilidad de datos (Capa Oro a Bronce)")
    st.info(
        "Cada registro en la Capa Oro es 100 % rastreable hasta su archivo original en la Capa Bronce, "
        "su fecha de ingesta en UTC y su identificador de proveedor oficial, cumpliendo con la gobernanza de datos."
    )
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.markdown("**Tipo de Cambio (Banxico SIE):**")
        st.dataframe(usd[["mes", "usd_media", "archivo_bronce_origen", "fecha_ingesta"]].tail(3), hide_index=True)
    with col_l2:
        st.markdown("**Ingresos Veterinarios (INEGI BISE):**")
        st.dataframe(vet[["mes", "indice_ingresos", "archivo_bronce_origen", "fecha_ingesta"]].tail(3), hide_index=True)
    with col_l3:
        st.markdown("**Directorio Geoespacial (INEGI DENUE):**")
        if not denue.empty:
            st.dataframe(denue[["id_denue", "nombre_comercial", "archivo_bronce_origen", "fecha_ingesta"]].head(3), hide_index=True)

    st.subheader("Bitácora de capturas automáticas")
    st.dataframe(bitacora.sort_values("timestamp_utc", ascending=False), hide_index=True, width="stretch")

    fiab = CALIDAD / "fiabilidad.csv"
    if fiab.exists():
        st.subheader("Fiabilidad y disponibilidad medida")
        st.dataframe(leer(fiab), hide_index=True, width="stretch")
        st.caption("Medición continua calculada a partir de la bitácora real de ejecuciones automáticas.")
