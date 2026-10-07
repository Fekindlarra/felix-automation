#!/usr/bin/env python3
"""
FASE 14 PASO 3: Generar datos de prueba para testing del pipeline real
Crea clientes en diferentes etapas del sales pipeline
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from orchestrator import FelixAutomationOrchestrator
from datetime import datetime, timedelta
import random

# Datos de prueba
SAMPLE_COMPANIES = [
    {"name": "TechVentures Chile", "industry": "Software", "website": "techventures.cl"},
    {"name": "E-Commerce Plus", "industry": "Retail", "website": "ecommerceplus.cl"},
    {"name": "Marketing Solutions", "industry": "Marketing", "website": "marketsol.cl"},
    {"name": "Digital Agency Pro", "industry": "Agencia", "website": "dagencyp.ro"},
    {"name": "Startup Accelerator", "industry": "Startups", "website": "startupaccel.cl"},
    {"name": "Fashion Store Online", "industry": "Moda", "website": "fashionstoreonline.cl"},
    {"name": "Restaurant Network", "industry": "Gastronomía", "website": "restaurantnetwork.cl"},
    {"name": "Real Estate Plus", "industry": "Inmobiliario", "website": "realestateplus.cl"},
    {"name": "Tourism Solutions", "industry": "Turismo", "website": "tourismsol.cl"},
    {"name": "Financial Tech", "industry": "Fintech", "website": "fintech.cl"},
]

STAGES = ["prospecto", "propuesta", "negociacion", "cerrado"]

class ClientMock:
    """Mock de cliente para testing"""
    def __init__(self, id, name, email, company, website, industry, stage, created_days_ago):
        self.id = id
        self.name = name
        self.email = email
        self.company = company
        self.website = website
        self.industry = industry
        self.stage = stage
        self.created_at = (datetime.now() - timedelta(days=created_days_ago)).isoformat()
        self.audit_type = random.choice(['quick', 'complete', 'deep'])
        self.phone = f"+56{random.randint(9,9)}{random.randint(1000000000, 9999999999)}"
        self.message = f"Interesado en auditoría {self.audit_type}"


def generate_sample_clients():
    """Generar clientes de ejemplo en diferentes etapas"""

    print("🌱 Generando datos de prueba para PASO 3...\n")

    orch = FelixAutomationOrchestrator(db_path='database.sqlite')
    orch.connect_database()

    clients_data = []
    client_id = 1

    # Distribuir clientes por etapa
    # Prospecto: 4 clientes (recientes)
    # Propuesta: 3 clientes (hace 5-10 días)
    # Negociación: 2 clientes (hace 15-20 días)
    # Cerrado: 1 cliente (hace 25+ días)

    distribution = {
        "prospecto": {"count": 4, "days_range": (1, 3)},
        "propuesta": {"count": 3, "days_range": (5, 10)},
        "negociacion": {"count": 2, "days_range": (15, 20)},
        "cerrado": {"count": 1, "days_range": (25, 30)},
    }

    company_idx = 0

    for stage, config in distribution.items():
        for i in range(config["count"]):
            if company_idx >= len(SAMPLE_COMPANIES):
                break

            company_data = SAMPLE_COMPANIES[company_idx]
            days_ago = random.randint(config["days_range"][0], config["days_range"][1])

            client = ClientMock(
                id=client_id,
                name=f"{company_data['name'].split()[0]} Contact",
                email=f"contact{client_id}@{company_data['website'].split('.')[0]}.cl",
                company=company_data["name"],
                website=company_data["website"],
                industry=company_data["industry"],
                stage=stage,
                created_days_ago=days_ago
            )

            clients_data.append(client)
            orch.clients_cache[client_id] = client

            print(f"✅ [{client_id}] {client.company:<25} {stage:<15} (Hace {days_ago} días)")

            client_id += 1
            company_idx += 1

    print(f"\n📊 Total clientes generados: {len(clients_data)}")
    print("\n📈 Distribución por etapa:")
    for stage in STAGES:
        count = sum(1 for c in clients_data if c.stage == stage)
        if count > 0:
            print(f"   {stage.capitalize():<15}: {count} clientes")

    print("\n✅ Datos de prueba listos para PASO 3")
    print("   El dashboard mostrará pipeline completo con predicciones para cada cliente")

    return clients_data


if __name__ == "__main__":
    generate_sample_clients()
