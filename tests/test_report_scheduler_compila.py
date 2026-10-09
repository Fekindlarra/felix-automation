"""Bloqueante 3.4.8: backend/report_scheduler.py tenía 'await' dentro de una
función síncrona (SyntaxError). El callback debe ejecutarse y notificar."""
import asyncio
from unittest.mock import MagicMock, patch

import backend.report_scheduler as rs


def test_callback_semanal_notifica_sin_error_de_sintaxis():
    notif = MagicMock()
    notif.notify_alert = MagicMock(side_effect=lambda **kw: asyncio.sleep(0))

    sched = rs.ReportScheduler.__new__(rs.ReportScheduler)
    sched.agent = MagicMock()
    sched.agent.generate_weekly_report.return_value = {"status": "ok", "pdf_file": "x.pdf"}

    with patch("backend.notifications.get_notification_service", return_value=notif):
        sched._generate_weekly()

    notif.notify_alert.assert_called_once()
