# 📚 Database Migration Guide - SQLite → PostgreSQL

**Versión:** FASE 11  
**Fecha:** 2026-10-05  
**Propósito:** Migración segura a PostgreSQL para producción  

---

## 📋 Pre-Migración Checklist

- [ ] Backup completo de `data/pipeline.db` realizado
- [ ] PostgreSQL 13+ instalado en servidor
- [ ] Usuario `felix_user` creado en PostgreSQL
- [ ] Base de datos `felix_prod` creada
- [ ] Credenciales verificadas
- [ ] Script de migración testeado en ambiente de staging
- [ ] Team notificado del mantenimiento

---

## 🔄 Procedimiento de Migración

### PASO 1: Backup Pre-Migración

```bash
# Backup SQLite
cd /home/claude/felix-automation
mkdir -p backups
cp data/pipeline.db backups/pipeline.db.backup.$(date +%Y%m%d_%H%M%S)

# Backup PostgreSQL (después de crear BD)
pg_dump -U felix_user -h localhost felix_prod > backups/felix_prod_pre_migration.sql
```

### PASO 2: Configurar PostgreSQL

```bash
# Conectar como postgres
sudo -u postgres psql

# Crear usuario
CREATE USER felix_user WITH PASSWORD 'your_strong_password_here';

# Crear database
CREATE DATABASE felix_prod OWNER felix_user;

# Dar permisos
GRANT ALL PRIVILEGES ON DATABASE felix_prod TO felix_user;
GRANT CREATE ON SCHEMA public TO felix_user;

# Salir
\q

# Verificar conexión
psql postgresql://felix_user:password@localhost:5432/felix_prod -c "SELECT version();"
```

### PASO 3: Ajustar Variables de Entorno

```bash
# Editar .env
nano /home/claude/felix-automation/.env

# Cambiar/agregar estas líneas:
DATABASE_TYPE=postgresql
DATABASE_URL=postgresql://felix_user:password@localhost:5432/felix_prod
SQLITE_BACKUP_PATH=data/pipeline.db

# Guardar (Ctrl+O, Enter, Ctrl+X)
chmod 600 .env
```

### PASO 4: Ejecutar Migración

```bash
cd /home/claude/felix-automation

# Activar environment
source venv/bin/activate

# Instalar dependencia PostgreSQL (si no está)
pip install psycopg2-binary

# Ejecutar script de migración
python scripts/migrate_to_postgresql.py "postgresql://felix_user:password@localhost:5432/felix_prod"

# Esperado:
# ============================================================
# FELIX AUTOMATION - DATABASE MIGRATION (SQLite → PostgreSQL)
# ============================================================
# ✓ Created table: clients
# ✓ Created table: pipeline
# ✓ Created table: audits
# ...
# ✓ MIGRATION SUCCESSFUL!
# ============================================================
# SUMMARY:
#   Tables migrated: 5
#   Total rows: 324
#   Errors: 0
# ============================================================
```

### PASO 5: Validar Datos

```bash
# Conectar a PostgreSQL
psql postgresql://felix_user:password@localhost:5432/felix_prod

# Verificar tablas
\dt

# Verificar datos
SELECT COUNT(*) FROM clients;
SELECT COUNT(*) FROM pipeline;
SELECT COUNT(*) FROM audits;

# Ver estructura de tabla
\d clients

# Salir
\q
```

### PASO 6: Actualizar Aplicación

```bash
# Editar orchestrator.py si es necesario
nano /home/claude/felix-automation/orchestrator.py

# Cambiar:
# db_type = "sqlite"  →  db_type = "postgresql"
# O usa variable de entorno: os.getenv('DATABASE_TYPE', 'sqlite')

# Reiniciar servicio
sudo systemctl restart felix-api

# Verificar logs
sudo journalctl -u felix-api -f
```

### PASO 7: Smoke Tests

```bash
# Test básico
cd /home/claude/felix-automation
source venv/bin/activate

python << 'PYTEST'
from orchestrator import FelixAutomationOrchestrator

# Conectar
orch = FelixAutomationOrchestrator()
orch.connect_database()

# Validar conexión
try:
    clients = orch.get_all_clients()
    print(f"✓ Database connected successfully")
    print(f"✓ Found {len(clients)} clients")
except Exception as e:
    print(f"✗ Error: {e}")
finally:
    orch.close_database()
PYTEST
```

---

## 🔙 Rollback (En Caso de Emergencia)

Si algo sale mal durante la migración:

### Opción 1: Revertir a SQLite (Rápido)

```bash
# Restaurar archivo original
cp backups/pipeline.db.backup.YYYYMMDD_HHMMSS data/pipeline.db

# Revertir .env a SQLite
nano /home/claude/felix-automation/.env
# Cambiar DATABASE_TYPE=sqlite

# Reiniciar
sudo systemctl restart felix-api

# Verificar logs
sudo tail -50 /var/log/felix/error.log
```

### Opción 2: Restaurar PostgreSQL desde Backup

```bash
# Conectar como postgres
sudo -u postgres psql

# Dropear database
DROP DATABASE felix_prod;

# Crear nueva
CREATE DATABASE felix_prod OWNER felix_user;
GRANT ALL PRIVILEGES ON DATABASE felix_prod TO felix_user;
\q

# Restaurar desde backup
psql -U felix_user -d felix_prod < backups/felix_prod_pre_migration.sql

# Verificar
psql postgresql://felix_user:password@localhost:5432/felix_prod -c "SELECT COUNT(*) FROM clients;"
```

