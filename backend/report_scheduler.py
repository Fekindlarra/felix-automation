#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Report Scheduler - FASE 13 Day 4
Automatiza generación de reportes semanales/mensuales
"""

import sys
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

sys.path.insert(0, str(Path(__file__).parent.parent))

from felix.orchestration.orchestrator import FelixAutomationOrchestrator
from agents.report_generator_agent import ReportGeneratorAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReportScheduler:
    """Scheduler para reportes automáticos"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.orchestrator = FelixAutomationOrchestrator()
        self.orchestrator.connect_database()
        self.agent = ReportGeneratorAgent(self.orchestrator)
        logger.info("✅ Report Scheduler inicializado")

    def schedule_reports(self):
        """Programar reportes automáticos"""
        # Reporte semanal: Lunes a las 8:00 AM
        self.scheduler.add_job(
            self._generate_weekly,
            CronTrigger(day_of_week=0, hour=8, minute=0),
            id="weekly_report",
            name="Reporte Semanal",
            replace_existing=True
        )
        logger.info("📅 Reporte Semanal programado (Lunes 8:00 AM)")

        # Reporte mensual: 1er día del mes a las 9:00 AM
        self.scheduler.add_job(
            self._generate_monthly,
            CronTrigger(day=1, hour=9, minute=0),
            id="monthly_report",
            name="Reporte Mensual",
            replace_existing=True
        )
        logger.info("📅 Reporte Mensual programado (Día 1 del mes, 9:00 AM)")

        # Iniciar scheduler
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("🚀 Report Scheduler iniciado")

    def _generate_weekly(self):
        """Callback para reporte semanal"""
        try:
            logger.info("🔄 Generando reporte semanal programado...")
            result = self.agent.generate_weekly_report()

            if "status" not in result or result.get("status") != "failed":
                logger.info(f"✅ Reporte semanal generado: {result.get('pdf_file', 'N/A')}")

                # Emitir notificación
                try:
                    from backend.notifications import get_notification_service
                    notif_service = get_notification_service()

                    # Notificar a admin (client_id=0)
                    asyncio.run(notif_service.notify_alert(
                        title="📊 Reporte Semanal Disponible",
                        message=f"Tu reporte semanal está listo para revisar.",
                        alert_type="info",
                        client_id=0,
                        icon="📊"
                    ))
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo emitir notificación: {e}")
            else:
                logger.error(f"❌ Error generando reporte semanal: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ Error en callback semanal: {e}")

    def _generate_monthly(self):
        """Callback para reporte mensual"""
        try:
            logger.info("🔄 Generando reporte mensual programado...")
            result = self.agent.generate_monthly_report()

            if "status" not in result or result.get("status") != "failed":
                logger.info(f"✅ Reporte mensual generado: {result.get('pdf_file', 'N/A')}")

                # Emitir notificación
                try:
                    from backend.notifications import get_notification_service
                    notif_service = get_notification_service()

                    # Notificar a admin (client_id=0)
                    asyncio.run(notif_service.notify_alert(
                        title="📊 Reporte Mensual Disponible",
                        message=f"Tu análisis mensual completo está listo.",
                        alert_type="info",
                        client_id=0,
                        icon="📊"
                    ))
                except Exception as e:
                    logger.warning(f"⚠️ No se pudo emitir notificación: {e}")
            else:
                logger.error(f"❌ Error generando reporte mensual: {result.get('error')}")
        except Exception as e:
            logger.error(f"❌ Error en callback mensual: {e}")

    def stop(self):
        """Detener scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("⏹️ Report Scheduler detenido")

    def get_jobs(self):
        """Obtener trabajos programados"""
        return self.scheduler.get_jobs()


# Instancia global
_report_scheduler = None


def get_report_scheduler():
    """Obtener instancia global del scheduler"""
    global _report_scheduler
    if _report_scheduler is None:
        _report_scheduler = ReportScheduler()
    return _report_scheduler


def main():
    """Testing del scheduler"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║         REPORT SCHEDULER                                      ║
║    Automatiza generación de reportes semanales/mensuales      ║
╚════════════════════════════════════════════════════════════════╝
    """)

    scheduler = get_report_scheduler()
    scheduler.schedule_reports()

    print("\n✅ Report Scheduler configurado:")
    for job in scheduler.get_jobs():
        print(f"  • {job.name}: {job.trigger}")

    print("\n⏳ Scheduler corriendo... (Presiona Ctrl+C para detener)")

    try:
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n⏹️ Deteniendo scheduler...")
        scheduler.stop()
        print("✅ Scheduler detenido")


if __name__ == "__main__":
    main()
