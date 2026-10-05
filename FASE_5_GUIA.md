# FASE 5: FOLLOW-UP AGENT 📧
## Automatización de Seguimientos Secuenciados

---

## 🎯 ¿Qué es FASE 5?

FASE 5 es el sistema que **automatiza seguimientos por email** de manera inteligente.

Imagina que enviaste una propuesta a un cliente. Sin FASE 5, tendrías que acordarte manualmente de cuándo hacer seguimiento. Con FASE 5:

1. **Día 2:** Envía un email diciendo "¿Viste la propuesta?"
2. **Día 4:** Envía datos competitivos ("Tu competencia está haciendo X")
3. **Día 7:** Envía el último valor ("Mira el ROI potencial")

**Todo automático**, sin que hagas nada. El sistema se acuerda, calcula fechas, genera emails personalizados y rastrea si el cliente los abrió.

---

## 📁 Componentes de FASE 5

### 1. **Follow-up Agent** (`agents/followup_agent.py`)
Es el "motor" que:
- Inicia secuencias de seguimiento para clientes
- Rastrea cuándo enviar cada follow-up (día 2, 4, 7)
- Genera emails personalizados automáticamente
- Marca emails como abiertos/clickeados
- Cierra secuencias cuando el cliente responde

### 2. **Data Files**
- `data/followup_sequences.json`: Estado actual de cada secuencia
- `data/followup_log.json`: Registro de todos los emails enviados
- `data/followup_export.json`: Datos exportables para análisis

---

## 🚀 Cómo Usar FASE 5

### PASO 1: Ejecutar el Test (Para entender el sistema)

```bash
cd /home/claude/felix-automation
python3 test_fase5.py
```

**Qué hace:**
- Inicia 3 secuencias de seguimiento (una por cliente)
- Simula el paso de tiempo para que los follow-ups se activen
- Envía 5 follow-ups de prueba
- Marca algunos como abiertos
- Genera reportes y estadísticas
- Exporta datos a JSON

**Archivos generados:**
- `data/followup_sequences.json` (estado de secuencias)
- `data/followup_log.json` (registro de envíos)
- `data/followup_export.json` (export para análisis)

### PASO 2: Usar en tu Código Python

Para integrar FASE 5 en tu sistema:

```python
from orchestrator import FelixAutomationOrchestrator
from agents.followup_agent import FollowUpAgent

# Inicializar
orchestrator = FelixAutomationOrchestrator()
orchestrator.connect_database()

agent = FollowUpAgent(orchestrator)

# ===== INICIAR SECUENCIA =====
# Cuando envías una propuesta, inicia el seguimiento automático
result = agent.start_followup_sequence(
    client_id=1,
    proposal_id=101  # ID de la propuesta que enviaste
)
print(f"Secuencia iniciada: {result['sequence_id']}")
# Output: Secuencia iniciada: 1

# ===== VER FOLLOW-UPS PENDIENTES =====
# Ejecuta esto cada hora (o con un scheduler)
pending = agent.get_pending_followups()
for item in pending:
    print(f"{item['client_name']}: {item['followup_name']}")
    # Enviar el email (ver abajo)
    agent.send_followup(
        sequence_id=item['sequence_id'],
        followup_number=item['followup_number']
    )

# ===== RASTREAR APERTURAS =====
# Cuando el cliente abre un email (via webhook de SendGrid):
agent.mark_followup_opened(
    sequence_id=1,
    followup_number=1
)

# ===== VER ESTADO DE UN CLIENTE =====
status = agent.get_followup_status(client_id=1)
print(f"{status['client_name']}: {status['followups_sent']}/3 enviados")
# Output: Raíces de Cauquenes: 2/3 enviados

# ===== COMPLETAR SECUENCIA =====
# Cuando el cliente dice "sí" o "no"
agent.complete_sequence(
    sequence_id=1,
    reason="cliente_respondió"  # O "rechazó"
)

# ===== GENERAR REPORTE =====
report = agent.get_followup_report()
print(report)

orchestrator.close_database()
```

---

## 📊 Las 3 Etapas de Follow-up

