#!/usr/bin/env python3
"""
EJECUTAR OPCIÓN C
Script wrapper que ejecuta OPCIÓN C con la configuración centralizada
"""

import sys
import os
from pathlib import Path
import yaml

# Agregar paths
sys.path.insert(0, str(Path(__file__).parent))

from main_orchestrator import MainOrchestratorFase8


def load_config(config_path: str = "config.yaml") -> dict:
    """Cargar configuración"""
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Configuración no encontrada: {config_path}")
        return {}


def run_opcion_c(client_ids=None):
    """Ejecutar OPCIÓN C"""
    print("""
    ╔═════════════════════════════════════════════════════════════════╗
    ║                                                                 ║
    ║   🚀 FELIX AUTOMATION - OPCIÓN C                               ║
    ║      AGENTES DE VENTA AUTOMATIZADOS                            ║
    ║                                                                 ║
    ║   Versión: 8.0 | Estado: EN CONSTRUCCIÓN (FASE 1)             ║
    ║                                                                 ║
    ╚═════════════════════════════════════════════════════════════════╝
    """)
    
    # Cargar configuración
    config = load_config("config.yaml")
    
    print(f"✅ Configuración cargada")
    print(f"   - Database: {config.get('database', {}).get('path', 'data/pipeline.db')}")
    print(f"   - Email Provider: {config.get('email', {}).get('provider', 'sendgrid')}")
    print(f"   - Demo Mode: {config.get('email', {}).get('demo_mode', True)}")
    print()
    
    # Crear orquestador
    orchestrator = MainOrchestratorFase8()
    
    try:
        # Ejecutar pipeline
        summary = orchestrator.execute_complete_pipeline(client_ids)
        
        # Guardar resumen
        orchestrator.save_execution_summary(summary)
        
        print()
        print("=" * 60)
        print("✅ OPCIÓN C COMPLETADO EXITOSAMENTE")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    finally:
        orchestrator.close()


if __name__ == "__main__":
    # Puede recibir IDs de clientes como argumentos
    client_ids = None
    if len(sys.argv) > 1:
        try:
            client_ids = [int(x) for x in sys.argv[1:]]
        except ValueError:
            print("Uso: python3 run_opcion_c.py [client_id1] [client_id2] ...")
            sys.exit(1)
    
    exit_code = run_opcion_c(client_ids)
    sys.exit(exit_code)
