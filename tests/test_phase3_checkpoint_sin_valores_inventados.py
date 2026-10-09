"""Bloqueante 3.4.9: el monitor de Phase 3 no debe inventar métricas.

Si una métrica no tiene dato, collect_metrics lanza MetricsCollectionError y
collect_checkpoint no emite checkpoint (None). Nunca se devuelven valores
fijos como 0.78, 0.0008, 45.0, 42, 140 u 8, ni un checkpoint que "pase".
"""
import sqlite3

import pytest

from backend.phase3_checkpoint_monitor import MetricsCollectionError, Phase3CheckpointMonitor


def _monitor_con_bd_vacia():
    m = Phase3CheckpointMonitor(db_path=":memory:")
    m.db = sqlite3.connect(":memory:")
    m.db.row_factory = sqlite3.Row  # sin tablas: las consultas fallan
    return m


def test_sin_datos_collect_metrics_lanza_error():
    with pytest.raises(MetricsCollectionError):
        _monitor_con_bd_vacia().collect_metrics()


def test_sin_datos_collect_checkpoint_no_emite_checkpoint():
    assert _monitor_con_bd_vacia().collect_checkpoint(48) is None
