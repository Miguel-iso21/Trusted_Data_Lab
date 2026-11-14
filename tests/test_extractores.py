"""Pruebas de extractores sin red: las respuestas HTTP son simuladas."""
import urllib.robotparser

import pandas as pd
import pytest

from extractores import banxico, base, inegi

PAYLOAD_BANXICO = {
    "bmx": {"series": [{"idSerie": "SF43718", "datos": [{"fecha": "02/01/2024", "dato": "16.9"}]}]}
}
PAYLOAD_INEGI = {
    "Series": [
        {
            "INDICADOR": "716898",
            "OBSERVATIONS": [
                {"TIME_PERIOD": "2024/02", "OBS_VALUE": "120.5"},
                {"TIME_PERIOD": "2024/01", "OBS_VALUE": "118.0"},
            ],
        }
    ]
}


class RespuestaFalsa:
    def __init__(self, payload, status=200, url="http://x"):
        self._payload, self.status_code, self.url = payload, status, url

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class ExtractorFalso:
    def __init__(self, payload):
        self.payload, self.urls = payload, []

    def get(self, url, **kwargs):
        self.urls.append(url)
        return RespuestaFalsa(self.payload, url=url)


# ---------- base ----------
def _extractor_con_reglas(reglas: list[str]) -> base.ExtractorEtico:
    ex = base.ExtractorEtico(pausa=0)
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(reglas)
    ex._reglas = lambda url: rp
    return ex


def test_base_bloquea_lo_que_robots_prohibe():
    ex = _extractor_con_reglas(["User-agent: *", "Disallow: /privado"])
    with pytest.raises(PermissionError):
        ex.get("https://sitio.mx/privado/datos")


def test_base_reintenta_ante_500_y_luego_responde(monkeypatch):
    monkeypatch.setattr(base.time, "sleep", lambda s: None)
    ex = _extractor_con_reglas(["User-agent: *", "Allow: /"])
    respuestas = iter([RespuestaFalsa({}, 500), RespuestaFalsa({"ok": 1}, 200)])
    ex.sesion.get = lambda url, timeout, **kw: next(respuestas)
    assert ex.get("https://sitio.mx/api").json() == {"ok": 1}


def test_base_se_rinde_tras_varios_intentos(monkeypatch):
    monkeypatch.setattr(base.time, "sleep", lambda s: None)
    ex = _extractor_con_reglas(["User-agent: *", "Allow: /"])
    ex.sesion.get = lambda url, timeout, **kw: RespuestaFalsa({}, 429)
    with pytest.raises(RuntimeError):
        ex.get("https://sitio.mx/api", intentos=2)


def test_base_se_identifica_con_user_agent():
    assert "TDL-Observatorio" in base.ExtractorEtico().sesion.headers["User-Agent"]


# ---------- banxico ----------
def test_banxico_sin_token_falla(monkeypatch):
    monkeypatch.delenv("BANXICO_TOKEN", raising=False)
    with pytest.raises(RuntimeError):
        banxico.capturar("reciente", ExtractorFalso(PAYLOAD_BANXICO))


def test_banxico_modo_invalido(monkeypatch):
    monkeypatch.setenv("BANXICO_TOKEN", "x")
    with pytest.raises(ValueError):
        banxico.capturar("otro", ExtractorFalso(PAYLOAD_BANXICO))


def test_banxico_main_guarda_en_bronce_y_bitacora(monkeypatch, tmp_path):
    monkeypatch.setenv("BANXICO_TOKEN", "x")
    monkeypatch.setattr(banxico, "BRONCE", tmp_path / "bronce")
    monkeypatch.setattr(banxico, "BITACORA", tmp_path / "bitacora.csv")
    monkeypatch.setattr(banxico, "ExtractorEtico", lambda: ExtractorFalso(PAYLOAD_BANXICO))
    assert banxico.main("historico") == 0
    assert len(list((tmp_path / "bronce" / "banxico").glob("*.csv"))) == 1
    assert pd.read_csv(tmp_path / "bitacora.csv")["estado"].tolist() == ["ok"]


def test_banxico_main_registra_falla(monkeypatch, tmp_path):
    monkeypatch.delenv("BANXICO_TOKEN", raising=False)
    monkeypatch.setattr(banxico, "BITACORA", tmp_path / "bitacora.csv")
    assert banxico.main("reciente") == 1
    assert pd.read_csv(tmp_path / "bitacora.csv")["estado"].tolist() == ["falla"]


# ---------- inegi ----------
def test_inegi_parser_ordena_y_convierte_fechas():
    df = inegi.parsear(PAYLOAD_INEGI, "http://x/<TOKEN>")
    assert df["fecha"].tolist() == ["2024-01-01", "2024-02-01"]
    assert df["valor"].tolist() == [118.0, 120.5]


def test_inegi_main_no_escribe_el_token(monkeypatch, tmp_path):
    monkeypatch.setenv("INEGI_TOKEN", "SECRETO123")
    monkeypatch.setattr(inegi, "BRONCE", tmp_path / "bronce")
    monkeypatch.setattr(inegi, "BITACORA", tmp_path / "bitacora.csv")
    monkeypatch.setattr(inegi, "ExtractorEtico", lambda: ExtractorFalso(PAYLOAD_INEGI))
    assert inegi.main() == 0
    archivo = next((tmp_path / "bronce" / "inegi").glob("*.csv"))
    assert "SECRETO123" not in archivo.read_text(encoding="utf-8")


def test_inegi_main_oculta_token_en_errores(monkeypatch, tmp_path):
    monkeypatch.setenv("INEGI_TOKEN", "SECRETO123")
    monkeypatch.setattr(inegi, "BITACORA", tmp_path / "bitacora.csv")

    def falla():
        raise RuntimeError("400 para url .../SECRETO123?type=json")

    monkeypatch.setattr(inegi, "capturar", falla)
    assert inegi.main() == 1
    assert "SECRETO123" not in (tmp_path / "bitacora.csv").read_text(encoding="utf-8")
