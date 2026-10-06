"""
Monitoring Initialization - FASE 14
Setup monitoring infrastructure at application startup
"""

def initialize_monitoring():
    """
    Initialize monitoring system at application startup.
    Call this once in your main application entry point.
    
    Example:
        from backend.monitoring_startup import initialize_monitoring
        
        if __name__ == "__main__":
            initialize_monitoring()
            # ... rest of your application code
    """
    try:
        from backend.monitoring import (
            get_metrics_collector,
            get_health_checker,
            get_performance_profiler,
            get_monitoring_dashboard
        )
        
        # Initialize singleton instances
        metrics = get_metrics_collector()
        health = get_health_checker()
        profiler = get_performance_profiler()
        dashboard = get_monitoring_dashboard()
        
        print("[MONITORING] ✓ Monitoring system initialized")
        print(f"[MONITORING] - MetricsCollector: {metrics}")
        print(f"[MONITORING] - HealthChecker: {health}")
        print(f"[MONITORING] - PerformanceProfiler: {profiler}")
        print(f"[MONITORING] - MonitoringDashboard: {dashboard}")
        
        return {
            'metrics_collector': metrics,
            'health_checker': health,
            'performance_profiler': profiler,
            'monitoring_dashboard': dashboard
        }
        
    except Exception as e:
        print(f"[MONITORING] ⚠ Failed to initialize monitoring: {e}")
        print(f"[MONITORING] Continuing with monitoring disabled")
        return None


def start_monitoring_background_tasks():
    """
    Start background tasks for monitoring (optional).
    Call this after initialize_monitoring() if you want automatic health checks.
    """
    try:
        import threading
        from backend.monitoring import get_health_checker
        
        health_checker = get_health_checker()
        
        def run_health_checks():
            """Run health checks every 30 seconds"""
            import time
            while True:
                try:
                    health_status = health_checker.check_health()
                    # Health checks run automatically, storing results in AlertManager
                except Exception as e:
                    print(f"[MONITORING] Health check error: {e}")
                time.sleep(30)
        
        # Start background thread (daemon)
        thread = threading.Thread(target=run_health_checks, daemon=True)
        thread.start()
        
        print("[MONITORING] ✓ Background health check thread started")
        return thread
        
    except Exception as e:
        print(f"[MONITORING] ⚠ Failed to start background tasks: {e}")
        return None


def get_monitoring_status():
    """
    Get current monitoring status for health dashboard.
    Returns dictionary with all metrics and health status.
    """
    try:
        from backend.monitoring import get_monitoring_dashboard
        
        dashboard = get_monitoring_dashboard()
        return dashboard.get_dashboard_data()
        
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Failed to get monitoring status: {e}'
        }
