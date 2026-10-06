# Manual de Usuario - FASE 14 v14.0.0
## Felix Automation - Sistema de Ventas Automático

---

## 📖 Introducción

Bienvenido a Felix Automation FASE 14. Este sistema automatiza y acelera tu proceso de ventas.

**Lo que hace:**
- Monitorea tus clientes en tiempo real
- Predice quién está cerca de comprar
- Envía emails automáticos
- Te muestra datos importantes en un dashboard

---

## 🏠 Pantalla Principal (Dashboard)

Cuando accedas, verás la pantalla principal con:

### 1. **Indicadores Principales (Arriba)**
```
┌─────────────────────────────────────────┐
│  Total Clientes: 45    Ventas: $125,000 │
│  Conversión: 35%       Predicción: 42%  │
└─────────────────────────────────────────┘
```

- **Total Clientes** → Cuántos clientes tienes en el sistema
- **Ventas** → Dinero generado
- **Conversión** → Qué % de clientes cerraron
- **Predicción** → Probabilidad de cerrar más ventas pronto

### 2. **Lista de Clientes (Centro)**
Ves todos tus clientes con:
- Nombre y empresa
- **Estado** → Dónde está en el proceso (Prospecto, Propuesta, Negociación, Cerrado)
- **Probabilidad** → % de chance de que compre (0-100%)
- **Próxima Acción** → Qué debe pasar ahora
- **Fecha** → Cuándo fue el último contacto

### 3. **Gráficos (Derecha)**
- **Embudo de Ventas** → Cuántos clientes en cada etapa
- **Tendencia** → Si están subiendo o bajando las conversiones
- **Top Clientes** → Los 5 clientes más prometedores

---

## 📊 Cómo Leer la Probabilidad de Compra

Cada cliente tiene un número del **0 a 100%** que significa:

| % | Significa | Qué hacer |
|---|-----------|-----------|
| 0-20% | Muy bajo interés | No enviar aún |
| 21-40% | Bajo interés | Enviar información |
| 41-60% | Interés medio | Hacer seguimiento |
| 61-80% | Alto interés | Llamar o propuesta |
| 81-100% | Muy alto interés | CERRAR AHORA |

**Ejemplo:**
- Cliente A: 85% → Está listo para comprar, llámalo
- Cliente B: 35% → Envíale más información
- Cliente C: 15% → Todavía no, espera

---

## 🔄 Las 4 Etapas de Venta

Tu proceso tiene 4 etapas. El sistema rastrea dónde está cada cliente:

### 1️⃣ **PROSPECTO**
- Cliente nuevo, apenas lo conoces
- Sistema: envía email de presentación
- Tu acción: esperar respuesta

### 2️⃣ **PROPUESTA**
- Cliente interesado, vio tu propuesta
- Sistema: envía seguimientos automáticos (día 2, 4, 7)
- Tu acción: responder preguntas

### 3️⃣ **NEGOCIACIÓN**
- Cliente en conversación seria
- Sistema: rastrea interacción
- Tu acción: cerrar detalles

### 4️⃣ **CERRADO**
- Cliente compró ✅ o rechazó ❌
- Sistema: registra resultado
- Tu acción: servicio o siguiente prospecto

---

## 📧 Emails A/B Testing

El sistema envía 2 versiones de emails (A y B) y te dice cuál funciona mejor.

**Qué significa:**
- **Versión A** → Primer email (más formal)
- **Versión B** → Segundo email (más personal)

**Métricas:**
- **Abiertos** → % de gente que abrió el email
- **Clicks** → % que hizo clic en el enlace
- **Conversión** → % que compró después

**Ejemplo:**
```
Versión A: 35% abiertos, 12% clicks
Versión B: 42% abiertos, 18% clicks ✅ GANADOR

→ Usar Versión B para futuros emails
```

---

## 🛒 Datos de Shopify

Si tienes tienda en Shopify, el sistema muestra:

- **Ventas Totales** → Dinero generado en tu tienda
- **Productos Top** → Los 5 productos más vendidos
- **Tasa de Conversión** → % de visitantes que compran
- **Últimas Órdenes** → Las 5 compras recientes

**Actualización:** Cada hora se sincroniza automáticamente

---

## ⚡ Alertas en Tiempo Real

El sistema te avisa cuando:

- ✅ Un cliente está listo para cerrar (probabilidad > 80%)
- ⚠️ Un cliente bajó interés (probabilidad bajó mucho)
- 📈 Algo extraño en los números
- 🎯 Es hora de hacer seguimiento

**Dónde ves:** En la parte superior derecha, números rojos = alertas

---

## 🎯 Predicciones de IA

El sistema predice:

1. **Probabilidad de Compra**
   - Analiza: emails abiertos, clics, visitas, tiempo
   - Te dice: % de chance de que compre

2. **Cuándo Comprará**
   - Analiza: histórico de ese cliente y similares
   - Te dice: en cuántos días probablemente cierre

3. **Qué Podría Salir Mal**
   - Analiza: patrones de abandono
   - Te dice: riesgos y cómo evitarlos

4. **Próximo Paso Recomendado**
   - Analiza: el perfil del cliente
   - Te dice: llama, envía propuesta, o espera

---

## 💡 Consejos Prácticos

### ✅ Hazlo
- Revisa el dashboard cada mañana (5 minutos)
- Prioriza clientes con probabilidad > 70%
- Actúa en alertas de rojo inmediatamente
- Cierra los que estén listos (>80%)

### ❌ No lo hagas
- No ignores las alertas rojas
- No esperes a que baje más la probabilidad
- No envíes emails a clientes con <20% (pierdes tiempo)
- No cierres mal los datos (el sistema los usa)

---

## 🔧 Problemas Comunes

### "No veo ningún cliente"
**Solución:** Los clientes se cargan en la tarde. Espera hasta las 16:00 hrs.

### "La probabilidad está en 0% en todos"
**Solución:** El sistema necesita datos. Primer día es normal, se ajusta después.

### "Un email no se envió"
**Solución:** Verifica que el email tenga dominio válido. Si sigue, reinicia.

### "No veo datos de Shopify"
**Solución:** El sistema se conecta cada hora. Puede demorar al inicio.

---

## 📱 En Móvil

Si accedes desde tu teléfono:
- Interfaz se adapta automáticamente
- Funciona offline (si descargaste antes)
- Alertas te llegan en tiempo real

---

## 🆘 Soporte

Si algo no funciona:

1. Recarga la página (F5 en PC, pull-down en móvil)
2. Limpia cookies (Ctrl+Shift+Delete)
3. Intenta en otro navegador
4. Contacta al soporte técnico

---

## 📚 Próximas Sesiones

Basado en lo que veas, tu estrategia:

**Semana 1:** Observar datos, entender patrones
**Semana 2:** Actuar en alertas, probar emails
**Semana 3+:** Optimizar basado en resultados

---

**¡Bienvenido a la automatización de ventas!** 🚀
