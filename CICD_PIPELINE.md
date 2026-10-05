# 🚀 CI/CD Pipeline Guide - GitHub Actions

**Versión:** FASE 11  
**Fecha:** 2026-10-05  
**Propósito:** Automatización completa de testing, building y deployment  

---

## 🎯 Pipeline Overview

```
Push to GitHub
    ↓
[1. Tests & Validation] ─→ Unit tests, E2E tests, Load testing
    ↓
[2. Security Checks] ──→ Bandit, Safety, Dependency scan
    ↓
[3. Build & Push] ────→ Docker image build to GitHub Container Registry
    ↓
[4. Deploy Staging] ──→ Automatic deployment to staging (main branch)
    ↓
[5. Deploy Production] → Manual trigger or production branch push
    ↓
[6. Monitoring] ──────→ Post-deployment smoke tests
```

---

## 🔧 Setup & Configuration

### PASO 1: Preparar Repositorio GitHub

```bash
# 1. Crear repositorio en GitHub (si no existe)
# https://github.com/new

# 2. Clonar
git clone https://github.com/tu-usuario/felix-automation.git
cd felix-automation

# 3. Verificar workflow está en lugar correcto
ls -la .github/workflows/production.yml
```

### PASO 2: Configurar Secrets en GitHub

Ir a: **Repo Settings → Secrets and variables → Actions**

Crear estos secrets:

```
STAGING_HOST = staging.tu-dominio.com
STAGING_USER = ubuntu
STAGING_DEPLOY_KEY = (SSH private key)

PRODUCTION_HOST = prod.tu-dominio.com
PRODUCTION_USER = ubuntu
PRODUCTION_DEPLOY_KEY = (SSH private key)
```

**Cómo generar SSH keys:**

```bash
# Generar par de claves
ssh-keygen -t ed25519 -f deploy_key -C "github-actions" -N ""

# Copiar public key al servidor
cat deploy_key.pub

# Agregar a ~/.ssh/authorized_keys en servidor staging/production
cat deploy_key.pub >> ~/.ssh/authorized_keys

# Copiar private key como secret
cat deploy_key
# (copiar contenido a STAGING_DEPLOY_KEY y PRODUCTION_DEPLOY_KEY)

# Limpiar
rm deploy_key deploy_key.pub
```

### PASO 3: Actualizar Variables en Workflow

Editar `.github/workflows/production.yml`:

```yaml
# Reemplazar:
environment:
  name: production
  url: https://your-domain.com  ← Tu dominio aquí

# En los pasos de health check:
curl https://your-domain.com/health  ← Tu dominio aquí
```

### PASO 4: Crear Branches de Deployment

```bash
# Main branch - para staging
git checkout -b main
git push -u origin main

# Production branch - para production
git checkout -b production
git push -u origin production

# Development branch - para feature branches
git checkout -b develop
git push -u origin develop
```

---

## 🔄 Flujo de Trabajo

### Opción A: Desarrollo Normal (Auto-deploy a Staging)

```bash
# 1. Crear feature branch
git checkout -b feature/nueva-funcionalidad

# 2. Hacer cambios
vim agents/lead_scorer_agent.py
# ... ediciones ...

# 3. Commit y push
git add .
git commit -m "Feat: Mejorar scoring de leads"
git push origin feature/nueva-funcionalidad

# 4. Crear Pull Request en GitHub
# → GitHub Actions ejecuta tests automáticamente

# 5. Si tests pasan, merge a main
# → Pipeline ejecuta tests completos
# → Deploys a staging automáticamente
# → Puedes revisar en https://staging.tu-dominio.com

# 6. Cuando esté listo para producción
git checkout production
git merge main
git push origin production
# → Pipeline pide confirmación manual
# → Deploy a producción inicia
```

### Opción B: Deploy Directo a Producción (Manual)

