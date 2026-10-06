"""
FASE 14 Backend API Routes
Real-time monitoring, alerts, metrics, and health check endpoints
"""

from flask import Flask, jsonify, request, Blueprint
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class MonitoringAPI:
    """API endpoints for monitoring system"""

    def __init__(self, health_checker, error_tracker, metrics_collector, alert_manager):
        """
        Initialize monitoring API

        Args:
            health_checker: HealthChecker instance
            error_tracker: ErrorTracker instance
            metrics_collector: MetricsCollector instance
            alert_manager: AlertManager instance
        """
        self.health_checker = health_checker
        self.error_tracker = error_tracker
        self.metrics_collector = metrics_collector
        self.alert_manager = alert_manager
        self.blueprint = Blueprint('monitoring', __name__, url_prefix='/api/monitoring')
        self._register_routes()

    def _register_routes(self):
        """Register all API routes"""
        self.blueprint.route('/health', methods=['GET'])(self.get_health)
        self.blueprint.route('/alerts', methods=['GET'])(self.get_alerts)
        self.blueprint.route('/alerts/<alert_id>/acknowledge', methods=['POST'])(self.acknowledge_alert)
        self.blueprint.route('/alerts/<alert_id>/resolve', methods=['POST'])(self.resolve_alert)
        self.blueprint.route('/metrics', methods=['GET'])(self.get_metrics)
        self.blueprint.route('/metrics/<component>', methods=['GET'])(self.get_component_metrics)
        self.blueprint.route('/errors', methods=['GET'])(self.get_errors)
        self.blueprint.route('/errors/<error_id>/resolve', methods=['POST'])(self.resolve_error)
        self.blueprint.route('/anomalies', methods=['GET'])(self.get_anomalies)
        self.blueprint.route('/status', methods=['GET'])(self.get_status)

    def get_health(self):
        """Get overall system health status"""
        try:
            if not self.health_checker:
                return jsonify({'error': 'Health checker not available'}), 503

            health = self.health_checker.check_all()
            return jsonify(health.to_dict()), 200

        except Exception as e:
            logger.error(f"Error getting health: {e}")
            return jsonify({'error': str(e)}), 500

    def get_alerts(self):
        """Get active alerts with optional filtering"""
        try:
            if not self.alert_manager:
                return jsonify({'alerts': []}), 200

            severity = request.args.get('severity')
            hours = request.args.get('hours', default=24, type=int)

            # Get summary
            summary = self.alert_manager.get_alert_summary(hours=hours)

            # Get active alerts
            active_alerts = self.alert_manager.get_active_alerts()
            if severity:
                from backend_alert_manager import AlertSeverity
                severity_enum = AlertSeverity[severity.upper()]
                active_alerts = [a for a in active_alerts if a.severity == severity_enum]

            return jsonify({
                'summary': summary,
                'alerts': [a.to_dict() for a in active_alerts],
                'count': len(active_alerts)
            }), 200

        except Exception as e:
            logger.error(f"Error getting alerts: {e}")
            return jsonify({'error': str(e)}), 500

    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        try:
            if not self.alert_manager:
                return jsonify({'error': 'Alert manager not available'}), 503

            acknowledged_by = request.json.get('acknowledged_by', 'system')
            success = self.alert_manager.acknowledge_alert(alert_id, acknowledged_by)

            if success:
                return jsonify({'message': 'Alert acknowledged', 'alert_id': alert_id}), 200
            else:
                return jsonify({'error': 'Alert not found'}), 404

        except Exception as e:
            logger.error(f"Error acknowledging alert: {e}")
            return jsonify({'error': str(e)}), 500

    def resolve_alert(self, alert_id: str):
        """Resolve an alert"""
        try:
            if not self.alert_manager:
                return jsonify({'error': 'Alert manager not available'}), 503

            success = self.alert_manager.resolve_alert(alert_id)

            if success:
                return jsonify({'message': 'Alert resolved', 'alert_id': alert_id}), 200
            else:
                return jsonify({'error': 'Alert not found'}), 404

        except Exception as e:
            logger.error(f"Error resolving alert: {e}")
            return jsonify({'error': str(e)}), 500

    def get_metrics(self):
        """Get all metrics with optional filtering"""
        try:
            if not self.metrics_collector:
                return jsonify({'metrics': []}), 200

            hours = request.args.get('hours', default=1, type=int)
            component = request.args.get('component')

            summary = self.metrics_collector.get_metric_summary(hours=hours)

            # Get anomalies
            anomalies = self.metrics_collector.get_anomalies(hours=hours)

            return jsonify({
                'summary': summary,
                'anomalies': [a.to_dict() for a in anomalies],
                'anomaly_count': len(anomalies)
            }), 200

        except Exception as e:
            logger.error(f"Error getting metrics: {e}")
            return jsonify({'error': str(e)}), 500

    def get_component_metrics(self, component: str):
        """Get metrics for specific component"""
        try:
            if not self.metrics_collector:
                return jsonify({'error': 'Metrics collector not available'}), 503

            seconds = request.args.get('seconds', default=300, type=int)
            health = self.metrics_collector.get_component_health(component, seconds=seconds)

            if not health.get('metrics'):
                return jsonify({'error': f'No metrics found for component {component}'}), 404

            return jsonify(health), 200

        except Exception as e:
            logger.error(f"Error getting component metrics: {e}")
            return jsonify({'error': str(e)}), 500

    def get_errors(self):
        """Get errors with optional filtering"""
        try:
            if not self.error_tracker:
                return jsonify({'errors': []}), 200

            hours = request.args.get('hours', default=24, type=int)
            category = request.args.get('category')
            component = request.args.get('component')

            # Get summary
            summary = self.error_tracker.get_error_summary(hours=hours)

            # Get critical errors
            critical = self.error_tracker.get_critical_errors(hours=hours)

            # Get aggregates
            aggregates = self.error_tracker.get_aggregates(hours=hours)

            return jsonify({
                'summary': summary,
                'critical_errors': [e.to_dict() for e in critical],
                'recurring_errors': [a.to_dict() for a in aggregates],
                'critical_count': len(critical),
                'recurring_count': len(aggregates)
            }), 200

        except Exception as e:
            logger.error(f"Error getting errors: {e}")
            return jsonify({'error': str(e)}), 500

    def resolve_error(self, error_id: str):
        """Resolve an error"""
        try:
            if not self.error_tracker:
                return jsonify({'error': 'Error tracker not available'}), 503

            resolution_notes = request.json.get('resolution_notes', '')
            self.error_tracker.resolve_error(error_id, resolution_notes)

            return jsonify({'message': 'Error resolved', 'error_id': error_id}), 200

        except Exception as e:
            logger.error(f"Error resolving error: {e}")
            return jsonify({'error': str(e)}), 500

    def get_anomalies(self):
        """Get detected anomalies"""
        try:
            if not self.metrics_collector:
                return jsonify({'anomalies': []}), 200

            hours = request.args.get('hours', default=24, type=int)
            anomalies = self.metrics_collector.get_anomalies(hours=hours)

            # Group by severity
            by_severity = {}
            for anomaly in anomalies:
                severity = anomaly.severity
                if severity not in by_severity:
                    by_severity[severity] = []
                by_severity[severity].append(anomaly.to_dict())

            return jsonify({
                'anomalies': [a.to_dict() for a in anomalies],
                'by_severity': by_severity,
                'count': len(anomalies)
            }), 200

        except Exception as e:
            logger.error(f"Error getting anomalies: {e}")
            return jsonify({'error': str(e)}), 500

    def get_status(self):
        """Get overall system status"""
        try:
            status = {
                'timestamp': datetime.utcnow().isoformat(),
                'health': None,
                'alerts': None,
                'errors': None,
                'metrics': None,
                'components': []
            }

            if self.health_checker:
                health = self.health_checker.check_all()
                status['health'] = {
                    'status': health.status.value,
                    'check_count': len(health.checks),
                    'healthy_count': len([c for c in health.checks if c.status.value == 'HEALTHY']),
                    'degraded_count': len([c for c in health.checks if c.status.value == 'DEGRADED']),
                    'critical_count': len([c for c in health.checks if c.status.value == 'CRITICAL'])
                }

                # Build component list
                for check in health.checks:
                    status['components'].append({
                        'name': check.component,
                        'status': check.status.value,
                        'response_time_ms': check.response_time_ms,
                        'message': check.message
                    })

            if self.alert_manager:
                summary = self.alert_manager.get_alert_summary(hours=1)
                status['alerts'] = summary

            if self.error_tracker:
                summary = self.error_tracker.get_error_summary(hours=1)
                status['errors'] = summary

            if self.metrics_collector:
                summary = self.metrics_collector.get_metric_summary(hours=1)
                status['metrics'] = summary

            return jsonify(status), 200

        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return jsonify({'error': str(e)}), 500


