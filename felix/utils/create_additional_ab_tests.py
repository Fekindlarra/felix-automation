#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crear A/B Tests 2, 3, 4 para validación paralela en Producción
Email types: proposal, audit_report, followup_2
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def create_test_2_proposal():
    """Test 2: proposal email type"""
    return {
        'test_name': 'FASE15 Phase3 - Proposal Optimization Test',
        'email_type': 'proposal',
        'variant_a_subject': 'Tu Propuesta de Optimización Personalizada',
        'variant_a_body': 'Basada en tu análisis, recomendamos estas mejoras específicas para tu negocio.',
        'variant_b_subject': 'Propuesta Exclusiva: Plan de Transformación Digital',
        'variant_b_body': 'Hemos diseñado un plan custom que maximiza ROI en 90 días. Mira los resultados.',
        'planned_duration_days': 14
    }

def create_test_3_audit_report():
    """Test 3: audit_report email type"""
    return {
        'test_name': 'FASE15 Phase3 - Audit Report Engagement Test',
        'email_type': 'audit_report',
        'variant_a_subject': 'Tu Auditoría Completa está Lista',
        'variant_a_body': 'Revisamos tu presencia digital en 3 plataformas. Descubre dónde estás ganando y dónde pierdes oportunidades.',
        'variant_b_subject': 'Reporte de Oportunidades Encontradas',
        'variant_b_body': 'Identificamos 12 oportunidades de crecimiento en tu estrategia actual. Accede al análisis detallado ahora.',
        'planned_duration_days': 14
    }

def create_test_4_followup_2():
    """Test 4: followup_2 email type"""
    return {
        'test_name': 'FASE15 Phase3 - Second Followup Conversion Test',
        'email_type': 'followup_2',
        'variant_a_subject': 'Seguimiento: ¿Dudas sobre tu auditoría?',
        'variant_a_body': 'Muchos clientes tienen preguntas después de revisar el reporte. Estoy aquí para ayudarte.',
        'variant_b_subject': 'Última Oportunidad: Validación Gratuita de Tu Plan',
        'variant_b_body': 'Te ofrecemos 1 sesión gratis para revisar juntos tu propuesta. Últimos 2 espacios disponibles.',
        'planned_duration_days': 7
    }

def insert_test(cursor, conn, test_data):
    """Insertar test en BD"""
    cursor.execute("""
        INSERT INTO ab_tests
        (test_name, email_type, variant_a_subject, variant_a_body,
         variant_b_subject, variant_b_body, active, planned_duration_days)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
    """, (
        test_data['test_name'],
        test_data['email_type'],
        test_data['variant_a_subject'],
        test_data['variant_a_body'],
        test_data['variant_b_subject'],
        test_data['variant_b_body'],
        test_data['planned_duration_days']
    ))
    conn.commit()
    return cursor.lastrowid

def main():
    """Crear 3 tests adicionales"""
    db = sqlite3.connect('data/pipeline.sqlite')
    cursor = db.cursor()

    print("=" * 80)
    print("🚀 CREANDO A/B TESTS ADICIONALES (2, 3, 4)")
    print("=" * 80)

    tests = [
        ("Test 2 (proposal)", create_test_2_proposal()),
        ("Test 3 (audit_report)", create_test_3_audit_report()),
        ("Test 4 (followup_2)", create_test_4_followup_2())
    ]

    created_tests = []

    for test_name, test_data in tests:
        print(f"\n📝 Creando {test_name}...")
        try:
            test_id = insert_test(cursor, db, test_data)
            created_tests.append({
                'id': test_id,
                'name': test_data['test_name'],
                'type': test_data['email_type']
            })
            print(f"   ✅ Test {test_id} creado: {test_data['test_name']}")
            print(f"   Email Type: {test_data['email_type']}")
            print(f"   Variante A: {test_data['variant_a_subject']}")
            print(f"   Variante B: {test_data['variant_b_subject']}")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Verificar tests creados
    print("\n" + "=" * 80)
    print("✅ RESUMEN DE TESTS CREADOS")
    print("=" * 80)

    cursor.execute("SELECT id, test_name, email_type, active FROM ab_tests ORDER BY id")
    all_tests = cursor.fetchall()

    print(f"\nTotal A/B Tests en Producción: {len(all_tests)}")
    for test in all_tests:
        status = "🟢 ACTIVO" if test[3] else "⚫ COMPLETADO"
        print(f"  Test {test[0]}: {test[1]}")
        print(f"    Email Type: {test[2]} {status}")

    db.close()

    return created_tests

if __name__ == "__main__":
    created = main()
    print("\n" + "=" * 80)
    print(f"✅ {len(created)} tests adicionales creados exitosamente")
    print("=" * 80)
