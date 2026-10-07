#!/usr/bin/env python3
"""
Test script for ML-based predictions
Tests the trained model integration without needing the full FastAPI server
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from api.ml_pipeline import pipeline
import pandas as pd

def test_ml_predictions():
    """Test ML model predictions on various client profiles"""

    print("🧪 Testing ML-Based Predictions")
    print("=" * 70)

    # Load model
    print("\n📂 Loading trained model...")
    try:
        pipeline.load()
        print("✅ Model loaded successfully")
    except FileNotFoundError:
        print("❌ Model not found. Run train_ml_model.py first")
        return 1

    # Test cases: different client profiles
    test_cases = [
        {
            "name": "High-potential ecommerce client",
            "web_score": 85,
            "facebook_score": 90,
            "google_score": 88,
            "business_type": "ecommerce",
            "company_size": "pyme",
            "emails_sent": 20,
            "emails_opened": 15,
        },
        {
            "name": "Medium-potential service client",
            "web_score": 65,
            "facebook_score": 70,
            "google_score": 75,
            "business_type": "services",
            "company_size": "startup",
            "emails_sent": 10,
            "emails_opened": 4,
        },
        {
            "name": "Low-potential retail client",
            "web_score": 40,
            "facebook_score": 35,
            "google_score": 38,
            "business_type": "retail",
            "company_size": "pyme",
            "emails_sent": 5,
            "emails_opened": 0,
        },
        {
            "name": "Inconsistent scores (high variance)",
            "web_score": 90,
            "facebook_score": 50,
            "google_score": 20,
            "business_type": "ecommerce",
            "company_size": "pyme",
            "emails_sent": 15,
            "emails_opened": 8,
        },
    ]

    results = []

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'─' * 70}")
        print(f"Test {i}: {test_case['name']}")
        print(f"{'─' * 70}")

        # Prepare input dataframe
        input_data = pd.DataFrame([{
            'web_score': test_case['web_score'],
            'facebook_score': test_case['facebook_score'],
            'google_score': test_case['google_score'],
            'business_type': test_case['business_type'],
            'company_size': test_case['company_size'],
            'emails_sent': test_case['emails_sent'],
            'emails_opened': test_case['emails_opened'],
        }])

        # Get predictions
        predictions, probabilities, shap_values = pipeline.predict(input_data)

        # Get explanation
        explanation = pipeline.explain_prediction(input_data, prediction_idx=0)

        # Display results
        print(f"  📊 Input Scores:")
        print(f"     - Web: {test_case['web_score']}")
        print(f"     - Facebook: {test_case['facebook_score']}")
        print(f"     - Google: {test_case['google_score']}")

        print(f"\n  🎯 Prediction Results:")
        print(f"     - Predicted Outcome: {'✅ CONVERT' if predictions[0] == 1 else '❌ NO CONVERT'}")
        print(f"     - Conversion Probability: {probabilities[0]:.1%}")
        print(f"     - Model Confidence: {explanation['probability']:.1%}")

        print(f"\n  📈 Top Positive Factors:")
        if explanation['positive_factors']:
            for factor in explanation['positive_factors'][:3]:
                print(f"     + {factor['feature']}: {factor['impact']:.3f}")
        else:
            print(f"     (None)")

        print(f"\n  📉 Top Negative Factors:")
        if explanation['negative_factors']:
            for factor in explanation['negative_factors'][:3]:
                print(f"     - {factor['feature']}: {factor['impact']:.3f}")
        else:
            print(f"     (None)")

        results.append({
            'test': test_case['name'],
            'prediction': 'CONVERT' if predictions[0] == 1 else 'NO CONVERT',
            'probability': probabilities[0],
        })

    # Summary
    print(f"\n{'═' * 70}")
    print("📋 Test Summary")
    print(f"{'═' * 70}")

    for result in results:
        emoji = "✅" if result['prediction'] == "CONVERT" else "❌"
        print(f"{emoji} {result['test']}: {result['probability']:.1%} conversion")

    # Validate model status
    print(f"\n📊 Model Status:")
    status = pipeline.get_status()
    print(f"   - Model Trained: {status['model_trained']}")
    print(f"   - Features: {len(status['feature_names'])} ({', '.join(status['feature_names'][:3])}...)")
    print(f"   - Feature Importance: {len(status['feature_importance'])} features analyzed")

    print("\n✅ All tests completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(test_ml_predictions())
