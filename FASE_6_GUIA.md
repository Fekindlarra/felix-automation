# FASE 6: SALES PIPELINE AGENT 📊
## Análisis Predictivo y Reportes del Pipeline

---

## 🎯 ¿Qué es FASE 6?

FASE 6 es el sistema que **analiza el pipeline de ventas de manera inteligente** e **identifica oportunidades y riesgos automáticamente**.

Imagina que tienes 100 clientes en diferentes etapas. Sin FASE 6:
- No sabes cuál tiene más probabilidad de cerrar
- No identificas clientes que hace 3 meses no habla con ellos
- No sabes qué pasos dar a continuación

Con FASE 6:
- **Predice** quién va a cerrar (con % de probabilidad)
- **Identifica** clientes en riesgo (sin movimiento)
- **Sugiere** exactamente qué hacer con cada cliente
- **Genera** reportes automáticos cada semana

---

## 📁 Componentes de FASE 6

### 1. **Sales Pipeline Agent** (`agents/sales_pipeline_agent.py`)
Es el motor que:
- Analiza la salud del pipeline completo
- Predice probabilidad de cierre por cliente
- Identifica clientes en riesgo
- Genera reportes semanales
- Exporta datos para análisis

### 2. **Data Files**
- `data/pipeline_analytics.json`: Análisis completo del pipeline

---

## 🚀 Cómo Usar FASE 6

### PASO 1: Ejecutar el Test

```bash
cd /home/claude/felix-automation
python3 test_fase6.py
```

**Qué hace:**
- Analiza salud del pipeline (clientes por etapa)
- Predice cierre para cada cliente (da % de probabilidad)
- Identifica clientes en riesgo
- Genera reporte semanal
- Exporta datos a JSON para análisis

### PASO 2: Usar en tu Código Python

```python
from agents.sales_pipeline_agent import SalesPipelineAgent

agent = SalesPipelineAgent(orchestrator)

# ===== SALUD DEL PIPELINE =====
health = agent.get_pipeline_health()
print(f"Total clientes: {health['total_clients']}")
print(f"Deals cerrados: {health['closed_deals']}")
print(f"Velocidad: {health['pipeline_velocity']}")

# ===== PREDECIR CIERRE =====
# Para cada cliente, da probabilidad de cerrar (0-100%)
prediction = agent.predict_deal_closure(client_id=1)
print(f"{prediction['client_name']}: {prediction['closure_probability']}")
print(f"Categoría: {prediction['category']}")  # MUY PROBABLE, PROBABLE, BAJO POTENCIAL

# ===== CLIENTES EN RIESGO =====
# Identifica clientes sin actualizar en 14+ días
at_risk = agent.get_at_risk_clients(days_threshold=14)
for client in at_risk:
    print(f"⚠️  {client['client_name']}: Sin actualizar {client['days_without_update']} días")

# ===== REPORTE SEMANAL =====
report = agent.generate_weekly_report()
print(report)

# ===== EXPORTAR ANALYTICS =====
analytics = agent.export_pipeline_analytics()
# Genera data/pipeline_analytics.json con todo listo para análisis
```

---

## 🎯 Cómo Predice FASE 6

FASE 6 analiza **5 factores** para predecir si un cliente cerrará:

| Factor | Peso | Descripción |
|--------|------|------------|
| Stage Progression | 30% | ¿En qué etapa está? (prospecto=baja, cerrado=alta) |
| Engagement | 25% | ¿Abrió emails? ¿Hizo clic? |
| Lead Score | 20% | ¿Qué score de potencial tiene? |
| Days in Stage | 15% | ¿Cuánto tiempo en esta etapa? |
| Communication Frequency | 10% | ¿Cuántos emails le enviaste? |

**Fórmula:**
```
Probabilidad = (Stage×0.30) + (Engagement×0.25) + (Score×0.20) + (Days×0.15) + (Comm×0.10)
```

**Resultado:**
- 🟢 **75%+**: MUY PROBABLE (cierre muy likely)
- 🟡 **50-74%**: PROBABLE (posible cierre)
- 🔴 **<50%**: BAJO POTENCIAL (difícil cierre)

---

## 📊 Métricas Que Calcula

### Pipeline Health (Salud General)
- **Total clientes**: Cuántos hay en pipeline
- **Deals cerrados**: Cuántos ya se cerraron
- **Pipeline velocity**: % de conversión
- **Tiempo por etapa**: Promedio de días en cada etapa

### Clientes en Riesgo
- Clientes sin actualización en 14+ días
- Etapa actual
- Última actividad
- Días sin contacto

### Predicciones
- Probabilidad de cierre (%)
- Categoría (MUY PROBABLE / PROBABLE / BAJO)
- Factores que influyen (scores por factor)

---

## 💾 Estructura de Datos

### `data/pipeline_analytics.json`
```json
{
  "timestamp": "2026-10-05T12:17:27",
  "pipeline_health": {
    "total_clients": 3,
    "closed_deals": 0,
    "pipeline_velocity": "0.0%",
    "stage_health": {
      "prospecto": {"count": 1, "avg_days": 0, ...},
      "propuesta": {"count": 1, "avg_days": 0, ...},
      ...
    }
  },
  "at_risk_clients": [
    {
      "client_id": 1,
      "client_name": "Raíces",
      "days_without_update": 21
    }
  ],
  "closure_predictions": [
    {
      "client_id": 1,
      "client_name": "Raíces",
      "closure_probability": "53.3%",
      "category": "PROBABLE",
      "factors": {
        "stage_progression": 50,
        "engagement": 0,
        ...
      }
    }
  ],
  "summary": {
    "total_clients": 3,
    "total_at_risk": 0,
    "high_probability_deals": 0,
    "average_closure_probability": 48.3
  }
}
```

---

## 🔗 Integración con Otros Agentes

FASE 6 usa datos de:

### **Funnel Management (FASE 7)**
- Estado del cliente en pipeline (etapa 1-4)
- Timestamps de actualización

### **Follow-up Agent (FASE 5)**
- Rastreo de emails abiertos
- Frecuencia de comunicación

### **Lead Scorer (FASE 3)**
- Score de potencial del cliente

---

## 🎨 Personalización

### Cambiar Threshold de Riesgo

En tu código:
```python
# Por defecto: 14 días sin actualización = EN RIESGO
at_risk = agent.get_at_risk_clients(days_threshold=7)  # 7 días
```

### Cambiar Factores de Predicción

En `agents/sales_pipeline_agent.py`:
```python
CIERRE_PESOS = {
    "stage_progression": 0.30,      # ← Cambiar estos números
    "engagement": 0.25,
    "lead_score": 0.20,
    "days_in_stage": 0.15,
    "communication_frequency": 0.10
}
# Deben sumar 1.0 (100%)
```

---

## 📋 Checklist: ¿Completaste FASE 6?

- ✅ Ejecutaste `test_fase6.py` sin errores
- ✅ Entiendes cómo predice probabilidad de cierre
- ✅ Sabes identificar clientes en riesgo
- ✅ Conoces los 5 factores de predicción
- ✅ Entiendes cómo exportar analytics a JSON

---

## 🚀 Próximos Pasos

Ya casi terminamos la automatización completa. Las próximas fases serán:

### **Integración Final**
- Conectar todos los agentes (1-6)
- Sistema end-to-end funcionando
- API para integraciones externas
- Dashboard web unificado

---

**FASE 6: COMPLETADA ✅**

Ahora tienes un sistema que predice cuál cliente va a cerrar y cuál necesita atención urgente.

