# FASE 9 - QUICK START GUIDE

## Setup Inicial

### 1. Definir Master Key (Producción)

```bash
# En tu shell o en variables de entorno de producción
export WHITEBOX_MASTER_KEY="CsXwABsetOW6UO87dlkyKDxCU5xtkL_IL1pwc7vtIMk="
# O genera una nueva:
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Verificar Configuración

```bash
grep -A 50 "^whitebox:" config.yaml
# Verificar que está habilitado:
# whitebox_enabled: true
```

### 3. Ejecutar Tests

```bash
python3 test_whitebox_integration.py
# Esperado: ✅ 4/4 TESTS PASSED
```

---

## Uso Básico

### Black-Box (Original OPCIÓN C)

```python
from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()
agent = MultiPlatformAuditorAgent(orch)

# Auditar cliente en Web + Facebook + Google
results = agent.audit_client(client_id=1)
# → {"web": {...}, "facebook_ads": {...}, "google_ads": {...}}

orch.close_database()
```

### White-Box (FASE 9 - Nuevo)

```python
# SHOPIFY
shopify_creds = {
    "store_url": "mystore.myshopify.com",
    "access_token": "shpat_xxxxx",
    "api_version": "2024-01"  # Optional
}
result = agent.audit_client_whitebox(1, "shopify", shopify_creds)
# → {"score": 79, "findings": {...}, "status": "completed"}

# JUMPSELLER
jumpseller_creds = {
    "store_id": "mitienda",
    "api_key": "js_xxxxx",
    "api_version": "2.0"  # Optional
}
result = agent.audit_client_whitebox(1, "jumpseller", jumpseller_creds)
# → {"score": 86, "findings": {...}, "status": "completed"}

# CODE/REPOSITORY
code_creds = {
    "repo_url": "https://github.com/user/repo",
    "ssh_host": "code.example.com",
    "ssh_user": "deploy",
    "ssh_password": "password"  # O ssh_key_path en lugar de password
}
result = agent.audit_client_whitebox(1, "code", code_creds)
# → {"score": 80, "findings": {...}, "status": "completed"}

# ✅ Credenciales automáticamente eliminadas de memoria
```

---

## Estructura de Datos

### Audit Result Structure

```python
{
    "client_id": 1,
    "platform": "shopify|jumpseller|code",
    "audit_type": "whitebox",
    "timestamp": "2026-10-05T12:50:45.541168",
    "score": 79,  # 0-100
    "status": "completed|failed",
    "findings": {
        "category_1": {...},
        "category_2": {...},
        # ... más categorías
    },
    "error": None  # Si status es "failed"
}
```

### Por Plataforma

**Shopify findings:**
```python
{
    "configuration": {...},
    "performance": {...},
    "security": {...},
    "integrations": {...},
    "seo": {...}
}
```

**Jumpseller findings:**
```python
{
    "configuration": {...},
    "products": {...},
    "transactions": {...},
    "integrations": {...},
    "security": {...}
}
```

**Code findings:**
```python
{
    "architecture": {...},
    "security": {...},
    "performance": {...},
    "best_practices": {...},
    "dependencies": {...}
}
```

---

## Credentials Manager - Uso Directo

### Encriptar/Desencriptar

```python
from whitebox.credentials_manager import CredentialsManager

manager = CredentialsManager(ttl_seconds=3600)

# Encriptar
creds = {"token": "shpat_xxx"}
encrypted = manager.encrypt_credentials("shopify", creds)

# Desencriptar
decrypted = manager.decrypt_credentials("shopify")

# Estado
status = manager.get_credentials_status()

# Limpiar explícitamente
manager.cleanup_platform_credentials("shopify")
```

### Validar Credenciales

```python
# Shopify
is_valid = manager.validate_shopify_token("shpat_1234...")

# Jumpseller
is_valid = manager.validate_jumpseller_key("js_abc...")

# SSH
is_valid = manager.validate_ssh_credentials(
    ssh_host="code.example.com",
    ssh_user="deploy",
    ssh_password="xxx"  # O ssh_key_path
)
```

---

## Auditors - Uso Directo

### Shopify Auditor

```python
from whitebox.shopify_auditor import ShopifyAuditor
from orchestrator import FelixAutomationOrchestrator

orch = FelixAutomationOrchestrator()
orch.connect_database()

auditor = ShopifyAuditor(orch)
result = auditor.audit_client(
    client_id=1,
    shopify_config={
        "store_url": "example.myshopify.com",
        "access_token": "shpat_xxxx"
    }
)

print(f"Score: {result['score']}/100")
```

### Jumpseller Auditor

```python
from whitebox.jumpseller_auditor import JumpsellerAuditor

auditor = JumpsellerAuditor(orch)
result = auditor.audit_client(
    client_id=1,
    jumpseller_config={
        "store_id": "mitienda",
        "api_key": "js_xxxx"
    }
)

print(f"Score: {result['score']}/100")
```

### Code Auditor

```python
from whitebox.code_auditor import CodeAuditor