| Etapa | Día | Nombre | Objetivo | Tipo |
|-------|-----|--------|----------|------|
| 1️⃣ | 2 | Primer Follow-up | Verificar si vieron propuesta | check_in |
| 2️⃣ | 4 | Segundo Follow-up | Compartir datos competitivos | data_share |
| 3️⃣ | 7 | Tercer Follow-up | Mostrar ROI potencial | last_touch |

### Detalles de cada Follow-up

**Follow-up #1 (Día 2) - Check In**
```
Asunto: ¿Viste tu propuesta? - [Cliente]
Mensaje: Solo checando si viste tu propuesta que te envié hace unos días.
         ¿Tienes preguntas sobre algún punto?
         [Link a calendly para agendar call]
```

**Follow-up #2 (Día 4) - Data Share**
```
Asunto: Datos que te pueden interesar - [Cliente]
Mensaje: Te quería compartir un dato que vi en tu auditoría:
         Tu competencia está invirtiendo en Google Ads.
         Tienes 3 oportunidades rápidas para mejorar tu posición.
         [Link a calendly]
```

**Follow-up #3 (Día 7) - Last Touch**
```
Asunto: Último dato: ROI potencial - [Cliente]
Mensaje: Negocios como el tuyo típicamente ven:
         • 40% mejora en quality score
         • 25% reducción en CPC
         • 60% más conversiones
         [Link a calendly]
```

---

## 💾 Estructura de Datos

### `data/followup_sequences.json`
Contiene el estado de cada secuencia:
```json
{
  "sequences": [
    {
      "sequence_id": 1,
      "client_id": 1,
      "client_name": "Raíces de Cauquenes",
      "client_email": "info@raices.cl",
      "proposal_id": 101,
      "status": "active",  // active, paused, completed, cancelled
      "started_at": "2026-10-05T10:00:00",
      "last_followup_at": "2026-10-05T12:00:00",
      "followups": {
        "1": {
          "sent": true,
          "sent_at": "2026-10-07T10:00:00",
          "opened": true,
          "clicked": false
        },
        "2": {
          "sent": false,
          "sent_at": null,
          "opened": false,
          "clicked": false
        },
        "3": {
          "sent": false,
          "sent_at": null,
          "opened": false,
          "clicked": false
        }
      },
      "notes": ""
    }
  ]
}
```

### `data/followup_log.json`
Registro de auditoría de todos los emails enviados:
```json
[
  {
    "timestamp": "2026-10-07T10:00:00",
    "sequence_id": 1,
    "client_id": 1,
    "client_name": "Raíces de Cauquenes",
    "followup_number": 1,
    "followup_type": "check_in",
    "recipient": "info@raices.cl",
    "subject": "¿Viste tu propuesta? - Raíces de Cauquenes",
    "status": "sent"
  }
]
```

---

## 🔗 Integración con Otros Agentes

FASE 5 se conecta con:

### **Proposal Generator (FASE 2)**
- Cuando generas una propuesta, inicia una secuencia con `start_followup_sequence()`

### **Funnel Management (FASE 7)**
- Los follow-ups rastrean el progreso del cliente en el embudo
- Si un cliente abre un email → aumenta probabilidad de que se mueva a siguiente etapa
- Si cliente completa secuencia → se marca en el pipeline

### **Email Sender (FASE 4)**
- Usa las plantillas de email del Follow-up Agent
- El Follow-up Agent rastrea aperturas/clicks (via webhooks de SendGrid)

---

## 📈 Métricas que Calcula FASE 5

Para cada cliente:
- **Follow-ups enviados:** Cuántos de 3 se han enviado
- **Tasa de apertura:** % de emails abiertos
- **Tiempo en seguimiento:** Cuántos días lleva la secuencia
- **Estado actual:** Activo/Completado/Pausado

Para el sistema completo:
- **Secuencias activas:** Cuántas están en progreso
- **Secuencias completadas:** Cuántas terminaron (sí o no)
- **Total follow-ups enviados:** Suma de todos
- **Tasa de apertura general:** % de todos los emails abiertos

---

## 🎨 Personalización

