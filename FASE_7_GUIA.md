# FASE 7: FUNNEL MANAGEMENT AGENT 📊
## Gestión del Embudo de Ventas y Dashboards

---

## 🎯 ¿Qué es FASE 7?

FASE 7 es el sistema que gestiona todo tu **embudo de ventas** (pipeline) y genera **dashboards visuales** para que tú y tus clientes puedan ver el progreso en tiempo real.

Imagina que tu proceso de venta es una **escalera de 4 pasos**:
1. **Prospecto** - Cliente identificado
2. **Propuesta** - Propuesta enviada
3. **Negociación** - Discutiendo términos
4. **Cerrado** - Contratado o rechazado

FASE 7 **controla quién está en qué paso** y **genera reportes visuales** automáticamente.

---

## 📁 Componentes de FASE 7

### 1. **Funnel Management Agent** (`agents/funnel_management_agent.py`)
Es el "cerebro" que:
- Mueve clientes entre etapas del pipeline
- Calcula métricas (total clientes, ingresos esperados, etc.)
- Genera datos para dashboards

### 2. **Dashboard Interno** 
Página web para **Felix y su equipo**. Muestra:
- ✅ Total de clientes en el pipeline
- ✅ Emails enviados esta semana
- ✅ Ingresos esperados (de leads ALTO potencial)
- ✅ Distribución de clientes por etapa (gráficos)
- ✅ Tabla completa de todos los clientes y su etapa

**Archivo:** `data/dashboard_interno.html`

### 3. **Dashboard Cliente** (Personalizado)
Página web para **cada cliente**. Muestra:
- ✅ Su posición actual en el proceso (visual tipo timeline)
- ✅ Sus scores de auditoría (Web, Facebook Ads, Google Ads)
- ✅ Oportunidades de mejora (% estimado + $ por mes)
- ✅ Timeline del proyecto (duración, ROI estimado, próximo paso)
- ✅ Botón para agendar llamada

**Archivos:** 
- `data/dashboard_cliente_1.html` (para cliente 1)
- `data/dashboard_cliente_2.html` (para cliente 2)
- etc.

---

## 🚀 Cómo Usar FASE 7

### PASO 1: Ejecutar el Test (Una sola vez para entender)

```bash
cd /home/claude/felix-automation
python3 test_fase7.py
```

**Qué hace:**
- Mueve 3 clientes a diferentes etapas
- Genera dashboards HTML (internos + por cliente)
- Crea archivos JSON con los datos
- Muestra reporte en consola

**Archivos generados:**
- `data/dashboard_interno.html`
- `data/dashboard_cliente_1.html`
- `data/dashboard_cliente_2.html`
- `data/dashboard_cliente_3.html`

### PASO 2: Ver los Dashboards

Abre cualquiera de estos archivos en tu navegador:
```
data/dashboard_interno.html
data/dashboard_cliente_1.html
```

Los dashboards muestran:
- Diseño profesional con gradientes morados
- Gráficos de barras mostrando distribución
- Datos en tiempo real de tu base de datos

### PASO 3: Usar en tu Código Python

Para usar FASE 7 en tu código:

```python
from agents.funnel_management_agent import FunnelManagementAgent

agent = FunnelManagementAgent(orchestrator)

# Mover cliente a una etapa
agent.move_client_to_stage(client_id=1, stage=2)  # A propuesta

# Obtener todos los clientes en una etapa
prospects = agent.get_clients_by_stage(1)  # Todos en prospecto

# Obtener métricas del pipeline
metrics = agent.get_pipeline_metrics()
print(f"Total clientes: {metrics['total_clientes']}")
print(f"Ingresos esperados: ${metrics['ingresos_esperados']:,.0f}")

# Generar datos para dashboard interno
internal_data = agent.get_dashboard_data_interno()
# Usar internal_data['metricas'], internal_data['por_etapa'], etc.

# Generar datos personalizados para un cliente
client_data = agent.get_dashboard_data_cliente(client_id=1)
# Usar para llenar dashboard del cliente
```

---

## 📊 Las 4 Etapas del Pipeline

| Etapa | Nombre | Descripción | Próximo Paso |
|-------|--------|-------------|------------|
| 1 | 🟦 PROSPECTO | Cliente identificado, sin contacto formal | Enviar presentación |
| 2 | 🟨 PROPUESTA | Propuesta enviada, esperando respuesta | Seguimiento y negociación |
| 3 | 🟪 NEGOCIACIÓN | Cliente interesado, discutiendo términos | Finalizar contrato |
| 4 | 🟩 CERRADO | Contratado o rechazado (fin del proceso) | N/A |

---

## 📈 Métricas que Calcula FASE 7

### Métricas Generales:
- **Total de clientes:** Cantidad total en el pipeline
- **Emails enviados:** Cuántos se mandaron esta semana
- **Ingresos esperados:** Estimado basado en clientes ALTO potencial
- **Leads ALTO potencial:** Clientes con score >= 75

