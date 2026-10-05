#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PASO 2: Analytics Scheduler
APScheduler integration for automated analytics runs and notifications
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job
import json
import sqlite3

logger = logging.getLogger(__name__)


class AnalyticsScheduler:
    """Manages automated analytics runs and notifications"""

    def __init__(self, orchestrator=None, sendgrid_api_key: str = None):
        """
        Initialize Analytics Scheduler

        Args:
            orchestrator: FelixAutomationOrchestrator instance
            sendgrid_api_key: SendGrid API key for email notifications
        """
        self.orchestrator = orchestrator
        self.sendgrid_api_key = sendgrid_api_key
        self.scheduler = BackgroundScheduler()
        self.jobs_tracking = {}
        self.notification_threshold = {
            'CRITICAL': True,  # Always notify
            'HIGH': True,
            'MEDIUM': False,
            'LOW': False
        }

    def start(self):
        """Start the scheduler"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Analytics Scheduler started")

    def stop(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("🛑 Analytics Scheduler stopped")

    def add_daily_analysis(self, hour: int = 8, minute: int = 0):
        """
        Schedule daily analysis run

        Args:
            hour: Hour to run (0-23)
            minute: Minute to run (0-59)
        """
        trigger = CronTrigger(hour=hour, minute=minute)
        job = self.scheduler.add_job(
            self._run_daily_analysis,
            trigger=trigger,
            id='daily_analytics',
            name='Daily Analytics Run',
            misfire_grace_time=600,
            replace_existing=True
        )
        logger.info(f"📅 Daily analysis scheduled for {hour:02d}:{minute:02d}")
        return job

    def add_weekly_analysis(self, day_of_week: int = 0, hour: int = 8):
        """
        Schedule weekly analysis run

        Args:
            day_of_week: Day of week (0=Monday, 6=Sunday)
            hour: Hour to run
        """
        trigger = CronTrigger(day_of_week=day_of_week, hour=hour, minute=0)
        job = self.scheduler.add_job(
            self._run_weekly_analysis,
            trigger=trigger,
            id='weekly_analytics',
            name='Weekly Analytics Run',
            misfire_grace_time=600,
            replace_existing=True
        )
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        logger.info(f"📆 Weekly analysis scheduled for {days[day_of_week]} at {hour:02d}:00")
        return job

    def run_analysis_now(self, analysis_type: str = 'full') -> Dict:
        """
        Trigger immediate analysis run

        Args:
            analysis_type: 'full', 'quick', or 'custom'

        Returns:
            Dict with job metadata and results
        """
        try:
            logger.info(f"🚀 Starting immediate {analysis_type} analysis run")
            result = self._execute_analysis(analysis_type)
            return result
        except Exception as e:
            logger.error(f"❌ Immediate analysis failed: {str(e)}")
            return {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _run_daily_analysis(self):
        """Execute daily analysis job"""
        logger.info("📅 Executing daily analysis run...")
        return self._execute_analysis('daily')

    def _run_weekly_analysis(self):
        """Execute weekly analysis job"""
        logger.info("📆 Executing weekly analysis run...")
        return self._execute_analysis('weekly')

    def _execute_analysis(self, analysis_type: str) -> Dict:
        """
        Core analysis execution logic

        Args:
            analysis_type: Type of analysis to run

        Returns:
            Analysis results dict
        """
        try:
            start_time = datetime.now()

            if not self.orchestrator:
                logger.warning("⚠️ Orchestrator not available for analysis")
                return self._empty_analysis_result(analysis_type, 'no_orchestrator')

            # Import here to avoid circular imports
            from analytics.dashboard_integration import DashboardIntegration

            dashboard = DashboardIntegration(self.orchestrator)
            analysis_data = dashboard.generate_dashboard_data()

            execution_time = (datetime.now() - start_time).total_seconds()

            # Store job history
            job_id = self._store_job_history(
                analysis_type=analysis_type,
                status='success',
                execution_time=execution_time,
                data=analysis_data
            )

            # Check for anomalies requiring notification
            anomalies = analysis_data.get('anomalies', {}).get('active', [])
            critical_anomalies = [
                a for a in anomalies
                if a.get('severity') == 'CRITICAL'
            ]

            # Send notifications if critical anomalies found
            if critical_anomalies and self.sendgrid_api_key:
                self._send_critical_anomaly_notification(
                    analysis_data, critical_anomalies, job_id
                )

            logger.info(
                f"✅ Analysis completed in {execution_time:.2f}s "
                f"({len(anomalies)} anomalies, {len(critical_anomalies)} critical)"
            )

            return {
                'job_id': job_id,
                'status': 'success',
                'analysis_type': analysis_type,
                'execution_time': execution_time,
                'timestamp': start_time.isoformat(),
                'summary': {
                    'total_predictions': len(analysis_data.get('predictions', {}).get('top_10', [])),
                    'total_anomalies': len(anomalies),
                    'critical_anomalies': len(critical_anomalies),
                    'recommendations': len(analysis_data.get('recommendations', {}).get('urgent', []))
                }
            }

        except Exception as e:
            logger.error(f"❌ Analysis execution failed: {str(e)}")
            self._store_job_history(
                analysis_type=analysis_type,
                status='failed',
                error=str(e)
            )
            return self._empty_analysis_result(analysis_type, 'execution_error', str(e))

    def _store_job_history(self, analysis_type: str, status: str,
                          execution_time: float = 0, error: str = None,
                          data: Dict = None) -> str:
        """
        Store job execution history in database

        Args:
            analysis_type: Type of analysis run
            status: 'success' or 'failed'
            execution_time: Execution time in seconds
            error: Error message if failed
            data: Analysis result data

        Returns:
            job_id (UUID)
        """
        try:
            if not self.orchestrator:
                logger.warning("⚠️ Cannot store job history - no orchestrator")
                return None

            import uuid
            job_id = str(uuid.uuid4())

            cursor = self.orchestrator.db_conn.cursor()

            # Ensure table exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scheduler_jobs (
                    id TEXT PRIMARY KEY,
                    analysis_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    execution_time REAL,
                    error TEXT,
                    data TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                INSERT INTO scheduler_jobs (id, analysis_type, status, execution_time, error, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                analysis_type,
                status,
                execution_time,
                error,
                json.dumps(data) if data else None
            ))

            self.orchestrator.db_conn.commit()
            logger.debug(f"📝 Job history stored: {job_id}")

            return job_id

        except Exception as e:
            logger.error(f"❌ Failed to store job history: {str(e)}")
            return None

    def _send_critical_anomaly_notification(self, analysis_data: Dict,
                                            critical_anomalies: List,
                                            job_id: str):
        """
        Send email notification for critical anomalies

        Args:
            analysis_data: Full analysis result
            critical_anomalies: List of critical anomalies
            job_id: Job ID for reference
        """
        try:
            if not self.sendgrid_api_key:
                logger.warning("⚠️ SendGrid API key not configured")
                return

            from sendgrid import SendGridAPIClient
            from sendgrid.helpers.mail import Mail, Content

            # Build email subject and body
            subject = f"🚨 Critical Anomalies Detected - Job {job_id[:8]}"

            anomaly_list = "\n".join([
                f"  • {a.get('type')}: {a.get('description')} (Client ID: {a.get('client_id')})"
                for a in critical_anomalies[:5]  # Limit to first 5
            ])

            body_text = f"""
