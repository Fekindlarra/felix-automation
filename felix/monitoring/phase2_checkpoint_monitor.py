#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Phase 2 Checkpoint Monitor - HORA 24-48 Automated Cycle
Ejecuta validaciones cada 2 horas con thresholds más estrictos
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from checkpoint_orchestrator import CheckpointOrchestrator

class Phase2CheckpointMonitor(CheckpointOrchestrator):
    def __init__(self, db_path="data/pipeline.sqlite"):
        super().__init__(db_path)
        self.phase2_dir = Path("logs/phase2")
        self.start_hora = 24  # Phase 2 starts at HORA 24
        self.end_hora = 48    # Phase 2 ends at HORA 48

        # Phase 2 thresholds (stricter than Phase 1)
        self.thresholds = {
            'ml_accuracy': {'min': 78, 'unit': '%'},  # Up from 75%
            'error_rate': {'max': 0.08, 'unit': '%'},  # Down from 0.1%
            'websocket_latency': {'max': 95, 'unit': 'ms'},  # Down from 100ms
            'predictions_per_hour': {'min': 42, 'unit': '/hora'},  # Up from 36
            'personalization_assignments': {'min': 140, 'unit': 'total'},  # 2x from 70
            'active_tests': {'min': 8, 'unit': 'tests'}  # Up from 5
        }

    def run_phase2_checkpoint(self, hora: int) -> bool:
        """Execute Phase 2 checkpoint with enhanced metrics tracking"""
        print(f"\n🔄 Phase 2 Checkpoint - HORA {hora}...")
        print(f"   Thresholds: STRICTER (Phase 2 mode)")

        # Get current metrics
        metrics = self.get_current_metrics()
        if not metrics:
            print("❌ Failed to fetch metrics")
            return False

        # Validate metrics with Phase 2 thresholds
        all_green, results, warnings = self.validate_metrics(metrics)

        # Update metrics dict
        for metric_name, result in results.items():
            metrics[metric_name] = result['value']

        # Print Phase 2 specific report
        print("\n" + "="*80)
        print(f"📊 PHASE 2 CHECKPOINT - HORA {hora}")
        print(f"   Thresholds: Enhanced (Phase 2)")
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
            print(f"\n✅ ALL METRICS GREEN - PHASE 2 STABLE")

        print(f"\n🎯 Phase 2 Status: {'✅ GO' if all_green else '⚠️ CAUTION'}")
        print("="*80)

        # Save Phase 2 checkpoint
        report = {
            'hora': hora,
            'phase': 2,
            'timestamp': datetime.now().isoformat(),
            'metrics': {k: v for k, v in metrics.items() if k != 'timestamp'},
            'status': 'GREEN' if all_green else 'CAUTION',
            'ready_for_phase3': all_green
        }

        filename = self.phase2_dir / f"checkpoint_hora{hora:02d}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\n💾 Phase 2 Checkpoint saved: {filename}")
        return all_green

def main():
    monitor = Phase2CheckpointMonitor()

    # Phase 2 checkpoints: HORA 24-48 (every 2 hours)
    schedule = list(range(24, 49, 2))

    print("\n" + "="*80)
    print("🚀 PHASE 2 MONITORING - HORA 24-48")
    print("="*80)
    print(f"Schedule: HORAS {schedule}")
    print(f"Total checkpoints: {len(schedule)}")
    print(f"Duration: 24 hours")
    print(f"Interval: Every 2 hours")
    print(f"Rollout Phase: 50% user allocation")
    print("="*80)

    # Run initial checkpoint at HORA 24 (Phase 2 start)
    print(f"\n📍 Starting Phase 2 Monitoring at HORA 24...")
    monitor.run_phase2_checkpoint(24)

    print("\n✅ Phase 2 Monitoring Framework Ready")
    print(f"   Next Checkpoint: HORA 26")
    print(f"   Final Decision: HORA 48")

if __name__ == "__main__":
    main()