# A/B Testing API
class ABTestingAPI:
    """API endpoints for A/B testing management"""

    def __init__(self, db_connection):
        """Initialize A/B Testing API"""
        self.db = db_connection
        self.blueprint = Blueprint('ab_testing', __name__, url_prefix='/api/ab-testing')
        self._register_routes()

    def _register_routes(self):
        """Register A/B testing routes"""
        self.blueprint.route('/tests', methods=['GET'])(self.list_tests)
        self.blueprint.route('/tests', methods=['POST'])(self.create_test)
        self.blueprint.route('/tests/<test_id>/results', methods=['GET'])(self.get_test_results)
        self.blueprint.route('/tests/<test_id>/winner', methods=['POST'])(self.mark_winner)
        self.blueprint.route('/tests/<test_id>/pause', methods=['POST'])(self.pause_test)
        self.blueprint.route('/assignments', methods=['GET'])(self.get_assignments)

    def list_tests(self):
        """List all A/B tests"""
        try:
            active_only = request.args.get('active_only', default=False, type=bool)
            query = "SELECT * FROM ab_tests"
            if active_only:
                query += " WHERE active = 1"
            query += " ORDER BY start_date DESC"

            cursor = self.db.cursor()
            cursor.execute(query)
            tests = cursor.fetchall()

            return jsonify({'tests': tests, 'count': len(tests)}), 200

        except Exception as e:
            logger.error(f"Error listing tests: {e}")
            return jsonify({'error': str(e)}), 500

    def create_test(self):
        """Create new A/B test"""
        try:
            data = request.json
            required = ['test_name', 'email_type', 'variant_a_template', 'variant_b_template']

            if not all(k in data for k in required):
                return jsonify({'error': 'Missing required fields'}), 400

            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO ab_tests (test_name, email_type, variant_a_template, variant_b_template, active)
                VALUES (?, ?, ?, ?, 1)
            """, (data['test_name'], data['email_type'], data['variant_a_template'], data['variant_b_template']))

            self.db.commit()
            test_id = cursor.lastrowid

            return jsonify({'message': 'Test created', 'test_id': test_id}), 201

        except Exception as e:
            logger.error(f"Error creating test: {e}")
            return jsonify({'error': str(e)}), 500

    def get_test_results(self, test_id: int):
        """Get results for specific test"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT * FROM v_ab_test_summary WHERE test_id = ?
            """, (test_id,))

            results = cursor.fetchall()
            if not results:
                return jsonify({'error': 'Test not found'}), 404

            return jsonify({'results': results}), 200

        except Exception as e:
            logger.error(f"Error getting test results: {e}")
            return jsonify({'error': str(e)}), 500

    def mark_winner(self, test_id: int):
        """Mark winner of A/B test"""
        try:
            data = request.json
            if 'winner' not in data or data['winner'] not in ['A', 'B']:
                return jsonify({'error': 'Invalid winner'}), 400

            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE ab_tests
                SET winner = ?, end_date = CURRENT_TIMESTAMP
                WHERE test_id = ?
            """, (data['winner'], test_id))

            self.db.commit()

            return jsonify({'message': 'Winner marked', 'test_id': test_id, 'winner': data['winner']}), 200

        except Exception as e:
            logger.error(f"Error marking winner: {e}")
            return jsonify({'error': str(e)}), 500

    def pause_test(self, test_id: int):
        """Pause an active test"""
        try:
            cursor = self.db.cursor()
            cursor.execute("UPDATE ab_tests SET active = 0 WHERE test_id = ?", (test_id,))
            self.db.commit()

            return jsonify({'message': 'Test paused', 'test_id': test_id}), 200

        except Exception as e:
            logger.error(f"Error pausing test: {e}")
            return jsonify({'error': str(e)}), 500

    def get_assignments(self):
        """Get variant assignments for a client"""
        try:
            client_id = request.args.get('client_id', type=int)
            test_id = request.args.get('test_id', type=int)

            query = "SELECT * FROM ab_test_assignments WHERE 1=1"
            params = []

            if client_id:
                query += " AND client_id = ?"
                params.append(client_id)

            if test_id:
                query += " AND test_id = ?"
                params.append(test_id)

            cursor = self.db.cursor()
            cursor.execute(query, params)
            assignments = cursor.fetchall()

            return jsonify({'assignments': assignments, 'count': len(assignments)}), 200

        except Exception as e:
            logger.error(f"Error getting assignments: {e}")
            return jsonify({'error': str(e)}), 500


