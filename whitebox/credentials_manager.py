#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Credentials Manager - FASE 9
Gestión segura de credenciales con encriptación y TTL
"""

import os
import json
import logging
from typing import Dict, Optional
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CredentialsManager:
    """Gestor seguro de credenciales con encriptación Fernet y TTL"""

    def __init__(self, master_key: Optional[str] = None, ttl_seconds: int = 3600):
        """
        Inicializa el gestor de credenciales

        Args:
            master_key: Clave maestra para Fernet (si None, busca en env var WHITEBOX_MASTER_KEY)
            ttl_seconds: Tiempo de vida de credenciales en segundos (default: 1 hora)
        """
        self.ttl_seconds = ttl_seconds

        # Obtener clave maestra
        if master_key is None:
            master_key = os.getenv('WHITEBOX_MASTER_KEY')

        if not master_key:
            # Generar nueva clave si no existe
            master_key = Fernet.generate_key().decode()
            logger.warning("⚠️  No WHITEBOX_MASTER_KEY found. Generar nueva clave:")
            logger.warning(f"   export WHITEBOX_MASTER_KEY={master_key}")

        self.cipher = Fernet(master_key.encode() if isinstance(master_key, str) else master_key)
        self._credentials_store = {}  # En memoria con TTL
        logger.info("✅ CredentialsManager inicializado")

    def encrypt_credentials(self, platform: str, creds: Dict) -> str:
        """
        Encripta credenciales usando Fernet

        Args:
            platform: Plataforma (shopify, jumpseller, code)
            creds: Diccionario con credenciales

        Returns:
            String encriptado
        """
        try:
            creds_json = json.dumps(creds)
            encrypted = self.cipher.encrypt(creds_json.encode())

            # Guardar en memoria con timestamp
            self._credentials_store[platform] = {
                'encrypted': encrypted,
                'created_at': datetime.now(),
                'expires_at': datetime.now() + timedelta(seconds=self.ttl_seconds)
            }

            logger.info(f"✅ Credenciales encriptadas para {platform}")
            return encrypted.decode()

        except Exception as e:
            logger.error(f"❌ Error encriptando credenciales: {e}")
            raise

    def decrypt_credentials(self, platform: str, encrypted_data: Optional[str] = None) -> Dict:
        """
        Desencripta credenciales

        Args:
            platform: Plataforma (shopify, jumpseller, code)
            encrypted_data: Datos encriptados (si None, busca en memoria)

        Returns:
            Diccionario con credenciales
        """
        try:
            # Si no se pasa encrypted_data, buscar en memoria
            if encrypted_data is None:
                if platform not in self._credentials_store:
                    raise ValueError(f"No credentials found for {platform}")

                store = self._credentials_store[platform]

                # Verificar TTL
                if datetime.now() > store['expires_at']:
                    del self._credentials_store[platform]
                    raise ValueError(f"Credenciales expiradas para {platform}")

                encrypted_data = store['encrypted']

            # Desencriptar
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode()

            decrypted = self.cipher.decrypt(encrypted_data)
            creds = json.loads(decrypted.decode())

            logger.info(f"✅ Credenciales desencriptadas para {platform}")
            return creds

        except Exception as e:
            logger.error(f"❌ Error desencriptando credenciales: {e}")
            raise

    def validate_shopify_token(self, token: str) -> bool:
        """
        Valida formato de token de Shopify

        Args:
            token: Access token de Shopify

        Returns:
            True si formato válido
        """
        try:
            if not token or len(token) < 10:
                logger.warning("❌ Token de Shopify inválido (muy corto)")
                return False

            # Token de Shopify generalmente comienza con shpat_
            if not token.startswith('shpat_'):
                logger.warning("⚠️  Token de Shopify no comienza con 'shpat_' - podría ser inválido")

            logger.info("✅ Token de Shopify validado")
            return True

        except Exception as e:
            logger.error(f"❌ Error validando token de Shopify: {e}")
            return False

    def validate_jumpseller_key(self, api_key: str) -> bool:
        """
        Valida formato de API key de Jumpseller

        Args:
            api_key: API key de Jumpseller

        Returns:
            True si formato válido
        """
        try:
            if not api_key or len(api_key) < 10:
                logger.warning("❌ API key de Jumpseller inválida (muy corta)")
                return False

            logger.info("✅ API key de Jumpseller validada")
            return True

        except Exception as e:
            logger.error(f"❌ Error validando API key de Jumpseller: {e}")
            return False

    def validate_ssh_credentials(self, ssh_host: str, ssh_user: str, ssh_password: Optional[str] = None,
                                ssh_key_path: Optional[str] = None) -> bool:
        """
        Valida credenciales SSH

        Args:
            ssh_host: Host SSH
            ssh_user: Usuario SSH
            ssh_password: Contraseña SSH (opcional)
            ssh_key_path: Ruta a clave SSH (opcional)

        Returns:
            True si credenciales válidas
        """
        try:
            if not ssh_host or not ssh_user:
                logger.warning("❌ Host o usuario SSH vacío")
                return False

            if not ssh_password and not ssh_key_path:
                logger.warning("❌ SSH requiere password o key path")
                return False

            if ssh_key_path and not Path(ssh_key_path).exists():
                logger.warning(f"❌ Archivo de clave SSH no encontrado: {ssh_key_path}")
                return False

            logger.info("✅ Credenciales SSH validadas")
            return True

        except Exception as e:
            logger.error(f"❌ Error validando credenciales SSH: {e}")
            return False

    def cleanup_expired_credentials(self) -> int:
        """
        Limpia credenciales expiradas por TTL

        Returns:
            Número de credenciales eliminadas
        """
        try:
            now = datetime.now()
            expired_platforms = []

            for platform, store in self._credentials_store.items():
                if now > store['expires_at']:
                    expired_platforms.append(platform)

            for platform in expired_platforms:
                del self._credentials_store[platform]
                logger.info(f"🗑️  Credenciales de {platform} eliminadas (expiradas)")

            return len(expired_platforms)

        except Exception as e:
            logger.error(f"❌ Error limpiando credenciales: {e}")
            return 0

    def cleanup_platform_credentials(self, platform: str) -> bool:
        """
        Limpia credenciales de una plataforma específica

        Args:
            platform: Plataforma (shopify, jumpseller, code)

        Returns:
            True si se eliminaron
        """
        try:
            if platform in self._credentials_store:
                del self._credentials_store[platform]
                logger.info(f"🗑️  Credenciales de {platform} eliminadas explícitamente")
                return True

            return False

        except Exception as e:
            logger.error(f"❌ Error limpiando credenciales de {platform}: {e}")
            return False

    def get_credentials_status(self) -> Dict:
        """
        Retorna estado actual de credenciales almacenadas

        Returns:
            Diccionario con estado (sin mostrar datos sensibles)
        """
        status = {}
        now = datetime.now()

        for platform, store in self._credentials_store.items():
            expires_in = (store['expires_at'] - now).total_seconds()
            status[platform] = {
                'stored': True,
                'created_at': store['created_at'].isoformat(),
                'expires_at': store['expires_at'].isoformat(),
                'expires_in_seconds': int(expires_in),
                'expired': expires_in <= 0
            }

        return status


def main():
    """Testing del CredentialsManager"""
    print("""
