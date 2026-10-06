# Guía de Acceso - FASE 14 v14.0.0
## Cómo acceder al sistema una vez esté en vivo

---

## 🌐 URLs de Acceso

Una vez que el sistema esté funcionando, accede desde:

### 1. **Dashboard Interno (Para ti - Felipe)**
```
http://localhost:3000/admin
```

**Qué ves aquí:**
- Todos los clientes
- Métricas completas
- Gráficos de ventas
- Predicciones
- Alertas
- Configuración del sistema

**Usuario:** admin  
**Contraseña:** (te daré en el deployment)

---

### 2. **Portal de Clientes (Para tus clientes)**
```
http://localhost:3000/portal
```

**Qué ven los clientes:**
- Su progreso en el proceso de venta
- Documentos y propuestas
- Próximos pasos
- Contacto

**Acceso:** Cada cliente tiene su usuario/contraseña

---

### 3. **API (Para integraciones)**
```
http://localhost:3000/api
```

**Qué es:** Para conectar con otros programas (si necesitas)

**Documentación:** http://localhost:3000/api/docs

---

## 🔐 Credenciales de Acceso

### Al Principio (Temporales)
```
Usuario: admin
Contraseña: admin123  (CAMBIAR INMEDIATAMENTE)
```

### Cómo Cambiar Contraseña
1. Accede al dashboard
2. Arriba a la derecha → Tu perfil
3. Cambiar contraseña
4. Escribe una contraseña segura (16+ caracteres, con números y símbolos)

---

## 🌍 Cuando Esté en Servidor Real

Si lo despliegas en internet:

```
Dashboard:        https://admin.enbuenamesa.com
Portal Clientes:  https://enbuenamesa.com
API:              https://api.enbuenamesa.com
```

**Nota:** Cambiar `localhost:3000` por tu dominio real

---

## ✅ PRIMERAS ACCIONES (Cuando esté vivo)

### Paso 1: Acceder
1. Abre navegador (Chrome, Firefox, Safari)
2. Escribe: `http://localhost:3000/admin`
3. Usuario: `admin`
4. Contraseña: `admin123`

### Paso 2: Cambiar Contraseña
1. Arriba a la derecha → Perfil
2. Contraseña nueva
3. Guardar

### Paso 3: Cargar Clientes
1. Menú izquierdo → Clientes
2. Botón "Importar"
3. Seleccionar archivo CSV
4. Confirmar

### Paso 4: Verificar Datos
1. Buscar un cliente en la lista
2. Verificar que los datos sean correctos
3. Ver la predicción de probabilidad

### Paso 5: Explorar Dashboard
1. Ir a "Dashboard" en menú
2. Ver gráficos y métricas
3. Entender dónde está cada cliente

---

## 🎨 Interfaz Explicada

### Menú Izquierdo
```
┌─────────────────┐
│ Dashboard       │  → Métricas principales
│ Clientes        │  → Lista de clientes
│ Predicciones    │  → Probabilidades de compra
│ Emails          │  → Historial de emails enviados
│ Reportes        │  → Gráficos y análisis
│ Configuración   │  → Ajustes del sistema
│ Ayuda           │  → Documentación
└─────────────────┘
```

### Barra Superior
```
┌──────────────────────────────────────┐
│ 🔍 Buscar │ 🔔 Alertas │ ⚙️ Perfil │
└──────────────────────────────────────┘
```

- **Buscar** → Encuentra clientes rápido
- **Alertas** → Notificaciones importantes (rojo = urgente)
- **Perfil** → Tu cuenta y configuración

---

## 🎯 Las Secciones Principales

### 📊 Dashboard
**Qué ves:**
- Número total de clientes
- Dinero en ventas
- % de conversión
- Clientes en cada etapa
- Gráficos de tendencia

**Qué hacer:**
- Revisar cada mañana
- Si hay alertas rojas, actúa inmediatamente

### 👥 Clientes
**Qué ves:**
- Lista con todos los clientes
- Nombre, email, empresa
- Probabilidad de compra
- Etapa actual
- Último contacto

