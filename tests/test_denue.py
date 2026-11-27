"""Pruebas de la fuente especializada INEGI DENUE, calidad espacial y cero datos personales."""
import pandas as pd

from extractores.denue import sanitizar_privacidad
from pipeline.limpieza import validar_denue
from pipeline.oro import procesar_denue_oro


def test_denue_cero_datos_personales():
    """Verifica que se cumpla la LFPDPPP descartando campos de personas físicas."""
    datos = pd.DataFrame([{
        "id_denue": "999",
        "nombre_comercial": "Veterinaria Prueba",
        "nombre_propietario": "Juan Pérez",
        "telefono_particular": "3121234567",
        "correo_personal": "juan@gmail.com",
    }])
    limpio = sanitizar_privacidad(datos)
    assert "nombre_propietario" not in limpio.columns
    assert "telefono_particular" not in limpio.columns
    assert "correo_personal" not in limpio.columns
    assert "nombre_comercial" in limpio.columns


def test_denue_puerta_calidad_aprueba_registros_validos():
    """Un registro de Colima con coordenadas válidas debe ser aprobado."""
    valido = pd.DataFrame([{
        "id_denue": "1001",
        "nombre_comercial": "Clínica Colima",
        "codigo_actividad": "541941",
        "municipio": "Colima",
        "latitud": 19.245,
        "longitud": -103.725,
        "estrato_personal": "0 a 5 personas",
    }])
    ok, malos = validar_denue(valido)
    assert len(ok) == 1
    assert malos.empty


def test_denue_puerta_calidad_cuarentena_coordenadas_fuera_de_rango():
    """Registros con coordenadas fuera de Colima o nulas van a cuarentena con su motivo."""
    df = pd.DataFrame([
        {
            "id_denue": "1002",
            "nombre_comercial": "Vet CDMX",
            "codigo_actividad": "541941",
            "municipio": "Colima",
            "latitud": 19.43,
            "longitud": -99.13,  # Fuera de Colima
            "estrato_personal": "0 a 5 personas",
        },
        {
            "id_denue": "1003",
            "nombre_comercial": "Vet Sin Coordenadas",
            "codigo_actividad": "541941",
            "municipio": "Colima",
            "latitud": None,
            "longitud": None,
            "estrato_personal": "0 a 5 personas",
        },
    ])
    ok, malos = validar_denue(df)
    assert len(ok) == 0
    assert len(malos) == 2
    assert "fuera_de_rango_colima" in malos.loc[0, "motivo_rechazo"]
    assert "latitud_o_longitud_nula" in malos.loc[1, "motivo_rechazo"]


def test_denue_procesamiento_oro_y_zonas():
    """Verifica la asignación de zonas funcionales y categorías estandarizadas."""
    df_plata = pd.DataFrame([
        {
            "id_denue": "101",
            "nombre_comercial": "Vet Centro",
            "codigo_actividad": "541941",
            "municipio": "Colima",
            "latitud": 19.24,
            "longitud": -103.72,
            "estrato_personal": "0 a 5 personas",
            "archivo_bronce_origen": "denue_test.csv",
            "capturado_en": "2026-11-23T10:00:00",
        },
        {
            "id_denue": "102",
            "nombre_comercial": "Pet Shop Puerto",
            "codigo_actividad": "461121",
            "municipio": "Manzanillo",
            "latitud": 19.10,
            "longitud": -104.32,
            "estrato_personal": "0 a 5 personas",
            "archivo_bronce_origen": "denue_test.csv",
            "capturado_en": "2026-11-23T10:00:00",
        },
    ])
    geo_oro, resumen = procesar_denue_oro(df_plata)
    assert geo_oro.loc[0, "zona_urbana"] == "Metropolitana Colima-Villa de Álvarez"
    assert geo_oro.loc[1, "zona_urbana"] == "Costera Manzanillo"
    assert "Clínica Veterinaria" in geo_oro.loc[0, "categoria_servicio"]
    assert "Pet Shop" in geo_oro.loc[1, "categoria_servicio"]
    assert len(resumen) == 2
