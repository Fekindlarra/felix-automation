#!/usr/bin/env python3
# ====================================================================
# Metrics Collection for FASE 14
# ====================================================================

import sqlite3
import json
import time
from datetime import datetime
from pathlib import Path

class MetricsCollector:
    """Collect system and application metrics"""

    def __init__(self, db_path: str = "data/pipeline.sqlite"):
        self.db_path = db_path
        self.metrics = {}
        self.timestamp = datetime.now().isoformat()

    def collect_database_metrics(self):
        """Collect database performance metrics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Query time benchmark
            start = time.time()
            cursor.execute("SELECT COUNT(*) FROM clients")
            query_time = (time.time() - start) * 1000  # ms

            # Table sizes
            cursor.execute("""
                SELECT name, COUNT(*) as rows
                FROM sqlite_master
                WHERE type='table'
                GROUP BY name
            """)
            table_counts = dict(cursor.fetchall())

            # Database file size
            db_size_mb = Path(self.db_path).stat().st_size / (1024 * 1024)

            conn.close()

            self.metrics['database'] = {
                'query_time_ms': round(query_time, 2),
                'table_counts': table_counts,
                'size_mb': round(db_size_mb, 2),
                'timestamp': self.timestamp
            }

            return True
        except Exception as e:
            print(f"Error collecting database metrics: {e}")
            return False

    def collect_system_metrics(self):
        """Collect system resources"""
        try:
            import os

            # Check disk space
            stat = os.statvfs('.')
            disk_total_gb = (stat.f_blocks * stat.f_frsize) / (1024**3)
            disk_used_gb = ((stat.f_blocks - stat.f_bfree) * stat.f_frsize) / (1024**3)
            disk_percent = (disk_used_gb / disk_total_gb) * 100

            self.metrics['system'] = {
                'disk_total_gb': round(disk_total_gb, 2),
                'disk_used_gb': round(disk_used_gb, 2),
                'disk_percent': round(disk_percent, 1),
                'timestamp': self.timestamp
            }

            return True
        except Exception as e:
            print(f"Error collecting system metrics: {e}")
            return False

    def save_metrics(self, output_file: str = "monitoring/metrics/current_metrics.json"):
        """Save collected metrics to file"""
        try:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving metrics: {e}")
            return False

    def print_summary(self):
        """Print metrics summary"""
        print("\n📊 METRICS SUMMARY")
        print("=" * 50)

        if 'database' in self.metrics:
            db = self.metrics['database']
            print(f"Database Query Time: {db['query_time_ms']:.2f}ms")
            print(f"Database Size: {db['size_mb']:.2f}MB")
            print(f"Tables: {len(db['table_counts'])}")

        if 'system' in self.metrics:
            sys = self.metrics['system']
            print(f"Disk Usage: {sys['disk_percent']:.1f}% ({sys['disk_used_gb']:.2f}GB / {sys['disk_total_gb']:.2f}GB)")

        print("=" * 50)


def main():
    collector = MetricsCollector()

    print("🔄 Collecting metrics...")
    collector.collect_database_metrics()
    collector.collect_system_metrics()
    collector.save_metrics()
    collector.print_summary()
    print("✓ Metrics saved to monitoring/metrics/current_metrics.json")


if __name__ == "__main__":
    main()
