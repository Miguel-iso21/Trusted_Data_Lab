# TDL · Observatorio veterinario de Colima

Observatorio de datos del proyecto integrador **Trusted Data Lab** (TecNM, 2026).
Observa el mercado de servicios veterinarios para mascotas y lo cruza con el tipo de cambio,
que encarece medicamentos, vacunas y alimento importados.

**Tablero público:** _pendiente_

## Qué observa

| Fuente | Qué captura | Frecuencia | Acceso |
|---|---|---|---|
| INEGI BISE, indicador 716898 | Ingresos de servicios veterinarios para mascotas (SCIAN 541941), índice 2018=100 | Mensual, desde 2008 | API con token |
| Banxico SIE, serie SF43718 | Tipo de cambio FIX MXN por USD | Diaria (días hábiles) | API con token |

## Arquitectura

```
extractores/   captura ética (robots.txt, User-Agent, pausa entre peticiones)
data/bronce/   datos crudos con fecha y origen de captura
data/plata/    limpios y validados (puerta de calidad)
data/oro/      listos para análisis + diccionario_oro.csv
data/cuarentena/  registros rechazados con su motivo
laboratorio/   pronóstico (descomposición, ADF, ACF/PACF, SES, Holt, Holt-Winters, ARIMA)
tablero/       tablero público en Streamlit (solo lee oro y salidas, no llama APIs)
calidad/       bitácora de capturas y registros PSP
.github/workflows/  captura diaria (08:00 Colima) e integración continua
```

## Cómo ejecutarlo

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/Mac: source .venv/bin/activate)
pip install -r requirements.txt

# Tokens gratuitos: https://www.banxico.org.mx/SieAPIRest/  y  https://www.inegi.org.mx/servicios/api_indicadores.html
set BANXICO_TOKEN=...            # Linux/Mac: export BANXICO_TOKEN=...
set INEGI_TOKEN=...
set TDL_CONTACTO=correo-del-equipo

python -m extractores.banxico reciente
python -m extractores.inegi
python -m pipeline.run           # bronce -> plata -> oro
python -m laboratorio.pronostico # resultados en laboratorio/salidas/
python -m pipeline.fiabilidad    # MTBF, MTTR y disponibilidad -> calidad/fiabilidad.csv
streamlit run tablero/app.py     # tablero en http://localhost:8501

pytest --cov                     # pruebas
ruff check .                     # linter
```

En GitHub, los tokens van como *secrets* del repositorio (`BANXICO_TOKEN`, `INEGI_TOKEN`)
y el contacto como variable (`TDL_CONTACTO`). Nunca se escriben en el código.
