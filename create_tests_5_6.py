#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crear A/B Tests 5, 6 para expansión de validación paralela
Email types: webinar_invitation, case_study
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def create_test_5_webinar():
    """Test 5: webinar_invitation email type"""
    return {
        'test_name': 'FASE15 Phase3 - Webinar Engagement Test',
        'email_type': 'webinar_invitation',
        'variant_a_subject': 'Invitación: Webinar Gratuito - Estrategia Digital 2026',
        'variant_a_body': 'Únete a nuestro expertos en una sesión de 60 minutos. Aprenderás cómo optimizar tu presencia digital y aumentar conversiones.',
        'variant_b_subject': 'Tu Asiento Está Reservado: Masterclass de Transformación Digital',
        'variant_b_body': 'Solo quedan 12 espacios para esta masterclass exclusiva. Descubre las tácticas que usan las empresas más exitosas para escalar.',
        'planned_duration_days': 7
    }

def create_test_6_case_study():
    """Test 6: case_study email type"""
    return {
        'test_name': 'FASE15 Phase3 - Case Study Social Proof Test',
        'email_type': 'case_study',
        'variant_a_subject': 'Caso de Éxito: +320% ROI en 90 Días',
        'variant_a_body': 'Lee cómo otra empresa en tu industria logró triplicar su retorno de inversión. Descubre su proceso paso a paso.',
        'variant_b_subject': 'Cliente Destacado: De Crisis a Crecimiento Exponencial',
        'variant_b_body': 'Descubre la historia de transformación de una empresa que pasó de perder oportunidades a liderar su mercado. Resultados: +400% leads.',
        'planned_duration_days': 14
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
    """Crear 2 tests adicionales"""
    db = sqlite3.connect('data/pipeline.sqlite')
    cursor = db.cursor()

    print("=" * 80)
    print("🚀 CREANDO A/B TESTS ADICIONALES (5, 6) - EXPANSIÓN PARALELA")
    print("=" * 80)

    tests = [
        ("Test 5 (webinar_invitation)", create_test_5_webinar()),
        ("Test 6 (case_study)", create_test_6_case_study())
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
    print("✅ RESUMEN DE TESTS EN PRODUCCIÓN")
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