### Cambiar Horarios (Días de Follow-up)

En `agents/followup_agent.py`, busca:
```python
FOLLOWUP_SCHEDULE = {
    1: {"days": 2, "name": "Primer Follow-up", "type": "check_in"},
    2: {"days": 4, "name": "Segundo Follow-up", "type": "data_share"},
    3: {"days": 7, "name": "Tercer Follow-up", "type": "last_touch"}
}
```

Cambia los números en `"days"`:
- Cambiar a día 1, 3, 5: `1: {"days": 1, ...}, 2: {"days": 3, ...}, 3: {"days": 5, ...}`

### Cambiar Contenido de Emails

En la función `_generate_followup_email()`, busca los templates y edita el "body":
```python
templates = {
    1: {
        "check_in": {
            "subject": "TU ASUNTO AQUÍ",
            "body": "TU CONTENIDO AQUÍ"
        }
    }
}
```

### Cambiar Nombre de Follow-ups

En `FOLLOWUP_SCHEDULE`, edita el campo "name":
```python
1: {"days": 2, "name": "TU NOMBRE AQUÍ", "type": "check_in"},
```

---

## 🛠️ Solución de Problemas

### "No veo follow-ups pendientes"
**Causas posibles:**
1. Recién iniciaste la secuencia (espera 2 días)
2. Ya enviaste todos los follow-ups

**Solución:**
- Ejecuta `test_fase5.py` que simula paso de tiempo automáticamente

### "No se guardan los emails en el log"
**Causa:** `data/followup_log.json` no existe

**Solución:**
```bash
# El agente lo crea automáticamente, pero si no:
mkdir -p data
```

### "Un cliente abrió un email pero no se registra"
**Causa:** Necesitas webhook de SendGrid

**Para futuras fases:** Configuraremos webhooks para que SendGrid nos notifique cuando se abre un email

---

## 📋 Checklist: ¿Completaste FASE 5?

- ✅ Ejecutaste `test_fase5.py` sin errores
- ✅ Entiendes las 3 etapas de follow-up (día 2, 4, 7)
- ✅ Sabes cómo iniciar una secuencia con `start_followup_sequence()`
- ✅ Conoces cómo ver pendientes con `get_pending_followups()`
- ✅ Entiendes cómo completar una secuencia
- ✅ Viste cómo generar reportes con `get_followup_report()`

---

## 🚀 Próximos Pasos

Después de FASE 5, continuaremos con:

### **FASE 6: Sales Pipeline Agent**
- Gestión avanzada del pipeline
- Reportes semanales automáticos
- Predicción de cierre de deals
- Sincronización con dashboard

### **Integración Completa**
- Todos los agentes trabajando juntos
- Sistema end-to-end funcionando
- API para integración con plataformas externas

---

## 📞 Comandos Rápidos

Para regenerar test data en cualquier momento:
```bash
cd /home/claude/felix-automation
python3 test_fase5.py
```

Para ver datos exportados:
```bash
cat data/followup_export.json
```

Para ver log de emails:
```bash
cat data/followup_log.json
```

---

## 📞 Preguntas Frecuentes

**P: ¿Cómo integro FASE 5 con SendGrid?**
R: En futuras fases configuraremos el Email Sender para que use las secuencias de FASE 5.

**P: ¿Puedo cambiar cuándo se envía cada follow-up?**
R: Sí, edita `FOLLOWUP_SCHEDULE` en `agents/followup_agent.py`.

**P: ¿Qué pasa si un cliente responde después del primer follow-up?**
R: Llama a `complete_sequence()` para marcar la secuencia como completada.

**P: ¿Los datos persisten si cierro la aplicación?**
R: Sí, todo se guarda en `data/followup_sequences.json` y `data/followup_log.json`.

**P: ¿Puedo pausar una secuencia temporalmente?**
R: Sí, actualizando el status en `followup_sequences.json` a "paused", luego "active" para reanudar.

---

**FASE 5: COMPLETADA ✅**

Ahora tienes un sistema profesional de automatización de seguimientos.

El siguiente paso es FASE 6: Sales Pipeline Agent (reportes avanzados).

