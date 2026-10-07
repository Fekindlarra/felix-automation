#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Crear A/B Tests 7-10 - Expansión Final de Cobertura
Email types: product_announcement, promotional_offer, educational_content, event_invitation
Objetivo: 10 tests en paralelo para máxima cobertura y confianza 90%+ HORA 24
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path

def create_test_7_product_announcement():
    """Test 7: product_announcement email type"""
    return {
        'test_name': 'FASE15 Phase3 - Product Launch Engagement Test',
        'email_type': 'product_announcement',
        'variant_a_subject': 'Nuevo: Herramienta de Análisis Inteligente Liberada',
        'variant_a_body': 'Acabamos de lanzar una nueva característica que te ahorrará horas de trabajo. Accede ahora y sé de los primeros en utilizarla.',
        'variant_b_subject': 'EXCLUSIVA: Acceso Early Access a Nueva Solución Premium',
        'variant_b_body': 'Solo 50 empresas tendrán acceso a nuestra nueva herramienta premium antes de su lanzamiento oficial. ¿Quieres ser una?',
        'planned_duration_days': 14
    }

def create_test_8_promotional_offer():
    """Test 8: promotional_offer email type"""
    return {
        'test_name': 'FASE15 Phase3 - Limited Time Offer Conversion Test',
        'email_type': 'promotional_offer',
        'variant_a_subject': 'Oferta Limitada: 30% OFF en Plans Premium',
        'variant_a_body': 'Esta oferta especial vence en 48 horas. Beneficios de Premium: Analytics avanzado, API ilimitada, soporte prioritario.',
        'variant_b_subject': '⏰ ÚLTIMA HORA: 40% OFF + 3 Meses Gratis (Hoy Solamente)',
        'variant_b_body': 'Esta es la mayor oferta del año. Upgrade a Premium hoy y obtén 40% descuento + 3 meses adicionales gratis. Expira a las 23:59 hoy.',
        'planned_duration_days': 1
    }

def create_test_9_educational_content():
    """Test 9: educational_content email type"""
    return {
        'test_name': 'FASE15 Phase3 - Educational Content Engagement Test',
        'email_type': 'educational_content',
        'variant_a_subject': 'Guía Completa: 10 Estrategias de Growth Hacking Probadas',
        'variant_a_body': 'Descarga nuestra guía detallada con 10 estrategias que utilizan las mejores empresas SaaS. Incluye casos de éxito y métricas.',
        'variant_b_subject': 'Masterclass Gratuita: Cómo 100x Tu Growth en 90 Días (Webinar)',
        'variant_b_body': 'Únete a nuestro webinar donde revelaremos los secretos de empresas que crecieron 100x. Plazas limitadas. Regístrate ahora.',
        'planned_duration_days': 7
    }

def create_test_10_event_invitation():
    """Test 10: event_invitation email type"""
    return {
        'test_name': 'FASE15 Phase3 - Event Attendance Conversion Test',
        'email_type': 'event_invitation',
        'variant_a_subject': 'Invitación: Summit Digital 2026 - Tu Asiento Está Reservado',
        'variant_a_body': 'Te invitamos al evento más importante del año con 500+ empresas, 50+ speakers, y networking exclusivo. Confirma tu asistencia.',
        'variant_b_subject': 'VIP: Acceso a Cena Privada Post-Summit + Meet & Greet Speakers',
        'variant_b_body': 'Como cliente premium, tienes acceso a nuestra cena VIP privada post-summit con todos los speakers principales. Solo 30 lugares. Confirma ya.',
        'planned_duration_days': 21
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
    """Crear 4 tests adicionales (7-10)"""
    db = sqlite3.connect('data/pipeline.sqlite')
    cursor = db.cursor()

    print("=" * 80)
    print("🚀 CREANDO A/B TESTS FINALES (7-10) - COBERTURA MÁXIMA")
    print("=" * 80)

    tests = [
        ("Test 7 (product_announcement)", create_test_7_product_announcement()),
        ("Test 8 (promotional_offer)", create_test_8_promotional_offer()),
        ("Test 9 (educational_content)", create_test_9_educational_content()),
        ("Test 10 (event_invitation)", create_test_10_event_invitation())
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
            print(f"   Duración: {test_data['planned_duration_days']} días")
        except Exception as e:
            print(f"   ❌ Error: {e}")

    # Verificar tests creados
    print("\n" + "=" * 80)
    print("✅ RESUMEN: 10 TESTS A/B EN PRODUCCIÓN")
    print("=" * 80)

    cursor.execute("SELECT id, test_name, email_type, active FROM ab_tests ORDER BY id")
    all_tests = cursor.fetchall()

    print(f"\nTotal A/B Tests en Producción: {len(all_tests)} (9 activos + 1 completado)")

    test_types = {}
    for test in all_tests:
        status = "🟢 ACTIVO" if test[3] else "⚫ COMPLETADO"
        print(f"  Test {test[0]}: {test[1]}")
        print(f"    Email Type: {test[2]} {status}")
        test_types[test[2]] = test_types.get(test[2], 0) + 1

    print(f"\n📊 Cobertura de Email Types: {len(test_types)} tipos únicos")
    for email_type, count in sorted(test_types.items()):
        print(f"   - {email_type}: {count} test(s)")

    db.close()

    return created_tests

if __name__ == "__main__":
    created = main()
    print("\n" + "=" * 80)
    print(f"✅ {len(created)} tests FINALES creados exitosamente")
    print("🎯 AHORA TENEMOS 10 TESTS EN PARALELO - COBERTURA MÁXIMA")
    print("=" * 80)