```bash
# 1. Ir a GitHub Actions
# https://github.com/tu-usuario/felix-automation/actions

# 2. Seleccionar "Production Deploy"

# 3. Click "Run workflow" → "production" branch

# 4. Esperar a que complete
# (aproximadamente 10-15 minutos)
```

---

## 📊 Componentes del Pipeline

### JOB 1: Tests & Validation

**Qué hace:**
- Inicia PostgreSQL en un container
- Ejecuta pylint y flake8
- Ejecuta unit tests con pytest
- Ejecuta end-to-end tests
- Ejecuta load testing
- Sube reporte de coverage

**Artifacts generados:**
- `test-results/load_test_*.json`
- `test-results/load_test_*.csv`

**Condición de fallo:**
- Cualquier test falla
- Coverage < 70%
- Load test falla

---

### JOB 2: Security Checks

**Qué hace:**
- Bandit security scanning
- Safety dependency checking
- Grep para credenciales hardcodeadas

**Artifacts generados:**
- `bandit-report.json`

**Condición de fallo:**
- Credenciales encontradas en código
- Vulnerabilidades críticas detectadas

---

### JOB 3: Build & Push

**Qué hace:**
- Construye Docker image
- Lo sube a GitHub Container Registry
- Taguea con: branch name, version, SHA

**Requisitos:**
- Los dos jobs anteriores deben pasar
- Solo en push a main o production

**Image tags generados:**
```
ghcr.io/tu-usuario/felix-automation:main
ghcr.io/tu-usuario/felix-automation:v1.0.0
ghcr.io/tu-usuario/felix-automation:sha-a1b2c3d
```

---

### JOB 4: Deploy to Staging

**Qué hace:**
- Conecta al servidor staging via SSH
- Descarga código más reciente
- Instala dependencias
- Ejecuta migraciones BD
- Reinicia servicio
- Verifica health check

**Requisitos:**
- Job 1, 2, 3 deben pasar
- Solo en push a main branch

**Servidor esperado:**
- IP/Hostname en STAGING_HOST
- Usuario en STAGING_USER
- SSH key en STAGING_DEPLOY_KEY

---

### JOB 5: Deploy to Production

**Qué hace:**
- Igual a Staging pero con más validaciones
- Pide confirmación manual antes de deployar
- Crea backup de BD
- Reinicia servicio
- Verifica todos los endpoints críticos

**Requisitos:**
- Job 1, 2, 3 deben pasar
- Manual approval o push a production branch

**Environment protection:**
```
Una vez confirmado, deployment procede inmediatamente
```

---

### JOB 6: Monitoring

**Qué hace:**
- Ejecuta smoke tests en servidor en vivo
- Verifica endpoints críticos
- Reporta métricas de performance

**Requisitos:**
- Production deployment debe completar exitosamente

---

## 📈 Monitoring & Logs

### Ver logs de una ejecución

```bash
# Via GitHub web UI
# https://github.com/tu-usuario/felix-automation/actions

# O via GitHub CLI
gh run list --repo tu-usuario/felix-automation
gh run view <run-id> --repo tu-usuario/felix-automation

# Ver log de un job específico
gh run view <run-id> --log --repo tu-usuario/felix-automation
```

### Descargar artifacts

```bash
# Via CLI
gh run download <run-id> -D ./artifacts

# Via web UI
# Click en la ejecución → "Artifacts" → Descargar
```

---

## ⚠️ Troubleshooting

### Error: "Permission denied (publickey)"

**Problema:** SSH deploy key no está configurado correctamente

```bash
# Verificar:
# 1. Secret STAGING_DEPLOY_KEY existe
# 2. Public key está en ~/.ssh/authorized_keys del servidor
# 3. Permisos correctos: chmod 600 ~/.ssh/authorized_keys

# Solución:
ssh -i deploy_key ubuntu@staging.tu-dominio.com "cat ~/.ssh/authorized_keys | grep github"
```

### Error: "Tests failed"

