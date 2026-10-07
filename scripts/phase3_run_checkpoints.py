#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FASE 15 Phase 3 - Run Checkpoint Monitoring Loop
Executes 13 checkpoints over 24-hour window at 2-hour intervals
HORA 48-72 = Oct 6-7, 2026
"""

import time
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.phase3_checkpoint_monitor import Phase3CheckpointMonitor, CheckpointDecision

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/phase3_checkpoints.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class Phase3CheckpointRunner:
    """Orchestrate Phase 3 checkpoint collection over 24 hours"""

    def __init__(self, db_path: str = "fase15.db"):
        self.db_path = db_path
        self.monitor = Phase3CheckpointMonitor(db_path)
        self.monitor.connect()

        # Checkpoint schedule: HORA 48-72 (every 2 hours, 13 checkpoints)
        self.checkpoints = [
            48, 50, 52, 54, 56, 58, 60, 62, 64, 66, 68, 70, 72
        ]

        self.checkpoint_results = {
            'total': len(self.checkpoints),
            'completed': 0,
            'green': 0,
            'yellow': 0,
            'red': 0,
            'rollbacks': 0,
            'continue': 0,
            'caution': 0
        }

        self.rollback_triggered = False

    def run_checkpoint_loop(self, test_mode: bool = False, delay_seconds: int = 7200):
        """
        Run checkpoints over 24-hour window

        Args:
            test_mode: If True, run all 13 checkpoints immediately (no delays)
            delay_seconds: Delay between checkpoints (default 2 hours = 7200s)
        """
        logger.info("\n" + "█"*80)
        logger.info("█  FASE 15 PHASE 3 - CHECKPOINT MONITORING LOOP")
        logger.info("█  24-Hour Execution Window: HORA 48-72")
        logger.info("█  13 Checkpoints at 2-hour intervals")
        logger.info("█"*80)

        # Check if Phase 3 is active
        if not self.monitor.is_phase3_active():
            logger.error("❌ Phase 3 is not active. Cannot run checkpoints.")
            logger.info("💡 Run phase3_activate.py first")
            return 1

        logger.info(f"✅ Phase 3 is active")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Checkpoint interval: {delay_seconds}s ({delay_seconds/3600:.1f} hours)")

        # Run each checkpoint
        for i, hora in enumerate(self.checkpoints, 1):
            logger.info(f"\n{'='*80}")
            logger.info(f"CHECKPOINT {i}/13 - HORA {hora}")
            logger.info(f"{'='*80}")

            # Collect checkpoint
            checkpoint = self.monitor.collect_checkpoint(hora)

            if checkpoint:
                # Update results
                self.checkpoint_results['completed'] += 1

                # Count by status
                if checkpoint.status.value == 'GREEN':
                    self.checkpoint_results['green'] += 1
                elif checkpoint.status.value == 'YELLOW':
                    self.checkpoint_results['yellow'] += 1
                else:
                    self.checkpoint_results['red'] += 1

                # Count by decision
                if checkpoint.decision == CheckpointDecision.ROLLBACK:
                    self.checkpoint_results['rollbacks'] += 1
                    self.rollback_triggered = True
                    logger.error(f"🚨 ROLLBACK TRIGGERED AT HORA {hora}")
                    return 1
                elif checkpoint.decision == CheckpointDecision.CONTINUE:
                    self.checkpoint_results['continue'] += 1
                else:
                    self.checkpoint_results['caution'] += 1
            else:
                logger.error(f"❌ Failed to collect checkpoint {i}")

            # Wait before next checkpoint
            if i < len(self.checkpoints):
                if test_mode:
                    logger.info("📍 Test mode: skipping delay")
                else:
                    logger.info(f"⏰ Waiting {delay_seconds}s ({delay_seconds/3600:.1f}h) until next checkpoint...")
                    time.sleep(delay_seconds)

        # Print summary
        self.print_summary()

        return 0

    def print_summary(self):
        """Print checkpoint execution summary"""
        logger.info("\n" + "█"*80)
        logger.info("█  CHECKPOINT MONITORING SUMMARY")
        logger.info("█"*80)

        logger.info(f"\nTotal Checkpoints: {self.checkpoint_results['total']}")
        logger.info(f"Completed: {self.checkpoint_results['completed']}/{self.checkpoint_results['total']}")

        logger.info(f"\nHealth Status:")
        logger.info(f"  🟢 GREEN (6/6):  {self.checkpoint_results['green']}")
        logger.info(f"  🟡 YELLOW (5/6): {self.checkpoint_results['yellow']}")
        logger.info(f"  🔴 RED (<5/6):   {self.checkpoint_results['red']}")

        logger.info(f"\nDecisions:")
        logger.info(f"  ✅ CONTINUE:    {self.checkpoint_results['continue']}")
        logger.info(f"  ⚠️  CAUTION:     {self.checkpoint_results['caution']}")
        logger.info(f"  🚨 ROLLBACK:    {self.checkpoint_results['rollbacks']}")

        # Final status
        if self.rollback_triggered:
            logger.error(f"\n❌ PHASE 3 EXECUTION FAILED - ROLLBACK TRIGGERED")
            status = "NO-GO"
        elif self.checkpoint_results['red'] > 0:
            logger.warning(f"\n⚠️  PHASE 3 EXECUTION COMPLETED - CAUTION STATUS")
            status = "CAUTION"
        elif self.checkpoint_results['green'] >= 10:
            logger.info(f"\n✅ PHASE 3 EXECUTION SUCCESSFUL - GO STATUS")
            status = "GO"
        else:
            logger.warning(f"\n⚠️  PHASE 3 EXECUTION COMPLETED - MARGINAL STATUS")
            status = "CAUTION"

        logger.info(f"Final Status: {status}")
        logger.info("█"*80 + "\n")

    def run_single_checkpoint(self, hora: int):
        """Run a single checkpoint by HORA number"""
        logger.info(f"Running checkpoint for HORA {hora}...")

        if not self.monitor.is_phase3_active():
            logger.error("❌ Phase 3 is not active")
            return 1

        checkpoint = self.monitor.collect_checkpoint(hora)
        return 0 if checkpoint else 1

    def close(self):
        """Cleanup"""
        if self.monitor:
            self.monitor.close()


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description='FASE 15 Phase 3 - Checkpoint Monitoring Loop'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run all checkpoints immediately (no delays)'
    )
    parser.add_argument(
        '--single',
        type=int,
        metavar='HORA',
        help='Run single checkpoint by HORA (e.g., --single 48)'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=7200,
        metavar='SECONDS',
        help='Delay between checkpoints (default: 7200s = 2 hours)'
    )
    parser.add_argument(
        '--db',
        default='fase15.db',
        help='Database path'
    )

    args = parser.parse_args()

    runner = Phase3CheckpointRunner(args.db)

    try:
        if args.single:
            return runner.run_single_checkpoint(args.single)
        else:
            return runner.run_checkpoint_loop(
                test_mode=args.test,
                delay_seconds=args.interval
            )
    finally:
        runner.close()


if __name__ == "__main__":
    exit(main())
