"""Bloqueante 3.4.9: el monitor de Phase 3 no debe inventar métricas.
Si no hay dato, el checkpoint debe fallar (cerrado), no pasar con valores fijos
como 0.78, 0.0008, 45.0, 42, 140 u 8."""
import sqlite3

from backend.phase3_checkpoint_monitor import Phase3CheckpointMonitor


def _monitor_con_bd_vacia():
    m = Phase3CheckpointMonitor(db_path=":memory:")
    m.db = sqlite3.connect(":memory:")
    m.db.row_factory = sqlite3.Row  # sin tablas: las consultas fallan
    return m


def test_sin_datos_no_inventa_metricas():
    snap = _monitor_con_bd_vacia().collect_metrics()
    assert snap.ml_accuracy != 0.78
    assert snap.error_rate != 0.0008
    assert snap.websocket_latency != 45.0
    assert snap.predictions_hour != 42
    assert snap.personalization_active != 140
    assert snap.active_tests != 8


def test_sin_datos_el_checkpoint_no_pasa():
    snap = _monitor_con_bd_vacia().collect_metrics()
    assert snap.health_score() < 6