### Por Etapa:
- **Distribución (%):** Qué porcentaje está en cada etapa
- **Recuento:** Cantidad de clientes en cada etapa

### Por Cliente:
- **Scores de auditoría:** Web, Facebook Ads, Google Ads, Total
- **Mejora estimada:** % de conversiones que se pueden mejorar
- **Impacto mensual:** $ USD/mes que se pueden ganar

---

## 🔗 Integración con Otros Agentes

FASE 7 **se conecta con:**

### Lead Scorer Agent (FASE 3)
- Califica clientes por potencial
- Identifica "leads ALTO potencial"
- FASE 7 los usa para calcular ingresos esperados

### Email Sender Agent (FASE 4)
- Cuando envías un email, FASE 7 puede registrarlo
- Actualiza el contador de "emails enviados"

### Follow-up Agent (FASE 5)
- Cuando haces follow-up, FASE 7 rastrea el estado
- Usa los datos para calcular el tiempo en cada etapa

---

## 💾 Archivos de Datos

FASE 7 guarda todos los datos en:

### `data/pipeline.json`
Contiene el estado actual de cada cliente:
```json
{
  "pipeline": [
    {
      "client_id": 1,
      "client_name": "Raíces de Cauquenes",
      "email": "info@raices.cl",
      "stage": 2,
      "stage_name": "propuesta",
      "created_at": "2026-10-05T12:00:00",
      "updated_at": "2026-10-05T12:07:08",
      "notes": ""
    },
    ...
  ]
}
```

### `data/dashboard_*.json`
Contiene los datos listos para mostrar en los dashboards (formato importable a cualquier aplicación).

---

## 🎨 Personalización

### Cambiar Colores
En el archivo HTML, encuentra esta sección:
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

Puedes cambiar `#667eea` y `#764ba2` por otros colores hex.

### Cambiar Nombres de Etapas
En `funnel_management_agent.py`, busca:
```python
ETAPAS = {
    1: "prospecto",
    2: "propuesta",
    3: "negociacion",
    4: "cerrado"
}
```

### Cambiar el Costo por Cliente
En `funnel_management_agent.py`, busca:
```python
metrics["ingresos_esperados"] = len(high_potential) * 3000
```

Cambia `3000` por el monto que desees.

---

## 🛠️ Solución de Problemas

### "No aparecen los dashboards"
**Solución:** Ejecuta primero `test_fase7.py` para que se generen los archivos.

### "Los datos no se actualizan"
**Solución:** Los dashboards HTML son estáticos. Para datos en vivo, necesitas:
1. Ejecutar `test_fase7.py` nuevamente
2. O integrar con tu sistema web dinámico (en futuras fases)

### "Los datos no se guardan en el JSON"
**Solución:** Asegúrate de que la carpeta `data/` existe:
```bash
mkdir -p data
```

---

## 📋 Checklist: ¿Completaste FASE 7?

- ✅ Entiendes las 4 etapas del pipeline
- ✅ Ejecutaste `test_fase7.py` sin errores
- ✅ Viste los dashboards HTML en tu navegador
- ✅ Entiendes cómo mover clientes entre etapas
- ✅ Sabes qué métricas calcula automáticamente
- ✅ Conoces cómo integrar FASE 7 en tu código

---

## 🚀 Próximos Pasos

Después de FASE 7, continuaremos con:

### **FASE 5: Follow-up Agent**
- Automatiza emails de seguimiento
- Secuencias automáticas (día 2, día 4, día 7)
- Tracking de respuestas

### **FASE 6: Sales Pipeline Agent**
- Gestión avanzada del pipeline
- Reportes semanales automáticos
- Predicción de cierre de deals

### **Integración Completa**
- Todos los agentes trabajando juntos
- Sistema end-to-end funcionando

---

## 📞 Preguntas Frecuentes

**P: ¿Cómo veo los dashboards sin abrir archivos HTML?**
R: Puedes crear un servidor web simple (en futuras fases) que los sirva automáticamente.

**P: ¿Puedo cambiar el color del dashboard?**
R: Sí, en los archivos HTML busca `linear-gradient` y cambia los colores hex.

**P: ¿Los datos persisten si cierro la aplicación?**
R: Sí, todo se guarda en `data/pipeline.json` y en la base de datos SQLite.

**P: ¿Cuál es la diferencia entre dashboard interno y de cliente?**
R: 
- **Interno:** Ves TODAS las métricas, todos los clientes, datos completos
- **Cliente:** Ve SOLO su progreso, sus scores, sus oportunidades

---

## 📞 Comando Rápido

Para regenerar los dashboards en cualquier momento:
```bash
cd /home/claude/felix-automation
python3 test_fase7.py
```

Luego abre:
- `data/dashboard_interno.html` (para ti)
- `data/dashboard_cliente_X.html` (para cada cliente)

---

**FASE 7: COMPLETADA ✅**

Ahora tienes un sistema profesional de gestión del embudo de ventas con dashboards visuales automáticos.