auditor = CodeAuditor(orch)
result = auditor.audit_client(
    client_id=1,
    code_config={
        "repo_url": "https://github.com/client/project",
        "ssh_host": "code.example.com",
        "ssh_user": "deploy",
        "ssh_password": "xxxx"
    }
)

print(f"Score: {result['score']}/100")
```

---

## Troubleshooting

### Error: WHITEBOX_MASTER_KEY not found

```
⚠️  No WHITEBOX_MASTER_KEY found. Generar nueva clave:
    export WHITEBOX_MASTER_KEY=...
```

**Solución:**
```bash
# Genera una clave nueva
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Exporta en tu entorno
export WHITEBOX_MASTER_KEY="the_key_from_above"

# O déjala en config.yaml (inseguro en producción)
```

### Error: Credenciales expiradas

Si ves "Credenciales expiradas", es porque:
1. Pasó más de 1 hora desde que se almacenaron
2. TTL se cumplió y se limpiaron automáticamente

**Solución:**
- Solicita las credenciales al cliente de nuevo
- O incrementa TTL en config.yaml (no recomendado)

### Error: Token inválido

```
❌ Token de Shopify inválido (muy corto)
⚠️ Token de Shopify no comienza con 'shpat_'
```

**Solución:**
- Verifica que el token es correcto
- Para Shopify: debe empezar con `shpat_`
- Para Jumpseller: debe ser API key válida

---

## Performance Tips

### Reduce TTL para Mayor Seguridad

```yaml
# config.yaml
whitebox:
  ttl_seconds: 1800  # 30 minutos en lugar de 1 hora
```

### Aumenta TTL para Menos Re-autenticación

```yaml
whitebox:
  ttl_seconds: 7200  # 2 horas
```

### Ajusta Timeouts por Plataforma

```yaml
whitebox:
  shopify:
    timeout: 120  # Aumentar si Shopify es lenta
  code:
    timeout: 180  # Más tiempo para análisis de código
```

---

## Ejemplos Completos

### Pipeline Completo: Black-Box + White-Box

```python
from orchestrator import FelixAutomationOrchestrator
from agents.multi_platform_auditor_agent import MultiPlatformAuditorAgent

orch = FelixAutomationOrchestrator()
orch.connect_database()
agent = MultiPlatformAuditorAgent(orch)

client_id = 1

# 1. Black-Box (Web + Ads)
print("1. Ejecutando Black-Box Audits...")
black_box = agent.audit_client(client_id, platforms=['web', 'facebook_ads', 'google_ads'])
print(f"   Web: {black_box['web']['overall_score']}/100")
print(f"   Facebook: {black_box['facebook_ads']['overall_score']}/100")
print(f"   Google: {black_box['google_ads']['overall_score']}/100")

# 2. White-Box (si cliente proporciona credenciales)
print("\n2. Ejecutando White-Box Audits...")

# Shopify
shopify_result = agent.audit_client_whitebox(
    client_id,
    "shopify",
    {"store_url": "...", "access_token": "shpat_..."}
)
print(f"   Shopify: {shopify_result['score']}/100")

# Jumpseller
jumpseller_result = agent.audit_client_whitebox(
    client_id,
    "jumpseller",
    {"store_id": "...", "api_key": "js_..."}
)
print(f"   Jumpseller: {jumpseller_result['score']}/100")

# Code
code_result = agent.audit_client_whitebox(
    client_id,
    "code",
    {"repo_url": "...", "ssh_host": "...", "ssh_user": "deploy", "ssh_password": "..."}
)
print(f"   Code: {code_result['score']}/100")

# 3. Resultado: 3 Black-Box + 3 White-Box audits en BD
print("\n✅ Auditorías completadas - Credenciales limpias")

orch.close_database()
```

---

## Monitoreo en Producción

### Logs a Revisar

```bash
# Logs del sistema
tail -f data/logs/sistema.log

# Logs de auditorios
tail -f data/logs/auditors.log

# Logs de White-Box
tail -f data/logs/whitebox.log
```

### Métricas a Monitorear

```python
# Ver estado de credenciales almacenadas
status = manager.get_credentials_status()
for platform, info in status.items():
    print(f"{platform}: expires in {info['expires_in_seconds']}s")

# Ver audits guardados
audits = orch.get_audit_history(client_id=1, limit=10)
for audit in audits:
    print(f"{audit.platform}: {audit.score}/100 ({audit.status})")
```

---

## Archivos Clave

- `whitebox/credentials_manager.py` - Encriptación
- `whitebox/shopify_auditor.py` - Shopify
- `whitebox/jumpseller_auditor.py` - Jumpseller
- `whitebox/code_auditor.py` - Análisis código
- `agents/multi_platform_auditor_agent.py` - Integración
- `config.yaml` - Configuración
- `test_whitebox_integration.py` - Testing

---

**Última actualización:** 2026-10-05  
**Status:** ✅ PRODUCCIÓN-LISTA