**Qué hacer:**
- Hacer clic en un cliente para ver detalles
- Cambiar estado si cierra o rechaza
- Agregar notas

### 🎯 Predicciones
**Qué ves:**
- % de probabilidad de compra
- Por qué tiene esa probabilidad
- Riesgos identificados
- Próximo paso recomendado

**Qué hacer:**
- Entender por qué el % es ese
- Actuar según recomendación

### 📧 Emails
**Qué ves:**
- Todos los emails enviados
- A quién se enviaron
- Si se abrieron (✅ abierto / ❌ no abierto)
- Clics en enlaces
- Conversiones

**Qué hacer:**
- Ver cuál es el mejor email (A o B)
- Copiar el que funciona mejor

### 📈 Reportes
**Qué ves:**
- Gráficos bonitos de todo
- Comparaciones de períodos
- Tendencias

**Qué hacer:**
- Usarlos para mostrar a clientes o jefe
- Entender qué está funcionando

---

## 🔧 Funciones Principales

### Agregar Cliente Manualmente
1. Menú → Clientes
2. Botón verde "Nuevo Cliente"
3. Llenar formulario
4. Guardar

### Cambiar Estado de Cliente
1. Hacer clic en cliente
2. Desplegable "Estado"
3. Seleccionar: Prospecto → Propuesta → Negociación → Cerrado
4. Guardar

### Enviar Email
1. Hacer clic en cliente
2. Botón "Enviar Email"
3. Seleccionar template (A o B)
4. Verificar y enviar

### Ver Predicción
1. Hacer clic en cliente
2. Sección "Predicción"
3. Leer análisis y recomendación

---

## ⚙️ Configuración Importante

**Menú → Configuración**

### General
- Nombre de empresa
- Logo
- Colores

### Emails
- Email de envío
- Plantillas por defecto
- Horarios de envío

### Integraciones
- Shopify
- Facebook Ads
- Google Ads

### Usuarios
- Agregar más personas (opcional)
- Cambiar permisos

---

## 🆘 Botones de Emergencia

### Si algo no funciona
1. **Recargar página**: F5 (PC) o Cmd+R (Mac)
2. **Limpiar datos**: Ctrl+Shift+Delete → Cookies
3. **Cambiar navegador**: Prueba Chrome si usas Firefox
4. **Reiniciar sistema**: Cierra todos los tabs y abre de nuevo

### Si sigue sin funcionar
Revisa:
- ¿Docker está corriendo? (verifica en terminal)
- ¿Es la URL correcta? (http://localhost:3000)
- ¿Actualizaste el navegador a última versión?

---

## 📱 En Celular

**URL en móvil:** `http://localhost:3000` (sigue siendo igual)

**Diferencias:**
- Interfaz se adapta automáticamente
- Algunos gráficos más pequeños
- Funciona casi igual que en PC

**Nota:** Si accedes remotamente, cambia `localhost` por tu IP o dominio

---

## 🔒 Seguridad - Consejos

✅ **Hazlo:**
- Cambiar contraseña al iniciar
- Usar contraseña fuerte (16+ caracteres)
- No compartir usuario/contraseña
- Cerrar sesión al terminar (si es compartido)

❌ **No lo hagas:**
- No dejes la contraseña en post-its
- No envíes credenciales por WhatsApp o email
- No uses contraseña fácil (123456, password)
- No dejes sesión abierta en computadora pública

---

## 📞 Soporte

Si tienes problemas:

1. **Refresca la página** (F5)
2. **Prueba con otro navegador**
3. **Reinicia Docker** (en terminal)
4. **Contacta soporte técnico**

---

## ✅ Checklist de Primer Día

- [ ] Accedí con usuario admin
- [ ] Cambié mi contraseña
- [ ] Importé lista de clientes
- [ ] Vi el dashboard
- [ ] Hice clic en un cliente
- [ ] Vi la predicción
- [ ] Exploré todas las secciones
- [ ] Entiendo dónde está todo

---

**¡Listo para acceder!** 🚀
