"""
ML Pipeline for Conversion Probability Predictions
Uses scikit-learn RandomForest with SHAP explainability

FASE 15: Advanced ML Predictions with Real-time Broadcasting
"""
import pickle
import logging
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    accuracy_score,
)

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logging.warning("SHAP library not installed - explainability disabled")

logger = logging.getLogger(__name__)

# Models directory
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
MODELS_DIR.mkdir(exist_ok=True)

MODEL_PATH = MODELS_DIR / "conversion_predictor_v1.pkl"
SCALER_PATH = MODELS_DIR / "feature_scaler_v1.pkl"
METADATA_PATH = MODELS_DIR / "model_metadata_v1.pkl"


class ConversionPredictionPipeline:
    """ML Pipeline for converting client attributes to conversion probability"""

    def __init__(self):
        self.model: Optional[RandomForestClassifier] = None
        self.scaler: Optional[StandardScaler] = None
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.feature_names: List[str] = []
        self.feature_importance: Dict[str, float] = {}
        self.explainer: Optional[object] = None
        self.metadata: Dict = {
            "trained_at": None,
            "accuracy": None,
            "auc_score": None,
            "model_version": "v1",
        }

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ML model

        Expected columns:
        - web_score: 0-100
        - facebook_score: 0-100
        - google_score: 0-100
        - business_type: string
        - company_size: string
        - days_active: int
        - emails_sent: int
        - emails_opened: int
        """
        df_prepared = df.copy()

        # Numeric features: scale 0-100 to 0-1
        numeric_cols = ["web_score", "facebook_score", "google_score"]
        for col in numeric_cols:
            if col in df_prepared.columns:
                df_prepared[col] = df_prepared[col] / 100.0

        # Categorical: encode
        categorical_cols = ["business_type", "company_size"]
        for col in categorical_cols:
            if col in df_prepared.columns:
                if col not in self.label_encoders:
                    self.label_encoders[col] = LabelEncoder()
                    df_prepared[col] = self.label_encoders[col].fit_transform(
                        df_prepared[col].astype(str)
                    )
                else:
                    # Handle unseen categories by mapping them to the most common one
                    try:
                        df_prepared[col] = self.label_encoders[col].transform(
                            df_prepared[col].astype(str)
                        )
                    except ValueError as e:
                        # Unseen category - map to most common value (index 0)
                        logger.warning(f"⚠️ Unseen category in {col}: {e}. Using default encoding.")
                        default_code = 0
                        df_prepared[col] = df_prepared[col].map(
                            lambda x: default_code if x not in self.label_encoders[col].classes_
                            else self.label_encoders[col].transform([str(x)])[0]
                        )

        # Engineered features
        if "emails_sent" in df_prepared.columns and "emails_opened" in df_prepared.columns:
            df_prepared["email_open_rate"] = (
                df_prepared["emails_opened"] /
                (df_prepared["emails_sent"] + 1)  # Avoid division by zero
            )

        # Select final features
        feature_cols = [
            "web_score",
            "facebook_score",
            "google_score",
            "business_type",
            "company_size",
            "email_open_rate",
        ]

        self.feature_names = [col for col in feature_cols if col in df_prepared.columns]
        return df_prepared[self.feature_names]

    def train(
        self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.2
    ) -> Dict:
        """
        Train RandomForest model on historical data

        Args:
            X: Feature matrix (clients × features)
            y: Target labels (0=not converted, 1=converted)
            test_size: Proportion for test split

        Returns:
            Training metrics dictionary
        """
        logger.info(f"🚀 Starting model training with {len(X)} samples")

        # Prepare features
        X_prepared = self.prepare_features(X)

        # Scale features
        self.scaler = StandardScaler()
        X_scaled = self.scaler.fit_transform(X_prepared)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size, random_state=42, stratify=y
        )

        logger.info(
            f"📊 Training set: {len(X_train)} samples | Test set: {len(X_test)} samples"
        )

        # Train RandomForest
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,  # Use all CPUs
        )

        self.model.fit(X_train, y_train)
        logger.info("✅ Model training complete")

        # Evaluate
        y_pred = self.model.predict(X_test)
        y_pred_proba = self.model.predict_proba(X_test)[:, 1]

        accuracy = accuracy_score(y_test, y_pred)
        auc = roc_auc_score(y_test, y_pred_proba)

        logger.info(f"📈 Accuracy: {accuracy:.2%} | AUC: {auc:.2%}")
        logger.info(f"\n{classification_report(y_test, y_pred)}")

        # Feature importance
        self.feature_importance = dict(
            zip(self.feature_names, self.model.feature_importances_)
        )
        logger.info(f"🎯 Top features: {sorted(self.feature_importance.items(), key=lambda x: x[1], reverse=True)[:5]}")

        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train, y_train, cv=5)
        logger.info(f"📊 Cross-validation scores: {cv_scores.mean():.2%} (+/- {cv_scores.std():.2%})")

        # Setup SHAP if available
        if SHAP_AVAILABLE:
            logger.info("🔍 Computing SHAP explanations...")
            try:
                self.explainer = shap.TreeExplainer(self.model)
            except Exception as e:
                logger.warning(f"SHAP setup failed: {e}")

        # Store metadata
        self.metadata = {
            "trained_at": datetime.now().isoformat(),
            "accuracy": float(accuracy),
            "auc_score": float(auc),
            "model_version": "v1",
            "feature_names": self.feature_names,
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
        }

        return {
            "accuracy": accuracy,
            "auc": auc,
            "cv_mean": cv_scores.mean(),
            "cv_std": cv_scores.std(),
            "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
            "feature_importance": self.feature_importance,
        }

    def predict(self, X: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray, Optional[np.ndarray]]:
        """
        Generate predictions for new clients

        Returns:
            predictions: Binary predictions (0/1)
            probabilities: Conversion probabilities (0-1)
            shap_values: SHAP explanations (if available)
        """
        if self.model is None:
            raise ValueError("Model not trained. Call train() first.")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.transform(X_prepared)

        predictions = self.model.predict(X_scaled)
        probabilities = self.model.predict_proba(X_scaled)[:, 1]

        shap_values = None
        if SHAP_AVAILABLE and self.explainer:
            try:
                shap_values = self.explainer.shap_values(X_scaled)
            except Exception as e:
                logger.warning(f"SHAP prediction failed: {e}")

        return predictions, probabilities, shap_values

    def explain_prediction(self, X: pd.DataFrame, prediction_idx: int = 0) -> Dict:
        """
        Generate SHAP explanation for a single prediction

        Returns:
            Explanation with top positive and negative factors
        """
        if self.model is None:
            raise ValueError("Model not trained")

        X_prepared = self.prepare_features(X)
        X_scaled = self.scaler.transform(X_prepared)

        # Get prediction probability
        probability = self.model.predict_proba(X_scaled[prediction_idx:prediction_idx+1])[0, 1]

        explanation = {
            "probability": probability,
            "positive_factors": [],
            "negative_factors": [],
        }

        # Try SHAP
        if SHAP_AVAILABLE and self.explainer:
            try:
                shap_values = self.explainer.shap_values(X_scaled[prediction_idx:prediction_idx+1])

                # Get top factors
                factors = list(zip(self.feature_names, shap_values[1][0]))
                factors_sorted = sorted(factors, key=lambda x: abs(x[1]), reverse=True)

                for feature, impact in factors_sorted[:5]:
                    if impact > 0:
                        explanation["positive_factors"].append({
                            "feature": feature,
                            "impact": float(impact),
                        })
                    else:
                        explanation["negative_factors"].append({
                            "feature": feature,
                            "impact": float(abs(impact)),
                        })
            except Exception as e:
                logger.warning(f"SHAP explanation failed: {e}")

        return explanation

    def save(self, path: Optional[Path] = None):
        """Save trained model to disk"""
        if self.model is None:
            raise ValueError("No model to save")

        path = path or MODEL_PATH
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "wb") as f:
            pickle.dump(self.model, f)

        with open(SCALER_PATH, "wb") as f:
            pickle.dump(self.scaler, f)

        with open(METADATA_PATH, "wb") as f:
            pickle.dump(self.metadata, f)

        logger.info(f"✅ Model saved to {path}")

    def load(self, path: Optional[Path] = None):
        """Load trained model from disk"""
        path = path or MODEL_PATH

        if not path.exists():
            raise FileNotFoundError(f"Model not found at {path}")

        with open(path, "rb") as f:
            self.model = pickle.load(f)

        with open(SCALER_PATH, "rb") as f:
            self.scaler = pickle.load(f)

        with open(METADATA_PATH, "rb") as f:
            self.metadata = pickle.load(f)

        self.feature_names = self.metadata.get("feature_names", [])
        logger.info(f"✅ Model loaded from {path}")

    def get_status(self) -> Dict:
        """Get model status"""
        return {
            "model_trained": self.model is not None,
            "metadata": self.metadata,
            "feature_names": self.feature_names,
            "feature_importance": self.feature_importance,
        }


# Global pipeline instance
pipeline = ConversionPredictionPipeline()
