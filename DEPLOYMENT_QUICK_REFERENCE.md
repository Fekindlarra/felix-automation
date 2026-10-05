# ⚡ REFERENCIA RÁPIDA - Despliegue Felix Automation
## Para tener a mano durante el despliegue

**Duración:** ~2.5-3 horas | **Versión:** 11.0 | **Fecha:** 2026-10-05

---

## 🚀 COMANDOS RÁPIDOS (Copia y Pega)

### 1. CONEXIÓN INICIAL (1 min)
```bash
ssh root@<DROPLET_IP>
passwd  # Cambiar password
```

### 2. PREPARACIÓN (10 min)
```bash
sudo apt-get update && sudo apt-get upgrade -y
cd /home && git clone <REPO_URL> felix-automation
cd felix-automation && ls -la  # Verificar setup.sh
```

### 3. SETUP AUTOMATIZADO (20 min)
```bash
cd /home/felix-automation
sudo bash setup.sh
# ⏳ Esperar a que termine (15-30 min)
# ✓ Verifica: "SETUP COMPLETADO EXITOSAMENTE"
```

### 4. GENERAR CLAVES (2 min)
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"  # SECRET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # WHITEBOX_MASTER_KEY
# Guardar ambas
```

### 5. EDITAR .env (5 min)
```bash
sudo nano /opt/felix-automation/.env
```

**Valores a editar:**
```
DATABASE_URL=postgresql://felix_user:PASSWORD@localhost:5432/felix_prod
SECRET_KEY=<pegar key #1>
WHITEBOX_MASTER_KEY=<pegar key #2>
SENDGRID_API_KEY=<tu-sendgrid-key>
ADMIN_EMAIL=felipe@enbuenamesa.com
```

### 6. CONFIGURAR PostgreSQL (3 min)
```bash
sudo -u postgres psql
ALTER USER felix_user WITH PASSWORD 'PASSWORD';
\q
```

### 7. PERMISOS .env (1 min)
```bash
sudo chown felix:felix /opt/felix-automation/.env
sudo chmod 600 /opt/felix-automation/.env
```

### 8. INICIAR SERVICIOS (2 min)
```bash
sudo systemctl start felix-api.service
sleep 3
sudo systemctl status felix-api.service  # Debe decir "active (running)"
curl http://localhost:8000/health  # Debe retornar OK
```

### 9. TEST END-TO-END (5 min)
```bash
cd /opt/felix-automation
sudo -u felix source venv/bin/activate
python test_end_to_end_complete.py
# Esperado: 90% éxito (9/10)
```

### 10. SSL CON CERTBOT (10 min)
```bash
sudo certbot certonly --nginx -d tu-dominio.com
# Esperar validación DNS
```

### 11. ACTUALIZAR NGINX CON SSL (2 min)
```bash
sudo nano /etc/nginx/sites-available/felix-automation
# Descomenta líneas 411-412 (ssl_certificate...)
sudo nginx -t
sudo systemctl restart nginx
```

### 12. VERIFICAR HTTPS (1 min)
```bash
curl -I https://tu-dominio.com/health  # Debe retornar 200
```

### 13. CONFIGURAR MONITOREO (5 min)
```bash
sudo docker run -d --name uptime-kuma --restart always \
  -p 3001:3001 -v uptime-kuma:/app/data \
  louislam/uptime-kuma:latest
# Acceder: https://tu-dominio.com:3001
```

---

## ✅ CHECKLIST COMPRIMIDA

### Pre-Deploy
- [ ] Droplet activo + IP registrada
- [ ] SSH acceso + password cambiado
- [ ] Dominio DNS apuntando a IP
- [ ] SendGrid API key listo
- [ ] setup.sh descargado

### Deploy
- [ ] Git clone completado
- [ ] setup.sh ejecutado exitosamente
- [ ] .env editado con valores
- [ ] PostgreSQL password actualizado
- [ ] Servicios iniciados (felix-api running)
- [ ] Health check retorna 200 OK
- [ ] Test end-to-end 90%+ éxito

### SSL & Seguridad
- [ ] Certbot certificado emitido
- [ ] Nginx SSL configurado
- [ ] HTTPS redirección funcionando
- [ ] curl -I https://tu-dominio.com/health → 200

### Monitoreo
- [ ] Uptime Kuma instalado
- [ ] Health check configurado
- [ ] Email alerts para Felipe

---

## 🆘 TROUBLESHOOTING 30s

| Problema | Comando | Fix |
|----------|---------|-----|
| ❌ Health check falla | `curl http://localhost:8000/health` | `sudo systemctl restart felix-api` |
| ❌ PostgreSQL error | `sudo systemctl status postgresql` | `sudo systemctl restart postgresql` |
| ❌ Port 8000 en uso | `sudo lsof -i :8000` | `sudo systemctl restart felix-api` |
| ❌ Nginx error | `sudo nginx -t` | Ver `/var/log/nginx/error.log` |
| ❌ SSL falla | `sudo certbot certonly --nginx -d domain` | Editar `/etc/nginx/sites-available/felix-automation` |

---

## 📊 LOGS ÚTILES

```bash
# En tiempo real
sudo journalctl -u felix-api -f

# Últimas 50 líneas
sudo tail -50 /var/log/felix/error.log

# Errores PostgreSQL
sudo tail -50 /var/log/postgresql/postgresql.log

# Errores Nginx
sudo tail -50 /var/log/nginx/error.log
```

---

## 🎯 VERIFICACIÓN FINAL

```bash
# 1. Servicios running
sudo systemctl status felix-api

# 2. Health check
curl -s https://tu-dominio.com/health | jq

# 3. Base de datos conecta
sudo -u felix psql -h localhost -U felix_user -d felix_prod -c "SELECT 1"

# 4. Logs sin errores
sudo tail -20 /var/log/felix/error.log

# 5. Memoria/CPU
free -h && uptime
```

---

## 📱 AVISOS IMPORTANTES

⚠️ **ANTES de setup.sh:**
- [ ] Tienes los valores para .env
- [ ] Tienes acceso SSH root
- [ ] Dominio DNS apuntando

⚠️ **DESPUÉS de setup.sh:**
- [ ] NO olvides editar .env con valores reales
- [ ] NO dejes PASSWORD por defecto en PostgreSQL
- [ ] NO expongas .env a internet

⚠️ **DESPUÉS de deploy:**
- [ ] Guardar contraseña PostgreSQL en lugar seguro
- [ ] Hacer primer backup: `pg_dump felix_prod > backup.sql`
- [ ] Informar a Felipe que está LIVE

---

**Contacto:** felipe@enbuenamesa.com  
**Doc Completa:** `DEPLOYMENT_READINESS_CHECKLIST.md`

