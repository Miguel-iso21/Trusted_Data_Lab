"""El tablero carga sin errores con los datos reales del repositorio."""
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1] / "tablero" / "app.py"


def test_tablero_carga_sin_errores():
    pytest.importorskip("streamlit")
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert len(at.metric) == 4
    assert "95 %" in at.info[0].value
