"""
FASE 14 Configuration Loader
Loads and validates config.yaml for production deployment
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger(__name__)


@dataclass
class ShopifyConfig:
    """Shopify API Configuration"""
    enabled: bool
    api_version: str
    rate_limit_requests: int
    rate_limit_seconds: int
    webhook_validation: bool
    webhook_secret: str
    sync_enabled: bool
    sync_schedule: str

    def validate(self) -> bool:
        """Validate Shopify configuration"""
        if self.enabled:
            if not self.api_version:
                raise ValueError("shopify.api_version is required when enabled")
            if self.rate_limit_requests <= 0:
                raise ValueError("shopify rate_limit must be > 0")
            if self.webhook_validation and not self.webhook_secret:
                raise ValueError("shopify.webhook_secret required for validation")
        return True


@dataclass
class PredictionsConfig:
    """ML Predictions Configuration"""
    enabled: bool
    confidence_threshold: float
    batch_enabled: bool
    batch_schedule: str
    broadcast_enabled: bool
    broadcast_frequency: int
    high_priority_threshold: float
    anomaly_detection_enabled: bool

    def validate(self) -> bool:
        """Validate predictions configuration"""
        if self.enabled:
            if not (0 <= self.confidence_threshold <= 100):
                raise ValueError("predictions.confidence_threshold must be 0-100")
            if not (0 <= self.high_priority_threshold <= 100):
                raise ValueError("predictions.high_priority_threshold must be 0-100")
            if self.broadcast_frequency <= 0:
                raise ValueError("predictions.broadcast_frequency must be > 0")
        return True


@dataclass
class ABTestingConfig:
    """A/B Testing Configuration"""
    enabled: bool
    test_duration_days: int
    min_sample_size: int
    significance_threshold: float
    split_ratio: int
    assignment_method: str
    test_type: str
    confidence_level: float
    power_analysis_enabled: bool

    def validate(self) -> bool:
        """Validate A/B testing configuration"""
        if self.enabled:
            if self.test_duration_days <= 0:
                raise ValueError("ab_testing.test_duration_days must be > 0")
            if self.min_sample_size < 30:
                raise ValueError("ab_testing.min_sample_size must be >= 30 (statistical validity)")
            if not (0 < self.significance_threshold < 1):
                raise ValueError("ab_testing.significance_threshold must be 0 < p < 1")
            if not (0 <= self.confidence_level <= 1):
                raise ValueError("ab_testing.confidence_level must be 0-1")
            if self.split_ratio not in [50]:  # Can extend for unequal splits
                raise ValueError("ab_testing.split_ratio currently supports 50 only")
            if self.assignment_method not in ["hash_deterministic", "random"]:
                raise ValueError("ab_testing.assignment_method must be hash_deterministic or random")
        return True


@dataclass
class WebSocketConfig:
    """WebSocket Configuration"""
    enabled: bool
    host: str
    port: int
    ssl_enabled: bool
    max_connections: int
    heartbeat_desktop: int
    heartbeat_mobile: int
    auth_method: str
    jwt_secret: str

    def validate(self) -> bool:
        """Validate WebSocket configuration"""
        if self.enabled:
            if self.port <= 0 or self.port > 65535:
                raise ValueError("websocket.port must be 1-65535")
            if self.max_connections <= 0:
                raise ValueError("websocket.max_connections must be > 0")
            if self.heartbeat_desktop <= 0 or self.heartbeat_mobile <= 0:
                raise ValueError("websocket heartbeat intervals must be > 0")
            if self.auth_method != "jwt":
                raise ValueError("websocket.auth_method currently supports jwt only")
            if self.ssl_enabled and not self.jwt_secret:
                raise ValueError("websocket.jwt_secret required for auth")
        return True


@dataclass
class DatabaseConfig:
    """Database Configuration"""
    db_type: str
    path: str
    pool_size: int
    timeout: int

    def validate(self) -> bool:
        """Validate database configuration"""
        if self.db_type == "sqlite":
            if not self.path:
                raise ValueError("database.path is required")
            if self.pool_size <= 0:
                raise ValueError("database.pool_size must be > 0")
        return True


@dataclass
class ConfigSchema:
    """Complete FASE 14 Configuration Schema"""
    database: DatabaseConfig
    shopify: ShopifyConfig
    predictions: PredictionsConfig
    ab_testing: ABTestingConfig
    websocket: WebSocketConfig

    # Optional sections
    logging_level: str = "INFO"
    features: Dict[str, bool] = field(default_factory=dict)
    environment: str = "development"

    def validate_all(self) -> bool:
        """Validate all configuration sections"""
        try:
            self.database.validate()
            self.shopify.validate()
            self.predictions.validate()
            self.ab_testing.validate()
            self.websocket.validate()
            logger.info("✓ All configuration validations passed")
            return True
        except ValueError as e:
            logger.error(f"✗ Configuration validation failed: {e}")
            raise


class ConfigLoader:
    """Load and manage FASE 14 configuration"""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration loader

        Args:
            config_path: Path to config.yaml file
        """
        self.config_path = Path(config_path)
        self.raw_config: Dict[str, Any] = {}
        self.schema: Optional[ConfigSchema] = None
        self._encryption_key: Optional[bytes] = None

    def load(self) -> ConfigSchema:
        """
        Load and validate configuration

        Returns:
            ConfigSchema object with all settings
        """
        # Load YAML
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            self.raw_config = yaml.safe_load(f)
            logger.info(f"✓ Loaded config from {self.config_path}")

        # Substitute environment variables
        self._substitute_env_vars()
        logger.info("✓ Substituted environment variables")

        # Parse sections
        self.schema = self._parse_config()

        # Validate
        self.schema.validate_all()
        logger.info("✓ Configuration validation complete")

        return self.schema

    def _substitute_env_vars(self) -> None:
        """Replace ${VAR} placeholders with environment variables"""
        config_str = json.dumps(self.raw_config)

        # Find all ${...} patterns
        import re
        pattern = r'\$\{([A-Z_]+)\}'

        def replace_var(match):
            var_name = match.group(1)
            var_value = os.getenv(var_name)
            if var_value is None:
                logger.warning(f"⚠️  Environment variable not set: {var_name}")
                return match.group(0)  # Keep original if not found
            return var_value

        config_str = re.sub(pattern, replace_var, config_str)
        self.raw_config = json.loads(config_str)

    def _parse_config(self) -> ConfigSchema:
        """Parse raw config into typed ConfigSchema"""
        cfg = self.raw_config

        # Database
        db_cfg = cfg.get('database', {})
        database = DatabaseConfig(
            db_type=db_cfg.get('type', 'sqlite'),
            path=db_cfg.get('path', 'database.sqlite'),
            pool_size=db_cfg.get('pool_size', 5),
            timeout=db_cfg.get('timeout', 30)
        )

        # Shopify
        shop_cfg = cfg.get('shopify', {})
        rl = shop_cfg.get('rate_limit', {})
        shopify = ShopifyConfig(
            enabled=shop_cfg.get('enabled', True),
            api_version=shop_cfg.get('api_version', '2024-01'),
            rate_limit_requests=rl.get('max_requests', 2),
            rate_limit_seconds=rl.get('time_window_seconds', 1),
            webhook_validation=shop_cfg.get('webhook_validation', True),
            webhook_secret=shop_cfg.get('webhook_secret', os.getenv('SHOPIFY_WEBHOOK_SECRET', '')),
            sync_enabled=shop_cfg.get('sync', {}).get('enabled', True),
            sync_schedule=shop_cfg.get('sync', {}).get('schedule', '0 */6 * * *')
        )

        # Predictions
        pred_cfg = cfg.get('predictions', {})
        predictions = PredictionsConfig(
            enabled=pred_cfg.get('enabled', True),
            confidence_threshold=pred_cfg.get('scoring', {}).get('confidence_threshold', 50.0),
            batch_enabled=pred_cfg.get('batch', {}).get('enabled', True),
            batch_schedule=pred_cfg.get('batch', {}).get('schedule', '0 9 * * *'),
            broadcast_enabled=pred_cfg.get('broadcast', {}).get('enabled', True),
            broadcast_frequency=pred_cfg.get('broadcast', {}).get('frequency_seconds', 300),
            high_priority_threshold=pred_cfg.get('broadcast', {}).get('high_priority_threshold', 75.0),
            anomaly_detection_enabled=pred_cfg.get('anomaly_detection', {}).get('enabled', True)
        )

        # A/B Testing
        ab_cfg = cfg.get('ab_testing', {})
        ab_testing = ABTestingConfig(
            enabled=ab_cfg.get('enabled', True),
            test_duration_days=ab_cfg.get('testing', {}).get('default_test_duration_days', 14),
            min_sample_size=ab_cfg.get('testing', {}).get('min_sample_size', 30),
            significance_threshold=ab_cfg.get('testing', {}).get('significance_threshold', 0.05),
            split_ratio=ab_cfg.get('testing', {}).get('default_split_ratio', 50),
            assignment_method=ab_cfg.get('assignment', {}).get('method', 'hash_deterministic'),
            test_type=ab_cfg.get('statistics', {}).get('test_type', 'chi_square'),
            confidence_level=ab_cfg.get('statistics', {}).get('confidence_level', 0.95),
            power_analysis_enabled=ab_cfg.get('statistics', {}).get('power_analysis', True)
        )

        # WebSocket
        ws_cfg = cfg.get('websocket', {})
        websocket = WebSocketConfig(
            enabled=ws_cfg.get('enabled', True),
            host=ws_cfg.get('host', '0.0.0.0'),
            port=ws_cfg.get('port', 8001),
            ssl_enabled=ws_cfg.get('ssl', True),
            max_connections=ws_cfg.get('max_connections', 1000),
            heartbeat_desktop=ws_cfg.get('heartbeat_interval_desktop', 30),
            heartbeat_mobile=ws_cfg.get('heartbeat_interval_mobile', 60),
            auth_method=ws_cfg.get('auth', {}).get('method', 'jwt'),
            jwt_secret=ws_cfg.get('auth', {}).get('secret', os.getenv('JWT_SECRET', ''))
        )

        return ConfigSchema(
            database=database,
            shopify=shopify,
            predictions=predictions,
            ab_testing=ab_testing,
            websocket=websocket,
            logging_level=cfg.get('logging', {}).get('level', 'INFO'),
            features=cfg.get('features', {}),
            environment=os.getenv('ENVIRONMENT', 'development')
        )

    def get_shopify_client_config(self) -> Dict[str, Any]:
        """Get Shopify API client configuration"""
        cfg = self.schema.shopify
        return {
            'api_version': cfg.api_version,
            'rate_limit': cfg.rate_limit_requests,
            'time_window': cfg.rate_limit_seconds,
            'webhook_validation': cfg.webhook_validation,
            'webhook_secret': cfg.webhook_secret,
            'connection_pool_size': 5,
            'timeout': 30
        }

    def get_ab_testing_config(self) -> Dict[str, Any]:
        """Get A/B testing configuration"""
        cfg = self.schema.ab_testing
        return {
            'min_sample_size': cfg.min_sample_size,
            'significance_threshold': cfg.significance_threshold,
            'confidence_level': cfg.confidence_level,
            'test_type': cfg.test_type,
            'assignment_method': cfg.assignment_method,
            'default_split': cfg.split_ratio,
            'default_duration_days': cfg.test_duration_days,
            'power_analysis': cfg.power_analysis_enabled
        }

    def get_predictions_config(self) -> Dict[str, Any]:
        """Get predictions configuration"""
        cfg = self.schema.predictions
        return {
            'confidence_threshold': cfg.confidence_threshold,
            'broadcast_enabled': cfg.broadcast_enabled,
            'broadcast_frequency': cfg.broadcast_frequency,
            'high_priority_threshold': cfg.high_priority_threshold,
            'anomaly_detection': cfg.anomaly_detection_enabled,
            'batch_enabled': cfg.batch_enabled,
            'batch_schedule': cfg.batch_schedule
        }

    def print_summary(self) -> None:
        """Print configuration summary"""
        if not self.schema:
            print("⚠️  Configuration not loaded yet")
            return

        print("\n" + "="*60)
        print("FASE 14 CONFIGURATION SUMMARY")
        print("="*60)

        print(f"\n📊 Database: {self.schema.database.db_type}")
        print(f"   Path: {self.schema.database.path}")
        print(f"   Pool: {self.schema.database.pool_size} connections")

        print(f"\n🛍️  Shopify API:")
        print(f"   Enabled: {self.schema.shopify.enabled}")
        print(f"   API Version: {self.schema.shopify.api_version}")
        print(f"   Rate Limit: {self.schema.shopify.rate_limit_requests} req/{self.schema.shopify.rate_limit_seconds}s")
        print(f"   Webhooks: {self.schema.shopify.webhook_validation}")

        print(f"\n🤖 ML Predictions:")
        print(f"   Enabled: {self.schema.predictions.enabled}")
        print(f"   Confidence Threshold: {self.schema.predictions.confidence_threshold}%")
        print(f"   Batch Processing: {self.schema.predictions.batch_enabled}")
        print(f"   Anomaly Detection: {self.schema.predictions.anomaly_detection_enabled}")

        print(f"\n📧 A/B Testing:")
        print(f"   Enabled: {self.schema.ab_testing.enabled}")
        print(f"   Min Sample Size: {self.schema.ab_testing.min_sample_size}")
        print(f"   Significance: p < {self.schema.ab_testing.significance_threshold}")
        print(f"   Confidence: {self.schema.ab_testing.confidence_level*100}%")
        print(f"   Assignment: {self.schema.ab_testing.assignment_method}")

        print(f"\n🔌 WebSocket:")
        print(f"   Enabled: {self.schema.websocket.enabled}")
        print(f"   Port: {self.schema.websocket.port}")
        print(f"   Max Connections: {self.schema.websocket.max_connections}")
        print(f"   Auth: {self.schema.websocket.auth_method}")

        print(f"\n📝 Environment: {self.schema.environment}")
        print(f"   Log Level: {self.schema.logging_level}")

        print("\n" + "="*60)


def load_config(config_path: str = "config.yaml") -> ConfigSchema:
    """
    Convenience function to load configuration

    Args:
        config_path: Path to config.yaml

    Returns:
        Loaded and validated ConfigSchema
    """
    loader = ConfigLoader(config_path)
    return loader.load()


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Load and display
    try:
        loader = ConfigLoader("config.yaml")
        config = loader.load()
        loader.print_summary()
        print("\n✅ Configuration loaded successfully!")
    except Exception as e:
        print(f"\n❌ Configuration loading failed: {e}")
        exit(1)