╔════════════════════════════════════════════════════════════════╗
║       CREDENTIALS MANAGER - TEST                              ║
║         Gestión Segura de Credenciales                        ║
╚════════════════════════════════════════════════════════════════╝
    """)

    # Inicializar manager
    manager = CredentialsManager(ttl_seconds=3600)

    # 1. Probar encriptación Shopify
    print("\n1️⃣ ENCRIPTACIÓN - Shopify")
    print("-" * 70)
    shopify_creds = {
        "store": "example.myshopify.com",
        "access_token": "shpat_1234567890abcdef"
    }

    encrypted_shopify = manager.encrypt_credentials("shopify", shopify_creds)
    print(f"✅ Credenciales Shopify encriptadas (primeros 50 chars)")
    print(f"   {encrypted_shopify[:50]}...")

    # 2. Probar validación
    print("\n2️⃣ VALIDACIÓN - Tokens")
    print("-" * 70)
    is_valid_shopify = manager.validate_shopify_token("shpat_1234567890abcdef")
    print(f"✅ Shopify token válido: {is_valid_shopify}")

    is_valid_jumpseller = manager.validate_jumpseller_key("abc123def456ghi789jkl")
    print(f"✅ Jumpseller API key válida: {is_valid_jumpseller}")

    # 3. Probar desencriptación
    print("\n3️⃣ DESENCRIPTACIÓN")
    print("-" * 70)
    decrypted = manager.decrypt_credentials("shopify")
    print(f"✅ Credenciales desencriptadas:")
    print(f"   Store: {decrypted['store']}")
    print(f"   Token: {decrypted['access_token'][:20]}...")

    # 4. Probar estado
    print("\n4️⃣ ESTADO DE CREDENCIALES")
    print("-" * 70)
    status = manager.get_credentials_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))

    # 5. Probar limpieza explícita
    print("\n5️⃣ LIMPIEZA EXPLÍCITA")
    print("-" * 70)
    cleaned = manager.cleanup_platform_credentials("shopify")
    print(f"✅ Credenciales de shopify eliminadas: {cleaned}")

    status_after = manager.get_credentials_status()
    print(f"✅ Credenciales restantes: {len(status_after)}")

    print("\n" + "=" * 70)
    print("✅ CredentialsManager testeado correctamente")
    print("=" * 70)


if __name__ == "__main__":
    main()