---

## 🧪 Testing Post-Migración

### Test 1: Verificar Integridad de Datos

```bash
# Comparar row counts entre SQLite y PostgreSQL
python << 'PYTEST'
import sqlite3
import psycopg2

# SQLite
sqlite_conn = sqlite3.connect('data/pipeline.db')
sqlite_cursor = sqlite_conn.cursor()

# PostgreSQL
pg_conn = psycopg2.connect("postgresql://felix_user:password@localhost:5432/felix_prod")
pg_cursor = pg_conn.cursor()

tables = ['clients', 'pipeline', 'audits', 'email_logs', 'followups']

print("Validando integridad de datos:")
for table in tables:
    sqlite_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    sqlite_count = sqlite_cursor.fetchone()[0]
    
    pg_cursor.execute(f"SELECT COUNT(*) FROM {table}")
    pg_count = pg_cursor.fetchone()[0]
    
    status = "✓" if sqlite_count == pg_count else "✗"
    print(f"  {status} {table}: SQLite={sqlite_count}, PostgreSQL={pg_count}")

sqlite_conn.close()
pg_conn.close()
PYTEST
```

### Test 2: Verificar Performance

```bash
# Medir tiempo de query
psql postgresql://felix_user:password@localhost:5432/felix_prod << 'PSQL'
-- Clients activos
\timing on
SELECT COUNT(*) FROM clients WHERE active = true;

-- Pipeline summary
SELECT stage, COUNT(*) FROM pipeline GROUP BY stage;

-- Top performers
SELECT email_sender_performance, COUNT(*) FROM pipeline GROUP BY email_sender_performance;
\timing off
PSQL
```

### Test 3: Ejecutar Pipeline Completo

```bash
cd /home/claude/felix-automation
source venv/bin/activate

# Test end-to-end
python test_end_to_end_complete.py

# Esperado:
# ✓ Test 1: Database Connection
# ✓ Test 2: Client Reading
# ✓ Test 3: Audits Execution
# ✓ Test 4: Proposal Generation
# ✓ Test 5: Email Sending (demo mode)
# ✓ Test 6: Pipeline Updates
# All tests passed!
```

---

## 📊 Schema Definitivo (PostgreSQL)

```sql
-- Clientes
CREATE TABLE clients (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    website TEXT,
    industry TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN DEFAULT true
);

-- Pipeline de Ventas
CREATE TABLE pipeline (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    stage TEXT NOT NULL, -- prospecto, propuesta, negociacion, cerrado
    entry_date TIMESTAMP,
    exit_date TIMESTAMP,
    days_in_stage INTEGER,
    conversion_likelihood NUMERIC(5,2),
    estimated_revenue NUMERIC(10,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Auditorías
CREATE TABLE audits (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    platform TEXT, -- web, facebook_ads, google_ads, shopify, jumpseller, code
    score INTEGER,
    findings JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Logs
CREATE TABLE email_logs (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    subject TEXT,
    status TEXT, -- sent, bounced, opened, clicked
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Follow-ups
CREATE TABLE followups (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES clients(id),
    sequence_number INTEGER,
    scheduled_date DATE,
    sent_date TIMESTAMP,
    response_received BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## ⚙️ Optimizaciones Post-Migración

```bash
# Analizar y optimizar
psql postgresql://felix_user:password@localhost:5432/felix_prod << 'PSQL'
-- Analizar tablas
ANALYZE;

-- Ver tamaño de base de datos
SELECT pg_size_pretty(pg_database_size('felix_prod'));

-- Ver tamaño por tabla
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
PSQL
```

---

## 📝 Logging de Migración

Todo el proceso se registra en `data/logs/migration.log`:

```
2026-10-05 14:23:45 - INFO - Connected to SQLite: data/pipeline.db
2026-10-05 14:23:46 - INFO - Connected to PostgreSQL
2026-10-05 14:23:47 - INFO - Created table: clients
2026-10-05 14:23:48 - INFO - Migrated 324 rows
2026-10-05 14:23:50 - INFO - ✓ MIGRATION SUCCESSFUL!
```

---

## ⚠️ Troubleshooting

### Error: "role does not exist"
```bash
# Recrear usuario PostgreSQL
sudo -u postgres psql
CREATE USER felix_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE felix_prod TO felix_user;
```

### Error: "permission denied"
```bash
# Verificar permisos
sudo -u postgres psql -d felix_prod
GRANT ALL ON SCHEMA public TO felix_user;
GRANT ALL ON ALL TABLES IN SCHEMA public TO felix_user;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO felix_user;
```

### Error: "connection refused"
```bash
# Verificar PostgreSQL está corriendo
sudo systemctl status postgresql

# Reiniciar si es necesario
sudo systemctl restart postgresql

# Verificar puerto 5432
sudo netstat -tuln | grep 5432
```

---

## ✅ Post-Migración Checklist

- [ ] Todos los datos migrados correctamente
- [ ] Smoke tests pasando
- [ ] Performance similar o mejor
- [ ] Backups verificados
- [ ] Documentación actualizada
- [ ] Team capacitado
- [ ] Monitoreo verificando PostgreSQL
- [ ] Alertas configuradas

---

**Soporte:** Felipe (@enbuenamesa.com)  
**En caso de problemas:** Contactar inmediatamente - Rollback disponible
