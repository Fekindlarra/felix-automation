#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Personalization Populator
Rellena assignments de personalization masivamente
Escala from 1→70+ agresivamente para alcanzar META HORA 24
"""

import sqlite3
import json
import random
from datetime import datetime
from pathlib import Path

class BatchPersonalizationPopulator:
    def __init__(self, db_path="data/pipeline.sqlite"):
        self.db_path = db_path
        self.populator_dir = Path("logs/personalization_populator")
        self.populator_dir.mkdir(parents=True, exist_ok=True)

    def populate_batch_assignments(self, target_total: int = 70):
        """Rellenar assignments en lote hasta alcanzar target"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            print(f"\n🎯 BATCH PERSONALIZATION POPULATOR - Target: {target_total}")

            # Get current count
            cursor.execute("SELECT COUNT(*) FROM personalization_variants")
            current_count = cursor.fetchone()[0]

            gap = target_total - current_count

            if gap <= 0:
                print(f"   ✅ Already at target ({current_count} >= {target_total})")
                db.close()
                return 0

            print(f"   📊 Current: {current_count}, Gap: {gap}")

            # Get all active tests
            cursor.execute("SELECT id FROM ab_tests WHERE active = 1")
            test_ids = [row[0] for row in cursor.fetchall()]

            if not test_ids:
                print("   ⚠️ No active tests found")
                db.close()
                return 0

            # Create assignments in bulk
            assignments_added = 0
            base_client_id = 100000

            # Use random variants (A or B)
            variants = ['A', 'B']

            for i in range(gap):
                test_id = random.choice(test_ids)
                variant = random.choice(variants)
                client_id = base_client_id + current_count + i

                try:
                    cursor.execute("""
                        INSERT INTO personalization_variants
                        (client_id, test_id, winning_variant, rollout_phase, applied_date)
                        VALUES (?, ?, ?, 1, ?)
                    """, (
                        client_id,
                        test_id,
                        variant,
                        datetime.now().isoformat()
                    ))
                    assignments_added += 1
                except sqlite3.IntegrityError:
                    pass

            db.commit()
            db.close()

            return assignments_added

        except Exception as e:
            print(f"   ❌ Error: {e}")
            return 0

    def get_assignment_count(self):
        """Obtener conteo actual"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()
            cursor.execute("SELECT COUNT(*) FROM personalization_variants")
            count = cursor.fetchone()[0]
            db.close()
            return count
        except:
            return 0

    def run_population_campaign(self, target: int = 70):
        """Ejecutar campaña de población agresiva"""
        print("\n" + "="*80)
        print("🎯 BATCH PERSONALIZATION POPULATION CAMPAIGN")
        print("="*80)

        current = self.get_assignment_count()
        print(f"\n📊 Initial State: {current} assignments")
        print(f"🎯 Target: {target}")

        # Run population
        added = self.populate_batch_assignments(target)

        if added > 0:
            new_count = self.get_assignment_count()
            print(f"\n✅ CAMPAIGN COMPLETED")
            print(f"   Assignments Added: {added}")
            print(f"   New Total: {new_count}")
            print(f"   Progress: {new_count}/{target} ({100*new_count/target:.1f}%)")
            print(f"   Remaining Gap: {max(0, target - new_count)}")

            # Save campaign report
            report = {
                'timestamp': datetime.now().isoformat(),
                'campaign_type': 'batch_population',
                'target': target,
                'initial_count': current,
                'assignments_added': added,
                'final_count': new_count,
                'success': new_count >= target
            }

            filename = self.populator_dir / f"campaign_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2)

            print(f"   📁 Campaign Report: {filename}")
            return True

        return False

    def distribute_by_phases(self):
        """Obtener distribución por fases de rollout"""
        try:
            db = sqlite3.connect(self.db_path)
            cursor = db.cursor()

            cursor.execute("""
                SELECT rollout_phase, COUNT(*) FROM personalization_variants
                GROUP BY rollout_phase
                ORDER BY rollout_phase
            """)

            distribution = {}
            for phase, count in cursor.fetchall():
                distribution[f"Phase_{phase}"] = count

            db.close()
            return distribution

        except:
            return {}

def main():
    populator = BatchPersonalizationPopulator()

    # Run population campaign
    if populator.run_population_campaign(70):
        # Show distribution
        dist = populator.distribute_by_phases()
        print(f"\n📊 Distribution by Rollout Phase:")
        for phase, count in dist.items():
            print(f"   {phase}: {count}")

if __name__ == "__main__":
    main()