# Shopify Integration API
class ShopifyIntegrationAPI:
    """API endpoints for Shopify integration"""

    def __init__(self, db_connection):
        """Initialize Shopify API"""
        self.db = db_connection
        self.blueprint = Blueprint('shopify', __name__, url_prefix='/api/shopify')
        self._register_routes()

    def _register_routes(self):
        """Register Shopify routes"""
        self.blueprint.route('/stores', methods=['GET'])(self.list_stores)
        self.blueprint.route('/stores', methods=['POST'])(self.register_store)
        self.blueprint.route('/stores/<store_id>/analytics', methods=['GET'])(self.get_analytics)
        self.blueprint.route('/stores/<store_id>/sync', methods=['POST'])(self.sync_store)
        self.blueprint.route('/webhooks/orders/created', methods=['POST'])(self.webhook_order_created)
        self.blueprint.route('/webhooks/orders/updated', methods=['POST'])(self.webhook_order_updated)

    def list_stores(self):
        """List all connected Shopify stores"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT * FROM v_shopify_analytics
            """)

            stores = cursor.fetchall()
            return jsonify({'stores': stores, 'count': len(stores)}), 200

        except Exception as e:
            logger.error(f"Error listing stores: {e}")
            return jsonify({'error': str(e)}), 500

    def register_store(self):
        """Register new Shopify store"""
        try:
            data = request.json
            required = ['client_id', 'shop_name', 'shop_domain', 'access_token']

            if not all(k in data for k in required):
                return jsonify({'error': 'Missing required fields'}), 400

            cursor = self.db.cursor()
            cursor.execute("""
                INSERT INTO shopify_stores (client_id, shop_name, shop_domain, access_token_encrypted, sync_status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (data['client_id'], data['shop_name'], data['shop_domain'], data['access_token']))

            self.db.commit()
            store_id = cursor.lastrowid

            return jsonify({'message': 'Store registered', 'store_id': store_id}), 201

        except Exception as e:
            logger.error(f"Error registering store: {e}")
            return jsonify({'error': str(e)}), 500

    def get_analytics(self, store_id: int):
        """Get analytics for specific store"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                SELECT * FROM v_shopify_analytics WHERE store_id = ?
            """, (store_id,))

            result = cursor.fetchone()
            if not result:
                return jsonify({'error': 'Store not found'}), 404

            return jsonify(result), 200

        except Exception as e:
            logger.error(f"Error getting analytics: {e}")
            return jsonify({'error': str(e)}), 500

    def sync_store(self, store_id: int):
        """Trigger sync for Shopify store"""
        try:
            cursor = self.db.cursor()
            cursor.execute("""
                UPDATE shopify_stores
                SET sync_status = 'syncing', last_sync = CURRENT_TIMESTAMP
                WHERE store_id = ?
            """, (store_id,))

            self.db.commit()

            return jsonify({'message': 'Sync triggered', 'store_id': store_id}), 200

        except Exception as e:
            logger.error(f"Error syncing store: {e}")
            return jsonify({'error': str(e)}), 500

    def webhook_order_created(self):
        """Handle Shopify order.created webhook"""
        try:
            # Verify webhook signature
            data = request.json

            # TODO: Implement webhook signature verification

            # Process order data and store in database
            logger.info(f"Order created webhook received: {data.get('id')}")

            return jsonify({'message': 'Webhook processed'}), 200

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return jsonify({'error': str(e)}), 500

    def webhook_order_updated(self):
        """Handle Shopify order.updated webhook"""
        try:
            data = request.json

            logger.info(f"Order updated webhook received: {data.get('id')}")

            return jsonify({'message': 'Webhook processed'}), 200

        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return jsonify({'error': str(e)}), 500


def create_api_blueprint(health_checker, error_tracker, metrics_collector, alert_manager, db_connection):
    """Factory function to create all API blueprints"""
    monitoring_api = MonitoringAPI(health_checker, error_tracker, metrics_collector, alert_manager)
    ab_testing_api = ABTestingAPI(db_connection)
    shopify_api = ShopifyIntegrationAPI(db_connection)

    return [
        monitoring_api.blueprint,
        ab_testing_api.blueprint,
        shopify_api.blueprint
    ]