Critical Anomalies Alert from Analytics Engine

Job ID: {job_id}
Timestamp: {datetime.now().isoformat()}

Total Critical Anomalies: {len(critical_anomalies)}

Top 5 Anomalies:
{anomaly_list}

Action Required: Review anomalies in dashboard and take corrective actions.

Dashboard: http://localhost:8000/dashboards/internal_dashboard.html
            """

            message = Mail(
                from_email='noreply@enbuenamesa.com',
                to_emails='felipe@enbuenamesa.com',
                subject=subject,
                plain_text_content=Content("text/plain", body_text)
            )

            sg = SendGridAPIClient(self.sendgrid_api_key)
            response = sg.send(message)

            logger.info(f"📧 Critical anomaly notification sent (Status: {response.status_code})")

        except Exception as e:
            logger.error(f"❌ Failed to send notification: {str(e)}")

    def get_job_history(self, limit: int = 50) -> List[Dict]:
        """
        Retrieve job execution history

        Args:
            limit: Maximum number of records to return

        Returns:
            List of job history records
        """
        try:
            if not self.orchestrator:
                return []

            cursor = self.orchestrator.db_conn.cursor()

            cursor.execute("""
                SELECT id, analysis_type, status, execution_time, error, timestamp
                FROM scheduler_jobs
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))

            rows = cursor.fetchall()

            return [
                {
                    'job_id': row[0],
                    'analysis_type': row[1],
                    'status': row[2],
                    'execution_time': row[3],
                    'error': row[4],
                    'timestamp': row[5]
                }
                for row in rows
            ]

        except Exception as e:
            logger.error(f"❌ Failed to retrieve job history: {str(e)}")
            return []

    def get_trend_analysis(self, days: int = 7) -> Dict:
        """
        Analyze trends over time period

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis dict
        """
        try:
            if not self.orchestrator:
                return self._empty_trend_analysis()

            cursor = self.orchestrator.db_conn.cursor()
            start_date = (datetime.now() - timedelta(days=days)).isoformat()

            cursor.execute("""
                SELECT DATE(timestamp) as date, COUNT(*) as count, AVG(execution_time) as avg_time
                FROM scheduler_jobs
                WHERE timestamp >= ? AND status = 'success'
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, (start_date,))

            rows = cursor.fetchall()

            daily_stats = [
                {
                    'date': row[0],
                    'runs': row[1],
                    'avg_execution_time': row[2]
                }
                for row in rows
            ]

            # Calculate week-over-week and month-over-month changes
            if len(daily_stats) >= 2:
                first_week_avg = sum(s['runs'] for s in daily_stats[:7]) / min(7, len(daily_stats))
                last_week_avg = sum(s['runs'] for s in daily_stats[-7:]) / min(7, len(daily_stats[-7:]))
                week_change = ((last_week_avg - first_week_avg) / first_week_avg * 100) if first_week_avg > 0 else 0
            else:
                week_change = 0

            return {
                'period_days': days,
                'daily_stats': daily_stats,
                'week_over_week_change': round(week_change, 1),
                'total_runs': sum(s['runs'] for s in daily_stats),
                'avg_execution_time': sum(s['avg_execution_time'] for s in daily_stats) / len(daily_stats) if daily_stats else 0
            }

        except Exception as e:
            logger.error(f"❌ Failed to calculate trend analysis: {str(e)}")
            return self._empty_trend_analysis()

    def configure_notifications(self, thresholds: Dict[str, bool]):
        """
        Configure notification thresholds

        Args:
            thresholds: Dict with severity levels as keys and bool as values
                Example: {'CRITICAL': True, 'HIGH': False, 'MEDIUM': False, 'LOW': False}
        """
        self.notification_threshold = {**self.notification_threshold, **thresholds}
        logger.info(f"📋 Notification thresholds updated: {self.notification_threshold}")

    def get_scheduler_status(self) -> Dict:
        """Get current scheduler status"""
        return {
            'running': self.scheduler.running,
            'jobs_count': len(self.scheduler.get_jobs()),
            'jobs': [
                {
                    'id': job.id,
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'trigger': str(job.trigger)
                }
                for job in self.scheduler.get_jobs()
            ]
        }

    @staticmethod
    def _empty_analysis_result(analysis_type: str, reason: str,
                              error_msg: str = None) -> Dict:
        """Return empty analysis result structure"""
        return {
            'status': 'failed',
            'analysis_type': analysis_type,
            'reason': reason,
            'error': error_msg,
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_predictions': 0,
                'total_anomalies': 0,
                'critical_anomalies': 0,
                'recommendations': 0
            }
        }

    @staticmethod
    def _empty_trend_analysis() -> Dict:
        """Return empty trend analysis structure"""
        return {
            'period_days': 0,
            'daily_stats': [],
            'week_over_week_change': 0,
            'total_runs': 0,
            'avg_execution_time': 0
        }