```bash
# Revisar logs del test en GitHub Actions
# Click en el step "Run unit tests"

# Ejecutar localmente para reproducir
python -m pytest tests/ -v

# Si está relacionado a BD:
docker run -d -p 5432:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test \
  postgres:15
pytest tests/ -v --tb=short
```

### Error: "Docker login failed"

**Problema:** Token GITHUB_TOKEN no está disponible

```bash
# Verificar en el archivo workflow:
# Este token se crea automáticamente y no necesita configuración

# Si sigue fallando:
# 1. Revisar permisos de repo en Settings → Actions
# 2. Asegurar que "Read and write permissions" está habilitado
```

### Error: "Deploy failed - health check failed"

```bash
# 1. SSH al servidor
ssh -i deploy_key ubuntu@prod.tu-dominio.com

# 2. Revisar logs del servicio
sudo journalctl -u felix-api -n 50

# 3. Verificar que el servicio está corriendo
sudo systemctl status felix-api

# 4. Revisar conectividad a BD
psql postgresql://felix_user:password@localhost/felix_prod -c "SELECT 1"

# 5. Revisar logs de nginx
sudo tail -50 /var/log/nginx/error.log
```

---

## 🔐 Security Best Practices

1. **Secrets Management**
   - Nunca commit secrets en código
   - Usar GitHub Secrets para credenciales
   - Rotar keys periódicamente

2. **SSH Keys**
   - Usar Ed25519 (más seguro que RSA)
   - Una key por ambiente (staging ≠ production)
   - Revocar keys cuando empleado se va

3. **Approval Process**
   - Production requiere aprobación manual
   - Revisar cambios antes de approve
   - Logging de quién aprobó y cuándo

4. **Secrets en Logs**
   - GitHub Actions enmascara valores de secrets
   - Pero sé cuidadoso con error messages
   - Nunca echoes credenciales en logs

---

## 📋 Checklist Pre-Deploy

- [ ] Todos los tests pasan localmente
- [ ] Código revisado por al menos una persona
- [ ] Load tests muestran performance aceptable
- [ ] Seguridad checks sin issues críticos
- [ ] Migraciones de BD probadas
- [ ] Rollback plan documentado
- [ ] Team notificado del deployment
- [ ] Backup de BD realizado (para production)
- [ ] Monitoring alerts activos

---

## 🔄 Rollback Procedure

Si algo sale mal en production:

```bash
# Opción 1: Rápido (via SSH)
ssh ubuntu@prod.tu-dominio.com

cd /opt/felix-automation
git checkout HEAD~1  # Revierte al commit anterior
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart felix-api

# Opción 2: Desde GitHub (re-run anterior workflow)
# Ir a Actions → Seleccionar run previo → "Re-run all jobs"

# Opción 3: Restaurar BD desde backup
sudo -u postgres psql
DROP DATABASE felix_prod;
CREATE DATABASE felix_prod OWNER felix_user;
\q

psql -U felix_user -d felix_prod < /backups/felix_prod_backup.sql
```

---

## 📊 Métricas & Reportes

### Coverage Report
Automáticamente publicado a Codecov.io después de cada run

### Performance Report
Guardado en artifacts como JSON y CSV

### Deployment Frequency
Visible en GitHub Insights → Deployments

### Mean Time to Deployment (MTTR)
Calculable desde historico de runs

---

## 🚀 Advanced: Custom Notifications

Agregar notificaciones a Slack/Discord:

```yaml
# En el job de cleanup, agregar:
- name: Notify Slack
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK }}
    payload: |
      {
        "text": "Deployment ${{ job.status }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*${{ job.status }}* - Production Deploy\n*Commit:* ${{ github.sha }}\n*Author:* ${{ github.actor }}"
            }
          }
        ]
      }
```

---

**Soporte:** Felipe (@enbuenamesa.com)  
**Documentación GitHub Actions:** https://docs.github.com/en/actions
