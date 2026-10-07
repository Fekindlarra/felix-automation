#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Checkpoint Orchestrator - HORA 6 to HORA 24 Monitoring Loop
Ejecuta validaciones cada 2 horas para confirmar metrics remain GREEN
Prepara go/no-go decision framework antes de HORA 24
"""

import sqlite3
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple

class CheckpointOrchestrator:
    def __init__(self, db_path="data/pipeline.sqlite"):
        self.db_path = db_path
        self.checkpoint_dir = Path("logs/checkpoints")
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        # Thresholds for GREEN status
        self.thresholds = {
            'ml_accuracy': {'min': 75, 'unit': '%'},
            'error_rate': {'max': 0.1, 'unit': '%'},
            'websocket_latency': {'max': 100, 'unit': 'ms'},
            'predictions_per_hour': {'min': 36, 'unit': '/hora'},
            'personalization_assignments': {'min': 70, 'unit': 'total'},
            'active_tests': {'min': 5, 'unit': 'tests'}
        }

        # HORA timeline
        self.start_hora = 6  # Oct 6, 2026
        self.end_hora = 24   # Oct 7, 2026 20:58 UTC
        self.checkpoint_interval = 2  # hours

    def calculate_hora(self, hours_from_start: int = 0) -> Tuple[str, int]:
        """Calculate current HORA based on elapsed time"""
        # Start time: Oct 6, 2026 12:00 UTC (HORA 6 = Oct 6 18:00)
        # Each HORA = 1 hour
        start = datetime(2026, 10, 6, 12, 0, 0)  # arbitrary baseline
        current = start + timedelta(hours=6 + hours_from_start)
        hora = 6 + hours_from_start
        return current.isoformat(), hora

    def get_current_metrics(self) -> Dict:
        """Fetch current system metrics"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            # ML Accuracy
            cursor.execute("SELECT AVG(ml_accuracy_percent) FROM prediction_accuracy_history")
            ml_acc = cursor.fetchone()[0] or 0

            # Error Rate
            cursor.execute("SELECT AVG(error_rate_percent) FROM system_health_history")
            error_rate = cursor.fetchone()[0] or 0

            # WebSocket Latency
            cursor.execute("SELECT websocket_latency_ms FROM system_health_history ORDER BY timestamp DESC LIMIT 1")
            result = cursor.fetchone()
            ws_lat = result[0] if result else 8

            # Predictions per Hour
            cursor.execute("SELECT AVG(predictions_per_hour) FROM system_health_history")
            pred_hour = cursor.fetchone()[0] or 0

            # Personalization Assignments
            cursor.execute("SELECT COUNT(*) FROM personalization_variants")
            assignments = cursor.fetchone()[0]

            # Active Tests
            cursor.execute("SELECT COUNT(*) FROM ab_tests WHERE active = 1")
            active_tests = cursor.fetchone()[0]

            db.close()

            return {
                'ml_accuracy': ml_acc,
                'error_rate': error_rate,
                'websocket_latency': ws_lat,
                'predictions_per_hour': pred_hour,
                'personalization_assignments': assignments,
                'active_tests': active_tests,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            print(f"❌ Error fetching metrics: {e}")
            return {}

    def validate_metrics(self, metrics: Dict) -> Tuple[bool, Dict, List[str]]:
        """Validate all metrics against thresholds"""
        all_green = True
        results = {}
        warnings = []

        for metric_name, value in metrics.items():
            if metric_name == 'timestamp':
                continue

            if metric_name not in self.thresholds:
                continue

            threshold = self.thresholds[metric_name]
            status = "✅ GREEN"

            if 'min' in threshold:
                if value < threshold['min']:
                    status = "⚠️ CAUTION"
                    all_green = False
                    warnings.append(f"{metric_name}: {value:.1f} (threshold: ≥{threshold['min']})")

            if 'max' in threshold:
                if value > threshold['max']:
                    status = "🔴 RED"
                    all_green = False
                    warnings.append(f"{metric_name}: {value:.1f} (threshold: <{threshold['max']})")

            results[metric_name] = {
                'value': value,
                'status': status,
                'unit': threshold['unit']
            }

        return all_green, results, warnings

    def print_checkpoint_report(self, hora: int, metrics: Dict, all_green: bool, warnings: List[str]):
        """Print formatted checkpoint report"""
        print("\n" + "="*80)
        print(f"📊 CHECKPOINT REPORT - HORA {hora}")
        print("="*80)
        print(f"Timestamp: {metrics.get('timestamp', 'unknown')}")

        print(f"\n{'Metric':<35} {'Value':<20} {'Status':<15}")
        print("-" * 70)

        for metric_name in ['ml_accuracy', 'error_rate', 'websocket_latency',
                           'predictions_per_hour', 'personalization_assignments', 'active_tests']:
            if metric_name in metrics and metric_name != 'timestamp':
                value = metrics[metric_name]
                unit = self.thresholds[metric_name]['unit']
                val_str = f"{value:.1f} {unit}"
                status = "✅ GREEN" if all_green and metric_name not in str(warnings) else "⚠️ CAUTION"

                print(f"{metric_name:<35} {val_str:<20} {status:<15}")

        if warnings:
            print(f"\n⚠️ WARNINGS ({len(warnings)}):")
            for warning in warnings:
                print(f"   • {warning}")
        else:
            print(f"\n✅ ALL METRICS GREEN")

        print(f"\n🎯 Overall Status: {'✅ GO' if all_green else '⚠️ CAUTION'}")
        print("="*80)

    def save_checkpoint(self, hora: int, metrics: Dict, all_green: bool):
        """Save checkpoint report to logs"""
        report = {
            'hora': hora,
            'timestamp': datetime.now().isoformat(),
            'metrics': {k: v for k, v in metrics.items() if k != 'timestamp'},
            'status': 'GREEN' if all_green else 'CAUTION',
            'ready_for_escalation': all_green
        }

        filename = self.checkpoint_dir / f"checkpoint_hora{hora:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Checkpoint saved: {filename}")
        return filename

    def run_checkpoint(self, hora: int) -> bool:
        """Execute single checkpoint at given HORA"""
        print(f"\n🔄 Running checkpoint for HORA {hora}...")

        # Get current metrics
        metrics = self.get_current_metrics()
        if not metrics:
            print("❌ Failed to fetch metrics")
            return False

        # Validate metrics
        all_green, results, warnings = self.validate_metrics(metrics)

        # Update metrics dict with validation results
        for metric_name, result in results.items():
            metrics[metric_name] = result['value']

        # Print report
        self.print_checkpoint_report(hora, metrics, all_green, warnings)

        # Save checkpoint
        self.save_checkpoint(hora, metrics, all_green)

        return all_green

    def generate_monitoring_schedule(self):
        """Generate schedule for all checkpoints HORA 6-24"""
        schedule = []
        for hours_offset in range(0, 19, 2):  # 0, 2, 4, ..., 18 hours
            hora = self.start_hora + hours_offset
            if hora <= self.end_hora:
                schedule.append(hora)

        return schedule

    def run_full_checkpoint_cycle(self):
        """Execute checkpoint for current HORA"""
        print("\n" + "="*80)
        print("🚀 CHECKPOINT ORCHESTRATOR - MONITORING CYCLE")
        print("="*80)

        schedule = self.generate_monitoring_schedule()
        print(f"\nSchedule: HORAS {schedule}")
        print(f"Total checkpoints before HORA 24: {len(schedule)}")

        # For now, run checkpoint for current HORA (simulating HORA 6)
        current_hora = self.start_hora
        print(f"\n📍 Current HORA: {current_hora}")

        return self.run_checkpoint(current_hora)

    def create_monitoring_script(self):
        """Generate shell script for automated checkpoint execution"""
        script = """#!/bin/bash
# Automated Checkpoint Monitoring - HORA 6 to HORA 24
# Run every 2 hours until HORA 24 (Oct 7, 2026 20:58 UTC)

HORAS=(6 8 10 12 14 16 18 20 22 24)

for HORA in "${HORAS[@]}"; do
    echo "📍 HORA $HORA - Running checkpoint validation"
    python3 << 'PYTHON_EOF'
from checkpoint_orchestrator import CheckpointOrchestrator
orchestrator = CheckpointOrchestrator()
success = orchestrator.run_checkpoint($HORA)
if not success:
    print(f"⚠️  CAUTION at HORA $HORA - Metrics not all GREEN")
PYTHON_EOF

    if [ $HORA -lt 24 ]; then
        echo "⏳ Waiting 2 hours until next checkpoint..."
        sleep 7200  # 2 hours in seconds (for production)
        # For testing: sleep 10  # 10 seconds
    fi
done

echo "✅ All checkpoints completed. Ready for HORA 24 GO/NO-GO decision."
"""
        script_path = Path("checkpoint_monitoring.sh")
        with open(script_path, 'w') as f:
            f.write(script)
        print(f"\n💾 Monitoring script created: {script_path}")
        return script_path

def main():
    orchestrator = CheckpointOrchestrator()

    # Show monitoring schedule
    schedule = orchestrator.generate_monitoring_schedule()
    print(f"\n📊 Monitoring Schedule (HORA 6-24):")
    print(f"   Checkpoints: {schedule}")
    print(f"   Interval: Every 2 hours")
    print(f"   Total: {len(schedule)} checkpoints")

    # Run initial checkpoint
    print(f"\n🔍 Running HORA 6 initial checkpoint...")
    orchestrator.run_full_checkpoint_cycle()

    # Generate monitoring script for future checkpoints
    orchestrator.create_monitoring_script()

if __name__ == "__main__":
    main()
