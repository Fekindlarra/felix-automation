# 🚀 FASE 14 - GUÍA DE DEPLOYMENT LOCAL (Para No Técnicos)
**Para: Felipe (usuario final sin experiencia en desarrollo)**  
**Objetivo:** Ejecutar FASE 14 en tu PC Windows/Mac sin necesidad de hosting pagado  
**Tiempo estimado:** 15-20 minutos

---

## 📋 Lo que necesitas antes de empezar

Verifica que tu PC tenga instalado:
- [ ] **Python 3.11 o superior** (Descargar de python.org si no lo tienes)
- [ ] **Git** (Para clonar el proyecto)

**Para verificar si tienes Python:**
1. Abre "CMD" o "PowerShell" (Windows) o "Terminal" (Mac)
2. Escribe: `python --version`
3. Debe mostrar: `Python 3.11.x` o superior

Si no lo tienes, descarga desde: https://www.python.org/downloads/

---

## 🎯 PASO 1: Preparar tu Computadora (5 minutos)

### A. Crear una carpeta para el proyecto
```bash
# En Windows:
mkdir C:\FelixAutomation
cd C:\FelixAutomation

# En Mac:
mkdir ~/FelixAutomation
cd ~/FelixAutomation
```

### B. Descargar el proyecto
```bash
# Copia el contenido de /home/claude/felix-automation a tu carpeta
# O si tienes Git instalado:
git clone <URL-del-repositorio> .
```

---

## 🔧 PASO 2: Activar el Ambiente Virtual (3 minutos)

El "ambiente virtual" es como un contenedor que evita conflictos con otras aplicaciones.

### Windows:
```bash
venv\Scripts\activate
```

**Verás que aparece `(venv)` al inicio de tu línea de comandos** - eso significa que funcionó.

### Mac/Linux:
```bash
source venv/bin/activate
```

---

## 📦 PASO 3: Instalar dependencias (3 minutos)

```bash
pip install -r requirements.txt
```

Esto instalará todas las librerías Python que necesita FASE 14.

**Espera a que termine** (verás un mensaje de "Successfully installed...").

---

## 🗄️ PASO 4: Preparar la Base de Datos (2 minutos)

```bash
python init_database.py
```

Esto crea la base de datos SQLite con todas las tablas necesarias.

**Verás un mensaje:** `✓ Database initialized successfully`

---

## 🚀 PASO 5: Iniciar el Servidor (2 minutos)

```bash
python backend/main.py
```

**Verás algo como:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**¡Significa que está funcionando!**

---

## 🌐 PASO 6: Acceder al Sistema

Abre tu navegador (Chrome, Firefox, Safari) e ingresa:

```
http://localhost:8000
```

Verás el **Dashboard de FASE 14** con:
- ✅ Lista de clientes
- ✅ Estado del pipeline de ventas
- ✅ Predicciones ML en tiempo real
- ✅ Tests A/B running
- ✅ Integración con Shopify

---

## 🛑 PASO 7: Detener el Servidor

Cuando termines, en la ventana del terminal presiona:

```
CTRL + C  (en Windows)
CMD + C   (en Mac)
```

Verás: `Shutdown complete` - listo para detener.

---

## 🔄 Cada vez que quieras usar FASE 14

Solo necesitas hacer 2 cosas:

### Día siguiente (Reinicio rápido):
```bash
cd C:\FelixAutomation
venv\Scripts\activate
python backend/main.py
```

Luego: http://localhost:8000

### Si cierras tu PC:
- La base de datos se guarda automáticamente
- Solo necesitas repetir el proceso anterior
- Todos tus datos estarán ahí

---

## ✨ Características que ya tienes en FASE 14

Sin hacer nada más, ahora tienes:

### 📊 Dashboard
- Vista de todos tus clientes
- Estado del pipeline (Prospecto → Propuesta → Negociación → Cerrado)
- Métricas en tiempo real

### 🤖 Automatización de Ventas
- Seguimiento automático de clientes
- Propuestas generadas automáticamente
- Emails de seguimiento programados

### 📈 Predicciones ML
- Probabilidad de conversión (0-100%)
- Factores de riesgo identificados
- Timeline estimado para cerrar

### 🧪 A/B Testing
- Pruebas de variantes de emails
- Análisis estadístico automático
- Ganador determinado cuando hay suficientes datos

### 📱 Móvil
- Dashboard funciona en celular
- Interfaz responsive (se adapta a cualquier pantalla)
- Modo offline (guarda datos localmente)

---

## 🆘 Si algo no funciona

### El servidor no inicia
**Solución:**
1. Verifica que Python 3.11+ esté instalado: `python --version`
2. Verifica que estés en la carpeta correcta
3. Verifica que el ambiente virtual esté activado (debe mostrar `(venv)`)

### No puedo acceder a localhost:8000
**Solución:**
1. Verifica que el servidor esté corriendo (debe tener un mensaje de "Uvicorn running")
2. Espera 5 segundos después de ejecutar el comando
3. Abre http://127.0.0.1:8000 en lugar de localhost

### La base de datos da error
**Solución:**
```bash
# Elimina la base de datos vieja
rm data/pipeline.sqlite

# Crea una nueva
python init_database.py
```

---

## 📞 Próximos Pasos

Una vez que tengas FASE 14 corriendo:

### Para tu cliente potencial:
1. Comparte el acceso: `http://[Tu-IP-Local]:8000`
2. Dale acceso a un cliente de prueba
3. Recopila feedback con el formulario (CLIENTE_FEEDBACK_FORM.md)

### Para ti:
1. Prueba las funciones principales
2. Verifica que los emails se envíen correctamente
3. Revisa el dashboard en móvil
4. Documenta los cambios que el cliente pide

---

## 🎓 Entender la estructura

No necesitas memorizar esto, pero útil saber:

```
C:\FelixAutomation\
├── backend/              ← El servidor (main.py)
├── frontend/             ← Las páginas que ves en el navegador
├── agents/               ← Los "robots" que automatizan tareas
├── analytics/            ← Predicciones y análisis ML
├── data/                 ← Dónde se guardan los datos
│   └── pipeline.sqlite   ← Base de datos (archivo único)
├── init_database.py      ← Script para crear la BD
└── requirements.txt      ← Lista de librerías necesarias
```

---

## ✅ Checklist Final

Antes de compartir con tu cliente:

- [ ] El servidor inicia sin errores
- [ ] Puedes acceder a http://localhost:8000
- [ ] El dashboard muestra datos
- [ ] Puedes ver clientes en la lista
- [ ] Los gráficos se cargan correctamente
- [ ] El sistema responde rápido

Si todas las opciones están marcadas, **¡estás listo para invitar a tu cliente!**

---

## 🎉 ¡Felicidades!

Ahora tienes un sistema de automatización de ventas completo corriendo en tu PC local, sin costos de hosting.

Pruébalo con tu cliente potencial y recopila feedback sobre qué cambios quiere.

**Contacto:** Si tienes dudas: felipe@enbuenamesa.com

---

*Última actualización: 6 de Octubre, 2026*  
*Para: FASE 14 v14.0.0*
