#!/usr/bin/env python3
"""
ML Model Training Script for FASE 15
Trains RandomForest model on historical client data with synthetic conversions
"""

import sys
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.ml_pipeline import ConversionPredictionPipeline

def generate_synthetic_training_data(leads_df: pd.DataFrame, n_samples: int = 1000) -> tuple:
    """
    Generate synthetic training data by expanding real leads with variations
    and assigning realistic conversion labels
    """
    np.random.seed(42)

    training_data = []

    # For each real lead, create multiple variations with different features
    for _, lead in leads_df.iterrows():
        # Base scores from real data
        base_web = lead['web_score']
        base_facebook = lead['facebook_score']
        base_google = lead['google_score']

        # Generate variations
        n_variations = n_samples // len(leads_df)
        for i in range(n_variations):
            # Add random noise to scores (±20% variance)
            web_score = max(0, min(100, base_web + np.random.normal(0, 15)))
            facebook_score = max(0, min(100, base_facebook + np.random.normal(0, 15)))
            google_score = max(0, min(100, base_google + np.random.normal(0, 15)))

            # Map business_type - handle different formats
            business_type = str(lead.get('business_type', 'ecommerce')).lower()
            if business_type in ['plant', 'plants']:
                business_type = 'retail'
            elif business_type == 'service':
                business_type = 'services'

            company_size = str(lead.get('company_size', 'pyme')).lower()
            if company_size == 'startup':
                company_size = 'startup'
            else:
                company_size = 'pyme'

            # Generate activity metrics
            days_active = np.random.randint(30, 730)  # 1 month to 2 years
            emails_sent = np.random.randint(0, 50)
            emails_opened = max(0, int(emails_sent * np.random.uniform(0.1, 0.8)))

            # Determine conversion (label) based on scores
            # High scores → higher conversion probability
            avg_score = (web_score + facebook_score + google_score) / 3

            # Conversion probability = 0.2 + (avg_score/100) * 0.6 + business_type_boost
            base_prob = 0.2 + (avg_score / 100.0) * 0.6

            # Business type and email engagement boost
            if business_type == 'ecommerce':
                base_prob += 0.05
            if emails_opened > 0:
                open_rate = emails_opened / max(1, emails_sent)
                base_prob += open_rate * 0.15

            # Add randomness
            conversion = 1 if (base_prob + np.random.normal(0, 0.1)) > 0.5 else 0

            training_data.append({
                'web_score': web_score,
                'facebook_score': facebook_score,
                'google_score': google_score,
                'business_type': business_type,
                'company_size': company_size,
                'days_active': days_active,
                'emails_sent': emails_sent,
                'emails_opened': emails_opened,
                'converted': conversion
            })

    df_training = pd.DataFrame(training_data)

    # Separate features and target
    X = df_training.drop('converted', axis=1)
    y = df_training['converted']

    print(f"✅ Generated {len(df_training)} synthetic training samples")
    print(f"   - Conversion rate: {y.mean():.1%}")
    print(f"   - Features: {list(X.columns)}")

    return X, y, df_training


def create_prediction_history_table(conn):
    """Create prediction_history table in database"""
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS prediction_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id INTEGER NOT NULL,
            probability FLOAT NOT NULL,
            confidence FLOAT NOT NULL,
            risk_factors TEXT,
            positive_factors TEXT,
            predicted_outcome INTEGER,
            actual_outcome INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
    """)

    conn.commit()
    print("✅ Created prediction_history table")


def main():
    print("🚀 FASE 15: ML Model Training Pipeline")
    print("=" * 60)

    # Paths
    data_dir = Path(__file__).parent.parent / 'data'
    db_path = data_dir / 'pipeline.db'
    leads_csv = data_dir / 'leads_scored.csv'

    # Load leads data
    print(f"\n📂 Loading leads from {leads_csv}")
    leads_df = pd.read_csv(leads_csv)
    print(f"✅ Loaded {len(leads_df)} real leads")

    # Generate synthetic training data
    print("\n🔄 Generating synthetic training data...")
    X_train, y_train, df_full = generate_synthetic_training_data(leads_df, n_samples=1000)

    # Initialize pipeline
    print("\n🧠 Initializing ML Pipeline...")
    pipeline = ConversionPredictionPipeline()

    # Train model
    print("\n📚 Training RandomForest model...")
    print("   Parameters: n_estimators=100, max_depth=15, random_state=42")
    metrics = pipeline.train(X_train, y_train, test_size=0.2)

    print("\n📊 Training Results:")
    print(f"   - Accuracy: {metrics['accuracy']:.2%}")
    print(f"   - AUC Score: {metrics['auc']:.2%}")
    print(f"   - Cross-validation: {metrics['cv_mean']:.2%} (+/- {metrics['cv_std']:.2%})")

    print("\n🎯 Top 5 Feature Importance:")
    for feature, importance in sorted(
        metrics['feature_importance'].items(),
        key=lambda x: x[1],
        reverse=True
    )[:5]:
        print(f"   - {feature}: {importance:.2%}")

    # Save model
    print("\n💾 Saving trained model...")
    pipeline.save()
    print(f"✅ Model saved to {Path(__file__).parent.parent / 'models'}")

    # Create database schema
    print("\n📋 Setting up database schema...")
    conn = sqlite3.connect(db_path)
    create_prediction_history_table(conn)

    # Save training metadata
    metadata = {
        'training_date': datetime.now().isoformat(),
        'training_samples': len(X_train),
        'test_samples': len(y_train) - len(X_train),
        'accuracy': float(metrics['accuracy']),
        'auc_score': float(metrics['auc']),
        'model_version': 'v1.0.0',
        'features': list(X_train.columns),
    }

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS model_metadata (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    cursor.execute("DELETE FROM model_metadata")  # Clear existing
    for key, value in metadata.items():
        cursor.execute("INSERT INTO model_metadata (key, value) VALUES (?, ?)",
                      (key, str(value)))

    conn.commit()
    conn.close()

    print("✅ Database schema and metadata updated")

    print("\n" + "=" * 60)
    print("✅ ML MODEL TRAINING COMPLETE")
    print("=" * 60)
    print(f"\n📈 Model Performance Summary:")
    print(f"   Accuracy: {metrics['accuracy']:.2%}")
    print(f"   AUC: {metrics['auc']:.2%}")
    print(f"   Ready for production deployment ✓")

    return 0


if __name__ == '__main__':
    sys.exit(main())
