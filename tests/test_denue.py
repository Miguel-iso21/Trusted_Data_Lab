"""Pruebas de la fuente especializada INEGI DENUE, calidad espacial y cero datos personales."""
import pandas as pd
import pytest

from extractores import denue
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


# ---------- extractor (sin red: respuestas simuladas) ----------
class _Resp:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class _ExtractorFalso:
    """Devuelve 1 establecimiento por clase SCIAN y registra las URL pedidas."""

    def __init__(self):
        self.urls = []

    def get(self, url, **kwargs):
        self.urls.append(url)
        clase = url.split("/")[-6]  # .../{clase}/0/{inicio}/{fin}/0/{token}
        return _Resp([{
            "Id": f"9{clase}", "CLEE": "06002", "Nombre": "VETERINARIA DE PRUEBA",
            "Razon_social": "JUAN PEREZ LOPEZ", "Telefono": "3121234567", "Correo_e": "x@y.mx",
            "Sitio_internet": "www.x.mx", "Clase_actividad": "Servicios veterinarios",
            "CLASE_ACTIVIDAD_ID": clase, "Estrato": "0 a 5 personas",
            "Ubicacion": "VILLA DE ALVAREZ, Villa de Álvarez, COLIMA",
            "Latitud": "19.26", "Longitud": "-103.73",
        }])


def test_municipio_se_toma_de_ubicacion_y_se_normaliza():
    assert denue.municipio_de_ubicacion("MANZANILLO, Manzanillo, COLIMA") == "Manzanillo"
    assert denue.municipio_de_ubicacion("TECOMAN, tecoman, COLIMA") == "Tecomán"
    assert denue.municipio_de_ubicacion("X, Guadalajara, JALISCO") == "Guadalajara"


def test_capturar_sin_token_falla_sin_datos_de_respaldo(monkeypatch):
    monkeypatch.delenv("DENUE_TOKEN", raising=False)
    with pytest.raises(RuntimeError, match="DENUE_TOKEN"):
        denue.capturar(_ExtractorFalso())


def test_capturar_no_guarda_datos_personales_ni_el_token(monkeypatch):
    monkeypatch.setenv("DENUE_TOKEN", "SECRETO123")
    ex = _ExtractorFalso()
    df = denue.capturar(ex)
    assert len(df) == len(denue.DENUE_SECTORES)  # una consulta por clase SCIAN
    for col in ("Razon_social", "razon_social", "Telefono", "Correo_e", "Sitio_internet"):
        assert col not in df.columns
    texto = df.to_csv(index=False)
    assert "JUAN PEREZ" not in texto and "3121234567" not in texto and "SECRETO123" not in texto
    assert set(df["municipio"]) == {"Villa de Álvarez"}
    assert all("/06/" in u for u in ex.urls)  # siempre la entidad de Colima


def test_main_registra_falla_en_bitacora(monkeypatch, tmp_path):
    monkeypatch.delenv("DENUE_TOKEN", raising=False)
    monkeypatch.setattr(denue, "BITACORA", tmp_path / "bitacora.csv")
    assert denue.main() == 1
    assert pd.read_csv(tmp_path / "bitacora.csv")["estado"].tolist() == ["falla"]


def test_filtro_812990_conserva_solo_negocios_de_mascotas():
    nombres = ["ESTETICA CANINA PATITAS", "HOTEL CANINO REYES", "PET WORLD", "REFUGIO ANIMAL MANZANILLO",
               "LECTURA DE CARTAS SIN NOMBRE", "CAMINOS DE LA VIDA", "VITA MEDICINA ESTETICA"]
    df = pd.DataFrame({"nombre_comercial": nombres})
    quedan = denue.filtrar_por_nombre(df, "812990")["nombre_comercial"].tolist()
    assert quedan == nombres[:4]
    assert len(denue.filtrar_por_nombre(df, "541941")) == len(nombres)  # otras clases no se filtran
