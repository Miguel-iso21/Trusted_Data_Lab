# Manual de Linaje y Trazabilidad de Datos (Capa Oro a Bronce)

**Observatorio Veterinario de Colima · Trusted Data Lab (TecNM 2026)**  
Entrega E2 · Versión 1.0 · Fecha: 23 de noviembre de 2026  
Equipo: José Miguel Castellanos (Data Engineer) · Leonardo Rodríguez García (Data Statistician)

---

## 1. Arquitectura de Linaje en la Arquitectura Medallion

Para garantizar la integridad y confiabilidad requeridas por la certificación **Sello TDL** y la norma **ISO/IEC 25012** (Calidad de Datos - Trazabilidad y Credibilidad), el observatorio implementa una trazabilidad bidireccional estricta en cada una de sus tres capas de almacenamiento:

```
[ Capa Bronce: Crudo ]
├── data/bronce/banxico/reciente_*.csv
├── data/bronce/inegi/indicadores_*.csv
└── data/bronce/denue/denue_colima_*.csv
         │
         │ (Puerta de Calidad 1: esquema, rangos, formato, sanitización de privacidad)
         ▼
[ Capa Plata: Limpio y Validado ]
├── data/plata/banxico_diario.csv
├── data/plata/inegi_mensual.csv
├── data/plata/denue_colima.csv & denue_colima.geojson
└── data/cuarentena/*_rechazados.csv (con motivo explícito)
         │
         │ (Transformación analítica, agregación mensual, normalización, enriquecimiento espacial)
         ▼
[ Capa Oro: Analítica Certificada ]
├── data/oro/usd_mxn_mensual.csv      <-- Conserva origen, ingesta y fuente
├── data/oro/vet_ingresos_mensual.csv  <-- Conserva origen, ingesta y fuente
├── data/oro/denue_colima_geo.csv     <-- Conserva id_denue, origen, ingesta y coordenadas
├── data/oro/denue_resumen_municipal.csv
└── data/oro/diccionario_oro.csv
```

---

## 2. Metadatos Obligatorios de Linaje por Registro

A diferencia de los enfoques donde el linaje se pierde tras la agregación o la limpieza, en este observatorio **cada registro individual de la Capa Oro porta sus metadatos de linaje de origen**:

| Campo de Linaje | Tipo | Descripción | Ejemplo de Valor |
|---|---|---|---|
| `archivo_bronce_origen` | `string` | Nombre exacto del archivo CSV en `data/bronce/` del que proviene el dato original. | `indicadores_20261122T203557.csv` |
| `fecha_ingesta` | `ISO 8601 UTC` | Marca de tiempo precisa de cuándo el extractor obtuvo el dato de la API oficial. | `2026-11-22T20:35:57+00:00` |
| `fuente_origen` | `string` | Identificador estandarizado de la fuente y servicio de procedencia. | `inegi-bise`, `banxico-sie`, `inegi-denue` |
| `id_denue` (en DENUE) | `string/int` | Identificador único asignado por el INEGI al establecimiento económico. | `10101` |

---

## 3. Matriz de Linaje por Dataset en Capa Oro

### 3.1. `data/oro/vet_ingresos_mensual.csv`
- **Origen en Bronce:** Archivos `data/bronce/inegi/indicadores_*.csv`.
- **Ruta de Transformación:** 
  1. Bronce: Se almacena la observación mensual original (`OBS_VALUE`) con indicador 716898.
  2. Plata: Se valida formato de fecha `YYYY-MM-DD`, que la serie no sea nula y que el valor esté en el rango $[10.0, 500.0]$. Si una misma fecha fue capturada en múltiples ejecuciones diarias, se conserva la captura más reciente. Se marcan atípicos con IQR ($k=1.5$).
  3. Oro: Se calculan las métricas normalizadas ($z$-score y min-max), se discretiza en terciles (`nivel`: bajo, medio, alto) y se inyecta la trazabilidad de `archivo_bronce_origen`, `fecha_ingesta` y `fuente_origen`.

### 3.2. `data/oro/usd_mxn_mensual.csv`
- **Origen en Bronce:** Archivos `data/bronce/banxico/reciente_*.csv` e `historico_*.csv`.
- **Ruta de Transformación:**
  1. Bronce: Datos diarios del tipo de cambio FIX (serie SF43718) con valores `N/E` en fines de semana o días inhábiles.
  2. Plata: Los registros con valor no numérico van a cuarentena; los válidos se validan en rango $[5.0, 50.0]$ y se marcan atípicos por IQR sin eliminarlos.
  3. Oro: Se agrupan los días hábiles de cada mes (`n_obs`), se calcula el promedio ponderado mensual (`usd_media`) y el cierre (`usd_cierre`), se excluye el mes en curso por estar incompleto y se asocia el último archivo y timestamp de ingesta en bronce del mes.

### 3.3. `data/oro/denue_colima_geo.csv` (Fuente Especializada E2)
- **Origen en Bronce:** Archivos `data/bronce/denue/denue_colima_*.csv`.
- **Ruta de Transformación:**
  1. Bronce: Extracción de unidades económicas de veterinarias, farmacias y estéticas de mascotas en Colima. Aplicación inmediata de la sanitización de privacidad (descarte de datos personales).
  2. Plata: Puerta de calidad espacial (`validar_denue`). Se comprueba que las coordenadas estén dentro del Bounding Box de Colima ($\text{lat} \in [18.5, 19.6]$, $\text{lon} \in [-104.8, -103.4]$) y pertenezcan a los 10 municipios reconocidos. Registros anómalos se canalizan a `data/cuarentena/denue_rechazados.csv` con causa detallada. Se construye la geometría espacial mediante GeoPandas (`EPSG:4326`).
  3. Oro: Clasificación funcional en zonas urbanas (`Metropolitana Colima-Villa de Álvarez`, `Costera Manzanillo`, `Valle Tecomán-Armería`, `Norte y Periférica`), asignación de categoría homogénea y conservación del ID DENUE y del archivo de bronce de origen.

---

## 4. Verificación de Trazabilidad y Reproducibilidad

Cualquier auditor externo o evaluador puede verificar el linaje ejecutando las pruebas automáticas o consultando el diccionario de datos:

```bash
# 1. Comprobación automatizada de linaje en toda la Capa Oro
pytest tests/test_linaje.py

# 2. Inspección del Diccionario de Datos en Capa Oro
head -n 25 data/oro/diccionario_oro.csv
```

El cumplimiento del 100 % en las pruebas confirma que no existen registros "huérfanos" en la Capa Oro: cada fila tiene un padre comprobable en la Capa Bronce.
